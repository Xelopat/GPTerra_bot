import os
from time import sleep
import openai

import matplotlib

import telebot
from matplotlib import pyplot as plt
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

from db import *
from keyboard import *
from functions import *
from config import *
from errors import *

try:
    os.mkdir("./users_photos")
except FileExistsError:
    pass
ruble_rate = take_rub()
matplotlib.use('Agg')
bot = telebot.TeleBot("6181517228:AAEtFBfBC_H8LAWxj9ZBnm9w1wtzcyfKvHw", parse_mode="HTML")  # server
kf = 3
kf_i = 2

my_key = get_key()
if my_key:
    openai.api_key = my_key
else:
    change_key("")
    openai.api_key = get_key()


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
        update_balance(refer, 5)
        update_refers(refer)
        bot.send_message(refer, f"Вы получили бонус: 5₽!. Ваш текущий баланс: {get_balance(refer)}₽",
                         reply_markup=main_k)
    bot.send_message(user_id, "Введите запрос", reply_markup=main_k)


@bot.message_handler(content_types=['text'])
def i_get_message(message):
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
                bot.send_message(user_id, "Введите новый ключ формат key amount login|pass",
                                 reply_markup=back_k)
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
            balance = get_balance(user_id)
            refers_c = get_refers(user_id)
            if user_id == 848438079:
                balance = "∞"
                bot.send_message(user_id, f"🍪Баланс: {balance}₽\n"
                                          f"👥Количество рефералов: {refers_c}")
                return
            bot.send_message(user_id, f"🍪Баланс: {balance}₽\n"
                                      f"Примерно\n"
                                      f"👥Количество рефералов: {refers_c}")
            return
        elif text == main_k.keyboard[0][1]["text"]:
            bot.send_message(user_id, f"🔄Выберите нейронку🔄", disable_web_page_preview=True,
                             reply_markup=all_ai_k)
            bot.register_next_step_handler_by_chat_id(user_id, switch_ai)
            return
        elif text == main_k.keyboard[0][1]["text"]:
            bot.send_message(user_id, f"text", disable_web_page_preview=True,
                             reply_markup=create_repost_k(user_id))
            return
        elif text == back_k.keyboard[0][0]["text"]:
            bot.send_message(user_id, f"Главное меню", reply_markup=main_k)
            return
        balance = get_balance(user_id)
        if balance <= 0:
            bot.send_message(user_id, "😕У вас закончились деньги. Для получения ещё 5₽"
                                      "Вам нужно привести друга или пополнить баланс",
                             reply_markup=create_repost_k(user_id))
            return
        if len(text) > 2000:
            bot.send_message(user_id, "⚠️Максимальное число символов - 2000⚠️")
            return

        try:
            my_model = get_model(user_id)
            if my_model == "DALLE":
                to_edit = bot.send_animation(user_id, open('load_photo.gif', 'rb'),
                                             reply_to_message_id=message_id).message_id
                response = openai.Image.create(
                    prompt=text,
                    n=1,
                    size="512x512"
                )
                amount = kf_i * (price["DALLE"] * ruble_rate)
                update_balance(user_id, -amount)
                image_url = response['data'][0]['url']
                img_data = requests.get(image_url).content
                with open(f'./users_photos/{user_id}.jpg', 'wb') as handler:
                    handler.write(img_data)
                bot.edit_message_media(InputMediaPhoto(open(f'./users_photos/{user_id}.jpg', 'rb')), user_id, to_edit)
            elif my_model == "gpt-3.5-turbo":
                to_edit = bot.send_message(user_id, "⌛️Ожидание ответа", reply_to_message_id=message_id).message_id
                new_message(user_id, 0, text)
                all_messages = get_messages(user_id)
                messages_mas = []
                for i in all_messages:
                    if i[0] == 0:
                        role = "user"
                    else:
                        role = "assistant"
                    messages_mas.append({"role": role, "content": i[1]})
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages_mas
                )
                tokens_used = response.usage.total_tokens
                amount = kf * (tokens_used * price[my_model] * ruble_rate / 1000)
                update_balance(user_id, -amount)
                result = response.choices[0].message.content
                bot.edit_message_text(result, chat_id, to_edit)
                new_message(user_id, 1, result)
            else:
                to_edit = bot.send_message(user_id, "⌛️Ожидание ответа", reply_to_message_id=message_id).message_id
                response = openai.Completion.create(engine=my_model,
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
                amount = kf * (tokens_used * price[my_model] * ruble_rate / 1000)
                update_balance(user_id, -amount)
                result = response.choices[0].text
                first = result.find("\n\n")
                if not result[first:]:
                    first = 0
                bot.edit_message_text(result[first:], chat_id, to_edit)
        except Exception as e:
            e = str(e)
            print(e)
            if e == limit_err:
                if change_key("limit"):
                    openai.api_key = get_key()
                    new_message(message)
                else:
                    bot.edit_message_text("🗝️Закончились ключи, ожидайте пополнения🗝️", chat_id, to_edit)
            elif e == overload_err:
                bot.edit_message_text("🗄️Сервер перегружен, повторите попытку позже🗄️", chat_id, to_edit)
            elif e == server_error:
                bot.edit_message_text("👾Ошибка CHAT-GPT👾", chat_id, to_edit)
            elif e == key_error_0 or e == key_error_1 or e == key_error_2:
                if change_key("key_error"):
                    openai.api_key = get_key()
                    new_message(message)
                else:
                    bot.edit_message_text("🗝️Закончились ключи, ожидайте пополнения🗝️", chat_id, to_edit)


@bot.callback_query_handler(func=lambda call: call.data == 'check_sub')
def check_sub(call):
    pass


def switch_ai(message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]["text"]:
        bot.send_message(user_id, "Админка", reply_markup=admin_k)
        return
    model = delete_emoji(text)
    if model in price:
        bot.send_message(user_id, description[model])
        update_model(user_id, model)
        bot.send_message(user_id, "Нейросеть успешно подключена. Введите запрос", reply_markup=main_k)
    else:
        bot.send_message(user_id, "Нет такой нейронки")
        bot.register_next_step_handler_by_chat_id(user_id, switch_ai)


def set_key(message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]["text"]:
        bot.send_message(user_id, "Админка", reply_markup=admin_k)
        return
    info = text.split()
    if len(info) == 3:
        new_key(info[0], info[1], info[2])
        openai.api_key = text
        bot.send_message(user_id, "Ключ добавлен", reply_markup=admin_k)
    else:
        bot.send_message(user_id, "Не все данные", reply_markup=admin_k)
        bot.register_next_step_handler_by_chat_id(user_id, set_key)


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
    except:
        sleep(3)
