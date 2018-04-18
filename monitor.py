#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
import re
import copy
import datetime
import time
import traceback
from itertools import repeat
import redis
import pymysql
import json
import pymongo
import os
import sys
import cachetools.func
from send_task import send_hotel_detail_task, send_poi_detail_task, send_qyer_detail_task,\
    send_image_task, send_ctripPoi_detail_task, send_GT_detail_task, send_PoiSource_detail_task, \
    send_result_detail_task, send_result_daodao_filter
from attach_send_task import qyer_supplement_map_info
from proj.my_lib.logger import get_logger
from send_email import send_email, SEND_TO, EMAIL_TITLE
from proj.my_lib.Common.Utils import get_each_task_collection, generate_collection_name
from proj.mysql_pool import service_platform_pool
from toolbox.Hash import get_token
from MongoTaskInsert import InsertTask, TaskType
from rabbitmq_func import detect_msg_num

logger = get_logger('monitor')

task_statistics = redis.Redis(host='10.10.180.145', db=9)
client = pymongo.MongoClient(host='10.10.231.105')
db = client['MongoTask']
HOTEL_SOURCE = (
    'agoda', 'booking', 'ctrip', 'elong', 'expedia', 'hotels', 'hoteltravel', 'hrs', 'cheaptickets', 'orbitz',
    'travelocity', 'ebookers', 'tripadvisor', 'ctripcn', 'hilton', 'ihg', 'holiday', 'accor', 'marriott', 'starwood',
    'hyatt', 'gha', 'shangrila', 'fourseasons')
RESULT_SOURCE = ['google', 'daodao']
POI_SOURCE = 'daodao'
QYER_SOURCE = 'qyer'
CTRIPPOI_SOURCE = 'ctripPoi'
POI_S = ('ctripPoi')
GT_SOURCE = 'GT'
PRIORITY = 3
# TODO  所有表的update_time字段加索引
# TODO  所有表的update_time字段改为timestramp(6)类型

SQL_FILE_TO_SOURCE = {
    'hotel_detail.sql': 'hotel',
    'daodao_rest_detail.sql': 'rest',
    'daodao_attr_detail.sql': 'attr',
    'daodao_shop_detail.sql': 'shop',
    'qyer_detail.sql': 'total',
    'list.sql': 'list',
    'result_list.sql': 'result_list',
    'images_hotel.sql': 'images_hotel',
    'images_poi.sql': 'images_daodao'
}
LOAD_FILES = {}


def loads_sql():
    sql_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql')
    files = os.listdir(sql_file_path)
    for file_name in files:
        with open(os.path.join(sql_file_path, file_name), 'r') as f:
            source = SQL_FILE_TO_SOURCE[file_name]
            LOAD_FILES[source] = f.read()

    LOAD_FILES['result'] = LOAD_FILES['hotel']


loads_sql()


def get_default_timestramp():
    return datetime.datetime(year=1970, month=2, day=4, hour=6, minute=8, second=10, microsecond=666666)


def update_task_statistics(task_tag, typ2, source, typ1, success_count, sum_or_set=True):
    try:
        report_key = "{0}|_|{1}|_|{2}|_|{3}|_|All".format(task_tag, typ2.title(), source.title(), typ1)
        if sum_or_set:
            task_statistics.incrby(report_key, success_count)
        else:
            task_statistics.set(report_key, success_count)
    except Exception as e:
        logger.error('redis推送入队任务总数报错  :  \n%s ' % traceback.format_exc(e))


def execute_sql(sql, commit=False):
    conn = service_platform_pool.connection()
    cursor = conn.cursor()
    logger.info(sql)
    cursor.execute(sql)
    if commit:
        conn.commit()
        cursor.close()
        conn.close()
        return

    result = cursor.fetchall()
    logger.info('row_count  :  %s ' % cursor.rowcount)
    cursor.close()
    conn.close()
    return result


def get_seek(task_name):
    sql = """select seek, priority, sequence from task_seek where task_name = '%s'"""
    conn = service_platform_pool.connection()
    cursor = conn.cursor()
    cursor.execute(sql % task_name)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.info('timestramp, priority :  %s ' % str(result))
    if not result or len(result) == 0:
        return get_default_timestramp(), PRIORITY, 0

    return result


