# !/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import
from celery.utils.log import get_task_logger
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from mioji.common.utils import simple_get_socks_proxy
from mioji import spider_factory
from proj.mysql_pool import service_platform_pool
import mioji.common.logger
import mioji.common.pool
import mioji.common.pages_store
import pymongo
import datetime
import mioji.common
import pymongo.errors
from proj.my_lib.logger import func_time_logger
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj import config
from mongo_pool import mongo_data_client
from proj.my_lib.Common.Browser import proxy_pool

mioji.common.pool.pool.set_size(2024)
logger = get_task_logger('hotel_list')
mioji.common.logger.logger = logger
mioji.common.pages_store.cache_dir = list_cache_path
mioji.common.pages_store.STORE_TYPE = cache_type

# client = pymongo.MongoClient(host='10.10.213.148', maxPoolSize=20)
# collections = client['data_result']['HotelList']
# pymongo client

client = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')
collections = client['data_result']['hotel_list']
filter_collections = client['data_result']['hotel_filter']
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
# get_proxy = simple_get_socks_proxy
get_proxy = proxy_pool.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
client = pymongo.MongoClient(host=config.MONGO_DATA_HOST)

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}

def hotel_list_database(tid, used_times, source, city_id, check_in, is_new_type=False, suggest_type='1', suggest='',
                        need_cache=True,flag=False):
    task = Task()
    task.source = source
    if not is_new_type:
        if source == 'hilton':
            task.content = check_in
        elif source == 'starwood':
            task.content = suggest+'&'
        elif source in ['hyatt']:
            task.content = ''
        elif source == 'gha':
            task.content = '&'.join(city_id, suggest)
        else:
            task.content = str(city_id) + '&' + '2&1&{0}'.format(check_in)

        task.ticket_info = {
            "is_new_type": False,
            'is_service_platform': True,
            'tid': tid,
            'used_times': used_times
        }
    else:
        task.ticket_info = {
            "is_new_type": True,
            "suggest_type": int(suggest_type),
            "suggest": suggest,
            "check_in": str(check_in),
            "stay_nights": '1',
            "occ": '2',
            'is_service_platform': True,
            'tid': tid,
            'used_times': used_times,
        }
        task.content = ''
    if flag:
        old_spider_tag = source+'FilterHotel'
        required = ['filter']
    else:
        old_spider_tag = source + 'ListHotel'
        required = ['hotel']
    spider = factory.get_spider_by_old_source(old_spider_tag)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=required, cache_config=cache_config)
    else:
        error_code = spider.crawl(required=required, cache_config=none_cache_config)
    logger.info(str(task.ticket_info) + '  --  ' + task.content)
    # logger.info(str(spider.result['hotel'][:100]))
    return error_code, spider.result, spider.page_store_key_list


class HotelListSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109, 29]

    def _execute(self, **kwargs):
        source = self.task.kwargs['source']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        fla = self.task.kwargs.get('list_more', False)
        @func_time_logger
        def hotel_list_crawl():
            error_code, result, page_store_key = hotel_list_database(tid=self.task.task_id,
                                                                     used_times=self.task.used_times,
                                                                     source=source,
                                                                     city_id=city_id,
                                                                     check_in=self.task.kwargs['check_in'],
                                                                     is_new_type=self.task.kwargs.get('is_new_type',
                                                                                                      False),
                                                                     suggest_type=self.task.kwargs.get('suggest_type',
                                                                                                       '1'),
                                                                     suggest=self.task.kwargs.get('suggest', ''),
                                                                     need_cache=self.task.used_times == 0,flag = fla)
            return error_code, result, page_store_key

        error_code, result, page_store_key = hotel_list_crawl()
        print(result)

        # more_list
        if fla:
            for line in result['filter']:
                line['country_id'] = country_id
                line['source'] = source
            filter_collections.insert_many(
                result['filter']
            )
            if len(result['filter']) > 0:
                self.task.error_code = 0
            elif int(error_code) == 0:
                raise ServiceStandardError(ServiceStandardError.EMPTY_TICKET)
            else:
                raise ServiceStandardError(error_code=error_code)
            return result, error_code, self.task.error_code, self.task.task_name, self.task.kwargs['suggest']

        if source == 'starwood' and error_code == 29:
            self.task.error_code = 109
            error_code = 109
        else:
            self.task.error_code = error_code

        res_data = []
        if source in ('ctrip', 'ctripcn', 'starwood', 'gha'):
            for line in result['hotel']:
                sid = line[3]
                hotel_url = line[-1]
                res_data.append((source, sid, city_id, country_id, hotel_url))
        elif source in ('hyatt'):
            for line in result['hotel']:
                sid = line[-1]
                hotel_url = line[1]
                res_data.append((source, sid, city_id, country_id, hotel_url))

        elif source == 'hilton':
            for dict_obj in result['hotel']:
                line = dict_obj.values()
                res_data.append((source, line[2], city_id, country_id, line[0]))
        else:
            for sid, hotel_url in result['hotel']:
                res_data.append((source, sid, city_id, country_id, hotel_url))



        @func_time_logger
        def hotel_list_insert_db():
            try:
                service_platform_conn = service_platform_pool.connection()
                cursor = service_platform_conn.cursor()
                sql = "INSERT IGNORE INTO {} (source, source_id, city_id, country_id, hotel_url) VALUES (%s,%s,%s,%s,%s)".format(
                    self.task.task_name)
                _res = cursor.executemany(sql, res_data)
                service_platform_conn.commit()
                cursor.close()
                service_platform_conn.close()
                self.task.list_task_insert_db_count = _res
                self.task.get_data_per_times = len(res_data)
            except Exception as e:
                self.logger.exception(msg="[mysql error]", exc_info=e)
                raise ServiceStandardError(error_code=ServiceStandardError.MYSQL_ERROR, wrapped_exception=e)

        hotel_list_insert_db()

        try:
            data_collections = mongo_data_client['ServicePlatform'][self.task.task_name]
            data_collections.create_index([('source', 1), ('source_id', 1), ('city_id', 1)], unique=True,
                                          background=True)
            data = []
            if data:
                for line in res_data:
                    data.append({
                        'list_task_token': self.task.list_task_token,
                        'task_id': self.task.task_id,
                        'source': line[0],
                        'source_id': line[1],
                        'city_id': line[2],
                        'country_id': line[3],
                        'hotel_url': line[4]
                    })
                data_collections.insert(data, continue_on_error=True)
        except pymongo.errors.DuplicateKeyError:
            logger.info("[Duplicate Key]")
        except Exception as exc:
            raise ServiceStandardError(error_code=ServiceStandardError.MONGO_ERROR, wrapped_exception=exc)

        # 由于错误都是 raise 的，
        # 所以当出现此种情况是，return 的内容均为正确内容
        # 对于抓取平台来讲，当出现此中情况时，数据均应该入库
        # 用 res_data 判断，修改 self.error_code 的值
        if len(res_data) > 0:
            self.task.error_code = 0
        elif int(error_code) == 0:
            raise ServiceStandardError(ServiceStandardError.EMPTY_TICKET)
        else:
            raise ServiceStandardError(error_code=error_code)
        return res_data, error_code, self.task.error_code, self.task.task_name, self.task.kwargs['suggest']


if __name__ == '__main__':
    print(hotel_list_database('booking', '51211', '20170801'))
