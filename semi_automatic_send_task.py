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
    for city_id, source, suggestions, select_index, country_id, suggest_type, is_new_type, part in datas:

        # print city_id, source, suggestions, select_index, country_id, suggest_type, is_new_type, part
        if select_index is None:  #新表直接拿suggestios赋值
            if source=='booking' or source=='ctrip':
                _suggest = suggestions
            else:
                _suggest = json.dumps(eval(suggestions))
        else: #老表需要解析json在通过select_index获取url
            if is_new_type==1:
                _suggest = json.loads(suggestions)[select_index-1]['url']
            else: #老表任务is_new_type为0的，当成新任务发，suggest_type为2

                try:
                    _suggest = json.dumps(json.loads(suggestions)[select_index - 1])
                except Exception as e:
                    _suggest = json.dumps(json.loads(suggestions.decode('string_escape'))[select_index - 1])

                suggest_type = 2
                is_new_type = 1

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
                    'part': part,
                    'is_new_type': is_new_type,
                    'suggest_type': suggest_type,
                    'suggest': _suggest,
                },#source, city_id, country_id, check_in, part, is_new_type, suggest_type, suggest
                'priority': 3,
                'finished': 0,
                'used_times': 0,
                'running': 0,
                'utime': datetime.datetime.now()
            }
            task_info['list_task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
            task_info['args']['check_in'] = check_in
            task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
            data.append(task_info)
            # print task_info

            if _count % 10000 == 0:
                print(_count)
                try:
                    success_count += hourong_patch(data)
                    data = []
                except Exception as exc:
                    print '==========================0======================='
                    print country_id, city_id
                    print traceback.format_exc(exc)
                    print '==========================1======================='

    else:
        if data:
            print(_count)
            success_count += hourong_patch(data)

    return success_count

def send_daodao_list_task(task_name, datas):
    data = []
    _count = 0
    success_count = 0
    for city_id, url, country_id, poi_type in datas:
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
                'poi_type': poi_type,
                'url': urlparse.urlsplit(url).path,
            },#source, url, city_id, country_id, poi_type
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        task_info['list_task_token'] = task_info['task_token']
        data.append(task_info)
        # print task_info

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
        if data:
            print(_count)
            success_count += hourong_patch(data)
    return success_count

def send_qyer_list_task(task_name, datas):
    data = []
    _count = 0
    success_count = 0
    for city_id, country_id, url, check_in in datas:
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
                'check_in': check_in,
                'city_url': url,
            },  # source, city_id, country_id, check_in, city_url
            'priority': 3,
            'finished': 0,
            'used_times': 0,
            'running': 0,
            'utime': datetime.datetime.now()
        }
        task_info['task_token'] = hashlib.md5(json.dumps(task_info['args'], sort_keys=True).encode()).hexdigest()
        task_info['list_task_token'] = task_info['task_token']
        data.append(task_info)
        # print task_info

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
        if data:
            print(_count)
            success_count += hourong_patch(data)
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