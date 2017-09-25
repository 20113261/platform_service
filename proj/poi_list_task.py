#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from __future__ import absolute_import

from mioji.spider_factory import factory
from mioji.common.task_info import Task
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.pool
import mioji.common.pages_store

from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.logger import get_logger
from proj.mysql_pool import service_platform_pool
from proj.list_config import cache_config, list_cache_path

import datetime

logger = get_logger("poiDaodao")

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)
mioji.common.pages_store.cache_dir = list_cache_path

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

mioji.common.logger.logger = logger

URL = 'https://www.tripadvisor.cn'
SQL = """replace into {table_name} (source, source_id, city_id, country_id, hotel_url, utime) values(%s, %s, %s, %s, %s, %s)"""
type_dict = {'attr': 'shop', 'rest': 'restaurant'}


def hotel_list_database(source, url, required):
    task = Task()
    task.content = URL + url
    task.source = source.lower().capitalize() + 'ListInfo'
    spider = factory.get_spider('daodao', task.source)
    spider.task = task
    code = spider.crawl(required=[required], cache_config=cache_config)
    return code, spider.result.get(required, {})


def insert(sql, data):
    # TODO 连接池处理未指定
    service_platform_conn = service_platform_pool.connection()
    cursor = service_platform_conn.cursor()
    cursor.executemany(sql, data)
    service_platform_conn.commit()
    cursor.close()
    service_platform_conn.close()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
def poi_list_task(self, source, url, city_id, country_id, poi_type, **kwargs):
    self.task_source = source.title()
    self.task_type = 'DaodaoListInfo'
    self.error_code = 103
    sql = SQL.format(table_name=kwargs.get('task_name'))
    code, result = hotel_list_database(source, url, type_dict[poi_type])

    self.error_code = code

    data = []
    try:
        for one in result:
            for key, view in one.items():
                data.append(
                    (source, int(view['source_id']), int(city_id), country_id, view['view_url'],
                     datetime.datetime.now()))
        insert(sql, data)
    except Exception as e:
        self.error_code = 33
        raise e

    self.error_code = code

    logger.info('code: %s' % self.error_code)
    return data
