#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
from celery.utils.log import get_task_logger
import mysql.connector
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseRoutineTask import BaseRoutineTask
from proj.my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.logger
import datetime
import pymongo
import mioji.common.pool

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)

# pymongo client

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['HotelList']['ctrip']
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

logger = get_task_logger(__name__)
mioji.common.logger.logger = logger

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}

# mysql connect pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
conn = mysql.connector.connect(pool_name="hotel-list-value-pool",
                               pool_size=10,
                               **db_config)


# def hotel_list_database(source, city_id):
#     task = Task()
#     task.content = str(city_id) + '&' + '2&{nights}&{check_in}'.format(**hotel_rooms)
#     spider = factory.get_spider_by_old_source(source + 'ListHotel')
#     spider.task = task
#     print spider.crawl(required=['hotel'])
#     return spider.result

def hotel_list_database(source, city_id, check_in):
    task = Task()
    task.content = str(city_id) + '&' + '2&1&{0}'.format(check_in)
    task.source = source + 'ListHotel'
    spider = factory.get_spider_by_old_source(task.source)
    spider.task = task
    print spider.crawl(required=['hotel'])
    return spider.result


@app.task(bind=True, base=BaseRoutineTask, max_retries=3, rate_limit='2/s')
def hotel_routine_list_task(self, source, city_id, check_in, **kwargs):
    self.task_source = source.title()
    self.task_type = 'HotelList'

    result = hotel_list_database(source=source, city_id=city_id, check_in=check_in)

    data_res = []
    if source == 'ctrip':
        for line in result['hotel']:
            city_id
            sid = line[3]
            hotel_url = line[-1]
            data_res.append((source, sid, city_id, hotel_url))
    else:
        for sid, hotel_url in result['hotel']:
            data_res.append((source, sid, city_id, hotel_url))

    cursor = conn.cursor()
    sql = "REPLACE INTO hotel_base_data_task (source, source_id, city_id, hotel_url) VALUES (%s,%s,%s,%s)"
    cursor.executemany(sql, data_res)
    cursor.close()
    conn.commit()
    return True


if __name__ == '__main__':
    print hotel_list_database('booking', '51211', '20170801')
