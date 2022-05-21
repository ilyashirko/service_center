import logging
import time
import zipfile
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from textwrap import dedent

import requests
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (CallbackQuery, ContentTypes, InlineKeyboardButton,
                           InlineKeyboardMarkup, InputFile, Message, ParseMode)
from aiogram.utils.callback_data import CallbackData
from django.core.management.base import BaseCommand
from environs import Env
from orders.management.commands.messages import (ASK_FOR_PHONE,
                                                 CHECK_PRICE_MESSAGE,
                                                 HELLO_AGAIN_MESSAGE,
                                                 HELLO_MESSAGE,
                                                 REQUEST_CONFIRM,
                                                 SUPPORT_REQUEST)

from .db_processing import (add_message, assign_master_for_request,
                            close_support_request, create_new_request,
                            create_support_request, get_last_messages,
                            get_master_id_from_request,
                            get_masters_first_last_names, get_request,
                            get_support_request,
                            get_telegram_id_from_foreignkey,
                            get_telegram_id_from_request, get_telegram_object)
from .keyboards import (ASK_FOR_PHONE_KEYBOARD, main_keyboard,
                        make_reply_keyboard)

LOG_FILENAME = 'log.log'

order_callback = CallbackData("id", "uuid", "key")

support_callback = CallbackData("id", "uuid", "key")


class CheckPrice(StatesGroup):
    request = State()
    phone = State()


