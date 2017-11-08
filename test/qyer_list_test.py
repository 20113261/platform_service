#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午11:14
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_list_test.py
# @Software: PyCharm
from proj.qyer_list_task import qyer_list_task
from proj.my_lib.BaseTask import TaskResponse

if __name__ == '__main__':
    # task.content = 'http://place.qyer.com/asilah/'
    # qyer_list_task('qyer', '10001', '101', '20170925', city_url='http://place.qyer.com/bangkok/',
    # task_name='list_qyer_total_test')

    qyer_list_task('qyer', 'test', 'test', '20170925', city_url='http://place.qyer.com/st-augustine/',
                   task_name='list_qyer_total_test', task_response=TaskResponse)
