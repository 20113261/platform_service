#coding:utf-8
# @Time    : 2018/5/22
# @Author  : xiaopeng
# @Site    : boxueshuyuan
# @File    : _HolidayListSDK.py
# @Software: PyCharm

# !/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function
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
import json
from proj.my_lib.logger import func_time_logger
from proj.list_config import cache_config, list_cache_path, cache_type, none_cache_config
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj import config
from mongo_pool import mongo_data_client
from proj.my_lib.Common.Browser import proxy_pool
from zxp_utils import get_zxp_proxy
from MongoTaskInsert_2 import InsertTask, TaskType
from proj.my_lib.Common.Task import Task as ResultTask

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
# get_proxy = proxy_pool.get_proxy
get_proxy = None

debug = True
spider_factory.config_spider(insert_db, get_proxy, debug, need_flip_limit=False)
client = pymongo.MongoClient(host=config.MONGO_DATA_HOST)

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}


def hotel_list_database(list_task,need_cache=True,flag=False):
    task = Task()
    task.source = list_task.kwargs['source']
    task.content = list_task.kwargs['content']
    task.ticket_info = {
        'tid': list_task.task_id,
        'used_times': list_task.used_times
    }

    if flag:
        old_spider_tag = task.source+'FilterHotel'
        required = ['filter']
    else:
        old_spider_tag = task.source + 'ListHotel'
        required = ['hotel']
    # mioji.common.spider.slave_get_proxy = get_zxp_proxy
    # mioji.common.spider.get_proxy = get_zxp_proxy()
    spider = factory.get_spider_by_old_source(old_spider_tag)
    spider.task = task
    if need_cache:
        error_code = spider.crawl(required=required, cache_config=cache_config)
    else:
        error_code = spider.crawl(required=required, cache_config=none_cache_config)
    # logger.info(str(task.ticket_info) + '  --  ' + '-'+str(error_code)+'-' +task.content)
    # logger.info(str(spider.result['hotel'][:100]))
    return error_code, spider.result, spider.page_store_key_list


class MyHotelListSDK(BaseSDK):
    def get_task_finished_code(self):
        return [0, 106, 107, 109, 29]

    def _execute(self, **kwargs):
        source = self.task.kwargs['source']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        fla = self.task.kwargs.get('list_more', False)
        @func_time_logger
        def hotel_list_crawl():
            error_code, result, page_store_key = hotel_list_database(self.task,
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

        res_data = self.insert_subtask(result)

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
        return len(res_data), error_code, self.task.error_code, self.task.task_name

    def insert_reuslt(self, result):
        '''如使用mysql，请使用连接池'''
        pass

    def insert_subtask(self, result):
        source = self.task.kwargs['source']
        city_id = self.task.kwargs['city_id']
        country_id = self.task.kwargs['country_id']
        res_data = []
        if source in ('ctrip', 'ctripcn', 'starwood', 'gha'):
            for line in result['hotel']:
                sid = line[3]
                hotel_url = line[-1]
                res_data.append((source, sid, city_id, country_id, hotel_url))
        elif source in ('bestwest'):
            for sr, sid, city_id, hotel_url in result['hotel']:
                res_data.append((source, sid, city_id, country_id, hotel_url))
        elif source in ('fourseasons'):
            for line in result['hotel']:
                sid = line[-1]
                hotel_url = line[0]
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

        try:
            # data_collections = mongo_data_client['ServicePlatform'][self.task.task_name]
            # data_collections.create_index([('source', 1), ('source_id', 1), ('city_id', 1)], unique=True,
            #                               background=True)
            data = []
            if res_data:
                for line in res_data:
                    data.append({
                        'source': line[0],
                        'source_id': line[1],
                        'city_id': line[2],
                        'country_id': line[3],
                        'hotel_url': line[4]
                    })
                self.task.gen_detail_task(data)

            return res_data

        except pymongo.errors.DuplicateKeyError:
            logger.info("[Duplicate Key]")
        except Exception as exc:
            raise ServiceStandardError(error_code=ServiceStandardError.MONGO_ERROR, wrapped_exception=exc)

if __name__ == '__main__':
    print(hotel_list_database('booking', '51211', '20170801'))
