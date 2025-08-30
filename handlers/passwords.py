# handlers/passwords.py
import os
import base64
import json
from pathlib import Path

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import StateFilter

from lib import crypto
from lib.keyboards import pw_menu_kb
from lib.db import get_conn
from lib.sessions import is_unlocked, get_key, set_unlocked

router = Router()

CFG_PATH = Path(__file__).parent.parent / 'data' / 'config.json'

class PwStates(StatesGroup):
    name = State()
    password = State()
    note = State()

@router.callback_query(lambda c: c.data == 'menu_passwords')
async def menu_pw(cq: CallbackQuery):
    await cq.message.edit_text('Меню паролей:', reply_markup=pw_menu_kb())
    await cq.answer()

@router.callback_query(lambda c: c.data == 'pw_add')
async def pw_add_cb(cq: CallbackQuery, state: FSMContext):
    await cq.message.answer('Введите название для пароля:')
    await state.set_state(PwStates.name)
    await cq.answer()

@router.message(StateFilter(PwStates.name))
async def pw_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Отправьте сам пароль:')
    await state.set_state(PwStates.password)

@router.message(StateFilter(PwStates.password))
async def pw_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer('Заметка к паролю (или `нет`):')
    await state.set_state(PwStates.note)

@router.message(StateFilter(PwStates.note))
async def pw_note(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    password = data.get('password')
    note = message.text if message.text.lower() != 'нет' else None
    uid = message.from_user.id
    if not is_unlocked(uid):
        await message.answer('Сначала выполните /unlock (или используйте пункт меню).')
        await state.clear()
        return
    key = get_key(uid)
    token = crypto.encrypt_with_key(key, password)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO passwords (user_id, name, encrypted_password, note) VALUES (?, ?, ?, ?)',
                (uid, name, token, note))
    conn.commit()
    conn.close()
    await message.answer('Пароль сохранён.')
    await state.clear()

@router.callback_query(lambda c: c.data == 'pw_list')
async def pw_list(cq: CallbackQuery):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, name, created_at FROM passwords WHERE user_id = ? ORDER BY created_at DESC', (cq.from_user.id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await cq.answer()
        await cq.message.answer('Паролей нет.')
        return
    text_lines = [f"#{r['id']} — {r['name']} (с {r['created_at']})" for r in rows]
    kb = InlineKeyboardBuilder()
    for r in rows:
        kb.button(text=f"#{r['id']}", callback_data=f"pw_view:{r['id']}")
    kb.button(text='⬅️ Назад', callback_data='menu_back')
    kb.adjust(2)
    await cq.message.edit_text('Список паролей:\n' + '\n'.join(text_lines), reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(lambda c: c.data and c.data.startswith('pw_view:'))
async def pw_view(cq: CallbackQuery):
    pid = int(cq.data.split(':', 1)[1])

    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM passwords WHERE id = ? AND user_id = ?', (pid, cq.from_user.id))
    r = cur.fetchone()
    conn.close()

    if not r:
        await cq.answer('Пароль не найден.', show_alert=True)
        return

    uid = cq.from_user.id
    if not is_unlocked(uid):
        await cq.answer('Сначала выполните /unlock.', show_alert=True)
        return

    key = get_key(uid)
    try:
        pw = crypto.decrypt_with_key(key, r['encrypted_password'])
    except Exception:
        await cq.answer('Не удалось расшифровать. Возможно, мастер-пароль изменён.', show_alert=True)
        return

    display_text = f"{r['note']} | {r['name']}:\n» {pw}"
    await cq.answer(display_text, show_alert=True)

@router.callback_query(lambda c: c.data and c.data.startswith('pw_delete:'))
async def pw_delete(cq: CallbackQuery):
    pid = int(cq.data.split(':',1)[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM passwords WHERE id = ? AND user_id = ?', (pid, cq.from_user.id))
    conn.commit()
    conn.close()
    await cq.answer('Удалено')
    await cq.message.edit_text('Пароль удалён.', reply_markup=pw_menu_kb())

@router.callback_query(lambda c: c.data == 'pw_unlock')
async def pw_unlock_cb(cq: CallbackQuery):
    owner = os.environ.get('OWNER_ID')
    if owner and str(cq.from_user.id) != str(owner):
        await cq.answer("Эта команда доступна только владельцу бота.")
        return

    if not CFG_PATH.exists():
        await cq.message.answer("Мастер-ключ не найден. Выполните на сервере: python manage.py set-master")
        await cq.answer()
        return

    try:
        cfg = json.loads(CFG_PATH.read_text(encoding='utf-8'))
        mkey_b64 = cfg.get('master_key')
        if not mkey_b64:
            await cq.message.answer("Мастер-ключ не найден. Выполните на сервере: python manage.py set-master")
            await cq.answer()
            return
        key = base64.b64decode(mkey_b64)
        set_unlocked(cq.from_user.id, key)
        await cq.message.answer("Разблокировано локальным мастер-ключом (без ввода пароля в чате).")
        await cq.answer()
    except Exception as e:
        await cq.message.answer("Не удалось прочитать master_key: " + str(e))
        await cq.answer()