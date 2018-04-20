#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/25 下午1:44
# @Author  : Hou Rong
# @Site    :
# @File    : delete_already_scanned_file.py
# @Software: PyCharm
import os
import logging
from logger import get_logger
from data_source import MysqlSource

devdb_config = {
    'user': 'mioji_admin',
    'password': 'mioji1109',
    'host': '10.10.228.253',
    'db': 'poi',
    'charset': 'utf8'
}

offset = 0
logger = get_logger("delete_scanned_file")
logger.setLevel(logging.INFO)


def delete_file(f_path):
    real_path = f_path.replace('/search/image/formatted_image', '/data/image/formatted_image/')
    if os.path.exists(real_path):
        logger.debug('[delete file][path: {}]'.format(real_path))
        os.remove(real_path)
    else:
        logger.debug('[file has been deleted or not exist][path: {}]'.format(real_path))


def _delete_already_scanned_file():
    global offset
    _count = 0
    sql = '''SELECT pic_name
FROM PoiPictureInformation
WHERE is_scaned = 1
LIMIT {}, 999999999999;'''.format(offset)
    for line in MysqlSource(devdb_config, table_or_query=sql, size=10000, is_table=False, is_dict_cursor=True):
        f_path = line['pic_name']
        try:
            delete_file(f_path=f_path)
        except Exception as exc:
            logger.exception(msg="[delete file exception][f_path: {}]".format(f_path), exc_info=exc)

        if offset % 10000 == 0:
            logger.info("[delete file count][offset: {}]".format(offset))
        _count += 1
        offset += 1


def delete_already_scanned_file():
    global offset
    max_retry_times = 10000
    while max_retry_times:
        max_retry_times -= 1
        try:
            _delete_already_scanned_file()
            break
        except Exception as exc:
            logger.exception(msg="[delete already scanned file error]", exc_info=exc)


if __name__ == '__main__':
    delete_already_scanned_file()
