# handlers/notes.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import StateFilter

from lib.db import get_conn
from lib.keyboards import main_menu_kb, notes_menu_kb

router = Router()

class NoteStates(StatesGroup):
    title = State()
    content = State()
    datetime = State()

@router.message(Command('start'))
async def start_cmd(message: Message):
    await message.answer('Главное меню:', reply_markup=main_menu_kb())

@router.callback_query(lambda c: c.data == 'menu_notes')
async def menu_notes(cq: CallbackQuery):
    await cq.message.edit_text('Меню заметок:', reply_markup=notes_menu_kb())
    await cq.answer()

@router.callback_query(lambda c: c.data == 'notes_add')
async def add_note_cb(cq: CallbackQuery, state: FSMContext):
    await cq.message.answer('Отправьте заголовок заметки:')
    await state.set_state(NoteStates.title)
    await cq.answer()

@router.message(StateFilter(NoteStates.title))
async def note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Отправьте содержание заметки:')
    await state.set_state(NoteStates.content)

@router.message(StateFilter(NoteStates.content))
async def note_content(message: Message, state: FSMContext):
    await state.update_data(content=message.text)
    await message.answer('Дата уведомления (YYYY-MM-DD HH:MM) или `нет`')
    await state.set_state(NoteStates.datetime)

@router.message(StateFilter(NoteStates.datetime))
async def note_datetime(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get('title')
    content = data.get('content')
    dt_text = message.text.strip()
    due_iso = None
    if dt_text.lower() != 'нет':
        try:
            from datetime import datetime
            due_dt = datetime.strptime(dt_text, '%Y-%m-%d %H:%M')
            due_iso = due_dt.isoformat()
        except Exception:
            await message.answer('Неверный формат даты. Повторите.')
            return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO notes (user_id, title, content, due_datetime, notified) VALUES (?, ?, ?, ?, ?)',
                (message.from_user.id, title, content, due_iso, 0))
    conn.commit()
    conn.close()
    await message.answer('Заметка сохранена.')
    await state.clear()

@router.callback_query(lambda c: c.data == 'notes_list')
async def notes_list(cq: CallbackQuery):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, title, due_datetime FROM notes WHERE user_id = ? ORDER BY created_at DESC', (cq.from_user.id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await cq.answer()
        await cq.message.answer('У вас нет заметок.')
        return
    text_lines = []
    kb = InlineKeyboardBuilder()
    for r in rows:
        text_lines.append(f"#{r['id']} — {r['title'] or '(без заголовка)'} — {r['due_datetime'] or '—'}")
        kb.button(text=f"#{r['id']}", callback_data=f"note_view:{r['id']}")
    kb.button(text='⬅️ Назад', callback_data='menu_back')
    kb.adjust(2)
    await cq.message.edit_text('Ваши заметки:\n' + '\n'.join(text_lines), reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(lambda c: c.data and c.data.startswith('note_view:'))
async def note_view(cq: CallbackQuery):
    nid = int(cq.data.split(':',1)[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM notes WHERE id = ? AND user_id = ?', (nid, cq.from_user.id))
    r = cur.fetchone()
    conn.close()
    if not r:
        await cq.answer('Не найдено', show_alert=True)
        return
    text = f"<b>{r['title']}</b>\n{r['content']}\n\nНапоминание: {r['due_datetime'] or '—'}"
    kb = InlineKeyboardBuilder()
    kb.button(text='🗑️ Удалить', callback_data=f'note_delete:{nid}')
    kb.button(text='⬅️ Назад', callback_data='notes_list')
    kb.adjust(2)
    await cq.message.edit_text(text, reply_markup=kb.as_markup())
    await cq.answer()

@router.callback_query(lambda c: c.data and c.data.startswith('note_delete:'))
async def note_delete(cq: CallbackQuery):
    nid = int(cq.data.split(':',1)[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (nid, cq.from_user.id))
    conn.commit()
    conn.close()
    await cq.answer('Удалено')
    await cq.message.edit_text('Заметка удалена.', reply_markup=notes_menu_kb())
