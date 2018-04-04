# coding=utf-8

'''
@author: feng
@date: 2018-03-01
@update: 18-03-05
@purpose:  grouptravel detail sdk
'''

from __future__ import absolute_import
import datetime
import pymongo
import time
import mioji.common.logger
import mioji.common.pages_store
import mioji.common.pool
from celery.utils.log import get_task_logger
from mioji import spider_factory
from mioji.common.task_info import Task
from mioji.spider_factory import factory

from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
# from proj.my_lib.Common.Browser import proxy_pool
from mioji.common.utils import simple_get_proxy

mioji.common.pool.pool.set_size(128)
logger = get_task_logger(__name__)
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, simple_get_proxy, debug, need_flip_limit=False)
SQL = "INSERT IGNORE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)"

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
db = client['data_result']
tuniu_collections = db['tuniuGT_detail']
ctrip_collections = db['ctripGT_detail']


def GTdetail_to_database(tid, used_times, source,ticket, need_cache=True):
    task = Task()
    task.ticket_info = {
        'tid': tid,
        'vacation_info': ticket,
        'source': source,
        'used_times': used_times
    }
    spider = factory.get_spider_by_old_source('{}|vacation_detail'.format(source))
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['vacation'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['vacation'], cache_config=none_cache_config)
    print(error_code)
    # logger.info(str(spider.result['vacation']) + '  --  ' + task.ticket_info['vacation_info']['url'])
    return error_code, spider.result['vacation'], spider.page_store_key_list

class GTDetailSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109,29]

    def _execute(self, **kwargs):
        source = self.task.kwargs['source']
        t1  = time.time()
        error_code, result, page_store_key = GTdetail_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            source=source,
            ticket=self.task.kwargs,
            need_cache=self.task.used_times == 0
        )

        t2 = time.time()
        logger.info('抓取耗时：   %s'.format(t2 - t1))

        if source == 'ctrip':
            my_collections = ctrip_collections
        elif source == 'tuniu':
            my_collections = tuniu_collections
        else:
            raise Exception(u'未知的源')

        my_collections.save({
            'source':source,
            'collections': self.task.collection,
            'task_id': self.task.task_id,
            'used_times': self.task.used_times[0],
            'stored_page_keys': page_store_key,
            'result': result,
            'args':self.task.kwargs,
            'insert_time': datetime.datetime.now()
        })

        t3 = time.time()
        logger.info('入库耗时：   %s'.format(t3 - t2))
        # -- detail 2 mysql --
        if len(result) > 0:
            self.task.error_code = 0
        elif len(result) == 0:
            self.task.error_code = 29
        # elif len(result) == 0:
        #     raise ServiceStandardError(ServiceStandardError.EMPTY_TICKET)
        else:
            raise ServiceStandardError(error_code=error_code)
        return self.task.error_code, len(result)

if __name__ == '__main__':
    from proj.my_lib.Common.Task import Task as ttt

    args =  {
        'source':'ctrip',
        "pid_3rd": "18557244",
        "dept_id": "1",
        "search_dept_city": "北京",
        "dest_id": "34745",
        "search_dest_city": "半月",
        "dept_city": "上海",
        "highlight": "列表页传入",
        "first_image": "https://dimg04.c-ctrip.com/images/300p0m000000derkj7459.png",
        "url": "http://vacations.ctrip.com/grouptravel/p18557244s1.html?kwd=%e5%8d%8a%e6%9c%88%e6%b9%be",
        "supplier": "列表页传入",
        "brand": "列表页出传入"
    }
    #args={'source':'tuniu','search_dept_city_id': '1602', 'url': 'http://www.tuniu.com/product/300095519', 'brand': '罗马假期', 'dept_city': '南京', 'search_dest_city': '普吉岛', 'first_image': 'http://m.tuniucdn.com/fb2/t1/G5/M00/09/0D/Cii-tFomThiIDU_GAAEyLjwgIi4AAAb6QIwFvUAATJG78_w160_h90_c1_t0.jpeg', 'search_dept_city': '南京', 'search_dest_city_id': '', 'id': '300095519'}


    task = ttt(_worker='', _task_id='demo', _source='ctripGT', _type='GT_detail', _task_name='list_ctripGT_total_test',
               _used_times=0, max_retry_times=6,
               kwargs=args, _queue='grouptravel',
               _routine_key='grouptravel', list_task_token='test', task_type=0, collection='')
    s = GTDetailSDK(task=task)
    s.execute()
