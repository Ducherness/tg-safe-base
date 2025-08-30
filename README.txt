Как запускать на Linux Mint (сервер):

1) Клонируйте проект на сервер и создайте виртуальное окружение:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # aiogram cryptography

2) Установите переменную окружения с токеном и запустите:

export BOT_TOKEN="<токен>"
python main.py

3) Рекомендуется настроить systemd unit для автозапуска.