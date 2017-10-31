#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/29 下午4:49
# @Author  : Hou Rong
# @Site    : 
# @File    : ks_upload_file_stream.py
# @Software: PyCharm
# from __future__ import print_function
import time
import os

from toolbox.Hash import file_hash

from proj.my_lib.hotel_img_func import get_stream_md5
from proj.my_lib.logger import get_logger, func_time_logger
from ks3.connection import Connection

logger = get_logger('ks_uploader')

ak = 'K0fJOlnF++ck5LznhuNZ'
sk = 'o4D5wjs6r02dxLDLyLbTTUenTvpmKgrBItra6qgb'

connection = Connection(ak, sk, host='kss.ksyun.com')


@func_time_logger
def upload_ks_file_stream(bucket_name, upload_key, file_obj, content_type='image/jpeg', hash_check=None):
    start = time.time()
    bucket = connection.get_bucket(bucket_name)
    key = bucket.new_key(upload_key)

    status = -1
    retry_times = 5
    headers = {
        'Content-Type': content_type,
        'x-application-context': 'application'
    }
    while status != 200 and retry_times >= 0:
        # 恢复 file seek
        file_obj.seek(0)
        retry_times -= 1
        try:
            res = key.set_contents_from_file(file_obj, policy='public-read-write', headers=headers)
            uploaded_key = bucket.get_key(upload_key)
            if hash_check is not None:
                if str(uploaded_key.etag.replace('"', '')) == str(hash_check):
                    status = res.status
                    logger.debug("[hash check ok][etag: {}][hash: {}]".format(uploaded_key.etag, hash_check))
                else:
                    status = -1
                    logger.debug("[hash check error][etag: {}][hash: {}]".format(uploaded_key.etag, hash_check))
            else:
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


@func_time_logger
def download(bucket_name, file_name, file_path):
    start = time.time()
    bucket = connection.get_bucket(bucket_name)
    obj = bucket.get_key(file_name)

    status = -1
    retry_times = 3
    while status == -1 and retry_times >= 0:
        retry_times -= 1
        try:
            obj.get_contents_to_filename(os.path.join(file_path, file_name))
            status = 0
        except Exception as exc:
            logger.exception(msg="[download file error]", exc_info=exc)
            status = -1
    if status == 0:
        logger.debug("[Succeed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, file_name,
                                                                                          time.time() - start))
        return True
    else:
        logger.debug("[Failed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, file_name,
                                                                                         time.time() - start))
        return False


if __name__ == '__main__':
    f = open('/tmp/1b78877b728d4bd6e8445d2d1102044c.png', 'rb')
    md5 = get_stream_md5(f)
    print(md5)
    f.seek(0)
    # f = open('/tmp/c0b9378743defc0c81ff308b112542a0.jpg', 'rb')
    # f = StringIO(content)
    # f_hash = file_hash(f)
    # print(f_hash)
    # import StringIO

    # 'Content-Type': 'application/octet-stream'
    # s = StringIO.StringIO(f.read())
    upload_ks_file_stream('mioji-wanle', 'huantaoyou/hello_world', f, hash_check=md5)
