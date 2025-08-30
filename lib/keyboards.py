# lib/keyboards.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='📝 Заметки', callback_data='menu_notes')
    kb.button(text='🔐 Пароли', callback_data='menu_passwords')
    kb.button(text='⚙️ Настройки', callback_data='menu_settings')
    kb.adjust(2)
    return kb.as_markup()

def notes_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Добавить заметку', callback_data='notes_add')
    kb.button(text='📋 Список заметок', callback_data='notes_list')
    kb.button(text='⬅️ Назад', callback_data='menu_back')
    kb.adjust(1)
    return kb.as_markup()

def pw_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text='➕ Добавить пароль', callback_data='pw_add')
    kb.button(text='📋 Список паролей', callback_data='pw_list')
    kb.button(text='🔒 Разблокировать', callback_data='pw_unlock')
    kb.button(text='⬅️ Назад', callback_data='menu_back')
    kb.adjust(1)
    return kb.as_markup()
