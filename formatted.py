from typing import List
list_ = [['a',10], ['b',9]]


def queue_format(list_: List):
    return '\n'.join(['   '.join([str(j) for j in i]) for i in list_])


def sort_nested(list_):
    return (sorted(list_, key=lambda x: x[1]))


# print(sort_nested(list_))