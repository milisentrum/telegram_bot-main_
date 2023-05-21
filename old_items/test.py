import numpy as np



size = 1000
age = np.around(np.random.random(size)*80, decimals=0).reshape(-1,1).astype(int)
gender = np.random.randint(0, 2, size).reshape(-1,1)
is_hurry = np.random.randint(0, 2, size).reshape(-1,1)
queue_rank = (np.random.randint(0, size, size=size)).reshape(-1,1)
print(np.concatenate((age,gender,is_hurry, queue_rank), axis=1))