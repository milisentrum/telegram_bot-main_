'''Файл для реализации базы данных и запросов к ней'''
import aiosqlite as sl
import sqlite3 as sl3
import os
from random import randrange
import datetime
import asyncio
from typing import *

clients = {}
db_path = os.path.join(os.path.dirname(__file__), 'cstmrs.db')

class Client:
    def __init__(self, chat_id, name, age, gender, priority, allowed_waiting_time,
                 time_arrive=datetime.datetime.now().strftime("%H:%M:%S"),
                 time_leave = None,
                 time_transfer = None,
                 number_of_premature_leaves = 0):
        self.chat_id = chat_id
        self.name = name
        self.age = age
        self.gender = gender
        self.priority = priority
        self.allowed_waiting_time = allowed_waiting_time
        self.time_arrive = time_arrive
        self.time_leave = time_leave
        self.time_transfer = time_transfer
        self.number_of_premature_leaves = number_of_premature_leaves

class QClient:
    def __init__(self, chat_id, name, age, gender, priority, allowed_waiting_time,
                 time_arrive=datetime.datetime.now().strftime("%H:%M:%S"),
                 time_leave=None,
                 time_transfer=None,
                 number_of_premature_leaves=0,
                 queue_num=0):
        self.chat_id = chat_id
        self.name = name
        self.age = age
        self.gender = gender
        self.priority = priority
        self.allowed_waiting_time = allowed_waiting_time
        self.time_arrive = time_arrive
        self.time_leave = time_leave
        self.time_transfer = time_transfer
        self.number_of_premature_leaves = number_of_premature_leaves
        self.queue=queue_num

#TODO: Сделать объект базы данных c таблицей. Сохранение дампа базы внутри этой папки
# Тут должен быть реализован метод загрузки в базу, в нужную таблицу данных из
# класса clients. Который просто применяется потом в route телеграм бота
# Делать любое общение с базой по виду 'with connect()  as conn:
# conn.<>'
#TODO: добавить в базу номер объекта

def random_date():
    x = datetime.datetime.now() - datetime.timedelta(minutes=randrange(60))
    return x.strftime("%H:%M:%S")

data_ = [
        (1234567890, 'Bob', 32, 'М', 1, 17, random_date(), None, None, 0),
        (9876543210, 'Charlie', 27, 'М', 3, 31, random_date(), None, None, 0),
        (2468135790, 'Diana', 45, 'Ж', 1, 29, random_date(), None, None, 0),
        (1357924680, 'Eva', 29, 'Ж', 1, 65, random_date(), None, None, 0),
        (3141592653, 'Frank', 38, 'М', 3, 48, random_date(), None, None,0),
        (2718281828, 'Grace', 19, 'Ж', 3, 110, random_date(), None, None,0),
        (1123581321, 'Henry', 55, 'М', 3, 94, random_date(), None, None,0),
        (2233445566, 'Iris', 22, 'Ж', 3, 81, random_date(), None, None,0),
        (4455667788, 'John', 42, 'М', 3, 20, random_date(), None, None,0),
        (9988776655, 'Kate', 24, 'Ж', 1, 5, random_date(), None, None,0),
        (7777777777, 'Leo', 50, 'М', 1, 3, random_date(), None, None,0),
        (9999999999, 'Mia', 31, 'Ж', 1, 140, random_date(), None, None,0),
        (1231231231, 'Nick', 36, 'М', 3, 65, random_date(), None, None,0),
        (4564564564, 'Olga', 28, 'Ж', 3, 58, random_date(), None, None,0),
        (7897897897, 'Peter', 43, 'М', 3, 34, random_date(), None, None,0),
        (6546546546, 'Rachel', 26, 'Ж', 1, 56, random_date(), None, None,0),
        (9879879879, 'Sam', 47, 'М', 2, 43, random_date(), None, None,0),
        (3213213213, 'Tom', 30, 'М', 2, 19, random_date(), None, None,0),
        (6549873210, 'Vera', 25, 'Ж', 2, 35, random_date(), None, None,0)]

