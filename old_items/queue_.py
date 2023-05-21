#TODO: Методология очереди. Добавить функцию возвращающую очередь обычным sort
import sqlite3 as sl
import os

def user_queue(message):
    db_path = os.path.join(os.path.dirname(__file__), '../queue_database', 'cstmrs.db')
    con = sl.connect(db_path)

    dat = con.execute("SELECT * FROM customers")
    dat_list = list(dat)  # convert to a list of tuples
    print(f"Data list: {dat_list}")

    sorted_users = sorted(dat_list, key=lambda x: x[5])  # sort by the 5th item in each tuple
    print(f"Sorted users: {sorted_users}")

    return sorted_users
