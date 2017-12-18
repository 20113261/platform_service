#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午11:14
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_list_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import qyer_list_task

if __name__ == '__main__':
    # args = {
    #     'source': 'qyer',
    #     'country_id': '412',
    #     'city_id': '40051',
    #     'check_in': '20170925',
    #     'city_url': 'http://place.qyer.com/praslin-island/'
    # }

    args = {
        "check_in": "20180128",
        "city_id": "20645",
        "country_id": "133",
        "source": "qyer",
        "city_url": "http://place.qyer.com/albania/",
        "date_index": 0
    }

    task = Task(_worker='', _task_id='demo', _source='qyer', _type='poi_list', _task_name='list_qyer_total_test',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    qyer_list_task(task=task)
