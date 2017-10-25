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
from proj.my_lib.ks_upload_file_stream import download
from proj.mysql_pool import service_platform_pool, spider_data_poi_pool
from proj.my_lib.logger import get_logger, func_time_logger

pool = gevent.pool.Pool(size=200)

logger = get_logger("pic_detect_download")

PARENT_PATH = "/data/image/formatted_image"
EACH_TIMES_DOWNLOAD = 1000


@func_time_logger
def download_and_update_table(file_name, parent_path, poi_id, task_id):
    download("mioji-attr", file_name, parent_path)
    logger.debug("[download pic finished][task_id: {}][poi_id: {}][file name: {}]".format(task_id, poi_id, file_name))

    # update task table status
    task_conn = service_platform_pool.connection()
    task_cursor = task_conn.cursor()
    task_cursor.execute('''UPDATE pic_detect_task SET status=2 WHERE id=%s;''', (task_id,))
    logger.debug("[update status finished][task_id: {}][poi_id: {}][file name: {}]".format(task_id, poi_id, file_name))

    # insert poi detect data table
    data_conn = spider_data_poi_pool.connection()
    data_cursor = data_conn.cursor()
    data = (poi_id, os.path.join(parent_path.replace('/data/image/formatted_image', '/search/image/formatted_image'),
                                 file_name))
    data_cursor.execute(
        '''INSERT IGNORE INTO PoiPictureInformation (poi_id, pic_name, is_scaned) VALUES (%s, %s, 0); ''',
        data)
    logger.debug("[update status finished][task_id: {}][poi_id: {}][file name: {}]".format(task_id, poi_id, file_name))

    # 由于事务关系原因，当两个 sql 均运行成功后才入库，否则不 commit
    task_conn.commit()
    task_cursor.close()
    task_conn.close()

    data_conn.commit()
    data_cursor.close()
    data_conn.close()


def download_pic():
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='ServicePlatform')
    cursor = conn.cursor()
    cursor.execute('''SELECT
  id,
  city_id,
  poi_id,
  pic_name
FROM pic_detect_task WHERE status=0 ORDER BY city_grade LIMIT {};'''.format(EACH_TIMES_DOWNLOAD))
    start = time.time()
    _count = 0
    for task_id, city_id, poi_id, file_name in cursor.fetchall():
        _count += 1
        city_path = os.path.join(PARENT_PATH, city_id)
        parent_path = os.path.join(city_path, poi_id)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)
        pool.apply_async(download_and_update_table, (file_name, parent_path, poi_id, task_id))
    pool.join()
    cursor.close()
    conn.close()
    logger.debug("[Total: {}][Takes: {}]".format(_count, time.time() - start))


if __name__ == '__main__':
    download_pic()
