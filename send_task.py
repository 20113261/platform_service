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
import proj.my_lib.my_mongo_insert
from pymongo.errors import DuplicateKeyError
from send_email import send_email, SEND_TO, EMAIL_TITLE

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']
redis_sourceid = redis.Redis(host='10.10.114.35', db=8)
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
        print traceback.format_exc(e)
        return -1

def get_country_id(tasks):
    conn_c = pymysql.connect(host='10.10.69.170', user='reader', password='miaoji1109', charset='utf8', db='base_data')
    cursor_c = conn_c.cursor()
    tasks_tmep = {args[2]: list(args) for args in tasks}
    print '================0'*3
    print tasks_tmep
    print ', '.join(tasks_tmep.keys())
    print '================1' * 3
    if not tasks_tmep:return []
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
    data = []
    _count = 0
    utime = None
    success_count = 0
    for source, source_id, city_id, hotel_url, utime in tasks:
        _count += 1
        task_info = {
            'worker': 'proj.hotel_tasks.hotel_base_data',
            'queue': 'hotel_detail',
            'routing_key': 'hotel_detail',
            'task_name': task_tag,
            'args': {
                'source': source,
                'other_info': {
                    'source_id': source_id,
                    'city_id': 'NULL'
                },
                'country_id': 'NULL',
                'part': task_tag
            },
            'priority': priority,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        task_info['args']['url'] = hotel_url

        data.append(task_info)

        if _count % 10000 == 0:
            print(_count)
            success_count = hourong_patch(data)
            data = []

    else:
        print(_count)
        if len(data)>0:
            success_count += hourong_patch(data)

    if success_count==-1:
        utime = None
    return utime, success_count

def send_poi_detail_task(tasks, task_tag, priority):
    data = []
    _count = 0
    utime = None
    success_count = 0
    typ1, typ2, source, tag = task_tag.split('_')
    for source, source_id, city_id, hotel_url, utime in tasks:
        _count += 1
        task_info = {
            'worker': 'proj.poi_task.get_lost_poi',
            'queue': 'poi_detail',
            'routing_key': 'poi_detail',
            'task_name': task_tag,
            'args': {
                'target_url': hotel_url,
                'city_id': 'NULL',
                'poi_type': typ2,
                'country_id': 'NULL',
                'part': task_tag
            },
            'priority': priority,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

        data.append(task_info)

        if _count % 10000 == 0:
            print(_count)
            success_count += hourong_patch(data)
            data = []

    else:
        print(_count)
        if len(data)>0:
            success_count += hourong_patch(data)

    if success_count==-1:
        utime = None

    return utime, success_count

def send_qyer_detail_task(tasks, task_tag, priority):
    data = []
    _count = 0
    utime = None
    success_count = 0
    for source, source_id, city_id, hotel_url, utime in tasks:
        _count += 1
        task_info = {
            'worker': 'proj.qyer_poi_tasks.qyer_poi_task',
            'queue': 'poi_detail',
            'routing_key': 'poi_detail',
            'task_name': task_tag,
            'args': {
                'target_url': hotel_url,
                'city_id': 'NULL',
                'part': task_tag
            },
            'priority': priority,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

        data.append(task_info)

        if _count % 10000 == 0:
            print(_count)
            success_count += hourong_patch(data)
            data = []

    else:
        print(_count)
        if len(data)>0:
            success_count += hourong_patch(data)

    if success_count==-1:
        utime = None

    return utime, success_count

def send_image_task(tasks, task_tag, priority, is_poi_task):
    _count = 0
    data = []
    md5_data = []
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='ServicePlatform')
    cursor = conn.cursor()
    update_time = None
    success_count = 0
    for source, source_id, city_id, img_items, update_time in tasks:
        if not is_poi_task and int(redis_sourceid.get(source + '|_|' +str(source_id)) or 0)>10:continue
        if img_items is None:continue
        for url in img_items.split('|'):
            if not url:continue
            md5 = hashlib.md5(source+str(source_id)+url).hexdigest()
            if redis_md5.get(md5):continue
            redis_md5.set(md5, 1)
            redis_sourceid.incr(source + str(source_id))
            md5_data.append((md5, datetime.datetime.now()))
            _count += 1
            suffix = task_tag.split('_', 1)[1]
            file_path = ''.join(['/data/nfs/image/', 'img_', suffix])
            desc_path = ''.join(['/data/nfs/image/', 'img_', suffix, '_filter'])
            task_info = {
                'worker': 'proj.tasks.get_images',
                'queue': 'file_downloader',
                'routing_key': 'file_downloader',
                'task_name': 'images_'+suffix,
                'args': {
                    'source': source,
                    'source_id': source_id,
                    'target_url': url,
                    'part': task_tag.split('_')[-1],
                    'file_path': file_path,
                    'desc_path': desc_path,
                    'is_poi_task': is_poi_task,
                    'new_part': task_tag
                },
                'priority': priority,
                'finished': 0,
                'used_times': 0,
                'running': 0,
                'utime': datetime.datetime.now()
            }

            task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()

            data.append(task_info)
            if _count % 10000 == 0:
                print _count
                success_count += hourong_patch(data)
                data = []

                try:
                    cursor.executemany('insert into crawled_url(md5, update_time) values(%s, %s)', args=md5_data)
                    conn.commit()
                    md5_data = []
                except Exception as e:
                    raise Exception('%s\n%s' % (str(md5_data), traceback.format_exc(e)))

    else:
        print(_count)
        if len(data)>0:
            success_count += hourong_patch(data)
        if len(md5_data)>0:
            try:
                cursor.executemany('replace into crawled_url(md5, update_time) values(%s, %s)', args=md5_data)
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                raise Exception('%s\n%s' % (str(md5_data), traceback.format_exc(e)))

    if success_count==-1:
        update_time = None

    return update_time, success_count

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
