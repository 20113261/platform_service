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
import pymysql

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']
redis_sourceid = redis.Redis(host='10.10.114.35', db=8)
redis_md5 = redis.Redis(host='10.10.114.35', db=9)
conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8', db='ServicePlatform')

def send_hotel_detail_task(tasks, task_tag):
    data = []
    _count = 0
    utime = None
    for source, source_id, city_id, hotel_url, utime in tasks:
        _count += 1
        task_info = {
            'worker': 'proj.hotel_tasks.hotel_base_data',
            'queue': 'poi_task_1',
            'routing_key': 'poi_task_1',
            'task_name': task_tag,
            'args': {
                'source': source,
                'url': hotel_url,
                'other_info': {
                    'source_id': source_id,
                    'city_id': city_id
                },
            },
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

        data.append(task_info)

        if _count % 10000 == 0:
            print(_count)
            try:
                # collections.insert(data, continue_on_error=True)
                data = []
            except Exception as exc:
                print '==========================0======================='
                print hotel_url, city_id
                print traceback.format_exc(exc)
                print '==========================1======================='

    else:
        print(_count)
        # collections.insert(data, continue_on_error=True)

    return utime

def send_poi_detail_task(tasks, task_tag):
    data = []
    _count = 0
    utime = None
    for source_id, city_id, utime in tasks:
        _count += 1
        task_info = {
            'worker': 'proj.hotel_tasks.hotel_base_data',
            'queue': 'poi_task_1',
            'routing_key': 'poi_task_1',
            'task_name': task_tag,
            'args': {
                'source_id': source_id,
                'city_id': city_id
            },
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

        data.append(task_info)

        if _count % 10000 == 0:
            print(_count)
            try:
                # collections.insert(data, continue_on_error=True)
                data = []
            except Exception as exc:
                print '==========================0======================='
                print source_id, city_id
                print traceback.format_exc(exc)
                print '==========================1======================='

    else:
        print(_count)
        # collections.insert(data, continue_on_error=True)

    return utime

def send_image_task(tasks, task_tag, is_poi_task):
    _count = 0
    data = []
    md5_data = []
    cursor = conn.cursor()
    update_time = None
    for source, source_id, img_items, update_time in tasks:
        if redis_sourceid.get(source + str(source_id)):continue

        for url in img_items.split('|'):
            md5 = hashlib.md5(source+str(source_id)+url).hexdigest()
            if redis_md5.get(md5):continue
            redis_md5.set(md5)
            md5_data.append((md5, datetime.datetime.now()))
            _count += 1
            suffix = task_tag.split('_', 1)[1]
            file_path = ''.join(['/data/nfs/image', 'img_', suffix])
            desc_path = ''.join(['/data/nfs/image', 'img_', suffix, '_filter'])
            task_info = {
                'worker': 'proj.tasks.get_images',
                'queue': 'file_downloader',
                'routing_key': 'file_downloader',
                'task_name': task_tag,
                'args': {
                    'source': source,
                    'source_id': source_id,
                    'target_url': url,
                    'part': task_tag.split('_')[-1],
                    'file_path': file_path,
                    'desc_path': desc_path,
                    'is_poi_task': is_poi_task
                },
                'priority': 3,
                'finished': 0,
                'used_times': 0,
                'running': 0,
                'utime': datetime.datetime.now()
            }

            task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

            data.append(task_info)
            if _count % 10000 == 0:
                print _count
                try:
                    # collections.insert(data, continue_on_error=True)
                    # pass
                    print url
                    # collections.update({
                    #     'task_token': hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
                    # }, {'$set': task_info}, upsert=True)
                except Exception as exc:
                    print '==========================0======================='
                    print source, source_id, url
                    print traceback.format_exc(exc)
                    print '==========================1======================='

                try:
                    # TODO 表明字段名未确定
                    cursor.executemany('insert into crawled_url(md5, update_time) values(%s, %s)', args=md5_data)
                    md5_data = []
                except Exception as e:
                    print traceback.format_exc(e)

    else:
        print(_count)
        # collections.insert(data, continue_on_error=True)

    return update_time

def insert_test():
    # TODO 返回成功入库总数
    data = []
    for i in range(100):
        d = {
            'task_name': 'continue_on_error_test',
            'task_token': i
        }
        data.append(d)
        try:
            a = collections.insert(data, manipulate=True, continue_on_error=True)
            a = collections.update({
                'task_token': i,
            }, {'$set': d}, upsert=True)
            print a
        except Exception as e:
            print traceback.format_exc(e)

if __name__ == '__main__':
    insert_test()
