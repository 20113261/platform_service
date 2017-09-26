#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/26 下午5:18
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_list.py
# @Software: PyCharm
from proj.poi_list_task import poi_list_task

if __name__ == '__main__':
    poi_list_task(
        source='daodao',
        url='/Tourism-g488103-Grand_Baie-Vacations.html',
        city_id='51513',
        country_id='409',
        poi_type='rest',
        task_name='list_rest_daodao_20170925d',
        retry_count=1
    )