class RequestService(StatesGroup):
    uuid = State()
    message = State()
    detailes_ask = State()
    master = State()


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

        log = logging.getLogger(LOG_FILENAME)
        log.setLevel(logging.INFO)

        filehandler = logging.FileHandler(LOG_FILENAME)
        basic_formater = logging.Formatter('%(asctime)s : [%(levelname)s] : %(message)s')
        filehandler.setFormatter(basic_formater)
        log.addHandler(filehandler)

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
                log.info(f"NEW USER - {message.from_user.id}")


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
                        )
                    ),
                    InlineKeyboardButton(
                        text="Позвонить клиенту",
                        callback_data=order_callback.new(
                            key='phonecall',
                            uuid=request.uuid
                        )
                    ),
                    InlineKeyboardButton(
                        text="Назначить мастера",
                        callback_data=order_callback.new(
                            key='assign_master',
                            uuid=request.uuid
                        )
                    )
                )
            )
            await message.answer(REQUEST_CONFIRM, reply_markup=main_keyboard())
            log.info(f'NEW REQUEST - {request.uuid} | {message.contact.phone_number}')

            
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

        @dp.callback_query_handler(order_callback.filter(key='assign_master'))
        async def callback_assign_master(callback_query: CallbackQuery,
                                         callback_data: dict,
                                         state: FSMContext = RequestService):
            masters = await get_masters_first_last_names()
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                env.int('ADMIN_TELEGRAM_ID'),
                text="Какого мастера назначить на данную заявку?",
                reply_markup=make_reply_keyboard(masters, row_width=1)
            )
            await RequestService.master.set()


        @dp.message_handler(state=RequestService.master)
        async def assign_master(message: Message, state: FSMContext):
            request_state_data = await state.get_data()
            uuid = request_state_data['uuid']
            master_id = await assign_master_for_request(uuid, message.text)
            if not master_id:
                await message.answer(
                    "Мастер не назначен, проверьте код",
                    reply_markup=main_keyboard()
                )
                return

            request = await get_request(uuid)

            inline_buttons = [
                InlineKeyboardButton(
                    text="Ответить клиенту",
                    callback_data=order_callback.new(
                        key='request_response',
                        uuid=request.uuid
                    )
                ),
                InlineKeyboardButton(
                    text="Позвонить клиенту",
                    callback_data=order_callback.new(
                        key='phonecall',
                        uuid=request.uuid
                    )
                )
            ]
            if master_id == env.int("ADMIN_TELEGRAM_ID"):
                inline_buttons.append(
                    InlineKeyboardButton(
                        text="Назначить мастера",
                        callback_data=order_callback.new(
                            key='assign_master',
                            uuid=request.uuid
                        )
                    )
                )
            
            

            await bot.send_message(
                master_id,
                text=(
                    f'Вам назначена заявка на ремонт!\n\n'
                    f'Клиент: {request.user_name} ({request.first_name})\n\n'
                    f'Первичное сообщение:\n'
                    f'{request.request}\n\n'
                    f'История переписки:\n'
                    f'{await get_last_messages(uuid)}'
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(*inline_buttons)
            )
            await state.finish()
            await message.answer(
                f"На заявку\n{request}\nназначен {message.text}",
                reply_markup=main_keyboard()
            )
            log.info(f'REQUEST ({request.uuid}) - MASTER ASSIGNED ({master_id})')
            
        
        @dp.callback_query_handler(order_callback.filter(key='request_response'))
        async def request_response(callback_query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext = RequestService):
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите сообщение для клиента...',
                reply_markup=make_reply_keyboard()
            )
            await RequestService.message.set()

        
        @dp.message_handler(state=RequestService.message)
        async def response_message(message: Message, state: FSMContext):
            request_state_data = await state.get_data()
            uuid = request_state_data['uuid']
            user_telegram_id = await get_telegram_id_from_request(uuid)
            request = await get_request(uuid)
            await add_message(uuid, message.text, True)
            await bot.send_message(
                user_telegram_id,
                text=dedent(
                    f"Вам ответил мастер по заказу:\n"
                    f"{request}\n\n"

                    f"Сообщение от мастера:\n"
                    f"{message.text}"
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(
                    InlineKeyboardButton(
                        text="Написать мастеру",
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
            log_message = " ".join(message.text.split("\n"))
            log.info(f'REQUEST [{request.uuid}]: MASTER ({message.from_user.id}) SENT MESSAGE TO CUSTOMER ({user_telegram_id}): {log_message}')
        

        @dp.callback_query_handler(order_callback.filter(key='details_ask'))
        async def request_response(callback_query: CallbackQuery,
                                   callback_data: dict,
                                   state: FSMContext = RequestService):
            await state.update_data(uuid=callback_data['uuid'])
            await bot.send_message(
                callback_query.from_user.id,
                text='Напишите что хотите уточнить.',
                reply_markup=make_reply_keyboard()
            )
            await RequestService.detailes_ask.set()


        @dp.message_handler(state=RequestService.detailes_ask)
        async def response_message(message: Message, state: FSMContext):
            request_state_data = await state.get_data()
            uuid = request_state_data['uuid']
            request = await get_request(uuid)
            
            master_id = await get_master_id_from_request(uuid)
            if not master_id:
                master_id = env.int('ADMIN_TELEGRAM_ID')
            
            inline_buttons = [
                InlineKeyboardButton(
                    text="Ответить клиенту",
                    callback_data=order_callback.new(
                        key='request_response',
                        uuid=request.uuid
                    )
                ),
                InlineKeyboardButton(
                    text="Позвонить клиенту",
                    callback_data=order_callback.new(
                        key='phonecall',
                        uuid=request.uuid
                    )
                )
            ]
            if master_id == env.int("ADMIN_TELEGRAM_ID"):
                inline_buttons.append(
                    InlineKeyboardButton(
                        text="Назначить мастера",
                        callback_data=order_callback.new(
                            key='assign_master',
                            uuid=request.uuid
                        )
                    )
                )

            last_messages = await get_last_messages(uuid, 3)

            await bot.send_message(
                master_id,
                text=(
                    f'Сообщение от клиента!\n\n'

                    f'Заявка: {request}\n\n'

                    f'Последние сообщения:\n'
                    f'{last_messages}'

                    f'\nСообщение: {message.text}'
                ),
                reply_markup=InlineKeyboardMarkup(row_width=1).add(*inline_buttons)
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
            log_message = " ".join(message.text.split("\n"))
            log.info(f'REQUEST [{request.uuid}]: CUSTOMER ({message.from_user.id}) SENT MESSAGE TO MASTER ({master_id}): {log_message}')


        @dp.callback_query_handler(order_callback.filter(key='phonecall'))
        @dp.callback_query_handler(order_callback.filter(key='phonecall_ask'))
        async def phonecall_ask(callback_query: CallbackQuery,
                                callback_data: dict,
                                state: FSMContext):
            request_object = await get_request(callback_data['uuid'])
            
            master_id = await get_master_id_from_request(callback_data['uuid'])
            if not master_id:
                master_id = env.int('ADMIN_TELEGRAM_ID')

            if callback_data['key'] == 'phonecall_ask':
                await bot.send_message(
                    master_id,
                    text="Клиент запросил обратный звонок!"
                )
            await bot.send_contact(
                master_id,
                phone_number=f'+{request_object.phone}',
                first_name=request_object.first_name,
            )
            user_telegram_id = await get_telegram_id_from_request(callback_data['uuid'])
            if callback_data['key'] == 'phonecall_ask':
                await bot.send_message(
                    user_telegram_id,
                    text="Ваш номер отправлен мастеру, ожидайте звонка."
                )
            log.info(f'REQUEST [{request_object.uuid}]: MASTER ({master_id}) GOT PHONENUMBER OF CUSTOMER ({user_telegram_id}): {request_object.phone}')

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
            log_message = " ".join(message.text.split("\n"))
            log.info(f'SUPPORT REQUEST [{new_support_request.uuid}] FROM {message.from_user.id}: {log_message}')
        
        
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
            support_state_data = await state.get_data()
            user_id = support_state_data['user_id']
            original_message = support_state_data['message']
            await bot.send_message(
                user_id,
                text=(
                    f'Вы обращались в техподдержку:\n'
                    f'"{original_message}".\n\n'
                    f'Ответ поддержки:\n'
                    f'{message.text}'
                )
            )
            await close_support_request(support_state_data['uuid'], message.text)
            await state.finish()
            log_message = " ".join(message.text.split("\n"))
            log.info(f'SUPPORT REQUEST [{support_state_data.uuid}] CLOSED WITH ANSWER FROM {message.from_user.id}: {log_message}')
        

        @dp.message_handler(commands="backup")
        async def backup(message: Message):
            if message.from_user.id != env.int('ADMIN_TELEGRAM_ID'):
                await bot.send_message(chat_id=env.int('ADMIN_TELEGRAM_ID'), text=f'ALERT!!!\n\nBACKUP REQUEST FROM {message.from_user.id} user')
                log.warning(f'BACKUP REQUEST FROM {message.from_user.id} user')
                return
            db = zipfile.ZipFile('database.zip', 'w')
            db.write("db.sqlite3")
            db.close()
            await bot.send_document(chat_id=env.int('ADMIN_TELEGRAM_ID'), document=open('database.zip', 'rb'))
            log.info(f'BACKUP SENT TO {env.int("ADMIN_TELEGRAM_ID")}')

            
            
        @dp.message_handler()
        async def unknown_message(message: Message):
            await message.reply(
                dedent(
                    f'Бот не поддерживает произвольные сообщения.\n\n'
                    
                    f'Нажмите необходимую кнопку для связи с мастером или поддержкой.'
                )
            )

        executor.start_polling(dp)
