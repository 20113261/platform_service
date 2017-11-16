#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午10:24
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_detail_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import poi_detail_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='daodao', _type='attr', _task_name='detail_attr_daodao_20170929a',
                _used_times=0, max_retry_times=6,
                kwargs={
                    'target_url': 'https://www.tripadvisor.cn/Attraction_Review-g303631-d553566-Reviews-Catedral_da_Se_de_Sao_Paulo-Sao_Paulo_State_of_Sao_Paulo.html',
                    'city_id': 'NULL',
                    'poi_type': 'attr',
                    'country_id': 'NULL', })
    poi_detail_task(task=task)
