#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
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
from proj.my_lib.BaseTask import BaseTask
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.logger
import datetime
import mioji.common.pool

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)


# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

logger = get_task_logger(__name__)
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

def hotel_list_database(source, city_id, url, check_in):
    task = Task()
    task.content = URL+url
    task.source = source.lower().capitalize() + 'ListInfo'
    spider = factory.get_spider_by_old_source(task.source)
    spider.task = task
    code = spider.crawl(required=['view'])
    return code, spider.result


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='5/s')
def hotel_routine_list_task(self, source, url, city_id, check_in, **kwargs):
    self.task_source = source.title()
    self.task_type = 'DaodaoListInfo'

    code, result = hotel_list_database(source=source, city_id=city_id, url=url, check_in=check_in)

    self.error_code = str(code)

    data_res = []
    for key, view in result.items():
        data_res.append((source, view[0], city_id, view[1], city_id[2], datetime.datetime.now()))

    cursor = conn.cursor()
    sql = "REPLACE INTO hotel_list_view (source, source_id, city_id, url, name, utime) VALUES (%s,%s,%s,%s,%s,%s)"
    cursor.executemany(sql, data_res)
    cursor.close()
    conn.commit()
    return True


if __name__ == '__main__':
    print hotel_list_database('daodao', '29106', '/Tourism-g187147-Paris_Ile_de_France-Vacations.html', '20170829')
