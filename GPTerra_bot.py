import os
from time import sleep
import openai

import matplotlib


import telebot
from matplotlib import pyplot as plt
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from db import *
from keyboard import *
from functions import *
from config import *

ruble_rate = take_rub()
help(openai.ErrorObject)
bot_name = ""
matplotlib.use('Agg')
bot = telebot.TeleBot("6181517228:AAEtFBfBC_H8LAWxj9ZBnm9w1wtzcyfKvHw", parse_mode="HTML")  # server
# openai.api_key = get_key()


@bot.my_chat_member_handler()
def join(message):
    chat_id = message.chat.id
    if message.new_chat_member.status != "member":
        del_user(chat_id)
    else:
        update_user(chat_id)


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text
    info = text.split()
    refer = None
    if len(info) == 2:
        refer = info[1]
    if not user_exists(user_id) and refer and refer != str(user_id):
        update_tokens(refer, 20000)
        update_refers(refer)
        bot.send_message(refer, f"Вы получили бонус: 20.000 токенов!. Ваш текущий баланс: {get_tokens(refer)} токенов",
                         reply_markup=main_k)
    bot.send_message(user_id, "Введите запрос", reply_markup=main_k)


@bot.message_handler(content_types=['text'])
def new_message(message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        text = message.text
        user_id = message.from_user.id
        message_id = message.id
        if user_id == 848438079:
            if text == ".":
                bot.send_message(user_id, "Админка", reply_markup=admin_k)
                return
            elif text[:3] == "sql":
                bot.send_message(user_id, sql(text[4:]), reply_markup=admin_k)
                return
            elif text == admin_k.keyboard[0][0]["text"]:
                bot.send_message(user_id, "Введите новый ключ", reply_markup=back_k)
                bot.register_next_step_handler_by_chat_id(chat_id, set_key)
                return
            elif text == admin_k.keyboard[0][1]["text"]:
                graphs = create_statistic()
                all_with_block = len(get_all_users(True))
                all_users = len(get_all_users())
                media_group = [InputMediaPhoto(open(graphs[0], 'rb'), caption=f"Всего: {all_with_block}\n"
                                                                              f"Удалили: {all_with_block - all_users}\n"
                                                                              f"Итого: {all_users}\n"),
                               InputMediaPhoto(open(graphs[1], 'rb'))]
                bot.send_media_group(user_id, media=media_group)
                return
            elif text == admin_k.keyboard[1][0]["text"]:
                bot.send_message(user_id, "Введите сообщение для рассылки", reply_markup=back_k)
                bot.register_next_step_handler_by_chat_id(chat_id, mailing)
                return
            elif text == back_k.keyboard[0][0]["text"]:
                bot.send_message(user_id, "Введите запрос", reply_markup=main_k)
                return
        if text == main_k.keyboard[0][0]["text"]:
            tokens = get_tokens(user_id)
            refers_c = get_refers(user_id)
            if user_id == 848438079:
                tokens = "∞"
                bot.send_message(user_id, f"🍪Количество токенов: {tokens}(~∞ слов)\n"
                                          f"👥Количество рефералов: {refers_c}")
                return
            bot.send_message(user_id, f"🍪Количество токенов: {tokens}(~{int(tokens) // 7} слов)\n"
                                      f"👥Количество рефералов: {refers_c}")
            return
        elif text == main_k.keyboard[0][1]["text"]:
            bot.send_message(user_id, f"Ваша реферальная ссылка для получения 20.000 токенов:\n"
                                      f"t.me/{bot_name}?start={user_id}", disable_web_page_preview=True,
                             reply_markup=create_repost_k(user_id))
            return
        tokens = get_tokens(user_id)
        if tokens <= 0 and user_id != 848438079:
            bot.send_message(user_id, "У вас закончились токены. Для получения ещё 20.000 токенов"
                                      "Вам нужно привести одного друга. Больше друзей - больше токенов",
                             reply_markup=create_repost_k(user_id))
            return
        if len(text) > 2000:
            bot.send_message(user_id, "Максимальное число символов - 2000")
            return
        to_edit = bot.send_message(user_id, "⌛️Ожидание ответа", reply_to_message_id=message_id).message_id
        try:
            response = openai.Completion.create(engine="text-davinci-003",
                                                prompt=text,
                                                temperature=0.7,
                                                max_tokens=2000,
                                                top_p=1.0,
                                                frequency_penalty=0.0,
                                                presence_penalty=0.6,
                                                stop=None,
                                                n=1
                                                )
            tokens_used = response.usage.total_tokens
            update_tokens(user_id, -tokens_used)
            result = response.choices[0].text
            first = result.find("\n\n")
            if not result[first:]:
                first = 0
            bot.edit_message_text(result[first:], chat_id, to_edit)
        except Exception as e:
            if user_id == 848438079:
                bot.edit_message_text(
                    f"😵‍💫 Ошибка сервера при обработке вашего запроса. Извините за это! (admin {e})", chat_id,
                    to_edit)
            else:
                bot.edit_message_text("😵‍💫 Ошибка сервера при обработке вашего запроса. Извините за это!", chat_id,
                                      to_edit)


@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub(call):
    pass


def set_key(message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]["text"]:
        bot.send_message(user_id, "Админка", reply_markup=admin_k)
        return
    update_key(text)
    openai.api_key = text
    bot.send_message(user_id, "Ключ обновлён", reply_markup=admin_k)


def create_statistic():
    statistic = get_statistic_day()
    plt.clf()
    date = [i[0].strftime('%m/%d') for i in statistic]
    plt.title('За день:', fontsize=20)
    bar = plt.bar(date, [i[1] for i in statistic])
    ax = plt.gca()
    for i, rect in enumerate(ax.patches):
        height = rect.get_height()
        label = statistic[i][1]
        ax.text(rect.get_x() + rect.get_width() / 2., height, '{}'.format(label), ha='center', va='bottom')
    for i in range(len(bar) - 1):
        bar[i].set_color('cornflowerblue')
    bar[-1].set_color("r")
    cwd = os.getcwd()
    plt.savefig(cwd + "/graph.png")

    statistic = get_statistic_all()
    plt.clf()
    date = [i[0].strftime('%m/%d') for i in statistic]
    plt.title('За всё время:', fontsize=20)
    bar = plt.bar(date, [i[1] for i in statistic])
    ax = plt.gca()
    for i, rect in enumerate(ax.patches):
        height = rect.get_height()
        label = statistic[i][1]
        ax.text(rect.get_x() + rect.get_width() / 2., height, '{}'.format(label), ha='center', va='bottom')
    for i in range(len(bar) - 1):
        bar[i].set_color('cornflowerblue')
    bar[-1].set_color("r")
    cwd = os.getcwd()
    plt.savefig(cwd + "/graph1.png")

    return [cwd + "/graph.png", cwd + "/graph1.png"]


def mailing(message):
    chat_id = message.chat.id
    try:
        text = message.text
    except:
        bot.send_message(chat_id, "Неверный формат", reply_markup=admin_k)
        return
    if text == back_k.keyboard[0][0]["text"] or text == "/start":
        bot.send_message(chat_id, "Админка", reply_markup=admin_k)
        return
    all_users = get_all_users()
    bot.send_message(chat_id, "Начинаю рассылку...", reply_markup=admin_k)
    for user_id in all_users:
        try:
            bot.send_message(user_id[0], text)
        except:
            pass
    bot.send_message(chat_id, "Рассылка завершена!")


while True:
    try:
        print("START_CHAT_GPT_ALL")
        bot.infinity_polling()
    except Exception as e:
        sleep(3)
