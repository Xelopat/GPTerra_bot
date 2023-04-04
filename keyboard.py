from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from db import *
from config import *

back_k = ReplyKeyboardMarkup(resize_keyboard=True)
back = KeyboardButton("Назад")
back_k.add(back)

main_k = ReplyKeyboardMarkup(resize_keyboard=True)
main_k.add("🤖Профиль🤖", "📢Поделиться📢")

admin_k = ReplyKeyboardMarkup(resize_keyboard=True)
admin_k.add("Ключ", "Статистика")
admin_k.add("Рассылка")
admin_k.add(back)


def create_repost_k(user_id):
    keyboard = InlineKeyboardMarkup()
    link = f"https://t.me/share/url?url=t.me/{bot_name}?start={user_id}"
    keyboard.add(InlineKeyboardButton("Поделиться", url=link))
    return keyboard

