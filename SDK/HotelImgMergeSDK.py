#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 上午11:01
# @Author  : Hou Rong
# @Site    : 
# @File    : HotelImgMergeSDK.py
# @Software: PyCharm
import json
import pymysql.cursors
from urlparse import urlparse, urljoin

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
def add_content_report(_source, error):
    r.incr("content_report|_|{}|_|{}".format(_source, error))


@retry(times=3)
def add_report(_source, _min_pixel, _task_name, report_key):
    r.incr("{}|_|{}|_|{}|_|{}".format(report_key, _task_name, _min_pixel, _source))


class ReportException(Exception):
    @property
    def type(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__repr__()


class UnknownSource(ReportException):
    def __init__(self, source):
        self.source = source

    def __repr__(self):
        return "[UnknownSource][source: {}]".format(self.source)


class UrlNone(ReportException):
    def __init__(self, source):
        self.source = source

    def __repr__(self):
        return "[UrlNone][source: {}]".format(self.source)


class UpdateHotelValidation(object):
    @staticmethod
    def default_api_task_key_and_content(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        content = '{}&{}&'.format(each_data["mid"], each_data["sid"])
        return workload_key, content, workload_source

    @staticmethod
    def sid_only_key_and_content(each_data, double_key=False):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        if not double_key:
            content = '{}&'.format(each_data["sid"])
        else:
            content = '{}&&'.format(each_data["sid"])
        return workload_key, content, workload_source

    @staticmethod
    def booking(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        # 1231656&hotel/us/victorian-alamo-square-two-bedroom-apartment&
        if not each_data['hotel_url']:
            raise UrlNone(source='booking')
        tmp_url = urlparse(each_data['hotel_url']).path[1:]
        content = '{}&{}&'.format(each_data["sid"], tmp_url.split('.zh-cn.html')[0])
        return workload_key, content, workload_source

    @staticmethod
    def elong(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        # NULL&&294945&&圣彼得无限酒店&&NULL&&
        content = 'NULL&&{}&&{}&&NULL&&'.format(each_data["sid"], each_data["name"])
        return workload_key, content, workload_source

    @staticmethod
    def expedia(each_data, source='expedia'):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        # http://www.expedia.com.hk/cn/Sapporo-Hotels-La'gent-Stay-Sapporo-Oodori-Hokkaido.h15110395.Hotel-Information?&
        if not each_data['hotel_url']:
            raise UrlNone(source=source)
        if source == 'expedia':
            host = "https://www.expedia.com.hk/cn"
        elif source == 'ebookers':
            host = "https://www.ebookers.com"
        elif source == 'orbitz':
            host = "https://www.orbitz.com"
        elif source == 'travelocity':
            host = "https://www.travelocity.com"
        elif source == 'cheaptickets':
            host = "https://www.cheaptickets.com"
        else:
            host = "https://www.expedia.com.hk/cn"
        content = "{}{}{}".format(host, urlparse(each_data['hotel_url']).path, '?&')
        return workload_key, content, workload_source

    @staticmethod
    def agoda(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        # http://www.expedia.com.hk/cn/Sapporo-Hotels-La'gent-Stay-Sapporo-Oodori-Hokkaido.h15110395.Hotel-Information?&
        if not each_data['hotel_url']:
            raise UrlNone(source='agoda')
        content = urljoin("https://www.agoda.com", urlparse(each_data['hotel_url']).path) + '&'
        return workload_key, content, workload_source

    @staticmethod
    def hotels(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        # 洛杉矶&&美国&&1439028&&163102&&1&&20171010
        content = 'NULL&&NULL&&NULL&&{}&&'.format(each_data["sid"])
        return workload_key, content, workload_source

    @staticmethod
    def hilton(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        content = 'NULL&{}&{}&'.format(each_data["mid"], each_data["sid"])
        return workload_key, content, workload_source

    @staticmethod
    def accor(each_data):
        workload_source = each_data["source"] + "Hotel"
        workload_key = 'NULL|{}|{}'.format(each_data["sid"], workload_source)
        content = '{}&{}&'.format(each_data["sid"], each_data["name"])
        return workload_key, content, workload_source

    def _get_content(self, source, line):
        if source in (
                "ctripcn", "yundijie", "daolvApi", "dotwApi", "expediaApi", "gtaApi", "hotelbedsApi",
                "innstantApi",
                "jacApi", "mikiApi", "touricoApi", "holiday", "hotelsproApi", "jielvApi", "aicApi", "veturisApi"):
            each_data = self.default_api_task_key_and_content(line)
            return each_data
        elif source in ("expedia", "cheaptickets", "orbitz", "ebookers", "travelocity"):
            # ep 系，使用 url 类型的
            each_data = self.expedia(line, source=source)
            return each_data
        elif source in ("hrs", "ctrip", "ihg"):
            # 单纯 sid 的
            each_data = self.sid_only_key_and_content(line)
            return each_data
        elif source in ("marriott",):
            # 单纯 sid 的，两个 &&
            each_data = self.sid_only_key_and_content(line, double_key=True)
            return each_data
        elif source == "hilton":
            # hilton 专用，content 前面多了一个 NULL
            each_data = self.hilton(line)
            return each_data
        elif source == "booking":
            # booking 专用
            each_data = self.booking(line)
            return each_data
        elif source == "elong":
            # elong 专用
            each_data = self.elong(line)
            return each_data
        elif source == "hotels":
            # hotels 专用
            each_data = self.hotels(line)
            return each_data
        elif source == "agoda":
            # agoda 专用
            each_data = self.agoda(line)
            return each_data
        elif source == "accor":
            # accor 专用
            each_data = self.accor(line)
            return each_data
        elif source in (
                "hoteltravelEN", "hoteltravel", "venere", "venereEN", "agodaApi",
                "amoma",
                "haoqiaoApi", "hostelworld", "hotelclub", "kempinski", "starwoodhotels", "tongchengApi"):
            # 不更新 workload validation
            # hoteltravel, venere 源被下掉了
            # 由于 ctrip 爬虫当前倒了，本次不更新 ctrip
            '''
            这些源当前不进行验证，不生成相关任务
            agodaApiHotel
            amomaHotel
            haoqiaoApiHotel
            hostelworldHotel
            hotelclubHotel
            ihgHotel
            kempinskiHotel
            starwoodhotelsHotel
            '''
            return None
        else:
            logger.warning("[Unknown Source: {}]".format(source))
            raise UnknownSource(source=source)

    def get_content(self, source, line):
        try:
            res = self._get_content(source, line)
            if res:
                return res[1]
            else:
                return None
        except ReportException as e:
            add_content_report(source, str(e.type))
            return None
        except Exception as e:
            raise ServiceStandardError(error_code=ServiceStandardError.UNKNOWN_ERROR, wrapped_exception=e)


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
def update_unid_content(data):
    conn = spider_data_base_data_pool.connection()
    cursor = conn.cursor()
    _sql = '''UPDATE hotel_unid
SET content = %s
WHERE SOURCE = %s AND sid = %s;'''
    _res = cursor.executemany(_sql, data)
    conn.commit()
    cursor.close()
    conn.close()
    logger.debug("[insert db][count: {}][data: {}]".format(len(data), data))
    return _res


@func_time_logger
@retry(times=3, raise_exc=True)
def _hotel_img_merge(uid, min_pixels, task_name, target_table):
    min_pixels = int(min_pixels)
    upload_hotel_validation = UpdateHotelValidation()
    # get source sid
    conn = spider_data_base_data_pool.connection()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute('''SELECT
  source,
  sid,
  uid,
  mid,
  name,
  name_en,
  hotel_url
FROM hotel_unid
WHERE uid = %s;''', (uid,))
    s_sid_set = set()
    workload_content_data = []
    for line in cursor.fetchall():
        s_sid_set.add("('{}', '{}')".format(line['source'], line['sid']))
        workload_content_data.append(
            (
                upload_hotel_validation.get_content(source=line['source'], line=line),
                line['source'],
                line['sid']
            )
        )
    s_sid_str = ','.join(s_sid_set)
    cursor.close()
    conn.close()

    # update hotel content
    update_unid_content(data=workload_content_data)

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
            j_data = json.loads(line['info'])

            if 'down_reason' in j_data:
                # 数据被手工过滤
                add_report("filter_with_down_reason", min_pixels, task_name, "filter_with_down_reason")
                continue
            if 'p_hash' not in j_data:
                continue
            else:
                p_hash = j_data['p_hash']

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

    if len(img_list) > 65534:
        total_length = 0
        final_img = []
        for each in img_list.split('|'):
            total_length += len(each) + 1
            if total_length > 65534:
                break
            final_img.append(each)
        img_list = '|'.join(final_img)

    update_img(uid, first_img, img_list, target_table)

    return uid, first_img, img_list


class HotelImgMergeSDK(BaseSDK):
    def _execute(self, **kwargs):
        res = _hotel_img_merge(self.task.kwargs['uid'], self.task.kwargs.get('min_pixels', '200000'),
                               self.task.task_name,
                               target_table=self.task.kwargs.get('target_table', 'hotel'))
        self.task.error_code = 0
        return res
