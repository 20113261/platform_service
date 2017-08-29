#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
# import os
# os.environ["CONFIG_FILE"] = '/root/data/lib/slave_develop_new/workspace/spider/SpiderClient/conf/conf_lwn.ini'
# from celery.utils.log import get_task_logger
import mysql.connector
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.logger
import datetime
import mioji.common.pool
import traceback
from proj.my_lib.logger import get_logger
logger = get_logger("viewDaodao")

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)

# from proj.test_spider import DaodaoViewSpider

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

# logger = get_task_logger(__name__)
mioji.common.logger.logger = logger

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
URL = 'https://www.tripadvisor.com.hk'

def hotel_list_database(source, url):
    task = Task()
    task.content = URL+url
    task.source = source.lower().capitalize() + 'ListInfo'
    spider = factory.get_spider('daodao', task.source)
    # spider = factory.get_spider_by_old_source(task.source)
    # spider = DaodaoViewSpider()
    spider.task = task
    code = spider.crawl(required=['view'])
    return code, spider.result.get('view', {})


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
def hotel_view_list_task(self, source, url, city_id, **kwargs):
    try:
        self.task_source = source.title()
        self.task_type = 'DaodaoListInfo'

        code, result = hotel_list_database(source, url)

        self.error_code = str(code)

        data_res = []

        for one in result:
            for key, view in one.items():
                data_res.append((source, int(view['source_id']), city_id, view['view_url'], view['view_name'].strip('\n').strip(), datetime.datetime.now()))

        cursor = conn.cursor()
        sql = "REPLACE INTO hotel_list_view (source, source_id, city_id, url, name, utime) VALUES (%s,%s,%s,%s,%s,%s)"
        cursor.executemany(sql, data_res)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logger.exception(traceback.format_exc(e))


if __name__ == '__main__':
    print hotel_view_list_task('daodao', '/Tourism-g4665321-Mendocino_County_California-Vacations.html', '29106')
