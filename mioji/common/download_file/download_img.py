#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/25 下午12:03
# @Author  : Hou Rong
# @Site    :
# @File    : download_img.py
# @Software: PyCharm
import gevent.monkey

gevent.monkey.patch_all()
import gevent.pool
import pymysql
import time
import os
from ks_upload_file_stream import download
from mysql_pool import service_platform_pool, spider_data_poi_pool
from logger import get_logger, func_time_logger

pool = gevent.pool.Pool(size=200)

logger = get_logger("pic_detect_download")

PARENT_PATH = "/data/image/formatted_image"

SCAN_FILTER = 6000
EACH_TIMES_PER_TASK = 1000
MAX_PIC_PER_VIEW = 10000

update_data_list = []
task_data_list = []
is_new_task = True


@func_time_logger
def insert_all_data():
    global update_data_list
    global task_data_list
    global is_new_task
    # init insert conn and cursor
    task_conn = service_platform_pool.connection()
    task_cursor = task_conn.cursor()

    data_conn = spider_data_poi_pool.connection()
    data_cursor = data_conn.cursor()

    # update task table and insert data table
    if is_new_task:
        _res = task_cursor.executemany('''UPDATE pic_detect_task_new SET status=2 WHERE id=%s;''', update_data_list)
    else:
        _res = task_cursor.executemany('''UPDATE pic_detect_task SET status=2 WHERE id=%s;''', update_data_list)
    logger.debug("[update status finished][update task: {}]".format(_res))
    _res = data_cursor.executemany(
        '''INSERT IGNORE INTO PoiPictureInformation (city_id, poi_id, pic_name, is_scaned) VALUES (%s, %s, %s, 0); ''',
        task_data_list)
    logger.debug(
        "[update status finished][insert poi face detect task: {}]".format(_res))

    # 由于事务关系原因，当两个 sql 均运行成功后才入库，否则不 commit
    task_conn.commit()
    task_cursor.close()
    task_conn.close()

    data_conn.commit()
    data_cursor.close()
    data_conn.close()


@func_time_logger
def download_and_prepare_data(file_name, parent_path, city_id, poi_id, task_id):
    global update_data_list
    global task_data_list
    download("mioji-attr", file_name, parent_path)
    logger.debug("[download pic finished][task_id: {}][poi_id: {}][file name: {}]".format(task_id, poi_id, file_name))

    # update task table status
    update_data = (task_id,)
    task_data = (
        city_id, poi_id,
        os.path.join(parent_path.replace('/data/image/formatted_image', '/search/image/formatted_image'),
                     file_name))
    update_data_list.append(update_data)
    task_data_list.append(task_data)


def _download_pic():
    global update_data_list
    global task_data_list
    global is_new_task
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='ServicePlatform')
    cursor = conn.cursor()
    # 优先使用新任务
    is_new_task = True
    _res = cursor.execute('''SELECT
  id,
  city_id,
  poi_id,
  pic_name
FROM pic_detect_task_new WHERE status=0 ORDER BY `city_grade`,`city_id`,`poi_id` LIMIT {};'''.format(MAX_PIC_PER_VIEW))

    if _res == 0:
        is_new_task = False
        # 新数据没有，则使用旧任务
        cursor.execute('''SELECT
          id,
          city_id,
          poi_id,
          pic_name
        FROM pic_detect_task WHERE status=0 ORDER BY `city_grade`,`city_id`,`poi_id` LIMIT {};'''.format(
            MAX_PIC_PER_VIEW))
    start = time.time()
    _count = 0

    update_data_list = []
    task_data_list = []
    old_poi_id = None
    for task_id, city_id, poi_id, file_name in cursor.fetchall():
        _count += 1
        city_path = os.path.join(PARENT_PATH, city_id)
        parent_path = os.path.join(city_path, poi_id)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        if old_poi_id != poi_id:
            old_poi_id = poi_id
            logger.info("[next poi][city_id: {}][poi_id: {}][_count: {}]".format(city_id, poi_id, _count))
            if _count > EACH_TIMES_PER_TASK:
                break

        pool.apply_async(download_and_prepare_data,
                         (file_name, parent_path, city_id, poi_id, task_id))
    pool.join(timeout=75)
    cursor.close()
    conn.close()
    insert_all_data()
    logger.debug("[Total: {}][Takes: {}]".format(_count, time.time() - start))


def un_scanned_pic_count():
    conn = spider_data_poi_pool.connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT count(*)
FROM PoiPictureInformation WHERE is_scaned=0;''')
    _res = cursor.fetchone()
    cursor.close()
    conn.close()

    return int(_res[0])


def download_pic():
    _count = un_scanned_pic_count()
    if _count > SCAN_FILTER:
        logger.debug("[un scanned pic larger than: {}][count: {}]".format(SCAN_FILTER, _count))
    else:
        logger.debug("[start download pic][un scanned pic: {}]".format(_count))
        _download_pic()


if __name__ == '__main__':
    download_pic()
