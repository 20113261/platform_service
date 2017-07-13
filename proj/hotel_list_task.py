# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
from __future__ import absolute_import
from celery.utils.log import get_task_logger
import json
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from .celery import app
from .my_lib.BaseTask import BaseTask
from .my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji import spider_factory
from mioji.common.utils import simple_get_socks_proxy
import mioji.common.spider
import mioji.common.logger
import datetime
import pymongo
import mioji.common.pool
mioji.common.pool.NEED_MONKEY_PATCH = False
mioji.common.pool.pool.set_size(2024)

# pymongo client

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['HotelList']['ctrip']
# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_socks_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)
mioji.common.spider.NEED_FLIP_LIMIT = False

logger = get_task_logger(__name__)
mioji.common.logger.logger = logger

hotel_default = {'check_in': '20170903', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170903', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}


# def hotel_list_database(source, city_id):
#     task = Task()
#     task.content = str(city_id) + '&' + '2&{nights}&{check_in}'.format(**hotel_rooms)
#     spider = factory.get_spider_by_old_source(source + 'ListHotel')
#     spider.task = task
#     print spider.crawl(required=['hotel'])
#     return spider.result

def hotel_list_database(source, city_id, check_in):
    task = Task()
    task.content = str(city_id) + '&' + '2&1&{0}'.format(check_in)
    spider = factory.get_spider_by_old_source(source + 'ListHotel')
    spider.task = task
    print spider.crawl(required=['hotel'])
    return spider.result


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def hotel_list_task(self, source, city_id, check_in, part, **kwargs):
    self.task_source = source.title()
    self.task_type = 'HotelList'
    try:
        result = hotel_list_database(source=source, city_id=city_id, check_in=check_in)
        data = []
        part = part.replace('list', 'detail')
        if source == 'ctrip':
            for line in result['hotel']:
                sid = line[3]
                hotel_url = line[-1]
                collections.save({
                    'sid': sid,
                    'hotel_url': hotel_url,
                    'parent_info': {
                        'source': source,
                        'city_id': city_id,
                        'check_in': check_in,
                        'part': part,
                        'task_id': kwargs['task_id']
                    },
                    'u_time': datetime.datetime.now()
                })
        else:
            for sid, hotel_url in result['hotel']:
                collections.save({
                    'sid': sid,
                    'hotel_url': hotel_url,
                    'parent_info': {
                        'source': source,
                        'city_id': city_id,
                        'check_in': check_in,
                        'part': part,
                        'task_id': kwargs['task_id']
                    },
                    'u_time': datetime.datetime.now()
                })

        update_task(kwargs['task_id'])
        print insert_task(data=data)
    except Exception as exc:
        self.retry(exc=exc)


if __name__ == '__main__':
    print hotel_list_database('booking', '51211', '20170801')
