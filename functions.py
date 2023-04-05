import re

import requests  # Модуль для обработки URL
from bs4 import BeautifulSoup  # Модуль для работы с HTML


def take_rub():
    link = 'https://www.google.com/search?sxsrf=ALeKk01NWm6viYijAo3HXYOEQUyDEDtFEw%3A1584716087546&source=hp&ei=N9l0XtDXHs716QTcuaXoAg&q=%D0%B4%D0%BE%D0%BB%D0%BB%D0%B0%D1%80+%D0%BA+%D1%80%D1%83%D0%B1%D0%BB%D1%8E&oq=%D0%B4%D0%BE%D0%BB%D0%BB%D0%B0%D1%80+&gs_l=psy-ab.3.0.35i39i70i258j0i131l4j0j0i131l4.3044.4178..5294...1.0..0.83.544.7......0....1..gws-wiz.......35i39.5QL6Ev1Kfk4'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
    full_page = requests.get(link, headers=headers)
    soup = BeautifulSoup(full_page.content, 'html.parser')
    convert = soup.findAll("span", {"class": "SwHCTb", "data-precision": 2})
    return float(convert[0].text.replace(",", "."))


def delete_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # эмодзи лиц
                               u"\U0001F300-\U0001F5FF"  # эмодзи природы
                               u"\U0001F680-\U0001F6FF"  # эмодзи транспорта
                               u"\U0001F1E0-\U0001F1FF"  # эмодзи флагов
                               "]+", flags=re.UNICODE)

    return emoji_pattern.sub(r'', text)
