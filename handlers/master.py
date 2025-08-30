# handlers/master.py
import os
import base64
import json
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from lib.sessions import set_unlocked, lock_user
from lib.keyboards import main_menu_kb

router = Router()
CFG_PATH = Path(__file__).parent.parent / 'data' / 'config.json'

def load_cfg():
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding='utf-8'))
    return {}

@router.callback_query(lambda c: c.data == 'menu_settings')
async def settings_cb(cq: CallbackQuery):
    await cq.message.edit_text(
        'Настройки:\n'
        'Рекомендуется установить мастер-ключ на сервере (см. README):\n'
        '`python manage.py set-master`\n\n'
        'Доступна локальная разблокировка через сохранённый мастер-ключ.',
        reply_markup=main_menu_kb()
    )
    await cq.answer()

@router.message(Command('unlock'))
async def cmd_unlock(message: Message):
    owner = os.environ.get('OWNER_ID')
    if owner and str(message.from_user.id) != str(owner):
        await message.answer("Эта команда доступна только владельцу бота.")
        return

    cfg = load_cfg()
    mkey_b64 = cfg.get('master_key')
    if not mkey_b64:
        await message.answer("Мастер-ключ не найден. Выполните на сервере: python manage.py set-master")
        return

    try:
        key = base64.b64decode(mkey_b64)
        set_unlocked(message.from_user.id, key)
        await message.answer("Разблокировано локальным мастер-ключом (без ввода пароля в чате).")
    except Exception as e:
        await message.answer("Не удалось прочитать master_key: " + str(e))

@router.message(Command('lock'))
async def cmd_lock(message: Message):
    lock_user(message.from_user.id)
    await message.answer('Сессия заблокирована.')

@router.callback_query(lambda c: c.data == 'menu_back')
async def cb_menu_back(cq: CallbackQuery):
    await cq.message.edit_text('Главное меню:', reply_markup=main_menu_kb())
    await cq.answer()
