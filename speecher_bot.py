import sys
import logging
import os
import time
import signal
import django
from django.db.models import Max
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from environs import Env


logging.basicConfig(filename='bot.log', level=logging.INFO)


os.environ['DJANGO_SETTINGS_MODULE'] = 'storage.settings'
django.setup()

from storage.settings import TELEGRAM_SPEECHERS_BOT_API_TOKEN
from db.models import Speech, Question, User

env = Env()
env.read_env(override=True)
bot = telebot.TeleBot(TELEGRAM_SPEECHERS_BOT_API_TOKEN)


def signal_handler(signum, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def check_speaker(username):
    try:
        Speech.objects.get(speaker__username=username)
    except Speech.DoesNotExist:
        return False
    except Speech.MultipleObjectsReturned:
        return True
    return True


def get_main_keyboard(username):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if check_speaker(username):
        text = 'Вы являетесь участником как минимум одного выступления.'
        keyboard.add(KeyboardButton('Посмотреть вопросы с конкретного выступления'))
        keyboard.add(KeyboardButton('Посмотреть вопросы с моего последнего выступления'))
    else:
        text = 'Вы не являетесь участником ни одного выступления. Пожалуйста, свяжитесь с организатором.'
        keyboard.add(KeyboardButton('Попробовать снова'))
    return keyboard, text


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == 'Попробовать снова')
def send_welcome(message):
    keyboard, text = get_main_keyboard(message.chat.username)
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Посмотреть вопросы с конкретного выступления')
def get_certain_speeches(message):
    keyboard, text = get_main_keyboard(message.chat.username)
    if check_speaker(message.chat.username):
        speeches = Speech.objects.filter(speaker__username=message.chat.username)
        for speech in speeches:
            text = f'Выступление с {speech.start_time} до {speech.end_time}'
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton('Посмотреть вопросы.', callback_data=f'speech={speech.id}'))
            bot.send_message(message.chat.id, text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if 'speech' in call.data:
        speech_id = int(call.data.split('=')[1])
        try:
            speaker = User.objects.get(username=call.message.chat.username)
            speech = Speech.objects.get(id=speech_id)
            questions = Question.objects.filter(
                to_who=speaker,
                communication_request=False,
                time__gte=speech.start_time,
                time__lte=speech.end_time,
            )
            for question in questions:
                text = f'Пользователь @{question.from_who.username}:'\
                    f'\nВопрос: {question.text}'
                bot.send_message(call.message.chat.id, text)
        except Speech.DoesNotExist:
            text = 'К сожалению это выступление не найдено.'
            bot.send_message(call.message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == 'Посмотреть вопросы с моего последнего выступления')
def get_last_speech_questions(message):
    if check_speaker(message.chat.username):
        keyboard, _ = get_main_keyboard(message.chat.username)
        speaker = User.objects.get(username=message.chat.username)
        speech_aggregated_max_time = Speech.objects.filter(speaker=speaker).aggregate(Max('end_time'))
        speech = Speech.objects.get(end_time=speech_aggregated_max_time['end_time__max'])
        questions = Question.objects.filter(
            to_who=speaker,
            communication_request=False,
            time__gte=speech.start_time,
            time__lte=speech.end_time,
        )
        for question in questions:
            text = f'Пользователь @{question.from_who.username}:'\
                   f'\nВопрос: {question.text}'
            bot.send_message(message.chat.id, text, reply_markup=keyboard)
    else:
        keyboard, text = get_main_keyboard(message.chat.username)
        bot.send_message(message.chat.id, text, reply_markup=keyboard)


def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            print(error)
            time.sleep(5)


if __name__ == '__main__':
    main()
