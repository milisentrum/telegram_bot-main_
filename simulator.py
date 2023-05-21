import time
from random import randint, choice
from datetime import datetime
from queue_database.database import *


async def display_current_rows(con):
    data = await con.execute("SELECT * FROM customers")
    async for row in data:
        print(row)


async def test_loop():
    async with sl.connect(db_path, check_same_thread=False) as con:
        while True:
            action = randint(1, 3)

            if action == 1:  # Add a new person to the queue
                names = [i[1] for i in data_]
                name, age, gender, priority, allowed_waiting_time, = choice(names) + f'_{randint(1, 10)}', randint(18, 80), choice(['М', 'Ж']), choice([1,2,3]), randint(1, 100)
                chat_id = randint(1000000000, 9999900000)
                time_arrive = datetime.datetime.now().strftime("%H:%M:%S")
                await con.execute("INSERT INTO customers (id, name, age, gender, priority, allowed_waiting_time, time_arrive, time_leave, time_transfer, number_of_premature_leaves) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (chat_id, name, age, gender, priority,allowed_waiting_time, time_arrive, None, None, 0))
                await con.commit()
                await asyncio.sleep(10)  # wait 10 seconds

            elif action == 2:  # Simulate pressing "I want to leave without waiting my turn" button
                chat_ids = []
                async with con.execute("SELECT id FROM customers WHERE time_leave IS NULL") as cursor:
                    async for row in cursor:
                        chat_ids.append(row[0])
                # async with await con.execute("SELECT id FROM customers WHERE time_leave IS NULL") as cursor:
                #     async for row in cursor:
                #         chat_ids.append(row[0])
                if chat_ids:
                    chat_id = chat_ids[randint(0, len(chat_ids) - 1)]
                    time_leave = datetime.datetime.now().strftime("%H:%M:%S")
                    await con.execute("UPDATE customers SET time_leave = ? WHERE id = ?;", (time_leave, chat_id))
                    await con.commit()
                    await asyncio.sleep(40) # wait 4 seconds

            elif action == 3:  # Simulate pressing "I want to move my turn by n minutes" button
                chat_ids = []
                async with con.execute("SELECT id FROM customers WHERE time_transfer IS NULL") as cursor:
                    async for row in cursor:
                        chat_ids.append(row[0])
                if chat_ids:
                    chat_id = chat_ids[randint(0, len(chat_ids) - 1)]
                    minutes = randint(1, 60)
                    await con.execute("UPDATE customers SET time_transfer = time((strftime('%s', time_arrive) + ? * 60), 'unixepoch') WHERE id = ?;", (minutes, chat_id))
                    await con.commit()
                    await asyncio.sleep(20)  # wait 2 seconds

            print("After changes:")
            await display_current_rows(con)
