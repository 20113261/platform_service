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
            'target_url': 'https://www.tripadvisor.cn//Attraction_Review-g262058-d12392505-Reviews-Edificio_de_Las_Tres_Campanas-Badajoz_Province_of_Badajoz_Extremadura.html',
            'city_id': '10639',
            'poi_type': 'attr',
            'country_id': 'NULL',
            'task_name': 'detail_hotel_hotels_20170925d',
            'retry_count': 0,
            'max_retry_times': 6
        }
    )
