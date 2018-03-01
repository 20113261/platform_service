# coding=utf-8

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
collections = client['data_result']['ctrip_poi_detail']


def ctrip_poidetail_to_database(tid, used_times, source, url, need_cache=True):
    task = Task()
    task.content = url
    task.ticket_info = {
        'tid': tid,
        'used_times': used_times
    }
    spider = factory.get_spider_by_old_source('CtripPoi')
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['POIdetail'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['POIdetail'], cache_config=none_cache_config)
    print(error_code)
    logger.info(str(spider.result['POIdetail']) + '  --  ' + task.content)
    return error_code, spider.result['POIdetail'], spider.page_store_key_list

class PoiCtripDetailSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109]

    def _execute(self, **kwargs):
        poi_id = self.task.kwargs['poi_id']
        tag = self.task.kwargs['tag']
        url = self.task.kwargs['detail_url']
        city_id = self.task.kwargs['city_id']

        error_code, result, page_store_key = ctrip_poidetail_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            source=self.task.kwargs['source'],
            url=url,
            need_cache=self.task.used_times == 0
        )

        collections.save({
            'collections': self.task.collection,
            'task_id': self.task.task_id,
            'used_times': self.task.used_times[0],
            'stored_page_keys': page_store_key,
            'url': url,
            'poi_id':poi_id,
            'tag': tag,
            'result': result,
            'city_id':city_id,
            'insert_time': datetime.datetime.now()
        })
        # -- detail 2 mysql --

        self.task.error_code = error_code

if __name__ == '__main__':
    from proj.my_lib.Common.Task import Task as ttt
    args = {
        'source': 'ctripoi',
        'poi_id': '109889',
        'tag': 'sight',
        'city_id':'000',
        'detail_url':'http://you.ctrip.com/sight/sedaxian120478/109889.html'
    }

    task = ttt(_worker='', _task_id='demo', _source='ctripPoi', _type='poi_detail', _task_name='ctrip_poi_detail',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='poi_list',
                _routine_key='poi_list', list_task_token='test', task_type=0, collection='')
    s = PoiCtripDetailSDK(task= task)
    s.execute()
