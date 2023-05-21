from telebot import types

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Register', 'Queue')
    return markup

def gender_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('М', 'Ж')
    return markup

def priority_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('низкий', 'средний', 'высокий')
    return markup

def post_registration_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Я хочу уйти, не дожидаясь своей очереди', 'Я хочу прийти через n минут', 'Текущая очередь']
    for button in buttons:
        keyboard.add(types.KeyboardButton(text=button))
    return keyboard

