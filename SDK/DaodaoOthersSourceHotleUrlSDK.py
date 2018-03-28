#!/usr/bin/env python
# -*- coding:utf-8 -*-
from proj.my_lib.Common.BaseSDK import BaseSDK
import pymongo
import types
from mioji import spider_factory
MONGODB_CONFIG = {
    'host': '10.10.213.148'
}
from mioji.common.task_info import Task
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from mioji.spider_factory import factory
from proj.my_lib import ServiceStandardError
from proj.my_lib.Common.Browser import proxy_pool
from celery.utils.log import get_task_logger
import mioji.common.logger
import mioji.common.pages_store
import mioji.common.pool
mioji.common.pool.pool.set_size(128)
logger = get_task_logger(__name__)
mioji.common.logger.logger = loggergg
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = simple_get_socks_proxy
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)

def hotel_url_to_database(tid, used_times, source, keyword, spider_tag, need_cache=False):
    task = Task()
    task.ticket_info['url'] = keyword
    spider = factory.get_spider_by_old_source(spider_tag)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(cache_config=cache_config)
    else:
        error_code = spider.crawl(cache_config=none_cache_config)
    print(error_code)
    return error_code, spider.result

class OthersSourceHotelUrl(BaseSDK):

    def _execute(self, **kwargs):
        url = kwargs.get('url')
        spider_tag = self.task.kwargs['spider_tag']
        source = self.task.kwargs['source']
        error_code, values = hotel_url_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            spider_tag=spider_tag,
            source=source,
            keyword=url,
            need_cache=self.task.used_times == 0
        )
        client = pymongo.MongoClient(**MONGODB_CONFIG)
        db = client['HotelUrl']['DaoDaoSourceUrl']
        db.insert(values)
        if error_code == 0:
            self.finished_error_code = 0
        else:
            raise ServiceStandardError.ServiceStandardError(error_code,msg="爬虫出现错误")

if __name__ == "__main__":
    pass