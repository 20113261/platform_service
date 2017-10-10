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
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config

from urlparse import urljoin
import traceback
import datetime

logger = get_logger("poiDaodao")

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

mioji.common.logger.logger = logger

URL = 'https://www.tripadvisor.cn'
SQL = """replace into {table_name} (source, source_id, city_id, country_id, hotel_url) values(%s, %s, %s, %s, %s, %s)"""
type_dict = {'attr': 'view', 'rest': 'restaurant'}
spider_name = {'attr': 'View', 'rest': 'Rest'}


def hotel_list_database(source, url, required, old_spider_name, need_cache=True):
    try:
        task = Task()
        task.content = urljoin(URL, url)
        logger.info('%s  %s' % (task.content, required))
        task.source = source.lower().capitalize() + 'ListInfo'
        # spider = factory.get_spider('daodao', task.source)
        spider = factory.get_spider_by_old_source('daodao' + old_spider_name)
        spider.task = task
        if need_cache:
            code = spider.crawl(required=[required], cache_config=cache_config)
        else:
            code = spider.crawl(required=[required], cache_config=none_cache_config)
        return code, spider.result.get(required, {})
    except Exception as e:
        logger.error(traceback.format_exc(e))
        raise e


def insert(sql, data):
    # TODO 连接池处理未指定
    service_platform_conn = service_platform_pool.connection()
    cursor = service_platform_conn.cursor()
    cursor.executemany(sql, data)
    service_platform_conn.commit()
    cursor.close()
    service_platform_conn.close()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def poi_list_task(self, source, url, city_id, country_id, poi_type, **kwargs):
    task_response = kwargs['task_response']
    task_response.source = source.title()
    task_response.type = 'DaodaoListInfo'

    sql = SQL.format(table_name=kwargs.get('task_name'))

    retry_count = kwargs.get('retry_count', 0)
    code, result = hotel_list_database(source, url, type_dict[poi_type], spider_name[poi_type],
                                       need_cache=retry_count == 0)

    task_response.error_code = code

    data = []
    try:
        for one in result:
            for key, view in one.items():
                data.append(
                    (source, view['source_id'], city_id, country_id, view['view_url']))
        insert(sql, data)
    except Exception as e:
        task_response.error_code = 33
        logger.error(traceback.format_exc(e))
        raise e

    # 由于错误都是 raise 的，
    # 所以当出现此种情况是，return 的内容均为正确内容
    # 对于抓取平台来讲，当出现此中情况时，数据均应该入库
    # 用 res_data 判断，修改 self.error_code 的值
    if len(data) > 0:
        task_response.error_code = 0
    else:
        task_response.error_code = 29

    return task_response.error_code, url
