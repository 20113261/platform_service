#!/usr/bin/env python
# -*-coding:utf-8 -*-

from __future__ import absolute_import
import datetime
import pymongo
import types
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
logger = get_task_logger(__name__)
MONGODB_CONFIG = {
    'host': '10.10.213.148'
}
insert_db = None
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
client = pymongo.MongoClient(**MONGODB_CONFIG)


def suggest_to_database(tid, used_times, source, key,keyword, spider_tag, need_cache=True):
    task = Task()
    task.content = keyword
    task.ticket_info['key']=key
    spider = factory.get_spider_by_old_source(spider_tag)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['suggest'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['suggest'], cache_config=none_cache_config)
    logger.info(
        str(len(spider.result['suggest'])) + '  --  ' + keyword)
    return error_code, spider.result['suggest']


class AllSuggestCitySDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109]
    def _execute(self, **kwargs):
        spider_tag = self.task.kwargs['spider_tag']
        collection_name = self.task.kwargs['collection_name']
        key_word = self.task.kwargs['keyword']
        key = self.task.kwargs['key']
        source = self.task.kwargs['source']

        error_code, values = suggest_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            spider_tag=spider_tag,
            source=source,
            keyword = key_word,
            key = key,
            need_cache=self.task.used_times == 0
        )

        collection = client['CitySuggest'][collection_name]
        for value in values:
            if isinstance(value,(types.DictType,types.ListType)):
                collection.insert(value)
            else:
                content = {'suggest':value}
                collection.insert(content)
        if len(values) > 0:
            self.task.error_code = 0
        else:
            self.task.error_code = 29
        return self.task.error_code



if __name__ == "__main__":
    from proj.my_lib.Common.Task import Task as ttt
    args = {
        'keyword': 'Praia Grande (普拉亚格兰德)',
        'spider_tag':'bestwestSuggest',
        'collection_name':'test',
        'source':'bestwest',
        'key':'123'
    }
    task = ttt(_worker='', _task_id='demo', _source='', _type='suggest', _task_name='tes',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='supplement_field',
                _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    ihg = AllSuggestCitySDK(task)

    ihg.execute()