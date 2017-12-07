#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/24 下午1:52
# @Author  : Hou Rong
# @Site    : 
# @File    : test_download_file.py
# @Software: PyCharm
import gevent.monkey

gevent.monkey.patch_all()
import gevent.pool
import pymysql
import time
import os
from proj.my_lib.ks_upload_file_stream import download, upload_ks_file_stream

pool = gevent.pool.Pool(size=200)

PARENT_PATH = "/search/hourong/tmp_img"


def download_pic():
    conn = pymysql.connect(host='10.10.228.253', user='mioji_admin', password='mioji1109', charset='utf8',
                           db='BaseDataFinal')
    cursor = conn.cursor()
    cursor.execute('''SELECT
  file_name,
  source,
  sid
FROM poi_images
WHERE source = 'qyer' AND length(file_name) > 32;''')
    start = time.time()
    _count = 0
    for file_name, source, sid in cursor.fetchall():
        _count += 1
        # parent_path = os.path.join(PARENT_PATH, "###".join([source, sid]))
        new_file_name = file_name.split('.')[0]
        parent_path = os.path.join(PARENT_PATH, new_file_name)

        if not os.path.exists(parent_path):
            os.makedirs(parent_path)
        pool.apply_async(download, ("mioji-attr", file_name, parent_path))
    pool.join()
    cursor.close()
    conn.close()
    print("[Total: {}][Takes: {}]".format(_count, time.time() - start))


if __name__ == '__main__':
    download_pic()
