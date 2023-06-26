import datetime
import os
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
import textwrap
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from environs import Env
from aiogram import Bot, Dispatcher, executor, types
from keybutton import start_button, add_speaker_buttons, change_the_program_button, view_donations_button, \
    inform_everyone_button
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'storage.settings'
django.setup()

from db.models import User, Donation, Event, Alert

env = Env()
env.read_env()

bot = Bot(env('TG_ORGANIZER_BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

MY_EVENT: Event = None


@sync_to_async
def get_message_donats(user) -> str:
    donat = Donation.objects.filter(user__event=user)
    message = ['{} {}руб.'.format(str(result.user.username), str(result.summ)) for result in donat]
    return textwrap.dedent("\n".join(message))


class StateUser(StatesGroup):
    speakers = State()
    programs = State()
    programs_name = State()
    programs_date = State()
    start = State()
    inform = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    async for event in Event.objects.all():
        markup.add(KeyboardButton(event.title))
    await message.answer('Выберите Мероприятие', reply_markup=markup)
    await StateUser.start.set()


@dp.message_handler(state=StateUser.start)
async def choose_event(message: types.Message, state: FSMContext):
    global MY_EVENT
    try:
        MY_EVENT = await Event.objects.aget(title=message.text)
    except Event.DoesNotExist:
        await message.answer(f'{message.text} нет такого мероприятия')
    await state.finish()
    await message.answer(f'Ваше Мероприятие: <<{MY_EVENT.title}>>', reply_markup=start_button())


@dp.message_handler(Text(equals='Добавить докладчиков'))
async def add_speakers(message: types.Message):
    await StateUser.speakers.set()
    await message.answer('Введите никнеймы "@nik @nik @nik" через пробел', reply_markup=add_speaker_buttons())


@dp.message_handler(Text(equals='Выбрать другое мероприятие'))
async def choose_other_event(message: types.Message):
    await start(message)


@dp.message_handler(Text(equals='Править программу'))
async def change_the_program(message: types.Message):
    await StateUser.programs.set()
    await message.answer('Что изменить?', reply_markup=change_the_program_button())


@dp.message_handler(Text(equals='Посмотреть донаты'))
async def view_donations(message: types.Message):
    donats = await get_message_donats(MY_EVENT)
    await message.answer(donats, reply_markup=view_donations_button())


@dp.message_handler(Text(equals='Уведомить всех'))
async def inform_everyone(message: types.Message):
    await StateUser.inform.set()
    await message.answer('Введите содержимое Уведомления?', reply_markup=inform_everyone_button())


@dp.message_handler(state=StateUser.speakers)
async def write_speaker(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await message.answer('Главное меню', reply_markup=start_button())
    else:
        new_message = message.text.replace('@', '')
        add_speakers = ''
        try:
            for username in new_message.split(' '):
                user = await MY_EVENT.users.aget(username=username)
                await MY_EVENT.speeches.aget_or_create(
                    speaker=user,
                    event=MY_EVENT,
                    start_time=datetime.datetime.now(),
                    end_time=datetime.datetime.now() + datetime.timedelta(hours=2)
                )
                add_speakers += '@{} '.format(username)
        except User.DoesNotExist:
            await message.answer(textwrap.dedent(f'''
            Пользователь с таким ником @{username}
            не зарегистрирован на {MY_EVENT.title.upper()} мероприятии'''))

        await bot.send_message(chat_id=env('ID_CHAT_CHANEL'), text=textwrap.dedent(f'''
        ❕❕❕Встречаем Новых Спикеров❕❕❕
        👏👏👏👏{add_speakers}👏👏👏👏'''))
        await message.answer(f'{add_speakers} добавлены и уведомлены', reply_markup=add_speaker_buttons())


@dp.message_handler(state=StateUser.inform)
async def send_chanel_message(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await message.answer('Главное меню', reply_markup=start_button())
    else:
        await state.finish()
        await Alert.objects.acreate(
            text=textwrap.dedent(
                f'''
                #‼️‼️‼️ВАЖНОЕ СООБЩЕНИЕ‼️‼️‼️
                #{message.text.upper()}
                '''
            )
        )
        #await bot.send_message(chat_id=env('ID_CHAT_CHANEL'), text=textwrap.dedent(f'''
        #‼️‼️‼️ВАЖНОЕ СООБЩЕНИЕ‼️‼️‼️
        #{message.text.upper()}'''))
        await message.answer('Уведомление отправлено', reply_markup=inform_everyone_button())


@dp.message_handler(state=StateUser.programs)
async def success_change_program(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await message.answer('Главное меню', reply_markup=start_button())
    elif message.text == 'Название':
        await StateUser.programs_name.set()
        await message.answer('Введите новое название')
    elif message.text == 'Дата':
        await StateUser.programs_date.set()
        await message.answer('Введите дату в формате YYYY-MM-DD')
    else:
        await state.finish()
        await message.answer('Скорректировал программу')


@dp.message_handler(state=StateUser.programs_name)
async def change_name_program(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await message.answer('Главное меню', reply_markup=start_button())
    else:
        MY_EVENT.title = message.text
        await MY_EVENT.asave(update_fields=['title'])
        await StateUser.programs.set()
        await message.answer(textwrap.dedent(f'''
        Новое название: {MY_EVENT.title}
        Хотите ещё внести изменения?'''), reply_markup=change_the_program_button())


@dp.message_handler(state=StateUser.programs_date)
async def change_data_program(message: types.Message, state: FSMContext):
    if message.text == 'Назад':
        await state.finish()
        await message.answer('Главное меню', reply_markup=start_button())
    else:
        MY_EVENT.date = message.text
        await MY_EVENT.asave(update_fields=['date'])
        await message.answer(textwrap.dedent(f'''
        Новая дата: {MY_EVENT.date}
        Хотите ещё внести изменения?'''), reply_markup=change_the_program_button())
        await StateUser.programs.set()


@dp.message_handler(Text(equals='Назад'))
async def back(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer('Главное меню', reply_markup=start_button())


executor.start_polling(dp)
