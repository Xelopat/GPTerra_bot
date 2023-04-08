from aiogram.dispatcher.filters.state import StatesGroup, State


class Form(StatesGroup):
    set_key = State()
    pay_balance = State()
    switch_ai = State()
    mailing = State()

    main = State()
