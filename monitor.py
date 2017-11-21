#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 上午9:38
# @Author  : Hou Rong
# @Site    :
# @File    : hotel_list_routine_tasks.py
# @Software: PyCharm
import re
import datetime
import time
import traceback
from itertools import repeat
import redis
import pymysql
import pymongo
import os
import sys
import cachetools.func
from send_task import send_hotel_detail_task, send_poi_detail_task, send_qyer_detail_task, send_image_task
from attach_send_task import qyer_supplement_map_info
from proj.my_lib.logger import get_logger
from send_email import send_email, SEND_TO, EMAIL_TITLE
from proj.my_lib.Common.Utils import get_each_task_collection, generate_collection_name
from proj.mysql_pool import service_platform_pool
from toolbox.Hash import get_token
from MongoTaskInsert import InsertTask, TaskType

logger = get_logger('monitor')

task_statistics = redis.Redis(host='10.10.180.145', db=9)
client = pymongo.MongoClient(host='10.10.231.105')
db = client['MongoTask']
HOTEL_SOURCE = (
    'agoda', 'booking', 'ctrip', 'elong', 'expedia', 'hotels', 'hoteltravel', 'hrs', 'cheaptickets', 'orbitz',
    'travelocity', 'ebookers', 'tripadvisor', 'ctripcn', 'hilton')
POI_SOURCE = 'daodao'
QYER_SOURCE = 'qyer'
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
        elif tab_args[2] == 'daodao':
            sql_file = LOAD_FILES['images_daodao']

    cursor.execute(sql_file % table_name)
    cursor.close()
    conn.close()


def monitoring_hotel_list2detail():
    sql = """select source, source_id, city_id, hotel_url, utime from %s where utime >= '%s' order by utime limit 5000"""

    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'list': continue
            if tab_args[1] != 'hotel': continue
            if tab_args[2] not in HOTEL_SOURCE: continue
            if tab_args[3] == 'test': continue

            timestamp, priority, sequence = get_seek(table_name)

            # update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List',
            #                        collections.find({"task_name": table_name}).count(), sum_or_set=False)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp, success_count = send_hotel_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('sequence  :  %s, success_count  :  %s' % (timestamp, success_count))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
            if success_count > 0:
                update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'Detail', success_count)
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
            if tab_args[0] != 'detail': continue
            if tab_args[1] != 'hotel': continue
            if tab_args[2] not in HOTEL_SOURCE: continue
            if tab_args[3] in ('test', '20170928d', '20170926a'): continue

            timestamp, priority, sequence = get_seek(table_name)

            images_table_name = ''.join(['images_', table_name.split('_', 1)[1]])
            if table_dict.get(images_table_name, True):
                create_table(images_table_name)

            sequence, success_count = send_image_task(execute_sql(sql % ('ServicePlatform.' + table_name, sequence)),
                                                      table_name,
                                                      priority, is_poi_task=False)
            logger.info('timestamp  :  %s, success_count  :  %s' % (timestamp, success_count))
            if sequence is not None:
                update_seek(table_name, timestamp, priority, sequence)
            if success_count > 0:
                update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'Images', success_count)
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
            if tab_args[0] != 'list': continue
            if tab_args[1] not in ('rest', 'attr', 'shop'): continue
            if tab_args[2] != POI_SOURCE: continue
            if tab_args[3] == 'test': continue

            timestamp, priority, sequence = get_seek(table_name)

            # update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List',
            #                        collections.find({"task_name": table_name}).count(), sum_or_set=False)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp, success_count = send_poi_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s, success_count  :  %s' % (timestamp, success_count))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
            if success_count > 0:
                update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'Detail', success_count)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def monitoring_poi_detail2imgOrComment():
    sql = """select source, id, city_id, imgurl, utime from %s where utime >= '%s' order by utime limit 5000"""
    try:
        table_dict = {name: _v for (name,), _v in zip(get_all_tables(), repeat(None))}

        for table_name in table_dict.keys():

            tab_args = table_name.split('_')
            if tab_args[0] != 'detail':
                continue
            if tab_args[1] not in ('rest', 'attr', 'shop', 'total'):
                continue
            if tab_args[2] != POI_SOURCE:
                continue
            if tab_args[3] == 'test':
                continue

            timestamp, priority, sequence = get_seek(table_name)

            images_table_name = ''.join(['images_', table_name.split('_', 1)[1]])
            if table_dict.get(images_table_name, True):
                create_table(images_table_name)

            timestamp, success_count = send_image_task(execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)),
                                                       table_name,
                                                       priority, is_poi_task=True)
            logger.info('timestamp  :  %s, success_count  :  %s' % (timestamp, success_count))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
            if success_count > 0:
                update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'Images', success_count)
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
            if tab_args[0] != 'list': continue
            if tab_args[1] != 'total': continue
            if tab_args[2] != QYER_SOURCE: continue
            if tab_args[3] == 'test': continue

            timestamp, priority, sequence = get_seek(table_name)

            # update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'List',
            #                        collections.find({"task_name": table_name}).count(), sum_or_set=False)

            detail_table_name = ''.join(['detail_', table_name.split('_', 1)[1]])
            if table_dict.get(detail_table_name, True):
                create_table(detail_table_name)

            timestamp, success_count = send_qyer_detail_task(
                execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)), detail_table_name, priority)
            logger.info('timestamp  :  %s, success_count  :  %s' % (timestamp, success_count))
            if timestamp is not None:
                update_seek(table_name, timestamp, priority, sequence)
            if success_count > 0:
                update_task_statistics(tab_args[-1], tab_args[1], tab_args[2], 'Detail', success_count)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


