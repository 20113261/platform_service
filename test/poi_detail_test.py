#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午10:24
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_detail_test.py
# @Software: PyCharm
from proj.poi_task import get_lost_poi
from proj.my_lib.BaseTask import TaskResponse

if __name__ == '__main__':
    get_lost_poi(
        **{
            # 'target_url': 'https://www.tripadvisor.cn//Restaurant_Review-g1049073-d2457617-Reviews-La_Tinita-Hanga_Roa_Easter_Island.html',
            # 'target_url': 'https://www.tripadvisor.cn/Attraction_Review-g194900-d4700816-Reviews-Tre_Ponti-Sanremo_Italian_Riviera_Liguria.html',
            'target_url': 'https://www.tripadvisor.cn//Attraction_Review-g154954-d252482-Reviews-Manitoba_Museum-Winnipeg_Manitoba.html',
            'city_id': 'NULL',
            'poi_type': 'attr',
            'country_id': 'NULL',
            'task_name': 'detail_attr_daodao_20170929a',
            'retry_count': 0,
            'max_retry_times': 6,
            'task_response': TaskResponse()
        }
    )
