import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiogram.utils.markdown as md
from aiogram.types import ParseMode
from queue_database.database import *
from formatted import *
from simulator import *
from functional import *


logging.basicConfig(level=logging.INFO)
API_TOKEN = "6289556666:AAGpinAWZMv3AaI3pNOk4s79_pFLP3jpV0E"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    name = State()
    age = State()
    gender = State()
    priority = State()
    allowed_waiting_time = State()
    suspend = State()

priority_level_dict = {'низкий':1,'средний':2,'высокий':3, }
inv_priority_level_dict = {v: k for k, v in priority_level_dict.items()}

@dp.message_handler(commands=["start", "help"])
async def start_command(message: types.Message):
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    reg = KeyboardButton("Регистрация")
    queue = KeyboardButton("Просмотр очереди")
    update = KeyboardButton("Обновление параметров")
    menu.add(reg, queue)
    menu.add(update)

    # await test_loop(con)


    # Send a message with the button menu
    await message.reply(
        "Привет!\nЯ бот для огрганизации очереди. Выберите вариант:",
        reply=False,
        reply_markup=menu,
    )


@dp.message_handler(lambda message: message.text == "Регистрация")
async def process_button1(message: types.Message):
    ReplyKeyboardRemove()
    await Form.name.set()
    await message.reply(
        "Напишите своё имя",
        reply=False,
    )


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.reply("Какой у вас возраст?")


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    return await message.reply("Нужно ввести число.\nКакой у вас возраст?")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(age=int(message.text))

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("М", "Ж")

    await message.reply("Ваш пол?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["М", "Ж"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    return await message.reply("Мы поддерживаем только два пола в данный момент. Выберите пол из клавиатуры.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await Form.next()
    async with state.proxy() as data:
        data['gender'] = message.text


    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("низкий", "средний", "высокий")

    await message.reply("Как бы вы оценили ваш уровень спешки?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["низкий", "средний", "высокий"], state=Form.priority)
async def process_priority_invalid(message: types.Message):
    return await message.reply("Мы поддерживаем только предложенные уровни спешки в данный момент\n"
                               "Выберите другой уровень из клавиатуры.")


@dp.message_handler(state=Form.priority)
async def process_priority(message: types.Message, state: FSMContext):
    # await Form.next()
    async with state.proxy() as data:
        data['priority'] = priority_level_dict[message.text]

    await Form.next()
    await message.reply("Сколько времени вы готовы ждать?(в минутах)")


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.allowed_waiting_time)
async def process_allowed_waiting_time_invalid(message: types.Message):
    return await message.reply("Нужно ввести число.\n"
                               "Сколько времени вы готовы ждать?(в минутах)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.allowed_waiting_time)
async def process_allowed_waiting_time(message: types.Message, state: FSMContext):
    # Update state and data
    # await state.update_data(age=int(message.text))
    async with state.proxy() as data:
        data['allowed_waiting_time'] = message.text

        cl = Client(chat_id=message.chat.id,
                    name=data['name'],
                    age=data['age'],
                    gender=data['gender'],
                    priority=data['priority'],
                    allowed_waiting_time=data['allowed_waiting_time'],)

        await bot.send_message(
                    cl.chat_id,
                    md.text(
                        md.text('Вы записаны в очередь, ', md.bold(cl.name), '!'),
                        md.text('Возраст:', md.code(cl.age)),
                        md.text('Пол:', cl.gender),
                        md.text('Уровень спешки:', inv_priority_level_dict[cl.priority]),
                        md.text('Готовы ожидать:', cl.allowed_waiting_time, ' мин'),
                        md.text('Время регистрации:', cl.time_arrive),
                        sep='\n',
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
        clients[cl.chat_id] = cl
        await insert(cl)

    await state.finish()


@dp.message_handler(lambda message: message.text == "Просмотр очереди")
async def process_button2(message: types.Message):
    queue_list = await customer_query(True, 'name', 'time_arrive')
    # logic of transforming by algorithm
    # queue_list is the first state, then we need to apply some logic on sorting, then transform by relaxation param
    ext = EXTimings()
    ext.fill_exams()
    q_list = await customer_query()
    # print("Hui", q_list)
    arr  = ext.original_order(q_list)
    sarsa_out =  ext.sarsa_adj(q_list)

    await bot.send_message(message.chat.id,md.text(
        md.text('\nOriginal order:\n', queue_format(queue_list)),
        md.text('\nAvg queue time:\n', ext.timedelta_orig),
        md.text('\nModified order:\n', queue_format(arr)),
        md.text('\nAvg queue time:\n', ext.timedelta_final),
        md.text('\nSarsa modified order:\n', queue_format(sarsa_out)),
        md.text('\nAvg queue time:\n', ext.timedelta_sarsa),
        sep='\n',)
    )


@dp.message_handler(lambda message: message.text == "Обновление параметров")
async def process_button3(message: types.Message):
    update_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)

    btns = [KeyboardButton("Я хочу уйти, не дожидаясь своей очереди"),
            KeyboardButton("Я хочу прийти через n минут"),
            ]

    for item in btns:
        update_menu.add(item)

    await message.reply(
        "Выберите параметры обновления",
        reply_markup=update_menu,
    )


@dp.message_handler(lambda message: message.text == "Я хочу уйти, не дожидаясь своей очереди")
async def process_button4(message: types.Message):
    await update(message.chat.id, premature_departure=True)
    await message.reply(
        md.text("Вы исключены из очереди"),
        reply=False,
    )


@dp.message_handler(lambda message: message.text == "Я хочу прийти через n минут")
async def process_button5(message: types.Message):
    await Form.suspend.set()
    return await message.reply("Через какое время вы вернетесь?(в минутах)")


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.suspend)
async def process_suspend_invalid(message: types.Message):
    return await message.reply("Нужно ввести число.\nЧерез какое время вы вернетесь?(в минутах)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.suspend)
async def process_suspend(message: types.Message):
    # Update state and data
    await Form.next()
    await update(message.chat.id, leave_time=int(message.text))
    await bot.send_message(message.chat.id,
        md.text(f"Обновлены параметры записи:\nВы отойдёте на {message.text} минут"))


if __name__ == "__main__":
    logging.info("Starting bot...")
    create_tables()
    loop = asyncio.get_event_loop()
    loop.create_task(test_loop())
    executor.start_polling(dp, skip_updates=True)