def update_seek(task_name, seek, priority=3, sequence=0):
    sql = """replace into task_seek (task_name, seek, priority, sequence) values('%s','%s', %d, %d);"""
    execute_sql(sql % (task_name, seek, priority, sequence), commit=True)


def get_all_tables():
    sql = """select table_name from information_schema.tables where table_schema = 'ServicePlatform';"""
    return execute_sql(sql)


def create_table(table_name):
    conn = service_platform_pool.connection()
    cursor = conn.cursor()
    tab_args = table_name.split('_')
    if tab_args[0] == 'detail':
        sql_file = LOAD_FILES[tab_args[1]]
    elif tab_args[0] == 'list':
        sql_file = LOAD_FILES['list']
    elif tab_args[0] == 'images':
        if tab_args[1] == 'hotel':
            sql_file = LOAD_FILES['images_hotel']
        elif tab_args[2] in ('daodao', 'qyer'):
            sql_file = LOAD_FILES['images_daodao']

    cursor.execute(sql_file % table_name)
    logger.info('已创建表: %s' % table_name)
    cursor.close()
    conn.close()

## --FYF
def monitoring_PoiSource_list2detail():
    sql = """select source, source_id, city_id,country_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 8000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'total':
                continue
            if tab_args[2] not in POI_S:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])

            # if table_dict.get(detail_table_name, True):
            #     create_table(detail_table_name)

            timestamp = send_PoiSource_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s' % (timestamp))

            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)

##-- fengyufei ctrip poi

def monitoring_ctripPoi_list2detail():
    sql = """select source, source_id, city_id,country_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 8000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'total':
                continue
            if tab_args[2] != CTRIPPOI_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])

            # if table_dict.get(detail_table_name, True):
            #     create_table(detail_table_name)

            timestamp = send_ctripPoi_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s' % (timestamp))

            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)
    # collections = pymongo.MongoClient('mongodb://root:miaoji1109-=@10.19.2.103:27017/')['data_result']['ctrip_poi_list']
    # for data in collections.find():
    #     table_name = data['collections'].split("_",6)[-1]
    #     results = data['result']
    #     timestamp, priority, sequence = get_seek(table_name)
    #     detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
    #     timestamp = send_ctripPoi_detail_task(results, detail_table_name, priority)
    #     if timestamp is not None:
    #         update_seek(table_name, timestamp, priority, sequence)


def monitoring_GT_list2detail():
    sql = """select source, source_id, city_id,country_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 8000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'total':
                continue
            if tab_args[2] != GT_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])

            # if table_dict.get(detail_table_name, True):
            #     create_table(detail_table_name)

            timestamp = send_GT_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s' % (timestamp))

            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)

##--


def monitoring_hotel_list2detail():
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 5000"""

    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'hotel':
                continue
            if tab_args[2] not in HOTEL_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            # update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List',
            #                        collections.find({"task_name": table_name}).count(), sum_or_set=False)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp = send_hotel_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('sequence  :  %s' % (timestamp,))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_result_list2detail():
    sql = """select id, source_list, utime from %s where status = 1 and utime >= '%s' order by utime limit 5000"""
    sources = ['agoda', 'booking', 'ctrip', 'expedia', 'elong', 'hotels']
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'result':
                continue
            if tab_args[2] not in RESULT_SOURCE:
                continue
            if tab_args[3] == 'test' or tab_args[3].endswith('f'):
                continue
            if table_name=='list_result_daodao_20180401a':continue
            if table_name=='list_result_google_20180401a':continue
            if table_name=='list_result_daodao_20180412b':continue

            timestamp, priority, sequence = get_seek(table_name)

            flag = 'g' if tab_args[2]=='google' else 'd'

            # update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List',
            #                        collections.find({"task_name": table_name}).count(), sum_or_set=False)

            detail_tables = {}
            for source in sources:
                detail_table_name = '_'.join(['detail', tab_args[1], flag+source, tab_args[3]])
                detail_tables[source] = detail_table_name
                if table_dict.get(detail_table_name, True):
                    create_table(detail_table_name)

            timestamp = send_result_detail_task(
                tab_args[2], execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_tables, priority)
            logger.info('sequence  :  %s' % (timestamp,))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)

