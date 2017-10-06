# !/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import
from celery.utils.log import get_task_logger
import json
import traceback
import copy
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji.common.utils import simple_get_socks_proxy
from mioji import spider_factory
from proj.mysql_pool import service_platform_pool
import mioji.common.spider
import mioji.common.logger
import datetime
import pymongo
import mioji.common.pool
import mioji.common.pages_store
import mioji.common
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config

mioji.common.pool.pool.set_size(2024)
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# pymongo client

# client = pymongo.MongoClient(host='10.10.231.105')
# collections = client['HotelList']['ctrip']
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}


def hotel_list_database(source, city_id, check_in, is_new_type=False, suggest_type='1', suggest='', need_cache=True):
    task = Task()
    if not is_new_type:
        if source == 'hilton':
            task.content = check_in
        else:
            task.content = str(city_id) + '&' + '2&1&{0}'.format(check_in)

        task.ticket_info = {
            "is_new_type": False
        }
    else:
        task.ticket_info = {
            "is_new_type": True,
            "suggest_type": int(suggest_type),
            "suggest": suggest,
            "check_in": str(check_in),
            "stay_nights": '1',
            "occ": '2'
        }
        task.content = ''

    spider = factory.get_spider_by_old_source(source + 'ListHotel')
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['hotel'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['hotel'], cache_config=none_cache_config)
    logger.info(str(task.ticket_info) + '  --  ' + task.content)
    return error_code, spider.result


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='8/s')
def hotel_list_task(self, source, city_id, country_id, check_in, part, is_new_type=False, suggest_type='1', suggest='',
                    **kwargs):
    self.task_source = source.title()
    self.task_type = 'HotelList'
    self.error_code = 103

    retry_count = kwargs.get('retry_count', 0)
    error_code, result = hotel_list_database(source=source, city_id=city_id, check_in=check_in, is_new_type=is_new_type,
                                             suggest_type=suggest_type, suggest=suggest, need_cache=retry_count == 0)
    self.error_code = error_code

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
        service_platform_conn = service_platform_pool.connection()
        cursor = service_platform_conn.cursor()
        sql = "REPLACE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)".format(
            kwargs['task_name'])
        cursor.executemany(sql, res_data)
        service_platform_conn.commit()
        cursor.close()
        service_platform_conn.close()
    except Exception as e:
        self.error_code = 33
        raise e

    if error_code in (0, '0') and self.error_code == 103:
        self.error_code = 0

    return res_data, error_code, self.error_code, kwargs['task_name'], suggest


if __name__ == '__main__':
    print(hotel_list_database('booking', '51211', '20170801'))
