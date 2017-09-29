#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/29 下午4:49
# @Author  : Hou Rong
# @Site    : 
# @File    : ks_upload_file_stream.py
# @Software: PyCharm
from __future__ import print_function
import time
from proj.my_lib.logger import get_logger
from ks3.connection import Connection

logger = get_logger('ks_uploader')

ak = 'K0fJOlnF++ck5LznhuNZ'
sk = 'o4D5wjs6r02dxLDLyLbTTUenTvpmKgrBItra6qgb'

connection = Connection(ak, sk, host='kss.ksyun.com')


def upload_ks_file_stream(bucket_name, upload_key, file_obj, content_type='image/jpeg'):
    start = time.time()
    bucket = connection.get_bucket(bucket_name)
    key = bucket.new_key(upload_key)

    status = -1
    retry_times = 3
    headers = {
        'Content-Type': content_type,
        'x-application-context': 'application'
    }
    while status != 200 and retry_times >= 0:
        retry_times -= 1
        try:
            res = key.set_contents_from_file(file_obj, policy='public-read-write', headers=headers)
            status = res.status
        except Exception as exc:
            logger.exception(msg="[upload file error]", exc_info=exc)
            status = -1
    if status == 200:
        logger.debug("[Succeed][upload file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, upload_key,
                                                                                        time.time() - start))
        return True
    else:
        logger.debug("[Failed][upload file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, upload_key,
                                                                                       time.time() - start))
        return False


if __name__ == '__main__':
    f = open('/tmp/c0b9378743defc0c81ff308b112542a0.jpg', 'rb')
    # import StringIO

    # 'Content-Type': 'application/octet-stream'
    # s = StringIO.StringIO(f.read())
    upload_ks_file_stream('mioji-attr', 'hello_world', f)
