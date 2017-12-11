#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/11 下午11:29
# @Author  : Hou Rong
# @Site    : 
# @File    : test_baidu_search.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
# from proj.total_tasks import baidu_search_task
from SDK import BaiDuSearchSDK

if __name__ == '__main__':
    args = {
        'keyword': 'site:place.qyer.com 巴伐利亚自由州'
    }
    task = Task(_worker='proj.total_tasks.baidu_search_task', _queue='supplement_field',
                _routine_key='supplement_field',
                _task_name='demo', _source='Qyer', _type='CityInfo', task_type=0, _used_times=0,
                max_retry_times=6, collection='Unknown', _task_id='demo', list_task_token='null', kwargs=args)

    # hotel_img_merge_task(task=task)
    # baidu_search_task(task=task)
    _sdk = BaiDuSearchSDK(task=task)
    _sdk.execute()
