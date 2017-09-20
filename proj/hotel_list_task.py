# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import
from celery.utils.log import get_task_logger
import json
import traceback
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji.common.utils import simple_get_socks_proxy
from mioji import spider_factory
import mioji.common.spider
import mioji.common.logger
import datetime
import pymongo
import mysql.connector
import mioji.common.pool
import mioji.common

mioji.common.pool.NEED_MONKEY_PATCH = False
mioji.common.pool.pool.set_size(2024)
mioji.common.spider.NEED_FLIP_LIMIT = False
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger

# pymongo client

# client = pymongo.MongoClient(host='10.10.231.105')
# collections = client['HotelList']['ctrip']
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}

db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
conn = mysql.connector.connect(pool_name="hotel-list-value-pool",
                               pool_size=15,
                               **db_config)


def hotel_list_database(source, city_id, check_in):
    task = Task()
    if source == 'hilton':
        task.content = check_in
    else:
        task.content = str(city_id) + '&' + '2&1&{0}'.format(check_in)

    spider = factory.get_spider_by_old_source(source + 'ListHotel')
    spider.task = task
    print spider.crawl(required=['hotel'])
    logger.info(str(spider.result['hotel']) + '  --  ' + task.content)
    return spider.result


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def hotel_list_task(self, source, city_id, country_id, check_in, part, **kwargs):
    self.task_source = source.title()
    self.task_type = 'HotelList'
    self.error_code = 0

    result = hotel_list_database(source=source, city_id=city_id, check_in=check_in)

    res_data = []
    if source in ('ctrip', 'ctripcn'):
        for line in result['hotel']:
            sid = line[3]
            hotel_url = line[-1]
            res_data.append((source, sid, city_id, country_id, hotel_url))
    elif source == 'hilton':
        for dict_obj in result['hotel']:
            line = dict_obj.values()
            res_data.append((source, line[2], city_id, country_id, line[0]))
    else:
        for sid, hotel_url in result['hotel']:
            res_data.append((source, sid, city_id, country_id, hotel_url))

    try:
        cursor = conn.cursor()
        sql = "REPLACE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)".format(
            kwargs['task_name'])
        cursor.executemany(sql, res_data)
        conn.commit()
    except Exception as e:
        self.error_code = 33
        raise e


if __name__ == '__main__':
    print hotel_list_database('booking', '51211', '20170801')
