#!/usr/bin/env python
# -*- coding:utf-8 -*-
import pymongo
import pymysql
from mioji import spider_factory
MONGODB_CONFIG = {
    'host': '10.10.213.148'
}
config = {
    'host': '10.10.230.206',
    'user': 'mioji_admin',
    'password': 'mioji1109',
    'db': 'daodao_google',
    'charset': 'utf8'
}
import json
from mioji.common.task_info import Task
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from mioji.spider_factory import factory
from proj.my_lib import ServiceStandardError
from proj.my_lib.Common.Browser import proxy_pool
from celery.utils.log import get_task_logger
import mioji.common.logger
import mioji.common.pool
mioji.common.pool.pool.set_size(128)
logger = get_task_logger(__name__)

import mioji.common.pages_store
mioji.common.pool.pool.set_size(1024)
mioji.common.logger.logger = logger
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
        error_code = spider.crawl(required=['hotel'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['hotel'], cache_config=none_cache_config)
    print(error_code)
    return error_code, spider.result

class OthersSourceHotelUrl(BaseSDK):

    def _execute(self, **kwargs):
        url = kwargs.get('url')
        spider_tag = kwargs.get('spider_tag')
        source = kwargs.get('source')
        data_from = kwargs.get('data_from')
        error_code, values = hotel_url_to_database(
            tid=self.task.task_id,
            used_times=self.task.used_times,
            spider_tag=spider_tag,
            source=source,
            keyword=url,
            need_cache=self.task.used_times == 0
        )
        temp_save = []
        if data_from == 'daodao':
            hotel_urls = values['hotel']
            insert_sql = "insert into daodao_hotel(hotel_name,hotel_name_en,agoda,booking,ctrip,elong,expedia,hotels,other_source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            conn = pymysql.connect(**config)
            cursor = conn.cursor()
            for hotel_url in hotel_urls:
                temp_save.append(
                    (
                        hotel_url.get('hotel_name',''),hotel_url.get('hotel_name_en',''),hotel_url.get('agoda',''),hotel_url.get('booking',''),hotel_url.get('ctrip',''),
                        hotel_url.get('elong',''),hotel_url.get('expedia',''),hotel_url.get('hotels',''),json.dumps(hotel_url)
                    )
                )
                if len(temp_save) >= 2000:
                    cursor.executemany(insert_sql,temp_save)
                    conn.commit()
                    temp_save = []
            else:
                cursor.executemany(insert_sql,temp_save)
                conn.commit()
        elif data_from == 'google':
            pass
        if error_code == 0:
            self.finished_error_code = 0
        else:
            raise ServiceStandardError.ServiceStandardError(error_code,msg="爬虫出现错误")

if __name__ == "__main__":
    from proj.my_lib.Common.Task import Task as Task_to
    url = "https://www.tripadvisor.cn/Hotels-g1189702-Tahkovuori_Northern_Savonia-Hotels.html"
    args = {
        'url': url,
        'source': 'daodao',
        'spider_tag': 'daodaoListHotel',
        'data_from': 'daodao'

    }

    task = Task_to(_worker='', _task_id='demo', _source='daodao', _type='suggest', _task_name='tes',
               _used_times=0, max_retry_times=6,
               kwargs=args, _queue='supplement_field',
               _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    ihg = OthersSourceHotelUrl(task)

    ihg.execute()