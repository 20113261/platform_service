#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/9 下午8:03
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_task_func_test.py
# @Software: PyCharm
from proj.my_lib.task_module.mongo_task_func import get_task_total_iter

if __name__ == '__main__':
    import time

    queue_name = 'file_downloader'
    print(time.time())
    for line in get_task_total_iter('file_downloader', limit=50, debug=True):
        # print(line)
        pass
    time.sleep(2)

    for line in get_task_total_iter('hotel_list', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)
    for line in get_task_total_iter('hotel_detail', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)

    for line in get_task_total_iter('poi_list', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)

    for line in get_task_total_iter('poi_detail', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)

    print(time.time())
    for line in get_task_total_iter('file_downloader', limit=50, debug=True):
        # print(line)
        pass
    time.sleep(2)

    for line in get_task_total_iter('hotel_list', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)
    for line in get_task_total_iter('hotel_detail', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)

    for line in get_task_total_iter('poi_list', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)

    for line in get_task_total_iter('poi_detail', limit=50, debug=True):
        # print(line)
        pass

    time.sleep(2)