def monitoring_result_daodao_filter():
    sql = """select id, source_list, utime from %s where source_list is not null and status = 1 and utime >= '%s' order by utime limit 2000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'result':
                continue
            if tab_args[2] != 'daodao':
                continue
            if tab_args[3] == 'test':
                continue
            if table_name=='list_result_daodao_20180401a':continue
            if table_name=='list_result_daodao_20180412b':continue

            timestamp, priority, sequence = get_seek(table_name+'f')

            timestamp = send_result_daodao_filter(
                tab_args[2], execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), table_name, priority)
            logger.info('sequence  :  %s' % (timestamp,))
            if timestamp is not None:
                update_seek(table_name+'f', timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_result_daodao_convergence():
    sql = "select id, localtion_id, source_list from {} where source_id = '%s'"
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'result':
                continue
            if tab_args[2] != 'daodao':
                continue
            if tab_args[3] == 'test' or tab_args[3].endswith('f'):
                continue
            if table_name!='list_result_daodao_20180412a':continue
            sql = sql.format(table_name)
            collection_name = 'Task_Queue_hotel_list_TaskName_'+table_name
            collections = db[collection_name]
            for line in collections.find({
                'convergenced': 0,
                'finished': 1,
                'used_times': {'$lt': 7}
            }, {
                'args': 1,
                'task_token': 1,
            }):
                task_token, source_id = line['task_token'], line['args']['source_id']
                # source_id = 'g123412'
                rows = execute_sql(sql % source_id)
                status = 1
                for id, localtion_id, hotels in rows:
                    for k,v in json.loads(hotels or '{}').iteritems():
                        if k in ('agoda', 'booking', 'ctrip', 'elong', 'hotels') and v in ('', None, 'NULL', 'null'):
                            status = 0
                            break
                    if status == 0:break

                if status == 0:
                    logger.info('重置任务source_id  :  %s' % (source_id,))
                    collections.update({
                        'task_token': task_token
                    },{
                        '$set': {
                            "finished": 0,
                            'running': 0,
                            'used_times': 0
                        }
                    }, multi=True)
                else:
                    logger.info('重置任务source_id  :  %s' % (source_id,))
                    collections.update({
                        'task_token': task_token
                    }, {
                        '$set': {
                            "convergenced": 1,
                        }
                    }, multi=True)

    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_hotel_detail2ImgOrComment():
    sql = """select source, source_id, city_id, img_items, id from %s where id >= %d order by id limit 5000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'detail':
                continue
            if tab_args[1] != 'hotel':
                continue
            if tab_args[2] not in HOTEL_SOURCE:
                continue
            if tab_args[3] in ('test', '20170928d', '20170926a'):
                continue

            timestamp, priority, sequence = get_seek(table_name)

            images_table_name = ''.join(['images_', table_name.split('_', 1)[1]])
            if table_dict.get(images_table_name, True):
                create_table(images_table_name)

            sequence = send_image_task(execute_sql(sql % ('ServicePlatform.' + table_name, sequence)),
                                       table_name,
                                       priority, is_poi_task=False)
            logger.info('timestamp  :  %s' % (timestamp,))
            if sequence is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_poi_list2detail():
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 5000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] not in ('rest', 'attr', 'shop'):
                continue
            if tab_args[2] != POI_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue
            if '_bak' in table_name:
                # 备份表不进入发任务
                continue

            timestamp, priority, sequence = get_seek(table_name)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp = send_poi_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s' % (timestamp,))

            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_poi_detail2imgOrComment():
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'detail':
                continue
            if tab_args[1] not in ('rest', 'attr', 'shop', 'total'):
                continue
            if tab_args[2] not in (POI_SOURCE, QYER_SOURCE):
                continue
            if tab_args[3] == 'test':
                continue

            if tab_args[2] == POI_SOURCE:
                sql = """select source, id, city_id, imgurl, utime from %s where utime >= '%s' order by utime limit 5000"""
            else:
                sql = """select source, id, city_id, imgurl, insert_time from %s where insert_time >= '%s' order by insert_time limit 5000"""

            if not tab_args[-1] >= '20171120a' and 'total_qyer_20171120a' not in table_name:
                # 过滤旧的图片任务
                continue

            timestamp, priority, sequence = get_seek(table_name)

            images_table_name = ''.join(['images_', table_name.split('_', 1)[1]])
            if table_dict.get(images_table_name, True):
                create_table(images_table_name)

            timestamp = send_image_task(execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)),
                                        table_name,
                                        priority, is_poi_task=True)
            logger.info('timestamp  :  %s' % (timestamp))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_qyer_list2detail():
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 5000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list':
                continue
            if tab_args[1] != 'total':
                continue
            if tab_args[2] != QYER_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp = send_qyer_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s' % (timestamp))

            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def _monitoring_zombies_task_by_hour(collections):
    try:
        cursor = collections.find(
            {'running': 1, 'utime': {'$lt': datetime.datetime.now() - datetime.timedelta(hours=1)}}, {'_id': 1},
            hint=[('running', 1), ('utime', -1)]).limit(
            10000)
        id_list = [id_dict['_id'] for id_dict in cursor]
        result = collections.update({
            '_id': {
                '$in': id_list
            }
        }, {
            '$set': {
                'running': 0
            }
        }, multi=True)
        logger.info('monitoring_zombies_task  --  filter:  %s, count: %d, result: %s' % (
            str(cursor._Cursor__spec), len(id_list), str(result)))
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_zombies_task_by_hour():
    for collections in get_each_task_collection(db=db):
        _monitoring_zombies_task_by_hour(collections=collections)


