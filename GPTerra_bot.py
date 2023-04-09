import io
import os
from time import sleep
import openai

import matplotlib

import telebot
from PIL import Image
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
pay_token = "381764678:TEST:54259"
kf = 3
kf_i = 2

my_key = get_key()
print(my_key)
if my_key and my_key[1] > 0:
    openai.api_key = my_key[0]
else:
    change_key()
    openai.api_key = get_key()[0]


@bot.my_chat_member_handler()
def join(message):
    chat_id = message.chat.id
    if message.new_chat_member.status != "member":
        del_user(chat_id)
    else:
        update_user(chat_id)


@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    text = message.text
    info = text.split()
    refer = None
    if len(info) == 2:
        refer = info[1]
    if not user_exists(user_id):
        if refer and refer != str(user_id):
            update_balance(refer, 5)
            update_refers(refer)
            bot.send_message(refer, f"Вы получили бонус: 5₽!. Ваш текущий баланс: {get_balance(refer)}₽",
                             reply_markup=main_k)
        bot.send_message(user_id, "Добро пожаловать в GPTerra🤖!"
                                  "Здесь ты можешь писать тексты📝, генерировать идеи💡 и создавать изображения🎨\n"
                                  "Сейчас у тебя на балансе 10₽. За каждого руга ты получишь ещё 5₽. "
                                  "(Ссылка для приглашения находится в профиле)",
                         reply_markup=main_chat_k)
        return
    model = get_model(user_id)
    if model == "gpt-3.5-turbo":
        bot.send_message(user_id, f"Введите запрос, текущая модель: gpt-3.5-turbo", reply_markup=main_chat_k)
    else:
        bot.send_message(user_id, f"Введите запрос, текущая модель: {model}", reply_markup=main_k)


