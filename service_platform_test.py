#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/10 上午10:20
# @Author  : Hou Rong
# @Site    :
# @File    : service_platform_test.py
# @Software: PyCharm
import uuid
import random
import os
import json
import logging
import functools
import inspect
import pymysql
import pandas
from DBUtils.PooledDB import PooledDB
from mioji.common.task_info import Task
from mioji.spider_factory import factory
from datetime import datetime, timedelta
from collections import defaultdict
from logging.handlers import RotatingFileHandler

log_path = "./"
CASE_NUM = 10
OLD_SOURCE = ''
REQUIRED = []


class NamedRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename):
        super(NamedRotatingFileHandler, self).__init__(
            filename=os.path.join(log_path, "{0}.log".format(filename)),
            maxBytes=100 * 1024 * 1024,
            backupCount=2
        )


def get_logger(logger_name):
    """
    初始化 logger get 可以获取到，为单例模式
    """
    if not os.path.exists(log_path):
        os.makedirs(log_path)
        os.mkdir(log_path)

    # getLogger 为单例模式
    service_platform_logger = logging.getLogger(logger_name)
    service_platform_logger.setLevel(logging.DEBUG)
    datefmt = "%Y-%m-%d %H:%M:%S"
    file_log_format = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s:        %(message)s"
    formtter = logging.Formatter(file_log_format, datefmt)

    # handler 存在的判定
    if not service_platform_logger.handlers:
        # rotating file logger
        file_handle = NamedRotatingFileHandler(logger_name)
        file_handle.setFormatter(formtter)
        service_platform_logger.addHandler(file_handle)
        steam_handler = logging.StreamHandler()
        service_platform_logger.addHandler(steam_handler)

    return service_platform_logger


func_count_dict = defaultdict(int)
time_logger = get_logger('func_time_logger')


def func_time_logger(fun):
    @functools.wraps(fun)
    def logging(*args, **kw):
        try:
            func_file = inspect.getfile(fun)
        except Exception:
            func_file = ''
        func_name = fun.__name__
        func_key = (func_file, func_name)
        func_count_dict[func_key] += 1
        begin = datetime.now()
        result = fun(*args, **kw)
        end = datetime.now()
        time_logger.debug('[文件: {}][函数: {}][耗时 {}][当前运行 {} 个此函数]'.format(
            func_file, func_name, end - begin, func_count_dict[func_key]
        ))
        func_count_dict[func_key] -= 1
        return result

    return logging


def init_pool(host, user, password, database, max_connections=5):
    mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=max_connections,
                             host=host, port=3306, user=user, passwd=password,
                             db=database, charset='utf8', use_unicode=False, blocking=True)
    return mysql_db_pool


db_config = dict(
    user='reader',
    password='mioji1109',
    host='10.10.230.206',
    database='source_info'
)
spider_data_poi_pool = init_pool(**db_config)


def fetchall(conn_pool, sql, is_dict=False):
    conn = conn_pool.connection()
    if is_dict:
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    else:
        cursor = conn.cursor()
    cursor.execute('''SET SESSION sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''));''')
    cursor.execute(sql)
    for line in cursor.fetchall():
        yield line
    cursor.close()
    conn.close()


def hotel_list_database(source, check_in, suggest_type='1', suggest=''):
    # 初始化任务
    task = Task()
    task.ticket_info = {
        "is_new_type": True,
        "suggest_type": int(suggest_type),
        "suggest": suggest,
        "check_in": str(check_in),
        "stay_nights": '1',
        "occ": '2',
        'is_service_platform': True,
        'tid': uuid.uuid4(),
        'used_times': random.randint(1, 6),
    }
    task.content = ''

    # 初始化 spider
    spider = factory.get_spider_by_old_source(OLD_SOURCE)
    spider.task = task

    # 请求
    error_code = spider.crawl(required=REQUIRED, cache_config=False)

    return error_code, spider.result, spider.page_store_key_list


def get_task(source):
    sql = '''SELECT
  sid,
  suggest
FROM ota_location
WHERE source = '{}'
ORDER BY rand()
LIMIT {};'''.format(source, CASE_NUM)
    return list(fetchall(spider_data_poi_pool, sql=sql, is_dict=True))


def test_crawl_result(source):
    logger = get_logger(datetime.now().strftime('{}_test_%Y%m%d'.format(source)))
    check_in = (datetime.now() + timedelta(days=20)).strftime('%Y%m%d')
    tasks = get_task(source=source)

    logger.info("[source: {}]".format(source))
    logger.info("[check_in: {}]".format(check_in))
    logger.info("[tasks: {}]".format(tasks))

    data = []
    columns = ['source', 'sid', 'suggest', 'check_in', 'error_code']
    for line in tasks:
        error_code, result, page_store_key_list = hotel_list_database(source=source, check_in=check_in,
                                                                      suggest=line['suggest'])

        report_data = {}
        for r in REQUIRED:
            key = '{}_{}_num'.format(source, r)
            value = len(result[r])

            report_data[key] = value
            if key not in columns:
                columns.append(key)

            key = '{}_{}_result'.format(source, r)
            value = json.dumps(result[r])

            report_data[key] = value
            if key not in columns:
                columns.append(key)

        res = {
            'source': source,
            'sid': line['sid'],
            'suggest': json.dumps(line['suggest']),
            'check_in': check_in,
            'error_code': error_code,
        }
        res.update(report_data)
        data.append(res)

    df = pandas.DataFrame(columns=columns,
                          data=data)
    df.to_excel(datetime.now().strftime('./{}_test_%Y%m%d.xlsx'.format(source)))

class TestBooking(unittest.TestCase):
    def test_name(self):
        name_cases = ['b36a1e904c0cf44784e36f29f3eba11e']
        name_result = [('', 'Penzi\xc3\xb3n Rogalo')]
        for case, res in zip(name_cases, name_result):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_booking_parser(j_data['data'])
            self.assertTupleEqual((result.hotel_name, result.hotel_name_en), res)


if __name__ == '__main__':
    REQUIRED = ['hotel']
    OLD_SOURCE = 'bookingListHotel'
    test_crawl_result('booking')
