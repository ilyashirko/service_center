from textwrap import dedent, indent
import requests

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (CallbackQuery, ContentTypes, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, ParseMode,
                           PreCheckoutQuery, ReplyKeyboardRemove)
from aiogram.utils.callback_data import CallbackData
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from environs import Env
from orders.management.commands.messages import (ASK_FOR_PHONE,
                                                 CHECK_PRICE_MESSAGE, HELLO_AGAIN_MESSAGE,
                                                 HELLO_MESSAGE,
                                                 REQUEST_CONFIRM, SUPPORT_REQUEST)

from .db_processing import (add_message, close_support_request, create_new_request, create_support_request, get_devices_types,
                            get_last_messages, get_request, get_support_request, get_telegram_id_from_foreignkey,
                            get_telegram_id_from_request, get_telegram_object)
from .keyboards import (ASK_FOR_PHONE_KEYBOARD, main_keyboard,
                        make_reply_keyboard)


class CheckPrice(StatesGroup):
    request = State()
    phone = State()
    
class RequestInfo(StatesGroup):
    uuid = State()
    message = State()
    detailes_ask = State()

class Support(StatesGroup):
    message = State()
    user_id = State()
    message = State()
    response = State()
    uuid = State()



class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **kwargs):
        env = Env()
        env.read_env()

        bot = Bot(token=env.str("TELEGRAM_BOT_TOKEN"), parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)


        @dp.message_handler(commands="main", state="*")
        @dp.message_handler(lambda message: message.text.lower() == "вернуться на главную",
                            state="*")
        async def main_menu(message: Message, state: FSMContext):
            await state.finish()
            await message.answer(
                "Бежим на главную!",
                reply_markup=main_keyboard()
            )


        @dp.message_handler(commands="start")
        async def start(message: Message):
            if await get_telegram_object(message.from_user.id):
                await message.reply(HELLO_AGAIN_MESSAGE, reply_markup=main_keyboard())
            else:
                await message.reply(HELLO_MESSAGE, reply_markup=main_keyboard())
                text = dedent(
                    f"""
                    Босс, у нас новый посетитель.

                    {message.from_user.first_name} ({message.from_user.id})
                    """
                )
                requests.get(
                    f"https://api.telegram.org/"
                    f"bot{env.str('ADMIN_BOT_TOKEN')}/sendMessage?"
                    f"chat_id={env.str('ADMIN_TELEGRAM_ID')}&text={text}"
                )


        @dp.message_handler(commands="check_price")
        @dp.message_handler(lambda message: message.text.lower() == "узнать стоимость ремонта")
        async def check_price(message: Message):
            await message.answer(CHECK_PRICE_MESSAGE, reply_markup=make_reply_keyboard())
            await CheckPrice.request.set()

        
        @dp.message_handler(state=CheckPrice.request)
        async def check_price_request(message: Message, state: FSMContext):
            await state.update_data(request=message.text)
            await message.answer(ASK_FOR_PHONE, reply_markup=ASK_FOR_PHONE_KEYBOARD)
            await CheckPrice.phone.set()


        order_callback = CallbackData("id", "uuid", "key")

        @dp.message_handler(state=CheckPrice.phone,
                            content_types=ContentTypes.CONTACT)
        async def check_price_phone(message: Message, state: FSMContext):
            user_data = await state.get_data()
            request = await create_new_request(
                user_telegram_id=message.from_user.id,
                message=user_data['request'],
                phone=message.contact.phone_number,
                user_name=message.from_user.username,
                first_name=message.from_user.first_name
            )
            await state.finish()
            
            await bot.send_message(
                env.int('ADMIN_TELEGRAM_ID'),
                dedent(
                    f"""
                    Новая заявка на ремонт!

                    Клиент: {message.from_user.first_name} ({message.from_user.username})
                    Телефон: {message.contact.phone_number}

                    Сообщение:
                    {user_data['request']}
                    """
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Ответить клиенту",
                        callback_data=order_callback.new(
                            key='request_response',
                            uuid=request.uuid
                        ),
                    )
                )
            )
            await message.answer(REQUEST_CONFIRM, reply_markup=main_keyboard())


        @dp.message_handler(state=CheckPrice.phone)
        async def invalid_number(message: Message, state: FSMContext):
            await message.reply(
                dedent(
                    """
                    Упс, не мгу разобрать номер.

                    Воспользуйтесь кнопкой "Отправить номер телефона" внизу экрана.
                    """
                ),
                reply_markup=ASK_FOR_PHONE_KEYBOARD
            )
            await CheckPrice.phone.set()

        
        @dp.callback_query_handler(order_callback.filter(key='request_response'))
        async def request_response(callback_query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext = RequestInfo):
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите сообщение для клиента...',
                reply_markup=make_reply_keyboard()
            )
            await RequestInfo.message.set()

        
        @dp.message_handler(state=RequestInfo.message)
        async def response_message(message: Message, state: FSMContext):
            request_info = await state.get_data()
            uuid = request_info['uuid']
            user_telegram_id = await get_telegram_id_from_request(uuid)
            request = await get_request(uuid)
            await add_message(uuid, message.text, True)
            await bot.send_message(
                user_telegram_id,
                text=dedent(
                    f"Вам ответил мастер по заказу:\n"
                    f"{request}\n\n"

                    f"Сообщение:\n"
                    f"{message.text}"
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Оформить заявку",
                        callback_data=order_callback.new(key='make_order', uuid=uuid)
                    ),
                    InlineKeyboardButton(
                        text="Уточнить детали",
                        callback_data=order_callback.new(key='details_ask', uuid=uuid)
                    ),
                    InlineKeyboardButton(
                        text="Запросить звонок",
                        callback_data=order_callback.new(key='phonecall_ask', uuid=uuid)
                    )
                )
            )
            await state.finish()
            await message.answer("Сообщение отправлено клиенту.", reply_markup=main_keyboard())
        

        @dp.callback_query_handler(order_callback.filter(key='details_ask'))
        async def request_response(callback_query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext = RequestInfo):
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите что хотите уточнить.',
                reply_markup=make_reply_keyboard()
            )
            await RequestInfo.detailes_ask.set()


        @dp.message_handler(state=RequestInfo.detailes_ask)
        async def response_message(message: Message, state: FSMContext):
            request_info = await state.get_data()
            uuid = request_info['uuid']
            user_telegram_id = await get_telegram_id_from_request(uuid)
            request = await get_request(uuid)
            extra = await get_last_messages(uuid, 3)
            await bot.send_message(
                env.int('ADMIN_TELEGRAM_ID'),
                text=(
                    f'Сообщение от клиента!\n\n'

                    f'Заявка: {request}\n\n'

                    f'Последние сообщения:\n'
                    f'{extra}'

                    f'\nСообщение: {message.text}'
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Ответить клиенту",
                        callback_data=order_callback.new(
                            key='request_response',
                            uuid=request.uuid
                        )
                    )
                )
            )
            await add_message(uuid, message.text, False)
            await message.answer(
                dedent(
                    """
                    Сообщение отправлено.
                    Ожидайте ответа.
                    """
                ),
                reply_markup=main_keyboard()
            )
            await state.finish()


        @dp.callback_query_handler(order_callback.filter(key='phonecall_ask'))
        async def phonecall_ask(callback_query: CallbackQuery,
                                callback_data: dict,
                                state: FSMContext = RequestInfo):
            request = await get_request(callback_data['uuid'])
            await bot.send_message(
                env.int('ADMIN_TELEGRAM_ID'),
                text="Клиент запросил обратный звонок!"
            )
            await bot.send_contact(
                env.int('ADMIN_TELEGRAM_ID'),
                phone_number=f'+{request.phone}',
                first_name=request.first_name,
            )

        support_callback = CallbackData('id', 'uuid', 'key')
        @dp.message_handler(commands='support')
        @dp.message_handler(lambda message: message.text.lower() == 'написать в поддержку')
        async def support(message: Message):
            await message.reply(SUPPORT_REQUEST, reply_markup=make_reply_keyboard())
            await Support.message.set()

        @dp.message_handler(state=Support.message)
        async def support_message(message: Message, state: FSMContext):
            if len(message.text) > 1000:
                await message.reply(dedent(
                    f"""
                    Ну я же просил не более 1000 символов.
                    
                    Вы набрали {len(message.text)}.
                    Попробуем еще раз, но чуть короче.
                    """
                ))
                await Support.message.set()
                return
            new_support_request = await create_support_request(message.from_user.id, message.text)
            await bot.send_message(
                env.int('ADMIN_TELEGRAM_ID'),
                dedent(
                    f"Новое обращение в техподдержку!\n\n"

                    f"Пользователь: {message.from_user.first_name} ({message.from_user.username})\n\n"
                    
                    f"Сообщение:\n"
                    f"{message.text}"
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Ответить пользователю",
                        callback_data=support_callback.new(
                            key='support_response',
                            uuid=new_support_request.uuid,
                        )
                    )
                )
            )
            await state.finish()
            await message.reply(
                dedent(
                    """
                    Сообщение отправлено.
                    Ожидайте ответа от администратора.
                    """
                ),
                reply_markup=main_keyboard()
            )
        
        
        @dp.callback_query_handler(support_callback.filter(key='support_response'))
        async def supporn_response_button(callback_query: CallbackQuery,
                                          callback_data: dict,
                                          state: FSMContext = Support):
            support_request = await get_support_request(callback_data['uuid'])
            telegram_object = await get_telegram_id_from_foreignkey(support_request)
            
            await state.update_data(user_id=telegram_object.telegram_id)
            await state.update_data(message=support_request.request)
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите ответ пользователю',
                reply_markup=make_reply_keyboard()
            )
            await Support.response.set()


        @dp.message_handler(state=Support.response)
        async def support_response(message: Message, state: FSMContext):
            support_info = await state.get_data()
            user_id = support_info['user_id']
            original_message = support_info['message']
            await bot.send_message(
                user_id,
                text=(
                    f'Вы обращались в техподдержку:\n'
                    f'"{original_message}".\n\n'
                    f'Ответ поддержки:\n'
                    f'{message.text}'
                )
            )
            await close_support_request(support_info['uuid'], message.text)
            await state.finish()
            

        @dp.message_handler()
        async def unknown_message(message: Message):
            await message.reply(
                dedent(
                    """Бот не поддерживает произвольные сообщения.
                    
                    Нажмите необходимую кнопку для связи с мастером или поддержкой.
                    """
                )
            )

        executor.start_polling(dp)