def _monitoring_zombies_task_total(collections):
    try:
        cursor = collections.find(
            {'running': 1}, {'_id': 1},
            hint=[('running', 1)]).limit(10000)
        id_list = [id_dict['_id'] for id_dict in cursor]
        result = collections.update({
            '_id': {
                '$in': id_list
            }
        }, {
            '$set': {
                'running': 0
            }
        }, multi=True)
        logger.info('monitoring_zombies_task  --  filter:  %s, count: %d, result: %s' % (
            str(cursor._Cursor__spec), len(id_list), str(result)))
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_zombies_task_total():
    for collections in get_each_task_collection(db=db):
        _res = re.findall("Task_Queue_(.+)_TaskName", collections.name)
        if not _res:
            continue
        if not _res[0]:
            continue
        queue_name = _res[0]

        idle_seconds, msg_num, max_msg_num = detect_msg_num(queue_name=queue_name)

        if idle_seconds < 120:
            continue
        _monitoring_zombies_task_total(collections=collections)


def monitoring_supplement_field():
    try:
        table_name = 'supplement_field'
        sql = """select table_name, type, source, sid, other_info, status, utime from %s where status = 0 and utime >= '%s' order by utime"""
        timestamp, _v, _seq = get_seek(table_name)
        timestamp = qyer_supplement_map_info(
            execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)))
        logger.info('supplement_field timestamp  :  %s' % (timestamp,))
        if timestamp is not None:
            update_seek(table_name, timestamp)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


MAX_CITY_TASK_PER_SEARCH = 10000
MAX_TASK_PER_CITY = 20
FINISHED_ZERO_COUNT = 4


@cachetools.func.ttl_cache(maxsize=256, ttl=600)
def get_city_date(task_name, date_index):
    date_index = int(date_index)
    city_collections = db['CityTaskDate']
    _res = city_collections.find_one({'task_name': task_name})
    return _res['dates'][date_index]


