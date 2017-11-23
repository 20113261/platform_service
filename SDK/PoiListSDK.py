#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/29 上午10:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
from __future__ import absolute_import

import traceback
from urlparse import urljoin

import mioji.common.pages_store
import mioji.common.pool
import mioji.common.spider
from mioji import spider_factory
from mioji.common.task_info import Task
from mioji.common.utils import simple_get_socks_proxy
from mioji.spider_factory import factory

from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.logger import get_logger
from proj.mysql_pool import service_platform_pool

logger = get_logger("poiDaodao")

mioji.common.spider.NEED_FLIP_LIMIT = False
mioji.common.pool.pool.set_size(2024)
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = True
spider_factory.config_spider(insert_db, None, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

mioji.common.logger.logger = logger

URL = 'https://www.tripadvisor.cn'
SQL = """replace into {table_name} (source, source_id, city_id, country_id, hotel_url) values(%s, %s, %s, %s, %s)"""
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
    _res = cursor.executemany(sql, data)
    service_platform_conn.commit()
    cursor.close()
    service_platform_conn.close()
    return _res


class PoiListSDK(BaseSDK):
    def _execute(self, **kwargs):
        sql = SQL.format(table_name=self.task.task_name)
        poi_type = self.task.kwargs['poi_type']
        code, result = hotel_list_database(self.task.kwargs['source'], self.task.kwargs['url'],
                                           type_dict[poi_type],
                                           spider_name[poi_type],
                                           need_cache=self.task.used_times == 0)
        self.logger.info('spider    %s %s' % (str(code), str(result)))
        self.task.error_code = code

        data = []
        try:
            for one in result:
                for key, view in one.items():
                    data.append(
                        (self.task.kwargs['source'], view['source_id'], self.task.kwargs['city_id'],
                         self.task.kwargs['country_id'], view['view_url']))
                    logger.info('%s' % str((self.task.kwargs['source'], view['source_id'], self.task.kwargs['city_id'],
                                            self.task.kwargs['country_id'], view['view_url'])))
            logger.info('%s %s' % (sql, str(data)))
            res = insert(sql, data)
            self.task.list_task_insert_db_count = res
            self.task.get_data_per_times = len(data)
        except Exception as e:
            self.logger.exception(msg="[insert db error]", exc_info=e)
            raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        # 由于错误都是 raise 的，
        # 所以当出现此种情况是，return 的内容均为正确内容
        # 对于抓取平台来讲，当出现此中情况时，数据均应该入库
        # 用 res_data 判断，修改 self.error_code 的值
        if len(data) > 0:
            self.task.error_code = 0
        else:
            raise ServiceStandardError(error_code=ServiceStandardError.EMPTY_TICKET)

        return self.task.error_code, self.task.kwargs['url']
