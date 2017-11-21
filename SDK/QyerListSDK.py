# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import

import mioji.common.logger
import mioji.common.pages_store
import mioji.common.pool
from celery.utils.log import get_task_logger
from mioji import spider_factory
from mioji.common.task_info import Task
from mioji.common.utils import simple_get_socks_proxy
from mioji.spider_factory import factory

from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.mysql_pool import service_platform_pool

mioji.common.pool.pool.set_size(2024)
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
SQL = "INSERT IGNORE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)"


def hotel_list_database(source, city_id, check_in, city_url, need_cache=True):
    task = Task()
    task.content = city_url
    spider = factory.get_spider_by_old_source('qyerList')
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['list'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['list'], cache_config=none_cache_config)
    print(error_code)
    logger.info(str(spider.result['list']) + '  --  ' + task.content)
    return error_code, spider.result['list']


class QyerListSDK(BaseSDK):
    def _execute(self, **kwargs):
        # 穷游数据特殊，29 不可以定为完成
        self.finished_error_code = [0, 106, 107, 109]

        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        check_in = self.task.kwargs['check_in']
        city_url = self.task.kwargs['city_url']

        error_code, result = hotel_list_database(source=self.task.kwargs['source'], city_id=city_id,
                                                 check_in=check_in,
                                                 city_url=city_url,
                                                 need_cache=self.task.used_times == 0)

        self.task.error_code = error_code

        sql = SQL.format(self.task.task_name)
        data = []
        for sid, url in result:
            data.append(('qyer', sid, city_id, country_id, url))
        try:
            service_platform_conn = service_platform_pool.connection()
            cursor = service_platform_conn.cursor()
            _res = cursor.executemany(sql, data)
            service_platform_conn.commit()
            cursor.close()
            service_platform_conn.close()
            self.task.list_task_insert_db_count = _res
        except Exception as e:
            raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        if len(data) > 0:
            self.task.error_code = 0
        else:
            raise ServiceStandardError(error_code=ServiceStandardError.EMPTY_TICKET)

        return result, error_code
