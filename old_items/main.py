import telebot
from telebot import types
from queue_database.database import insert, clients, Client, update, setup_database
from queue_ import user_queue
from datetime import datetime
from old_items.keyboard import main_keyboard, gender_keyboard, post_registration_keyboard, priority_keyboard

con = setup_database()

bot = telebot.TeleBot("5961404725:AAF9AytLyTrZCDy7qcNAaG_zC-9jKxxtp8g")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(chat_id=message.chat.id, text="Привет, я бот для огрганизации очереди.",
                     reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == 'Register')
def handle_register(message):
    message_ = bot.reply_to(message, "Как тебя зовут?", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message_, user_name)

def is_valid_name(name):
    return len(name) >= 2 and name.isalpha()

def user_name(message):
    try:
        chat_id = message.chat.id
        name = message.text.strip()

        while not is_valid_name(name):
            if len(name) < 2:
                message_ = bot.reply_to(message, "Имя должно содержать не менее 2 символов. Пожалуйста, попробуйте еще раз:")
            elif not name.isalpha():
                message_ = bot.reply_to(message, "Имя должно состоять только из букв. Пожалуйста, попробуйте еще раз:")
            bot.register_next_step_handler(message_, user_name)
            return

        client = Client(name)
        clients[chat_id] = client

        message_ = bot.reply_to(message, "Возраст:")
        bot.register_next_step_handler(message_, user_age)
    except Exception as e:
        print(e)

def is_valid_age(age):
    return age.isdigit() and len(age) < 3

def user_age(message):
    try:
        chat_id = message.chat.id
        age = message.text.strip()

        while not is_valid_age(age):
            if not age.isdigit():
                message_ = bot.reply_to(message, "Возраст должен быть числом. Пожалуйста, попробуйте еще раз:")
            elif len(age) >= 3:
                message_ = bot.reply_to(message, "Возраст не должен содержать более 3-х цифр. Пожалуйста, попробуйте еще раз:")
            bot.register_next_step_handler(message_, user_age)
            return

        client = clients[chat_id]
        client.age = age

        gender_markup = gender_keyboard()
        message_ = bot.reply_to(message, "Пол", reply_markup=gender_markup)
        bot.register_next_step_handler(message_, user_gender)
    except Exception as e:
        print(e)

def user_gender(message):
    try:
        chat_id = message.chat.id
        gender = message.text
        client = clients[chat_id]
        client.gender = gender

        priority_markup = priority_keyboard()  # you will define this function later

        message_ = bot.reply_to(message, "Пожалуйста, выберите свой уровень приоритета:", reply_markup=priority_markup)
        bot.register_next_step_handler(message_, user_priority)
    except Exception as e:
        print(e)



def user_priority(message):
    try:
        chat_id = message.chat.id
        priority = message.text  # 'low', 'medium', or 'high'
        client = clients[chat_id]
        client.priority = priority

        current_time = datetime.now().strftime("%H:%M:%S")
        client.time_arrive = current_time

        message_ = bot.reply_to(message, "Как долго вы готовы ожидать в очереди? (в минутах)")
        bot.register_next_step_handler(message_, user_allowed_waiting_time)
    except Exception as e:
        print(e)


def user_allowed_waiting_time(message):
    try:
        chat_id = message.chat.id
        allowed_waiting_time_text = message.text

        # Check that the input is a number
        if not allowed_waiting_time_text.isdigit():
            bot.reply_to(message, "Время ожидания должно быть положительным числом. Попробуйте еще раз.")
            return

        allowed_waiting_time = int(allowed_waiting_time_text)  # Convert the input to integer

        # Check that the input is a positive number
        if allowed_waiting_time < 0:
            bot.reply_to(message, "Время ожидания не может быть отрицательным. Попробуйте еще раз.")
            return

        client = clients[chat_id]
        client.allowed_waiting_time = allowed_waiting_time

        insert(message, con)
        message_ = bot.reply_to(message, "Отлично, регистрация прошла успешно!")
        bot.send_message(chat_id=message.chat.id, text="Выберите действие", reply_markup=post_registration_keyboard())
    except Exception as e:
        print(e)

@bot.message_handler(func=lambda message: message.text == 'Я хочу уйти, не дожидаясь своей очереди')
def want_to_leave_now(message):
    user_goaway(message, premature=True)

@bot.message_handler(commands=['goaway'])
def user_goaway(message, premature=False):
    try:
        chat_id = message.chat.id
        client = clients[chat_id]
        current_time = datetime.now().strftime("%H:%M:%S")
        client.time_leave = current_time

        if premature:
            client.num_premature_departures += 1

        update(con, chat_id, leave_time=current_time, premature_departure=premature)
        message_ = bot.reply_to(message, "Отлично, можешь идти!", reply_markup=types.ReplyKeyboardRemove())

    except Exception as e:
        print(e)



@bot.message_handler(func=lambda message: message.text in ['Queue', 'Current queue'])
def handle_queue(message):
    try:
        sorted_users = user_queue(message)
        if not sorted_users:
            bot.send_message(chat_id=message.chat.id, text="Очередь пуста")
        else:
            queue_message = "\n".join([f"{row[1]}" for row in sorted_users])
            bot.send_message(chat_id=message.chat.id, text=queue_message)
    except Exception as e:
        print(e)


@bot.message_handler(func=lambda message: message.text in ['Я хочу уйти, не дожидаясь своей очереди',
                                                           'Я хочу прийти через n минут',
                                                           'Текущая очередь'])
def handle_post_registration(message):
    if message.text in ['Текущая очередь']:
        handle_queue(message)
    elif message.text == 'Я хочу уйти, не дожидаясь своей очереди':
        want_to_leave_now(message)
    elif message.text == 'Я хочу прийти через n минут':
        message_ = bot.reply_to(message, "Введите количество минут:")
        bot.register_next_step_handler(message_, set_user_minutes)


def set_user_minutes(message):
    try:
        chat_id = message.chat.id
        client = clients[chat_id]
        minutes = message.text.strip()

        if not minutes.isdigit():
            message_ = bot.reply_to(message, "Количество минут должно быть числом. Пожалуйста, попробуйте еще раз:")
            bot.register_next_step_handler(message_, set_user_minutes)
            return

        update(con, chat_id, transfer_minutes=minutes)

        message_ = bot.reply_to(message, f"Ваше время изменено на {minutes} минут.")
    except Exception as e:
        print(e)


bot.enable_save_next_step_handlers(delay=1)
bot.load_next_step_handlers()
bot.infinity_polling()


# todo: сделать приветственное окошко и возможность записи в очередь после ухода чела для него еще раз не перезапуская бот