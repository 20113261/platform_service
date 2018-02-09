# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
@author: feng
@date: 2018-02-01
@purpose: ctrip poi list sdk
'''
from __future__ import absolute_import
import datetime
import pymongo
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
from proj.my_lib.Common.Browser import proxy_pool


mioji.common.pool.pool.set_size(128)
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = simple_get_socks_proxy
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
SQL = "INSERT IGNORE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)"

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
collections = client['data_result']['ctrip_poi_list']


def ctrip_poilist_to_database(tid, used_times, source, city_id, city_url, need_cache=True):
    task = Task()
    task.content = city_url
    task.ticket_info = {
        'tid': tid,
        'used_times': used_times
    }
    spider = factory.get_spider_by_old_source('ctripPOI')
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['POIlist'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['POIlist'], cache_config=none_cache_config)
    print(error_code)
    logger.info(str(spider.result['POIlist']) + '  --  ' + task.content)
    return error_code, spider.result['POIlist'], spider.page_store_key_list


class PoiCtripListSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109, 29]

    def _execute(self, **kwargs):
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        city_url = self.task.kwargs['city_url']

        error_code, result, page_store_key = ctrip_poilist_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            source=self.task.kwargs['source'],
            city_id=city_id,
            city_url=city_url,
            need_cache=self.task.used_times == 0
        )

        collections.save({
            'collections': self.task.collection,
            'task_id': self.task.task_id,
            'used_times': self.task.used_times[0],
            'stored_page_keys': page_store_key,
            'city': city_url,
            'result': result,
            'insert_time': datetime.datetime.now()
        })

        self.task.error_code = error_code

        sql = SQL.format(self.task.task_name)
        data = []
        for sid, tag, url in result:
            data.append(('ctripPoi', sid, city_id, country_id, url))
        try:
            service_platform_conn = service_platform_pool.connection()
            cursor = service_platform_conn.cursor()
            _res = cursor.executemany(sql, data)
            service_platform_conn.commit()
            cursor.close()
            service_platform_conn.close()
            self.task.get_data_per_times = len(data)
            self.task.list_task_insert_db_count = _res
        except Exception as e:
            raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        if len(data) > 0:
            self.task.error_code = 0
        else:
            raise ServiceStandardError(error_code=ServiceStandardError.EMPTY_TICKET)

        return result, error_code


if __name__ == '__main__':
    from proj.my_lib.Common.Task import Task as ttt
    args = {
        "city_id": "20645",
        "country_id": "133",
        "source": "ctripoi",
        "city_url": "asti7060",
        "date_index": 0
    }

    task = ttt(_worker='', _task_id='demo', _source='ctripPoi', _type='poi_list', _task_name='list_qyer_total_test',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    s = PoiCtripListSDK(task= task)
    s.execute()
