from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from db import *
from config import *

back_k = ReplyKeyboardMarkup(resize_keyboard=True)
back = KeyboardButton("Назад")
back_k.add(back)

main_k = ReplyKeyboardMarkup(resize_keyboard=True)
main_k.add("👩🏻‍💻Профиль👩🏻‍💻", "🤖Выбор нейросети🤖")

admin_k = ReplyKeyboardMarkup(resize_keyboard=True)
admin_k.add("+Ключ", "Статистика")
admin_k.add("Рассылка")
admin_k.add(back)

all_ai_k = ReplyKeyboardMarkup(resize_keyboard=True)
all_ai_k.add("💬gpt-3.5-turbo💬", "💪text-davinci-003💪")
all_ai_k.add("🤓babbage🤓", "🤪ada🤪")
all_ai_k.add("🖼️DALLE🖼️")
all_ai_k.add(back)


def create_repost_k(user_id):
    keyboard = InlineKeyboardMarkup()
    link = f"https://t.me/share/url?url=t.me/{bot_name}?start={user_id}"
    keyboard.add(InlineKeyboardButton("Поделиться", url=link))
    return keyboard
