#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/21 下午3:56
# @Author  : Hou Rong
# @Site    : 
# @File    : europe_station_test.py
# @Software: PyCharm
import sys

sys.path.append('/data/lib')
import pymysql
from SDK import EuropeStationSDK
from proj.my_lib.Common.Task import Task

if __name__ == '__main__':
    db = pymysql.connect(host='10.10.230.206', user='mioji_admin', passwd='mioji1109', db='source_info', charset='utf8')
    cur = db.cursor()
    try:
        sql = '''SELECT
  sid,
  s_city,
  s_country
FROM ota_location_for_european_trail;'''
        cur.execute(sql)
        r = cur.fetchall()
        lis = []
        for g in r:
            lis.append(g[0] + '&' + g[1] + '&' + g[2])
    except Exception as e:
        print('err', e)
    cur.close()
    db.close()
    args = {
        'city_code': g[0],
        'city_name': g[1],
        'country_code': g[2]
    }
    task = Task(_worker='', _task_id='demo', _source='ihg', _type='poi_list', _task_name='ihg_city_suggest',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')

    _sdk = EuropeStationSDK(task=task)
    _sdk.execute()
