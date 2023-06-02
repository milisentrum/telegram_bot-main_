import datetime
from datetime import timedelta
import numpy as np
from queue_database.database import *
from formatted import *
import threading
import time

class EXTimings():
    def __init__(self, rate_per_hour=3.5, start_hour=datetime.datetime.now().hour, end_hour=20):
        self.interval = 60/rate_per_hour
        self.now = datetime.datetime.now()
        self.start = datetime.datetime(self.now.year, self.now.month, self.now.day, start_hour, 0)
        self.end = datetime.datetime(self.now.year, self.now.month, self.now.day, end_hour, 0)
        self.exams = [self.start]
        self.closest_index = 0
        self.queue_db = None
        self._running = True
        self.timedelta_orig = None
        self.timedelta_final = None
        self.timedelta_sarsa = None
        self.Q = None

    async def initialize(self):
        self.queue_db = await customer_query(sort_dttm=True)
        asyncio.ensure_future(self.check_for_new_users())

    '''
    Эта функция отвечает за синхронизацию текущей очереди с базой данных. 
    Она получает текущие записи из базы данных, сравнивает их с существующей очередью и 
    добавляет все новые записи в очередь. Перед добавлением новые записи сортируются.
    '''
    async def count_time(self):
        current_db = await customer_query()
        self.queue_db = self.sort_and_insert(self.queue_db, await self.db_list_lsync(current_db))

    '''
    Эта функция принимает в качестве аргументов два списка: список текущей очереди и список базы данных. 
    Она возвращает список записей, которые присутствуют в списке базы данных, но отсутствуют в списке очереди. 
    Это используется для определения новых записей, которые были добавлены в базу данных, но еще не включены в очередь.
    '''
    async def db_list_lsync(self, q_list: list):
        db_list = await customer_query()
        return [db_item for q_item, db_item in zip(q_list, db_list) if q_item[0] != db_item[0]]

    def sort_and_insert(self, sorted_list, new_users):
        for user in new_users:
            sorted_list.append(user)
        sorted_list.sort(key=lambda x: (x[4], x[6]))
        return sorted_list

    async def check_for_new_users(self):
        while self._running:
            while True:
                new_users = await self.db_list_lsync(await customer_query())
                if new_users:
                    self.queue_db = self.sort_and_insert(self.queue_db, new_users)
                await asyncio.sleep(1)

    def get_nearest(self, ):
        i = 0
        now_ = datetime.datetime.now()
        while i < len(self.exams) and now_ > self.exams[i]:
            i += 1
        self.closest_index = i

    '''
    Эта функция используется для заполнения списка экзаменов временными метками. 
    Она начинает с начального времени и продолжает добавлять интервалы (рассчитанные на основе ставки в час), 
    пока не достигнет конечного времени. Этот список представляет собой доступные временные интервалы для экзаменов.
    '''
    def fill_exams(self, ):
        while self.exams[-1] + timedelta(days=0, seconds=self.interval * 60, microseconds=0) < self.end:
            self.exams.append(self.exams[-1] + timedelta(seconds=self.interval * 60))

    def sort_nested(self, list_, ind=6):
        return sorted(list_, key=lambda x: x[ind])


    def sarsa_step(self, list__, idx):
        delta = np.random.randint(1,5)
        list_ = list__.copy()
        lenl = len(list_)
        if idx == 0:
            to = idx + delta
        elif idx == len(list_) - delta:
            to = idx - delta
        else:
            if np.random.rand() > 0.5:
                to = idx + delta
                to = min(lenl-1, to)
            else:
                to = idx - delta
                to = max(0, to)

        list_[idx], list_[to] = list_.copy()[to], list_.copy()[idx]
        return list_.copy(), to


    def timer_value(self, list_):
        timedelta_f = []
        m = self.closest_index
        for i in range(len(list_)):
            if (i) % 4 == 0:
                m = (m + 1) % len(self.exams)
            timedelta_f.append([(self.exams[m] - datetime.datetime.strptime(list_[i, 6],
                                                                            "%H:%M:%S") - timedelta(
                days=45060)).seconds])
        return int(np.mean(np.array(timedelta_f).reshape(-1, 1)))


    def qsa(self, time_new, time_last, action):
        return time_last - time_new + action

    def sarsa_adj(self, list_):
        original_order = np.array(self.sort_nested([i for i in list_ if i[8] is None]))
        queue_pos_orig = np.array([[i] for i in range(len(original_order))])
        original_order = np.append(original_order, queue_pos_orig, axis=1)
        ll = len(list_)
        iter=10
        golden_table = original_order.copy()
        alpha = 0.1
        time_golden = self.timer_value(golden_table)
        aplha = 0
        i, timer_last = 0, time_golden
        current = golden_table.copy()
        while (i < iter) and timer_last/time_golden > 0.8:
            max_ = -10000000
            print('iter: ', i)
            for j in range(len(current)):
                q_1 = None
                current_time = self.timer_value(current)
                q_1, to = self.sarsa_step(current, j)
                time_1 = self.timer_value(q_1)

                if time_1>current_time:
                    action_coef1 = 10
                else:
                    action_coef1 = -10

                action_coef2 = (q_1[j][4] - current[to][4]) * (j - to)

                qsa = self.qsa(time_1, current_time, action_coef2)

                # print('Q1', len(q_1), idx, to)
                for jj in range(len(q_1)):
                    q_1_ = None
                    q_1_, to_ = self.sarsa_step(q_1, jj)
                    # print(q_1_)
                    time_1_ = self.timer_value(q_1_)
                    if time_1_ > time_1:
                        action_coef1_ = 8
                    else:
                        action_coef1_ = -8

                    # print('Q1_', len(q_1_), idx_, to_)

                    action_coef2_ = (q_1_[jj][4] - q_1[to_][4]) * (jj - to_)
                    qsa_ = self.qsa(time_1_, time_1, action_coef2_)

                    qsa += alpha * (action_coef1 + action_coef1_ + 0.9 * qsa_ - qsa )

                    if max(max_,qsa) == qsa:
                        possible_out = None
                        max_ = qsa
                        possible_out = q_1.copy()
            current = None
            current = possible_out.copy()
            i+=1

        self.timedelta_sarsa = to_time(self.timer_value(current))
        m = self.closest_index
        exams = []
        for i in range(len(original_order)):
            if (i) % 4 == 0:
                m = (m + 1) % len(self.exams)
            exams.append([self.exams[m].strftime("%H:%M:%S")])
        current = np.append(current, np.array(exams).reshape(-1, 1), axis=1)
        return current[:, [1, 11]]




    def original_order(self, list_):
        original_order = np.array(self.sort_nested([i for i in list_ if i[8] is None]))
        queue_pos_orig = np.array([[i] for i in range(len(original_order))])
        original_order = np.append(original_order, queue_pos_orig, axis=1)
        timedelta_, exams = [], []
        self.get_nearest()
        m = self.closest_index
        for i in range(len(original_order)):
            if (i) % 4 == 0:
                m = (m + 1) % len(self.exams)
            timedelta_.append([(self.exams[m] - datetime.datetime.strptime(original_order[i, 6], "%H:%M:%S") - timedelta(days=45060)).seconds])
            exams.append([self.exams[m].strftime("%H:%M:%S")])
        timedelta_ = np.array(timedelta_).reshape(-1, 1)
        self.timedelta_orig = to_time(int(np.mean(timedelta_))) #.strftime("%H:%M:%S")

        original_order = np.append(original_order, timedelta_, axis=1)

        original_order = np.append(original_order, (-original_order[:, 11] + 60 * original_order[:, 5]).reshape(-1, 1), axis=1)
        original_order = original_order[original_order[:, 4].argsort()[::-1]]
        queue_pos_new = np.array([[i] for i in range(len(original_order))])
        original_order = np.append(original_order, queue_pos_new, axis=1)
        final_order = np.append(original_order, (
                    original_order[:, 10] * 0.754 + original_order[:, 12] * 0.001 + 0.143 * original_order[:, 13]).reshape(-1, 1), axis=1)
        final_order = final_order[final_order[:, 14].argsort()]
        final_order = np.append(final_order, np.array(exams).reshape(-1, 1), axis=1)

        timedelta_f, exams_f = [], []
        for i in range(len(final_order)):
            if (i) % 4 == 0:
                m = (m + 1) % len(self.exams)
            timedelta_f.append([(self.exams[m] - datetime.datetime.strptime(final_order[i, 6], "%H:%M:%S") - timedelta(days=45060)).seconds])
            exams_f.append([self.exams[m].strftime("%H:%M:%S")])
        timedelta_f = np.array(timedelta_f).reshape(-1, 1)
        self.timedelta_final = to_time(int(np.mean(timedelta_f))) #.strftime("%H:%M:%S")

        return final_order[:, [1, 15]]

    def stop(self):
        self._running = False
