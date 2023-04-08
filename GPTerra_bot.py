import asyncio
import os
from time import sleep
import openai

import matplotlib

import aiogram
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor

from matplotlib import pyplot as plt
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo

from db import *
from my_states import *
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
bot = aiogram.Bot("6181517228:AAEtFBfBC_H8LAWxj9ZBnm9w1wtzcyfKvHw", parse_mode="HTML")
storage = MemoryStorage()
dp = aiogram.Dispatcher(bot, storage=storage)

kf = 3
kf_i = 2

my_key = get_key()
if my_key:
    openai.api_key = my_key
else:
    change_key("")
    openai.api_key = get_key()


@dp.my_chat_member_handler()
async def join(message):
    chat_id = message.chat.id
    if message.new_chat_member.status != "member":
        del_user(chat_id)
    else:
        update_user(chat_id)


@dp.message_handler(commands=['start'], state="*")
async def start_message(message: types.Message):
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
            await bot.send_message(refer, f"Вы получили бонус: 5₽!. Ваш текущий баланс: {get_balance(refer)}₽",
                                   reply_markup=main_k)
        await bot.send_message(user_id, "Добро пожаловать в GPTerra🤖!"
                                        "Здесь ты можешь писать тексты📝, генерировать идеи💡 и создавать изображения🎨\n"
                                        "Сейчас у тебя на балансе 10₽. За каждого руга ты получишь ещё 5₽. "
                                        "(Ссылка для приглашения находится в профиле)",
                               reply_markup=main_chat_k)
        return
    model = get_model(user_id)
    if model == "gpt-3.5-turbo":
        await bot.send_message(user_id, f"Введите запрос, текущая модель: gpt-3.5-turbo", reply_markup=main_chat_k)
    else:
        await bot.send_message(user_id, f"Введите запрос, текущая модель: {model}", reply_markup=main_k)


@dp.message_handler(state="*")
async def main_state(message: types.Message):
    if message.chat.type == "private":
        chat_id = message.chat.id
        text = message.text
        user_id = message.from_user.id
        message_id = message.message_id
        if user_id == 848438079:
            if text == ".":
                await bot.send_message(user_id, "Админка", reply_markup=admin_k)
                return
            elif text[:3] == "sql":
                await bot.send_message(user_id, sql(text[4:]), reply_markup=admin_k)
                return
            elif text == admin_k.keyboard[0][0]:
                await bot.send_message(user_id, "Введите новый ключ формат key amount login|pass",
                                       reply_markup=back_k)
                await Form.set_key.set()
                return
            elif text == admin_k.keyboard[0][1]:
                graphs = create_statistic()
                all_with_block = len(get_all_users(True))
                all_users = len(get_all_users())
                media_group = [InputMediaPhoto(open(graphs[0], 'rb'), caption=f"Всего: {all_with_block}\n"
                                                                              f"Удалили: {all_with_block - all_users}\n"
                                                                              f"Итого: {all_users}\n"),
                               InputMediaPhoto(open(graphs[1], 'rb'))]
                await bot.send_media_group(user_id, media=media_group)
                return
            elif text == admin_k.keyboard[1][0]:
                await bot.send_message(user_id, "Введите сообщение для рассылки", reply_markup=back_k)
                await Form.mailing.set()
                return
            elif text == back_k.keyboard[0][0]:
                await bot.send_message(user_id, "Введите запрос", reply_markup=main_k)
                return
        if text == main_k.keyboard[0][0]:
            balance = get_balance(user_id)
            refers_c = get_refers(user_id)
            await bot.send_message(user_id, f"🍪Баланс: {balance}₽\n"
                                            f"👥Количество рефералов: {refers_c}",
                                   reply_markup=create_profile_k(user_id))
            return
        elif text == main_k.keyboard[0][1]:
            await bot.send_message(user_id, f"🔄Выберите нейронку🔄", disable_web_page_preview=True,
                                   reply_markup=all_ai_k)
            await Form.switch_ai.set()
            return
        elif text == main_chat_k.keyboard[1][0]:
            await bot.send_message(user_id, f"История успешно очищена! Начните диалог сначала")
            del_messages(user_id)
            return
        elif text == back_k.keyboard[0][0]:
            await bot.send_message(user_id, f"Главное меню", reply_markup=main_k)
            return
        balance = get_balance(user_id)
        if balance <= 0:
            await bot.send_message(user_id, "😕У тебя закончились деньги. Для получения ещё 5₽"
                                            "Вам нужно привести друга. Также ты можешь пополнить баланс",
                                   reply_markup=create_profile_k(user_id))
            return
        if len(text) > 2048:
            await bot.send_message(user_id, "⚠ Максимальное количество символов - 2048 ⚠️")
            return
        try:
            my_model = get_model(user_id)
            if my_model == "DALLE":
                to_edit = await bot.send_animation(user_id, open('load_photo.gif', 'rb'),
                                                   reply_to_message_id=message_id)
                to_edit = to_edit.message_id
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
                await bot.edit_message_media(InputMediaPhoto(open(f'./users_photos/{user_id}.jpg', 'rb')),
                                             user_id, to_edit)
            elif my_model == "gpt-3.5-turbo":
                to_edit = await bot.send_message(user_id, "⌛️Ожидание ответа",
                                                 reply_to_message_id=message_id)
                to_edit = to_edit.message_id
                new_message(user_id, 0, text)
                all_messages = get_messages(user_id)
                messages_mas = []
                for i in all_messages:
                    if i[0] == 0:
                        role = "user"
                    else:
                        role = "assistant"
                    messages_mas.append({"role": role, "content": i[1]})
                response = await asyncio.get_event_loop().run_in_executor(None,
                                                                          openai.ChatCompletion.create(
                                                                              model="gpt-3.5-turbo",
                                                                              messages=messages_mas)
                                                                          )
                tokens_used = response.usage.total_tokens
                amount = kf * (tokens_used * price[my_model] * ruble_rate / 1000)
                update_balance(user_id, -amount)
                result = response.choices[0].message.content
                await bot.edit_message_text(result, chat_id, to_edit)
                new_message(user_id, 1, result)
            else:
                to_edit = await bot.send_message(user_id, "⌛️Ожидание ответа",
                                                 reply_to_message_id=message_id)
                to_edit = to_edit.message_id
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
                await bot.edit_message_text(result[first:], chat_id, to_edit)
        except Exception as e:
            e = str(e)
            print(e)
            if e == limit_err:
                if change_key("limit"):
                    openai.api_key = get_key()
                    await main_state(message)
                else:
                    await bot.send_message(chat_id, "🗝️Закончились ключи, ожидайте пополнения🗝️")
            elif e == overload_err:
                await bot.send_message(chat_id, "🗄️Сервер перегружен, повторите попытку позже🗄️")
            elif e == server_error:
                await bot.send_message(chat_id, "👾Ошибка CHAT-GPT👾")
            elif e == key_error_0 or e == key_error_1 or e == key_error_2:
                if change_key("key_error"):
                    openai.api_key = get_key()
                    await main_state(message)
                else:
                    await bot.send_message(chat_id, "🗝️Закончились ключи, ожидайте пополнения🗝️")