def generate_data(con):
    query_ = """INSERT INTO customers 
                                   (   id,
                                       name,
                                       age,
                                       gender,
                                       priority,
                                       allowed_waiting_time,
                                       time_arrive,
                                       time_leave,
                                       time_transfer,
                                       number_of_premature_leaves)
                                        values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   """
    con.executemany(query_, data_)
    con.commit()

def create_tables():
    with sl3.connect(db_path, check_same_thread=False) as con:
        for row in con.execute("select count(*) from sqlite_master where type='table' and name='customers'"):
            if row[0] == 0:
                con.execute("""
                        CREATE TABLE customers (
                            -- id str PRIMARY KEY,
                            id str,
                            name VARCHAR(30),
                            age INT,
                            gender VARCHAR(10),
                            priority INT,
                            allowed_waiting_time INT,
                            time_arrive TEXT,
                            time_leave TEXT,
                            time_transfer TEXT,
                            number_of_premature_leaves INT DEFAULT 0); """)  #is_hurry будет принимать 0 или 1, т.к. bool нет в sqlite3,
                                                  #format for text variables "HH:MM:SS"
                con.commit()
                print("[DB]>>Database created")
                generate_data(con)
                print("[DB]>>Queue generated")

async def staff(client: Client):
    data = (client.chat_id, client.name, client.age, client.gender, client.priority,
            client.allowed_waiting_time, client.time_arrive, client.time_leave,
            client.time_transfer, client.number_of_premature_leaves)
    return data

async def insert(client: Client):
    async with sl.connect(db_path, check_same_thread=False) as con:
        data = await staff(client)
        await con.execute("INSERT INTO customers (id, name, age, gender, priority, "
                    "allowed_waiting_time, time_arrive, time_leave, time_transfer, number_of_premature_leaves) "
                    "values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        await con.commit()
        print("[DB]>>New record added successfully")

async def is_id_unique(table_name, id):
    async with sl.connect(db_path, check_same_thread=False) as con:
        # Execute a SELECT query to retrieve the IDs from the table
        id_list = []
        async with con.execute(f"SELECT id FROM {table_name}") as cursor:
            async for row in cursor:
                id_list.append(row[0])
        # Check if the ID being added already exists in the list
        return id not in id_list


async def update(chat_id, leave_time=None, transfer_minutes=None, premature_departure=False):
    async with sl.connect(db_path, check_same_thread=False) as con:
        if leave_time:
            sql = "UPDATE customers SET time_leave = ? WHERE id = ?;"
            values = (leave_time, chat_id)
            await con.execute(sql, values)

        if transfer_minutes:
            sql = '''
            UPDATE customers
            SET time_transfer = time((strftime('%s', time_arrive) + ? * 60), 'unixepoch')
            WHERE id = ?;
            '''
            values = (transfer_minutes, chat_id)
            await con.execute(sql, values)

        if premature_departure:
            sql = "UPDATE customers SET number_of_premature_leaves = number_of_premature_leaves + 1 WHERE id = ?;"
            values = (chat_id,)
            await con.execute(sql, values)
        await con.commit()

        print("updated values")
        async with con.execute("SELECT * FROM customers") as cursor:
            async for row in cursor:
                print(row)


async def customer_query(sort_dttm=None, *args):
    async with sl.connect(db_path, check_same_thread=False) as con:
        if not args:
            columns = '*'
        else:
            columns = ','.join(args)

        if sort_dttm:
            sort_dttm = 'ORDER BY time_arrive ASC'
        else:
            sort_dttm = ''

        dat = []
        async with con.execute(f"SELECT {columns} FROM customers {sort_dttm}") as cursor:
            async for row in cursor:
                dat.append(row)
        return dat


async def customer_suspend(id=None):
    async with sl.connect(db_path, check_same_thread=False) as con:
        dat = []
        async with con.execute(f"SELECT * FROM customers WHERE id = {id}") as cursor:
            async for row in cursor:
                dat.append(row)
        return dat
