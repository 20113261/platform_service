#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:24
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_list_test.py
# @Software: PyCharm
from proj.celery import app
# from proj.hotel_list_task import hotel_list_task

if __name__ == '__main__':
    # hotel_list_task('booking', '10001', '501', '20171102', 'test', task_name="list_hotel_booking_test")

    print(app.send_task(
        'proj.hotel_list_task.hotel_list_task',
        args=('booking', '51211', '501', '20171102', 'test'),
        kwargs=dict(task_name="list_hotel_booking_test"),
        queue='hotel_list_task',
        routing_key='hotel_list_task'
    ))
