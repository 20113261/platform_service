# !/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
import json
import traceback
import dataset
import common.common
from mioji.spider_factory import factory
from mioji.common.task_info import Task
from .celery import app
from .my_lib.BaseTask import BaseTask
from .my_lib.task_module.task_func import update_task, insert_task, get_task_id
from mioji import spider_factory

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = common.common.get_proxy
debug = False
spider_factory.config_spider(insert_db, get_proxy, debug)

hotel_default = {'check_in': '20171203', 'nights': 1, 'rooms': [{}]}
hotel_rooms = {'check_in': '20171203', 'nights': 1, 'rooms': [{'adult': 1, 'child': 3}]}
hotel_rooms_c = {'check_in': '20171203', 'nights': 1, 'rooms': [{'adult': 1, 'child': 2, 'child_age': [0, 6]}] * 2}

db = dataset.connect('mysql+pymysql://hourong:hourong@10.10.180.145/TAX?charset=utf8')
table = db['Expedia']


def hotel_list_database(source, city_id):
    task = Task()
    task.content = str(city_id) + '&' + '2&{nights}&{check_in}'.format(**hotel_rooms)
    spider = factory.get_spider_by_old_source(source + 'ListHotel')
    spider.task = task
    print spider.crawl(required=['hotel'])
    return spider.result


def hotel_tax(task, city_id):
    spider = spider_factory.factory.get_spider('expedia', 'expedia_tax')
    spider.task = task
    spider.crawl()
    return spider.result


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='15/s')
def hotel_tax_list_task(self, source, city_id, part, **kwargs):
    try:
        result = hotel_list_database(source=source, city_id=city_id)
        data = []
        part = part.replace('list', 'detail')
        hotel_count = 0
        for sid, hotel_url in result['hotel']:
            hotel_count += 1
            if hotel_count >= 20:
                break
            worker = u'hotel_tax_detail'
            task_content = hotel_url.split('?')[0] + "?&1&20171210"
            args = json.dumps(
                {u'task_content': unicode(task_content),
                 u'city_id': unicode(city_id)})

            task_id = get_task_id(worker, args)
            data.append((task_id, worker, args, unicode(part)))

        update_task(kwargs['task_id'])
        print insert_task(data=data)
    except Exception as exc:
        self.retry(exc=traceback.format_exc(exc))


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='120/s')
def hotel_tax_detail(self, task_content, city_id, **kwargs):
    try:
        task = Task()
        task.content = task_content
        result = hotel_tax(task, city_id)
        data = result.values()[-1][-1]
        data['task_content'] = task_content
        data['city_id'] = city_id
        table.insert(data)
        if kwargs.get('task_id'):
            update_task(kwargs['task_id'])
    except Exception as exc:
        self.retry(exc=traceback.format_exc(exc))


if __name__ == '__main__':
    # print hotel_list_database('booking', '51211')
    # print hotel_list_database('expedia', '10001')
    # raise Exception()
    task = Task()
    # hotel_url
    hotel_url = "https://www.expedia.com.hk/cn/Hotels-Hotel-Romance-Malesherbes-By-Patrick-Hayat.h1753932.Hotel-Information?chkin=2017%2F5%2F20&chkout=2017%2F5%2F21&rm1=a2&regionId=0&hwrqCacheKey=95ac5f10-6c82-4163-9959-901ddc9c674aHWRQ1493094040336&vip=false&c=1993f64d-88df-4719-a274-c3cf51ad721f&&exp_dp=885.37&exp_ts=1493094041525&exp_curr=HKD&exp_pg=HSR"
    task.content = hotel_url.split('?')[0] + "?&1&20170910"
    print task.content

    print hotel_tax(task, '10001')