@bot.message_handler(content_types=['text', 'photo'])
def i_get_message(message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        text = message.text
        if not text:
            text = ""
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
                all_keys = get_all_keys()
                key_text = ""
                for i in all_keys:
                    key_text += f"<code>{i[0]}</code>: {i[1]}$ (<code>{i[2]}</code>)  -  {'active' if i[3] else ''}\n\n"
                bot.send_message(user_id, f"Все ключи:\n{key_text}", parse_mode="HTML")
                return
            elif text == admin_k.keyboard[1][0]["text"]:
                bot.send_message(user_id, "Введите сообщение для рассылки", reply_markup=back_k)
                bot.register_next_step_handler_by_chat_id(chat_id, mailing)
                return
            elif text == admin_k.keyboard[1][1]["text"]:
                graphs = create_statistic()
                all_with_block = len(get_all_users(True))
                all_users = len(get_all_users())
                media_group = [InputMediaPhoto(open(graphs[0], 'rb'), caption=f"Всего: {all_with_block}\n"
                                                                              f"Удалили: {all_with_block - all_users}\n"
                                                                              f"Итого: {all_users}\n"),
                               InputMediaPhoto(open(graphs[1], 'rb'))]
                bot.send_media_group(user_id, media=media_group)
                return
            elif text == back_k.keyboard[0][0]["text"]:
                bot.send_message(user_id, "Введите запрос", reply_markup=main_k)
                return
        if text == main_k.keyboard[0][0]["text"]:
            balance = get_balance(user_id)
            refers_c = get_refers(user_id)
            bot.send_message(user_id, f"🍪Баланс: {balance}₽\n"
                                      f"👥Рефералы: {refers_c} ",
                             reply_markup=create_profile_k(user_id))
            return
        elif text == main_k.keyboard[0][1]["text"]:
            bot.send_message(user_id, f"🔄Выбери нейронку🔄", disable_web_page_preview=True,
                             reply_markup=all_ai_k)
            bot.register_next_step_handler_by_chat_id(user_id, switch_ai)
            return
        elif text == main_chat_k.keyboard[1][0]["text"]:
            bot.send_message(user_id, f"История успешно очищена! Начните диалог сначала")
            del_messages(user_id)
            return
        elif text == back_k.keyboard[0][0]["text"]:
            bot.send_message(user_id, f"Главное меню", reply_markup=main_k)
            return
        balance = get_balance(user_id)
        if balance <= 0:
            bot.send_message(user_id, "😕У тебя закончились деньги. Для получения ещё 5₽ "
                                      "тебе нужно привести друга.\nТакже ты можешь пополнить баланс🥹",
                             reply_markup=create_profile_k(user_id))
            return
        if len(text) > 2048:
            bot.send_message(user_id, "⚠ Максимальное количество символов - 2048 ⚠️")
            return
        try:
            my_model = get_model(user_id)
            if my_model == "DALLE":
                to_edit = bot.send_animation(user_id, open('load_photo.gif', 'rb'), caption="Генерация...",
                                             reply_to_message_id=message_id).message_id
                reply_message = message.reply_to_message
                photo = message.photo
                if reply_message or photo:
                    if photo:
                        file_info = bot.get_file(photo[-1].file_id)
                    else:
                        file_info = bot.get_file(reply_message.photo[-1].file_id)
                    downloaded_file = bot.download_file(file_info.file_path)
                    image = Image.open(io.BytesIO(downloaded_file))
                    width, height = image.size
                    if width != height:
                        bot.edit_message_caption("Для лучшего результата следует отправлять квадратные изображения!",
                                                 user_id, to_edit)
                    new_image = image.resize((512, 512))
                    new_image.save(f"./users_photos/{user_id}_e.png")
                    response = openai.Image.create_variation(
                        image=open(f"./users_photos/{user_id}_e.png", "rb"),
                        n=1,
                        size="512x512"
                    )
                else:
                    response = openai.Image.create(
                        prompt=text,
                        n=1,
                        size="512x512"
                    )
                key_used = price[my_model]
                amount = kf_i * key_used * ruble_rate
                image_url = response['data'][0]['url']
                img_data = requests.get(image_url).content
                with open(f'./users_photos/{user_id}.png', 'wb') as handler:
                    handler.write(img_data)
                bot.edit_message_media(InputMediaPhoto(open(f'./users_photos/{user_id}.png', 'rb'),
                                                       caption=f"<a href='{image_url}'>Готово! *тык</a>",
                                                       parse_mode="HTML"),
                                       user_id, to_edit)
            elif my_model == "gpt-3.5-turbo":
                to_edit = bot.send_message(user_id, "⏳️Ожидание ответа", reply_to_message_id=message_id).message_id
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
                key_used = tokens_used * price[my_model] / 1000
                amount = kf * key_used * ruble_rate
                result = response.choices[0].message.content
                bot.edit_message_text(result, chat_id, to_edit)
                new_message(user_id, 1, result)
            else:
                to_edit = bot.send_message(user_id, "⏳  ️Ожидание ответа", reply_to_message_id=message_id).message_id
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
                key_used = tokens_used * price[my_model] / 1000
                amount = kf * key_used * ruble_rate
                result = response.choices[0].text
                bot.edit_message_text(text + result, chat_id, to_edit)
            update_balance(user_id, -amount)
            update_key_balance(-key_used)
            if get_key()[1] <= 0:
                change_key()
                reload_key = get_key()
                if reload_key:
                    openai.api_key = reload_key[0]
        except Exception as e:
            e = str(e)
            if e == limit_err:
                if change_key():
                    openai.api_key = get_key()[0]
                    i_get_message(message)
                else:
                    bot.send_message(chat_id, "🗝️Закончились ключи, ожидайте пополнения🗝️")
            elif e == overload_err:
                bot.send_message(chat_id, "🗄️Сервер перегружен, повторите попытку позже🗄️")
            elif e == server_error:
                bot.send_message(chat_id, "👾Ошибка CHAT-GPT👾")
            elif e == key_error_0 or e == key_error_1 or e == key_error_2:
                if change_key():
                    openai.api_key = get_key()[0]
                    i_get_message(message)
                else:
                    bot.send_message(chat_id, "🗝️Закончились ключи, ожидайте пополнения🗝️")
            elif e == safety:
                bot.send_message(chat_id, "Запрос отклонён системой безопасности openai")
            elif e == load_photo:
                bot.send_message(chat_id, "Изображение должно быть меньше 4МБ")
            else:
                bot.send_message(chat_id, "Неизвестная ошибка!")
                bot.send_message(848438079, e)


@bot.callback_query_handler(func=lambda call: call.data == 'balance_plus')
def balance_plus(call):
    user_id = call.from_user.id
    call_id = call.id
    bot.answer_callback_query(call_id)
    bot.send_message(user_id, "Выберите сумму для пополнения", reply_markup=amount_to_pay_k)
    bot.register_next_step_handler_by_chat_id(user_id, pay_balance)


@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def process_successful_payment(message):
    user_id = message.from_user.id
    amount = message.successful_payment.total_amount / 100
    if amount >= 500:
        amount *= 1.15
    elif amount >= 250:
        amount *= 1.1
    update_balance(user_id, amount)
    model = get_model(user_id)
    if model == "gpt-3.5-turbo":
        bot.send_message(message.chat.id, f'Спасибо за покупку, {amount}₽ успешно зачислено!\n'
                                          f'Твой баланс: {get_balance(user_id)}₽', reply_markup=main_chat_k)
    else:
        bot.send_message(message.chat.id, f'Спасибо за покупку, {amount}₽ успешно зачислено!\n'
                                          f'Твой баланс: {get_balance(user_id)}₽', reply_markup=main_k)


def pay_balance(message):
    text = message.text
    user_id = message.from_user.id
    if not text:
        return
    if text == back_k.keyboard[0][0]["text"]:
        model = get_model(user_id)
        if get_balance(user_id) > 0:
            if model == "gpt-3.5-turbo":
                bot.send_message(user_id, f"Введите запрос, текущая модель: gpt-3.5-turbo", reply_markup=main_chat_k)
            else:
                bot.send_message(user_id, f"Введите запрос, текущая модель: {model}", reply_markup=main_k)
        else:
            bot.send_message(user_id, f"Я написал бота в одиночку и мне будет приятно, "
                                      f"если ты поможешь в его развитии. \nВ будущем я хочу написать свою нейронку, "
                                      f"но для этого нужны большие вычислительный мощности, "
                                      f"на которые у меня пока нет денег", reply_markup=main_k)
        return
    sum_to_pay = text.replace("₽", "").split()[0]
    try:
        sum_to_pay = int(sum_to_pay)
        if 100 > sum_to_pay:
            raise ZeroDivisionError
    except ValueError:
        bot.send_message(user_id, f"Некорректные данные (сумма это число). Попробуй ещё раз :)")
        bot.register_next_step_handler_by_chat_id(user_id, pay_balance)
        return
    except ZeroDivisionError:
        bot.send_message(user_id, f"Сумма должна быть не менее 100₽. Мы уже работаем над этим")
        bot.register_next_step_handler_by_chat_id(user_id, pay_balance)
        return
    try:
        bot.send_invoice(
            message.chat.id,
            title="Пополнение баланса",
            description="Спасибо за покупку, благодаря тебе проект развивается",
            provider_token=pay_token,
            currency='rub',
            photo_size=512,
            photo_width=512,
            photo_height=512,
            photo_url="https://i.ibb.co/yycBNXr/money.jpg",
            is_flexible=False,
            prices=[telebot.types.LabeledPrice(label='Пополнение баланса', amount=sum_to_pay * 100)],
            start_parameter='time-machine-example',
            invoice_payload=f'receive_money {sum_to_pay}'
        )
    except:
        bot.send_message(user_id, f"Ошибка, пожалуйста, попробуйте ещё раз")
        bot.register_next_step_handler_by_chat_id(user_id, pay_balance)
        return


def switch_ai(message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]["text"]:
        model = get_model(user_id)
        if model == "gpt-3.5-turbo":
            bot.send_message(user_id, f"Введите запрос, текущая модель: gpt-3.5-turbo", reply_markup=main_chat_k)
        else:
            bot.send_message(user_id, f"Введите запрос, текущая модель: {model}", reply_markup=main_k)
        return
    model = delete_emoji(text)
    if model in price:
        if model == "gpt-3.5-turbo":
            keyboard = main_chat_k
        else:
            keyboard = main_k
        bot.send_message(user_id, "Нейросеть успешно подключена. Введите запрос", reply_markup=keyboard)
        for i in description[model]:
            bot.send_message(user_id, i)
        update_model(user_id, model)
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
        print("START GPTerra")
        bot.infinity_polling()
    except:
        sleep(3)