def city2list():
    # aaa = str([str(collection_name) for collection_name in db.collection_names() if str(collection_name).startswith('City_Queue_')])
    for collection_name in db.collection_names():
        if not str(collection_name).startswith('City_Queue_'):
            continue
        if collection_name in ('City_Queue_grouptravel_TaskName_city_total_GT_20180312a', 'City_Queue_grouptravel_TaskName_city_total_GT_20180314a'):continue
        if not collection_name.endswith('0416a'):continue
        collections = db[collection_name]
        _count = 0

        # 先获取一条数据，用以初始化入任务模块，可能这条数据有问题
        for each in collections.find({}):
            if 'task_name' in each:
                per_data = copy.deepcopy(each)
                break
        # per_data = collections.find_one()
        task_name = per_data['task_name']

        new_task_name = re.sub('city_', 'list_', task_name)
        create_table(new_task_name)
        logger.info('转换任务名  %s : %s' % (task_name, new_task_name))

        with InsertTask(worker=per_data['worker'], queue=per_data['queue'], routine_key=per_data['routing_key'],
                        task_name=new_task_name, source=per_data['source'], _type=per_data['type'],
                        priority=per_data['priority'], task_type=TaskType.LIST_TASK) as it:
            for line in collections.find({"finished": 0}):
                # 由于上方使用取多个，找 task_name 的方法来实现，这里会判断 task_name 是否在此当中
                if 'task_name' not in line:
                    continue
                if int(line['date_index']) > len(set(list(map(lambda x: x[0], line['data_count'])))):
                    # 当前日期数目如果与已回来的任务数目相同，或者小于的话，则应该推进任务分发，否则为任务还没有完成，需要等待任务完成后再分发
                    # 发任务数目与返回的全量任务 id 数目相同时，代表之前发的任务已经完成
                    continue

                if len(set(list(map(lambda x: x[0], line['data_count'])))) >= MAX_TASK_PER_CITY:
                    # 当前已完成任务数目大于城市最大任务数目，可认为任务完成
                    collections.update({'list_task_token': line['list_task_token']}, {"$set": {"finished": 1}})

                if len(filter(lambda x: x[-1], line['data_count'])) > FINISHED_ZERO_COUNT:
                    # 如果正常返回的数据中连续 FINISHED_ZERO_COUNT 次为 0 ，认为任务完成，并修改状态位置
                    if all(
                            map(
                                lambda x: int(x[3]) == 0,
                                list(
                                    sorted(
                                        filter(
                                            lambda x: x[-1],
                                            line['data_count']
                                        ),
                                        key=lambda x: x[1]
                                    )
                                )[-FINISHED_ZERO_COUNT:]
                            )
                    ):
                        # 全部为 0 则表明该城市任务已经积累完成
                        collections.update({'list_task_token': line['list_task_token']}, {"$set": {"finished": 1}})
                        continue
                # if all(map(lambda x: x[3] == 0,
                #            list(filter(lambda x: x[-1], line['data_count']))[-FINISHED_ZERO_COUNT:])):
                #     # 全部为 0 则表明该城市任务已经积累完成
                #     collections.update({'list_task_token': line['list_task_token']}, {"$set": {"finished": 1}})
                #     continue

                _count += 1
                if _count == MAX_CITY_TASK_PER_SEARCH:
                    # 到达最大城市任务数目后，结束任务分发
                    break

                # 基本信息，第几个日期
                date_index = line['date_index']

                args = line['args']
                new_date = get_city_date(task_name, date_index)
                args['check_in'] = new_date
                args['date_index'] = date_index

                it.insert_task(args=args)

                # 更新任务状态
                collections.update({
                    '_id': line['_id']
                }, {
                    '$inc': {'date_index': 1}
                })


class TaskSender(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    #monitoring_ctripPoi_list2detail()

    # monitoring_PoiSource_list2detail()

    #monitoring_hotel_list2detail()


    # monitoring_poi_detail2imgOrComment()
    # monitoring_hotel_detail2ImgOrComment()
    # while True:
        #monitoring_qyer_list2detail()
        # monitoring_zombies_task_total()
    # city2list()
    # monitoring_result_list2detail()
    # monitoring_result_daodao_filter()
    monitoring_result_daodao_convergence()
        # get_default_timestramp()
        # get_seek('hotel_list2detail_test')
        # update_seek('hotel_list2detail_test', datetime.datetime.now(), 9)
        # test_timstramp()
        #monitoring_hotel_list2detail()
        # monitoring_hotel_detail2ImgOrComment()
        # monitoring_zombies_task()
        # monitoring_ctripPoi_list2detail()
# query_sql = '''SELECT
#   source,
#   id,
#   city_id,
#   imgurl,
#   utime
# FROM detail_attr_daodao_20170929a
# WHERE source = 'daodao' AND id IN ('1407969',
#                                    '2349919',
#                                    '311968',
#                                    '311974',
#                                    '317946',
#                                    '4377562',
#                                    '550339',
#                                    '553566');'''
#     task = execute_sql(query_sql)
#     send_image_task(task,
#                     'images_attr_daodao_20170929a',
#                     11, is_poi_task=True)
