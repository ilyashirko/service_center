from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

ASK_FOR_PHONE_KEYBOARD = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=1
).add(
    KeyboardButton("Отправить номер телефона", request_contact=True),
    'Вернуться на главную')


def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*(
        "Узнать стоимость ремонта",        
    ))
    return keyboard


def make_reply_keyboard(buttons: list = [],
                        one_time: bool = False,
                        row_width: int = 2,
                        extra_buttons: list = []) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=one_time,
        row_width=row_width
    )
    print(buttons)
    for button in buttons:
        print(button)
    keyboard.add(*(buttons + extra_buttons + ['Вернуться на главную']))
    return keyboard


