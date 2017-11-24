#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm

import pymongo
import traceback
import hashlib
import datetime
import json
import redis
import hashlib
import sys
import pymysql
import mock
from MongoTaskInsert import InsertTask, TaskType

import proj.my_lib.my_mongo_insert
from pymongo.errors import DuplicateKeyError
from send_email import send_email, SEND_TO, EMAIL_TITLE
from proj.my_lib.logger import get_logger

from warnings import filterwarnings

filterwarnings('ignore', category=pymysql.err.Warning)
logger = get_logger("send_task")

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']
redis_md5 = redis.Redis(host='10.10.114.35', db=9)


def hourong_patch(data):
    try:
        with mock.patch('pymongo.collection.Collection._insert', proj.my_lib.my_mongo_insert.Collection._insert):
            result = collections.insert(data, continue_on_error=True)
            return result['n']
    except DuplicateKeyError as e:
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)
        logger.exception(msg="[exception]", exc_info=e)
        return -1


def get_country_id(tasks):
    conn_c = pymysql.connect(host='10.10.69.170', user='reader', password='miaoji1109', charset='utf8', db='base_data')
    cursor_c = conn_c.cursor()
    tasks_tmep = {args[2]: list(args) for args in tasks}
    logger.debug(tasks_tmep)
    logger.debug(', '.join(tasks_tmep.keys()))
    if not tasks_tmep:
        return []
    sql = """SELECT id, country_id FROM base_data.city where id in (%s)""" % ', '.join(tasks_tmep.keys())
    cursor_c.execute(sql)
    countrys = cursor_c.fetchall()
    # print countrys
    for id, country_id in countrys:
        tasks_tmep[id].append(country_id)

    cursor_c.close()
    conn_c.close()
    return tasks_tmep.values()


def send_hotel_detail_task(tasks, task_tag, priority):
    timestamp = None
    if not tasks:
        return timestamp

    source = tasks[0][0]
    with InsertTask(worker='proj.total_tasks.hotel_detail_task', queue='hotel_detail', routine_key='hotel_detail',
                    task_name=task_tag, source=source.title(), _type='Hotel',
                    priority=priority) as it:
        for source, source_id, city_id, hotel_url, timestamp in tasks:
            it.insert_task({
                'source': source,
                'url': hotel_url,
                'part': task_tag,
                'source_id': source_id,
                'city_id': 'NULL',
                'country_id': 'NULL'
            })
        return timestamp


def send_poi_detail_task(tasks, task_tag, priority):
    utime = None
    typ1, typ2, source, tag = task_tag.split('_')
    with InsertTask(worker='proj.total_tasks.poi_detail_task', queue='poi_detail', routine_key='poi_detail',
                    task_name=task_tag, source='Daodao', _type='DaodaoDetail',
                    priority=priority) as it:
        for source, source_id, city_id, hotel_url, utime in tasks:
            it.insert_task({
                'target_url': hotel_url,
                'city_id': 'NULL',
                'poi_type': typ2,
                'country_id': 'NULL',
                'part': task_tag
            })

    return utime


def send_qyer_detail_task(tasks, task_tag, priority):
    utime = None
    with InsertTask(worker='proj.total_tasks.qyer_detail_task', queue='poi_detail', routine_key='poi_detail',
                    task_name=task_tag, source='Qyer', _type='QyerDetail',
                    priority=priority) as it:
        for source, source_id, city_id, qyer_url, utime in tasks:
            it.insert_task({
                'target_url': qyer_url,
                'city_id': 'NULL',
                'part': task_tag
            })

    return utime


def send_image_task(tasks, task_tag, priority, is_poi_task):
    _count = 0
    md5_data = []
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='ServicePlatform')
    cursor = conn.cursor()
    update_time = None
    if not tasks:
        return update_time

    source = tasks[0][0]
    suffix = task_tag.split('_', 1)[1]
    with InsertTask(worker='proj.total_tasks.images_task', queue='file_downloader', routine_key='file_downloader',
                    task_name='images_' + suffix, source=source.title(), _type='DownloadImages',
                    priority=priority) as it:
        for source, source_id, city_id, img_items, update_time in tasks:
            if img_items is None:
                continue
            for url in img_items.split('|'):
                if not url:
                    continue
                md5 = hashlib.md5(source + str(source_id) + url).hexdigest()

                if '20171122a' not in task_tag and '20171120a' not in task_tag:
                    if redis_md5.get(md5):
                        continue

                redis_md5.set(md5, 1)
                md5_data.append((md5, datetime.datetime.now()))
                _count += 1
                bucket_name = "mioji-{}".format(task_tag.split('_')[1])
                if bucket_name == 'mioji-wanle':
                    file_prefix = "huantaoyou"
                else:
                    file_prefix = ""

                it.insert_task({
                    'source': source,
                    'new_part': task_tag,
                    'target_url': url,
                    'is_poi_task': is_poi_task,
                    'source_id': source_id,
                    'part': task_tag.split('_')[-1],
                    'bucket_name': bucket_name,
                    'file_prefix': file_prefix
                })

                if _count % 5000 == 0:
                    cursor.executemany('insert ignore into crawled_url(md5, update_time) values(%s, %s)', args=md5_data)
                    conn.commit()
                    md5_data = []
        else:
            if len(md5_data) > 0:
                cursor.executemany('insert ignore into crawled_url(md5, update_time) values(%s, %s)', args=md5_data)
                conn.commit()
                cursor.close()
                conn.close()
    return update_time


# def insert_test():
#     # TODO 返回成功入库总数
#     data = []
#     for i in range(100):
#         d = {
#             'task_name': 'continue_on_error_test',
#             'task_token': i
#         }
#         data.append(d)
#         try:
#             a = collections.insert(data, manipulate=True, continue_on_error=True)
#             a = collections.update({
#                 'task_token': i,
#             }, {'$set': d}, upsert=True)
#             print a
#         except Exception as e:
#             logger.exception(msg="[insert task error]", exc_info=e)
#             print traceback.format_exc(e)


if __name__ == '__main__':
    pass
    # insert_test()
