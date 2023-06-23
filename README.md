#  meetup_storage

## Требования к использованию

Требуется [Python](https://www.python.org/downloads/) версии 3.7 или выше и установленный [pip](https://pip.pypa.io/en/stable/getting-started/). Для установки необходимых зависимостей используйте команду:  
1. Для Unix/macOs:
```commandline
python -m pip install -r requirements.txt
```
2. Для Windows:
```commandline
py -m pip download --destination-directory DIR -r requirements.txt
```

## Установка

1. Выполнить миграцию: `python3 manage.py migrate`
2. В папке `storage` создать файл `.env`, заполнить его по образцу:
```comandline
BOT_API_TOKEN=ваш_токен
SECRET_KEY=ThisIsSoMuchSecretKey
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE=sqlite:///db.sqlite3
```
где нужно заменить `ваш_токен` на токен вашего бота.

3. Переместить скрипт со своим ботом в главную директорию.
4. Добавить в него следующее (в начало, до импорта моделей):
```python
os.environ['DJANGO_SETTINGS_MODULE'] = 'storage.settings'
django.setup()

from storage.settings import BOT_API_TOKEN
from db.models import Speech

env = Env()
env.read_env(override=True)
bot = telebot.TeleBot(BOT_API_TOKEN)
```

5. вызывать его простой командой `python3 your_bot.py`.