def _monitoring_zombies_task(collections):
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


def monitoring_zombies_task():
    for collections in get_each_task_collection(db=db):
        _monitoring_zombies_task(collections=collections)


def monitoring_supplement_field():
    try:
        table_name = 'supplement_field'
        sql = """select table_name, type, source, sid, other_info, status, utime from %s where status = 0 and utime >= '%s' order by utime"""
        timestamp, _v, _seq = get_seek(table_name)
        timestamp, success_count = qyer_supplement_map_info(
            execute_sql(sql % ('ServicePlatform.' + table_name, timestamp)))
        logger.info('supplement_field timestamp  :  %s, success_count  :  %s' % (timestamp, success_count))
        if timestamp is not None:
            update_seek(table_name, timestamp)
    except Exception as e:
        logger.error(traceback.format_exc(e))
        send_email(EMAIL_TITLE,
                   '%s   %s \n %s' % (sys._getframe().f_code.co_name, datetime.datetime.now(), traceback.format_exc(e)),
                   SEND_TO)


MAX_CITY_TASK_PER_SEARCH = 20000


@cachetools.func.ttl_cache(maxsize=256, ttl=600)
def get_city_date(task_name, date_index):
    date_index = int(date_index)
    city_collections = db['CityTaskDate']
    _res = city_collections.find_one({'task_name': task_name})
    return _res['dates'][date_index]


def city2list():
    collections = db['City_Queue_poi_list_TaskName_city_total_qyer_20171120a']
    _count = 0

    # 先获取一条数据，用以初始化入任务模块
    per_data = collections.find_one()
    task_name = per_data['task_name']

    create_table(task_name)

    new_task_name = re.sub('city_', 'list_', task_name)
    with InsertTask(worker=per_data['worker'], queue=per_data['queue'], routine_key=per_data['routing_key'],
                    task_name=new_task_name, source=per_data['source'], _type=per_data['type'],
                    priority=per_data['priority'], task_type=TaskType.LIST_TASK) as it:
        for line in collections.find({}):
            if int(line['date_index']) == len(line['task_result']):
                # 发任务数目与任务状态返回相等，代表该任务已经成功完成
                _count += 1
                if _count == MAX_CITY_TASK_PER_SEARCH:
                    # 到达最大城市任务数目后，结束任务分发
                    break

                # 基本信息，第几个日期
                date_index = line['date_index']

                args = line['args']
                new_date = get_city_date(task_name, date_index)
                args['check_in'] = new_date

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
    city2list()
    # get_default_timestramp()
    # get_seek('hotel_list2detail_test')
    # update_seek('hotel_list2detail_test', datetime.datetime.now(), 9)
    # test_timstramp()
    # monitoring_hotel_list2detail()
    # monitoring_hotel_detail2ImgOrComment()
    # monitoring_zombies_task()
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
