#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 上午11:01
# @Author  : Hou Rong
# @Site    : 
# @File    : HotelImgMergeSDK.py
# @Software: PyCharm
import json
import redis
from ast import literal_eval

from pymysql.cursors import DictCursor
from proj.mysql_pool import base_data_final_pool, spider_data_base_data_pool
from collections import defaultdict
from proj.my_lib.Common.Utils import retry
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.my_lib.logger import get_logger, func_time_logger
from proj.my_lib.Common.BaseSDK import BaseSDK
from proj.my_lib.ServiceStandardError import ServiceStandardError

logger = get_logger("hotel_img_merge")

first_img_priority = {
    'booking': 10,
    'ctrip': 9,
    'expedia': 8,
    'agoda': 7,
    'hotels': 6,
    'elong': 5
}

r = redis.Redis(host='10.10.180.145', db=2)


@retry(times=3)
def add_report(_source, _min_pixel, _task_name, report_key):
    r.incr("{}|_|{}|_|{}|_|{}".format(report_key, _task_name, _min_pixel, _source))


@func_time_logger
@retry(times=3, raise_exc=True)
def update_img(uid, first_img, img_list, target_table):
    conn = spider_data_base_data_pool.connection()
    cursor = conn.cursor()
    _sql = '''UPDATE {}
SET first_img = %s, img_list = %s
WHERE uid = %s;'''.format(target_table)
    _res = cursor.execute(_sql, (first_img, img_list, uid))
    conn.commit()
    cursor.close()
    conn.close()
    logger.debug("[insert db][uid: {}][first_img: {}][img_list: {}]".format(uid, first_img, img_list))
    return _res


@func_time_logger
@retry(times=3, raise_exc=True)
def _hotel_img_merge(uid, min_pixels, task_name, target_table):
    min_pixels = int(min_pixels)
    # get source sid
    conn = spider_data_base_data_pool.connection()
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
  source,
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
        # 错误图片，直接过滤
        if r.get('error_img_{}'.format(line['pic_md5'])) == '1':
            continue

        if not line['size']:
            continue

        # get max size
        h, w = literal_eval(line['size'])
        h = int(h)
        w = int(w)
        size = h * w
        if size > max_size:
            max_size = size
            max_size_img = line['pic_md5']

        add_report(line['source'], min_pixels, task_name, "total")
        logger.debug("[total img][source: {}]".format(line['source']))

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

        p_hash_dict[p_hash].append((line['pic_md5'], size, line['source']))

    # 从 pHash 中获取最好的一张图片
    for key_p_hash, images in p_hash_dict.items():
        img = sorted(images, key=lambda x: x[1], reverse=True)
        for i in img:
            add_report(i[-1], min_pixels, task_name, "finished")
            logger.debug("[saved img][source: {}]".format(i[-1]))
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
            if max_size_img != '':
                add_report("all", min_pixels, task_name, "all_failed")
            first_img = img_list = max_size_img

    length = len(result)

    if length == 0:
        add_report("all", min_pixels, task_name, "0")
    elif 10 >= length > 0:
        add_report("all", min_pixels, task_name, "1_10")
    elif 30 >= length > 10:
        add_report("all", min_pixels, task_name, "11_30")
    elif length > 30:
        add_report("all", min_pixels, task_name, "30_max")

    update_img(uid, first_img, img_list, target_table)

    return uid, first_img, img_list


class HotelImgMergeSDK(BaseSDK):
    def _execute(self, **kwargs):
        res = _hotel_img_merge(self.task.kwargs['uid'], self.task.kwargs.get('min_pixels', '200000'),
                               self.task.task_name,
                               target_table=self.task.kwargs.get('target_table', 'hotel'))
        self.task.error_code = 0
        return res
