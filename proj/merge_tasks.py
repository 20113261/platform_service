#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 上午11:01
# @Author  : Hou Rong
# @Site    : 
# @File    : merge_tasks.py
# @Software: PyCharm
import json
import redis
from ast import literal_eval

from pymysql.cursors import DictCursor
from mysql_pool import base_data_final_pool, base_data_test_pool
from collections import defaultdict
from proj.my_lib.Common.Utils import retry

first_img_priority = {
    'booking': 10,
    'ctrip': 9,
    'expedia': 8,
    'agoda': 7,
    'hotels': 6,
    'elong': 5
}


def hotel_img_merge(uid, min_pixels=200000):
    return _hotel_img_merge(uid, min_pixels)


@retry(times=3, raise_exc=True)
def _hotel_img_merge(uid, min_pixels):
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
  file_md5,
  info
FROM hotel_images
WHERE (source, source_id) IN ({});'''.format(s_sid_str))

    # init
    max_size = -1
    max_size_img = ''
    result = set()
    p_hash_dict = defaultdict(list)

    for line in cursor.fetchall():
        # line['pic_md5']
        # line['size']
        # line['file_md5']
        line['info']

        # get max size
        h, w = literal_eval(line['size'])
        h = int(h)
        w = int(w)
        size = h * w
        if size > max_size:
            max_size = size
            max_size_img = line['pic_md5']

        # pHash filter
        if not line['info']:
            continue
        else:
            p_hash = json.loads(line['info'])['p_hash']

        # 过滤规则
        # pixel
        if size < min_pixels:
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

        p_hash_dict[p_hash].append((line['pic_md5'], size))

    # 从 pHash 中获取最好的一张图片
    for key_p_hash, images in p_hash_dict.items():
        img = sorted(images, key=lambda x: x[1], reverse=True)
        result.add(img[0][0])

    cursor.close()
    conn.close()

    conn = base_data_final_pool.connection()
    cursor = conn.cursor()
    query_sql = '''SELECT
  source,
  first_img
FROM first_images
WHERE (source, source_id) IN ({});'''.format(s_sid_str)
    cursor.execute(query_sql)
    _first_img_list = []
    for line in cursor.fetchall():
        _source = line[0]
        _first_img = line[1]
        if _first_img in result:
            _first_img_list.append({'img': _first_img, 'priority': first_img_priority[_source]})
    cursor.close()
    conn.close()

    first_img = ''
    # 首先使用第三方首图作为 first_img
    _first_img_list = sorted(_first_img_list, key=lambda x: x['priority'], reverse=True)
    if _first_img_list:
        first_img = _first_img_list[0]['img']

    # 图片列表字段生成
    img_list = '|'.join(result)

    # 如果没有，使用第一张图片作为首图，否则使用垃圾图中最大图片作为首图
    if not first_img:
        if result:
            first_img = list(result)[0]
        else:
            first_img = img_list = max_size_img

    return uid, first_img, img_list
