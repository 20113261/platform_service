#!/usr/bin/env python
# -*- coding:utf-8 -*-
from mioji import spider_factory
import json
from mioji.common.task_info import Task
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.mysql_pool import service_platform_pool
from proj.my_lib.logger import func_time_logger
from mioji.spider_factory import factory
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.Common.Browser import proxy_pool
from celery.utils.log import get_task_logger
import mioji.common.logger
import mioji.common.pool
import mioji.common.pages_store
mioji.common.pool.pool.set_size(128)

logger = get_task_logger('daodaoHotel')
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = simple_get_socks_proxy
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)


def hotel_url_to_database(source, keyword, need_cache=False):
    task = Task()
    task.ticket_info['url'] = keyword
    task.ticket_info['hotel_name'] = keyword
    old_target = source + 'ListHotel'
    spider = factory.get_spider_by_old_source(old_target)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=['hotel'], cache_config=cache_config)
    else:
        error_code = spider.crawl(required=['hotel'], cache_config=none_cache_config)
    print(error_code)
    # if data_from == 'google':
    #     return error_code,spider.result,spider.user_datas['search_result']
    print spider.result['hotel']
    return error_code, spider.result['hotel']


class OthersSourceHotelUrl(BaseSDK):

    def get_task_finished_code(self):
        return [0, 106, 107, 109, 29]

    def _execute(self, **kwargs):
        url = kwargs.get('url')
        tag = kwargs.get('tag')
        source = kwargs.get('source')
        name = kwargs.get('name')
        name_en = kwargs.get('name_en')
        city_id = kwargs.get('city_id')
        country_id = kwargs.get('country_id')
        table_name = 'list_result_{0}_{1}'.format(source, tag)

        error_code, hotel_result = hotel_url_to_database(
            source=source,
            keyword=url,
            need_cache=self.task.used_times == 0,
        )
        temp_save = []

        if source == 'daodao':
            for hotel in hotel_result:
                name = hotel.get('hotel_name', '')
                name_en = hotel.get('hotel_name_en', '')
                hotels = hotel.copy()
                status = 1 if hotels else 0
                temp_save.append((name, name_en, city_id, country_id, 'daodao', status, json.dumps(hotels) if hotels else None))

        elif source == 'google':
            for hotel in hotel_result:
                status = 1 if hotel_result else 0
                temp_save.append((name, name_en, city_id, country_id, 'google', status, json.dumps(hotel) if hotel else None))

        print temp_save
        @func_time_logger
        def hotel_list_insert_db(table_name, res_data):
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sql = "insert into {} (name, name_en, city_id, country_id, `from`, status, source_list) VALUES (%s,%s,%s,%s,%s,%s,%s)".format(table_name)
                cursor.executemany(sql, res_data)
                service_platform_conn.commit()
                cursor.close()
                service_platform_conn.close()
            except Exception as e:
                self.logger.exception(msg="[mysql error]", exc_info=e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        hotel_list_insert_db(table_name, temp_save)

        if len(temp_save) > 0:
            self.task.error_code = 0
        elif int(error_code) == 0:
            self.task.error_code = 29
            raise ServiceStandardError(ServiceStandardError.EMPTY_TICKET)
        else:
            raise ServiceStandardError(error_code=error_code)
        return len(temp_save), error_code


if __name__ == "__main__":
    from proj.my_lib.Common.Task import Task as Task_to
    # url = "https://www.tripadvisor.cn/Hotels-g1189702-Tahkovuori_Northern_Savonia-Hotels.html"
    # args = {
    #     'url': url,
    #     'source': 'daodao',
    #     'tag': '20180401a',
    #     'name': 'test_chinese',
    #     'name_en': 'test_english',
    # }
    url = "Le Stanze di Dolly"
    args = {
        'url': url,
        'source': 'google',
        'tag': '20180401a',
        'name': '',
        'name_en': 'Le Stanze di Dolly',
    }

    task = Task_to(_worker='', _task_id='demo', _source='daodao', _type='suggest', _task_name='tes',
               _used_times=0, max_retry_times=6,
               kwargs=args, _queue='supplement_field',
               _routine_key='supplement_field', list_task_token='test', task_type=0, collection='')
    ihg = OthersSourceHotelUrl(task)

    ihg.execute()