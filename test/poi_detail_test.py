#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午10:24
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_detail_test.py
# @Software: PyCharm
import sys

sys.path.append('/data/lib')
from proj.my_lib.Common.Task import Task
from proj.total_tasks import poi_detail_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='Daodao', _type='attr', _task_name='detail_attr_daodao_20171222a',
                _used_times=0, max_retry_times=6,
                kwargs={
                    # 'target_url': 'https://www.tripadvisor.cn//Attraction_Review-g187492-d13168754-Reviews-Centro_de_Interpretacion_de_los_Castros-Leon_Province_of_Leon_Castile_and_Leon.html',
                    # 'target_url': 'https://www.tripadvisor.cn//Attraction_Review-g297697-d10126675-Reviews-JBS_Photo_Canvas-Kuta_Kuta_District_Bali.html',
                    'target_url': 'https://www.tripadvisor.cn//Attraction_Review-g297697-d10126675-Reviews-JBS_Photo_Canvas-Kuta_Kuta_District_Bali.html',
                    'city_id': 'NULL',
                    'poi_type': 'attr',
                    'country_id': 'NULL',
                    'part': "detail_attr_daodao_20171222a"
                }, _routine_key='list_task', _queue='poi_detail', list_task_token='demo', task_type=0)
    poi_detail_task(task=task)
