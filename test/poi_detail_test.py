#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午10:24
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_detail_test.py
# @Software: PyCharm
from proj.poi_task import get_lost_poi

if __name__ == '__main__':
    get_lost_poi(
        **{
            'target_url': 'https://www.tripadvisor.cn//Restaurant_Review-g1049073-d2457617-Reviews-La_Tinita-Hanga_Roa_Easter_Island.html',
            'city_id': '51512',
            'poi_type': 'rest',
            'country_id': 'NULL',
            'task_name': 'detail_rest_daodao_20170925d',
            'retry_count': 4,
            'max_retry_times': 6
        }
    )
