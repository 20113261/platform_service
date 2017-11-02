#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 上午11:01
# @Author  : Hou Rong
# @Site    : 
# @File    : merge_tasks.py
# @Software: PyCharm
from ast import literal_eval

from pymysql.cursors import DictCursor
from mysql_pool import base_data_final_pool, spider_data_base_data_pool, base_data_test_pool


def hotel_img_merge(uid):
    # get source sid
    conn = base_data_test_pool.connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT
  source,
  sid
FROM hotel_unid
WHERE uid = %s;''', (uid,))
    s_sid_str = ','.join(map(lambda x: "('{}', '{}')".format(*x), cursor.fetchall()))
    cursor.close()
    conn.close()

    # get img info
    conn = base_data_final_pool.connection()
    cursor = conn.cursor(cursor=DictCursor)
    cursor.execute('''SELECT
  pic_md5,
  size,
  file_md5
FROM hotel_images
WHERE (source, source_id) IN ({});'''.format(s_sid_str))

    # init
    max_size = -1
    max_size_img = ''
    md5_set = set()
    p_hash_set = set()
    result = set()

    for line in cursor.fetchall():
        line['pic_md5']
        line['size']
        line['file_md5']

        # get max size
        h, w = literal_eval(line['size'])
        h = int(h)
        w = int(w)
        size = h * w
        if size > max_size:
            max_size = size
            max_size_img = line['pic_md5']

        # 过滤规则
        # pixel
        if size < 200000:
            continue

        # scale
        # min scale
        scale = w / h
        if scale < 0.9:
            if w < 500:
                continue

        # max scale
        if scale > 2.5:
            continue

        md5_set.add(line['file_md5'])
        result.add(line['pic_md5'])
    cursor.close()
    conn.close()

    img_list = '|'.join(result)
    if img_list:
        # 首图策略
        first_img = list(result)[0]
    else:
        first_img = img_list = max_size_img
    return uid, first_img, img_list
