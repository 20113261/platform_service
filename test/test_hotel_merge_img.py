#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 下午2:35
# @Author  : Hou Rong
# @Site    : 
# @File    : test_hotel_merge_img.py
# @Software: PyCharm
from proj.merge_tasks import hotel_img_merge
from proj.my_lib.Common.TaskResponse import TaskResponse

if __name__ == '__main__':
    hotel_img_merge(
        **{
            'uid': 'ht21794341',
            'min_pixels': '200000',
            "task_name": "test_task",
            "task_response": TaskResponse()
        })
