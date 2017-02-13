# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
import json
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from .celery import app
from .my_lib.BaseTask import BaseTask
from .my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji import spider_factory
from mioji.common.utils import simple_get_http_proxy

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_http_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)

hotel_default = {'check_in': '20170603', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20170603', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20170603', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}


def hotel_list_database(source, city_id):
    task = Task()
    task.extra['hotel'] = hotel_default
    task.content = city_id
    spider = factory.get_spider(source, 'hotelList')
    spider.task = task
    return spider.crawl(required=['hotelList_hotel'])


#     return spider.crawl()

@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def hotel_list_task(self, source, city_id, part, **kwargs):
    try:
        result = hotel_list_database(source=source, city_id=city_id)
        update_task(kwargs['task_id'])
        data = []
        part = part.replace('list', 'detail')
        for sid, hotel_url in result[0]['hotelList_hotel']:
            other_info = {
                u'source_id': unicode(sid),
                u'city_id': unicode(city_id)
            }
            worker = u'hotel_base_data'
            args = json.dumps(
                {u'source': unicode(source), u'hotel_url': unicode(hotel_url), u'other_info': other_info,
                 u'part': unicode(part)})

            special_hotel_task_args = json.dumps(
                {u'source': unicode(source), u'other_info': other_info,
                 u'part': unicode(part)})
            task_id = get_task_id(worker, special_hotel_task_args)
            data.append((task_id, worker, args, unicode(part)))
        print insert_task(data=data)
    except Exception as exc:
        self.retry(exc=exc)


if __name__ == '__main__':
    print hotel_list_database('booking', '11958')
