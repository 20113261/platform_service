# !/usr/bin/python
# -*- coding: UTF-8 -*-
from monitor import create_table, update_task_statistics
from send_task import hourong_patch

import pymysql
import json
import datetime
import traceback
import pymongo
import hashlib
import urlparse


client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']

# TODO {0}|_|{1} tag + source   [city_id,]
def send_hotel_list_task(task_name, datas):
    data = []
    _count = 0
    success_count = 0
    for city_id, args in datas.items():
        # print args
        source, suggestions, select_index, country_id = args
        city_url = json.loads(suggestions)[select_index-1]['url']
        for i in range(10):
            check_in = ''.join(str(datetime.datetime.now()+datetime.timedelta(days=10*i)).split(' ')[0].split('-'))
            _count += 1
            task_info = {
                'worker': 'proj.hotel_list_task.hotel_list_task',
                'queue': 'hotel_list',
                'routing_key': 'hotel_list',
                'task_name': task_name,
                'args': {
                    'source': source,
                    'city_id': city_id,
                    'country_id': country_id,
                    'check_in': check_in,
                    'part': '102',
                    'is_new_type': True,
                    'suggest_type': 1,
                    'suggest': city_url,
                },
                'priority': 3,
                'finished': 0,
                'used_times': 0,
                'running': 0,
                'utime': datetime.datetime.now()
            }
            task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
            data.append(task_info)
            print task_info

            if _count % 10000 == 0:
                print(_count)
                try:
                    success_count += hourong_patch(data)
                    data = []
                except Exception as exc:
                    print '==========================0======================='
                    print city_url, city_id
                    print traceback.format_exc(exc)
                    print '==========================1======================='

    else:
        print(_count)
        # success_count += hourong_patch(data)

    return success_count

def send_daodao_list_task(task_name, datas):
    data = []
    _count = 0
    success_count = 0
    for city_id, args in datas.items():
        # print args
        url, country_id = args
        _count += 1
        task_info = {
            'worker': 'proj.poi_list_task.poi_list_task',
            'queue': 'poi_list',
            'routing_key': 'poi_list',
            'task_name': task_name,
            'args': {
                'source': 'daodao',
                'city_id': city_id,
                'country_id': country_id,
                'poi_type': 'rest',
                'url': urlparse.urlsplit(url).path,
            },
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        data.append(task_info)
        print task_info

        if _count % 10000 == 0:
            print(_count)
            try:
                success_count += hourong_patch(data)
                data = []
            except Exception as exc:
                print '==========================0======================='
                print url, city_id
                print traceback.format_exc(exc)
                print '==========================1======================='

    else:
        print(_count)
        # success_count += hourong_patch(data)
    return success_count

def send_qyer_list_task(task_name, datas):
    data = []
    _count = 0
    success_count = 0
    for city_id, args in datas.items():
        # print args
        url, country_id = args
        _count += 1
        task_info = {
            'worker': 'proj.qyer_list_task.qyer_list_task',
            'queue': 'poi_list',
            'routing_key': 'poi_list',
            'task_name': task_name,
            'args': {
                'source': 'qyer',
                'city_id': city_id,
                'country_id': country_id,
                'check_in': '20170925',
                'part': '1',
                'city_url': url,
            },  # source, city_id, country_id, check_in, city_url
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        data.append(task_info)
        print task_info

        if _count % 10000 == 0:
            print(_count)
            try:
                success_count += hourong_patch(data)
                data = []
            except Exception as exc:
                print '==========================0======================='
                print url, city_id
                print traceback.format_exc(exc)
                print '==========================1======================='

    else:
        print(_count)
        # success_count += hourong_patch(data)
    return success_count

task2func = {
    'list_hotel': send_hotel_list_task,
    'list_total': send_qyer_list_task,
    'default': send_daodao_list_task
}

def list_task(task_name, datas):
    tab_args = task_name.split('_')
    create_table(task_name)

    func = task2func.get(tab_args[0]+'_'+tab_args[1], task2func['default'])

    success_count = func(task_name, datas)

    if success_count != 0:
        update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List', success_count, sum_or_set=False)