@dp.callback_query_handler(lambda call: call.data == 'balance_plus')
async def balance_plus(call):
    user_id = call.from_user.id
    call_id = call.id
    await bot.answer_callback_query(call_id)
    await bot.send_message(user_id, "Выберите сумму для пополнения")
    await Form.pay_balance.set()


@dp.message_handler(state=Form.pay_balance)
async def pay_balance(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if not text:
        return
    if text == back_k.keyboard[0][0]:
        model = get_model(user_id)
        if get_balance(user_id) > 0:
            if model == "gpt-3.5-turbo":
                await bot.send_message(user_id, f"Введите запрос, текущая модель: gpt-3.5-turbo",
                                       reply_markup=main_chat_k)
            else:
                await bot.send_message(user_id, f"Введите запрос, текущая модель: {model}", reply_markup=main_k)
        else:
            await bot.send_message(user_id,
                                   f"Поддержи пожалуйста проект. Я написал бота в одиночку и мне будет приятно, "
                                   f"если ты поможешь в его развитии. \nВ будущем я хочу написать свою нейронку, "
                                   f"но для этого нужны большие вычислительный мощности, "
                                   f"на которые у меня пока нет денег", reply_markup=main_k)
        await Form.main.set()
        return
    sum_to_pay = text.split()[0]
    try:
        int(sum_to_pay)
    except ValueError:
        await bot.send_message(user_id, f"Некорректные данные. Сумма это число. Попробуй ещё раз :)")
        return


@dp.message_handler(state=Form.switch_ai)
async def switch_ai(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]:
        await bot.send_message(user_id, "Админка", reply_markup=admin_k)
        return
    model = delete_emoji(text)
    if model in price:
        await bot.send_message(user_id, description[model])
        update_model(user_id, model)
        if model == "gpt-3.5-turbo":
            keyboard = main_chat_k
        else:
            keyboard = main_k
        await bot.send_message(user_id, "Нейросеть успешно подключена. Введите запрос", reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Нет такой нейронки")
    await Form.main.set()


@dp.message_handler(state=Form.set_key)
async def set_key(message: types.Message):
    text = message.text
    user_id = message.from_user.id
    if text == back_k.keyboard[0][0]:
        await bot.send_message(user_id, "Админка", reply_markup=admin_k)
        return
    info = text.split()
    if len(info) == 3:
        new_key(info[0], info[1], info[2])
        openai.api_key = text
        await bot.send_message(user_id, "Ключ добавлен", reply_markup=admin_k)
    else:
        await bot.send_message(user_id, "Не все данные", reply_markup=admin_k)
        return
    await Form.main.set()


@dp.message_handler(state=Form.mailing)
async def mailing(message: types.Message):
    chat_id = message.chat.id
    try:
        text = message.text
    except:
        await bot.send_message(chat_id, "Неверный формат", reply_markup=admin_k)
        return
    if text == back_k.keyboard[0][0] or text == "/start":
        await bot.send_message(chat_id, "Админка", reply_markup=admin_k)
        await Form.main.set()
        return
    all_users = get_all_users()
    await bot.send_message(chat_id, "Начинаю рассылку...", reply_markup=admin_k)
    await Form.main.set()
    for user_id in all_users:
        try:
            await bot.send_message(user_id[0], text)
        except:
            pass
    await bot.send_message(chat_id, "Рассылка завершена!")


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


async def main():
    await dp.start_polling()


while True:
    try:
        print("START GPTerra")
        asyncio.run(main())
    except:
        sleep(3)
