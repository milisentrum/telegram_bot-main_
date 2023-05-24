import datetime
from datetime import timedelta
import numpy as np
from queue_database.database import *

set_ = [(1234567890, 'Bob', 32, 'М', 1, 17, '15:46:29', None, None, 0),
(9876543210, 'Charlie', 27, 'М', 3, 31, '15:49:29', None, '16:14:29', 0),
(2468135790, 'Diana', 45, 'Ж', 1, 29, '15:01:29', None, None, 0),
(1357924680, 'Eva', 29, 'Ж', 1, 65, '15:54:29', None, None, 0),
(3141592653, 'Frank', 38, 'М', 3, 48, '15:55:29', None, None, 0),
(2718281828, 'Grace', 19, 'Ж', 3, 110, '14:59:29', None, None, 0),
(1123581321, 'Henry', 55, 'М', 3, 94, '15:20:29', None, None, 0),
(2233445566, 'Iris', 22, 'Ж', 3, 81, '15:04:29', None, None, 0),
(4455667788, 'John', 42, 'М', 3, 20, '15:28:29', None, None, 0),
(9988776655, 'Kate', 24, 'Ж', 1, 5, '15:27:29', None, None, 0),
(7777777777, 'Leo', 50, 'М', 1, 3, '15:52:29', None, None, 0),
(9999999999, 'Mia', 31, 'Ж', 1, 140, '15:46:29', None, None, 0),
(1231231231, 'Nick', 36, 'М', 3, 65, '15:40:29', None, None, 0),
(4564564564, 'Olga', 28, 'Ж', 3, 58, '15:44:29', None, None, 0),
(7897897897, 'Peter', 43, 'М', 3, 34, '15:38:29', None, None, 0),
(6546546546, 'Rachel', 26, 'Ж', 1, 56, '15:52:29', None, None, 0),
(9879879879, 'Sam', 47, 'М', 2, 43, '15:16:29', None, None, 0),
(3213213213, 'Tom', 30, 'М', 2, 19, '15:10:29', None, None, 0),
(6549873210, 'Vera', 25, 'Ж', 2, 35, '15:24:29', None, None, 0),]

class EXTimings():
    def __init__(self, rate_per_hour=3.5, start_hour=10, end_hour=20):

        self.interval = 60/rate_per_hour
        self.now = datetime.datetime.now()
        self.start = datetime.datetime(self.now.year, self.now.month, self.now.day, start_hour, 0)
        self.end = datetime.datetime(self.now.year, self.now.month, self.now.day, end_hour, 0)
        self.exams = [self.start]
        self.closest_index = 0
        self.queue_db = await customer_query(sort_dttm=True)

    def count_time(self, ):
        current_db=await customer_query()
        self.queue_db.append(self.sort_nested(self.db_list_lsync(self.queue_db, current_db)))


    def db_list_lsync(self, q_list:list, db_list:list):
        return [db_item for q_item,db_item in zip(q_list, db_list) if q_item[0] != db_item[0]]


    def fill_exams(self, ):
        while self.exams[-1] +timedelta(days=0,seconds=self.interval*60,microseconds=0) < self.end:
            self.exams.append(self.exams[-1]+timedelta(seconds=self.interval*60))

    def get_nearest(self, ):
        i = 0
        now_ = datetime.datetime.now()
        while now_>self.exams[i]:
            i+=1
        self.closest_index = i

    def sort_nested(self, list_, ind=6):
        return sorted(list_, key=lambda x: x[ind])

    def original_order(self, list_):
        original_order = np.array(self.sort_nested([i for i in list_ if i[8] is None]))

        #queue pos
        queue_pos_orig = np.array([[i] for i in range(len(original_order))])
        original_order = np.append(original_order, queue_pos_orig, axis=1)

        #delta from next exam
        timedelta_,exams = [], []
        self.get_nearest()
        m = self.closest_index
        for i in range(len(original_order)):
            if (i)%4==0:
                m+=1
            timedelta_.append([(self.exams[m] - datetime.datetime.strptime(original_order[i, 6], "%H:%M:%S") - timedelta(days=45060)).seconds])
            exams.append([self.exams[m].strftime("%H:%M:%S")])
        original_order = np.append(original_order, np.array(timedelta_), axis=1)
        # original_order = np.append(original_order, np.array(exams), axis=1)

        original_order = np.append(original_order, (-original_order[:, 11]+60*original_order[:, 5]).reshape(-1,1), axis=1)

        original_order = original_order[original_order[:, 4].argsort()[::-1]]
        queue_pos_new = np.array([[i] for i in range(len(original_order))])
        original_order = np.append(original_order, queue_pos_new, axis=1)

        final_order = np.append(original_order, (original_order[:, 10] * 0.754 + original_order[:, 12] * 0.001 + 0.143 * original_order[:, 13]).reshape(-1,1), axis=1)
        final_order = final_order[final_order[:, 14].argsort()]
        final_order = np.append(final_order, np.array(exams).reshape(-1,1),axis=1)
        return final_order[:, [1,15]]





# todo: асинхронный while true lsync бд
