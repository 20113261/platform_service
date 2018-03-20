# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
@author: feng
@date: 2018-02-01
@update: 18-03-05
@purpose: grouptravel list sdk
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

import json

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
db = client['data_result']


def GT_to_database(tid, used_times, source, vacation_type, ticket, need_cache=True):
    task = Task()
    task.ticket_info = {
        'tid': tid,
        'vacation_info':ticket,
        'source':vacation_type,
        'used_times': used_times
    }
    spider = factory.get_spider_by_old_source('{}|vacation_list'.format(source))
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['list'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['list'], cache_config=none_cache_config)
    print(error_code)
    logger.info(str(spider.result['list']) + '  --  ' + task.ticket_info['vacation_info']['dept_info']['id']+'-'+task.ticket_info['vacation_info']['dest_info']['id'])
    return error_code, spider.result['list'], spider.page_store_key_list


class GTListSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109, 27]

    def _execute(self, **kwargs):
        dept_info = self.task.kwargs['dept_info']
        dest_info = self.task.kwargs['dest_info']
        source = self.task.kwargs['source']
        error_code, result, page_store_key = GT_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            vacation_type = self.task.kwargs['vacation_type'],
            source=source,
            ticket=self.task.kwargs,
            need_cache=self.task.used_times == 0
        )

        db[source +'GT_list'].save({
            'collections': self.task.collection,
            'task_id': self.task.task_id,
            'used_times': self.task.used_times[0],
            'stored_page_keys': page_store_key,
            'dept_info':dept_info,
            'dest_info':dest_info,
            'result': result,
            'source':self.task.kwargs['source'],
            'insert_time': datetime.datetime.now()
        })

        self.task.error_code = error_code

        sql = SQL.format(self.task.task_name)
        data = []
        if source == 'ctrip':
            for res in result:
                data.append((source, res['pid_3rd'], dept_info['id'], dest_info['id'], json.dumps(res)))
        elif source == 'tuniu':
            for res in result:
                data.append((source, res['id'], dept_info['id'], dest_info['id'], json.dumps(res)))
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

        if error_code == 27 or len(data) > 0:
            self.task.error_code = 0
        else:
            raise ServiceStandardError(error_code=ServiceStandardError.EMPTY_TICKET)

        return result, error_code


if __name__ == '__main__':
    from proj.my_lib.Common.Task import Task as ttt
    args = {
        "dept_info": {
            "id": "1211",
            "name": "南阳",
            "name_en": "nanyang"
        },
        "dest_info": {
            "id": "2002213",
            "name": "巴厘岛",
            "name_en": "tour"
            },
        "vacation_type": "grouptravel",
        "source":'tuniu'
    }

    task = ttt(_worker='', _task_id='demo', _source='ctripGT', _type='GT_list', _task_name='list_total_ctripGT_test',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='grouptravel',
                _routine_key='grouptravel', list_task_token='test', task_type=0, collection='')
    s = GTListSDK(task= task)
    s.execute()
