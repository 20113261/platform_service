# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import
from celery.utils.log import get_task_logger
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from mioji.common.utils import simple_get_socks_proxy
from mioji import spider_factory
from proj.mysql_pool import service_platform_pool
import mioji.common.logger
import mioji.common.pool
import mioji.common
import mioji.common.pages_store
from proj.list_config import cache_config, list_cache_path

mioji.common.pool.pool.set_size(2024)
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
SQL = "REPLACE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)"


def hotel_list_database(source, city_id, check_in, city_url):
    task = Task()
    task.content = city_url
    spider = factory.get_spider_by_old_source('qyerList')
    spider.task = task
    error_code = spider.crawl(required=['list'], cache_config=cache_config)
    print(error_code)
    logger.info(str(spider.result['list']) + '  --  ' + task.content)
    return error_code, spider.result['list']


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def qyer_list_task(self, source, city_id, country_id, check_in, city_url='', **kwargs):
    self.task_source = source.title()
    self.task_type = 'QyerList'
    self.error_code = 0

    error_code, result = hotel_list_database(source=source, city_id=city_id, check_in=check_in, city_url=city_url)

    sql = SQL.format(kwargs['task_name'])
    datas = []
    for item in result:
        for typ, urls in item.items():
            for sid, url in urls:
                datas.append(('qyer', sid, city_id, country_id, url))
                # if url.endswith('/'):
                #     datas.append(('qyer', sid, city_id, country_id, url))
                # else:
                #     datas.append(('qyer', sid, city_id, country_id, url))

    try:
        service_platform_conn = service_platform_pool.connection()
        cursor = service_platform_conn.cursor()
        cursor.executemany(sql, datas)
        service_platform_conn.commit()
        cursor.close()
        service_platform_conn.close()
    except Exception as e:
        self.error_code = 33
        raise e

    self.error_code = error_code
    return result, error_code


if __name__ == '__main__':
    print qyer_list_task('booking', '51211', '20170801')
