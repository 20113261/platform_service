# !/usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
import json
import datetime
import traceback
import pymongo

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']


def insert_new_task(datas):
    conn_s = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='source_info')
    cursor_s =  conn_s.cursor()
    conn_c = pymysql.connect(host='10.10.69.170', user='reader', password='miaoji1109', charset='utf8', db='base_data')
    cursor_c = conn_c.cursor()

    cursor_s.execute("""SELECT city_id, source, suggestions, select_index FROM source_info.hotel_suggestions_city where source = 'ctrip' and is_new_type = 1;""")


    datas = {}
    for city_id, source, suggestions, select_index in cursor_s.fetchall():
        datas[city_id] = [source, suggestions, select_index]

    sql ="""SELECT id, country_id FROM base_data.city where id in (%s)""" % ', '.join(datas.keys())
    # print sql
    cursor_c.execute(sql)

    countrys = cursor_c.fetchall()
    # print countrys
    for id, country_id in countrys:
        datas[id].append(country_id)

    data = []
    _count = 0
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
                'task_name': 'list_hotel_ctrip_20170925a',
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
                    collections.insert(data, continue_on_error=True)
                    data = []
                except Exception as exc:
                    print '==========================0======================='
                    print city_url, city_id
                    print traceback.format_exc(exc)
                    print '==========================1======================='

    else:
        print(_count)
        collections.insert(data, continue_on_error=True)