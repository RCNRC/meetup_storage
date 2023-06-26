from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BACK_BUTTONS = KeyboardButton('Назад')


def start_button() -> ReplyKeyboardMarkup:
    button1 = KeyboardButton('Уведомить всех')
    button2 = KeyboardButton('Добавить докладчиков')
    button3 = KeyboardButton('Править программу')
    button4 = KeyboardButton('Посмотреть донаты')
    button5 = KeyboardButton('Выбрать другое мероприятие')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.insert(button2)
    markup.add(button1)
    markup.add(button3)
    markup.insert(button4)
    markup.add(button5)

    return markup


def add_speaker_buttons() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(BACK_BUTTONS)

    return markup


def change_the_program_button() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton('Название')
    button2 = KeyboardButton('Дата')
    markup.add(BACK_BUTTONS)
    markup.add(button1)
    markup.add(button2)

    return markup


def view_donations_button() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(BACK_BUTTONS)
    return markup


def inform_everyone_button() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(BACK_BUTTONS)

    return markup

