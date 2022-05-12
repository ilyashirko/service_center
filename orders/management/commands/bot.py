from textwrap import dedent

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
                                                 CHECK_PRICE_MESSAGE,
                                                 HELLO_MESSAGE,
                                                 REQUEST_CONFIRM)

from .db_processing import (add_message, create_new_request, get_devices_types, get_last_three_messages, get_request,
                            get_telegram_id_from_request)
from .keyboards import (ASK_FOR_PHONE_KEYBOARD, main_keyboard,
                        make_reply_keyboard)


class CheckPrice(StatesGroup):
    request = State()
    phone = State()
    
class RequestInfo(StatesGroup):
    uuid = State()
    message = State()
    detailes_ask = State()



class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **kwargs):
        env = Env()
        env.read_env()

        bot = Bot(token=env.str("TELEGRAM_BOT_TOKEN"), parse_mode=ParseMode.HTML)
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)


        @dp.message_handler(commands="main", state="*")
        @dp.message_handler(lambda message: message.text.lower() == "вернуться на главную", state="*")
        async def main_menu(message: Message, state: FSMContext):
            await state.finish()
            await message.answer(
                "Бежим на главную!",
                reply_markup=main_keyboard()
            )


        @dp.message_handler(commands="start")
        async def start(message: Message):
            await message.reply(HELLO_MESSAGE, reply_markup=main_keyboard())


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

        @dp.message_handler(
            state=CheckPrice.phone, content_types=ContentTypes.CONTACT
        )
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
            print(type(order_callback.new(key='request_response', uuid=request.uuid)))
            print(order_callback.new(key='request_response', uuid=request.uuid))
            await bot.send_message(
                434137786,
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
                        text="Ответить клиенту", callback_data=order_callback.new(key='request_response', uuid=request.uuid)
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
                reply_markup=ReplyKeyboardRemove()
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
                    f"""
                    Вам ответил мастер по заказу:
                    {request}

                    Сообщение:
                    {message.text}
                    """
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
        
        @dp.callback_query_handler(order_callback.filter(key='details_ask'))
        async def request_response(callback_query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext = RequestInfo):
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите что хотите уточнить.',
                reply_markup=ReplyKeyboardRemove()
            )
            await RequestInfo.detailes_ask.set()

        @dp.message_handler(state=RequestInfo.detailes_ask)
        async def response_message(message: Message, state: FSMContext):
            request_info = await state.get_data()
            uuid = request_info['uuid']
            user_telegram_id = await get_telegram_id_from_request(uuid)
            request = await get_request(uuid)
            await bot.send_message(
                434137786,
                text=dedent(
                    f"""
                    Сообщение от клиента!

                    Заявка: {request}

                    История переписки: {await get_last_three_messages(uuid)}

                    Сообщение: {message.text}
                    """
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Ответить клиенту", callback_data=order_callback.new(key='request_response', uuid=request.uuid)
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

        executor.start_polling(dp)
