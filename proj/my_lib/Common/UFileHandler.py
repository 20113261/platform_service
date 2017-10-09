#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/30 下午3:16
# @Author  : Hou Rong
# @Site    : 
# @File    : UFileHandler.py
# @Software: PyCharm
from __future__ import absolute_import
import json
import zlib
import requests
import time
import datetime
import logging
import proj.my_lib.Common.Utils
from ucloud.ufile import putufile, downloadufile, postufile, deleteufile
from ucloud.compact import BytesIO
from proj.my_lib.logger import get_logger
from ucloud.ufile import config

u_logger = logging.getLogger("UCLOUD")
u_logger.setLevel(logging.ERROR)
logger = get_logger("ufile_uploader")

local_ip = proj.my_lib.Common.Utils.get_local_ip()
if local_ip.startswith('10.10'):
    config.set_default(uploadsuffix='.ufile.cn-north-03.ucloud.cn')
    config.set_default(downloadsuffix='.ufile.cn-north-03.ucloud.cn')
elif local_ip.startswith('10.19'):
    config.set_default(uploadsuffix='.ufile.cn-north-04.ucloud.cn')
    config.set_default(downloadsuffix='.ufile.cn-north-04.ucloud.cn')
else:
    logger.debug("[no ucloud machine][use public ip]")
config.set_default(connection_timeout=60)

public_key = 'vCuKhG6UcHvB1UswK/q5zjMMHxt7PjKIu3/6q1JtxiZHtAuv'
private_key = 'fdfbdf9cb0ebfeed522f664efc44f752694b15f6'
put_handler = putufile.PutUFile(public_key, private_key)
bucket_name = "verify-case"


class FileInfo(object):
    st_mtime = 0.0
    content_type = ''


def has_file(key):
    # download_handler = downloadufile.DownloadUFile(public_key=public_key, private_key=private_key)
    # url = download_handler.private_download_url(bucket_name, key)
    # return url
    return get_ufile_and_info(key)


def delete_ufile(key):
    start = time.time()
    status = -1
    retry_times = 3
    while status != 200 and retry_times >= 0:
        retry_times -= 1
        try:
            delete_handler = deleteufile.DeleteUFile(public_key=public_key, private_key=private_key)
            ret, resp = delete_handler.deletefile(bucket_name, key)
            status = resp.status_code
        except Exception as exc:
            logger.exception(msg="[delete file error]", exc_info=exc)
            status = -1
    if status == 200:
        logger.debug("[Succeed][delete file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                        time.time() - start))
        return True
    else:
        logger.debug("[Failed][delete file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                       time.time() - start))
        return False


def get_ufile_and_info(key):
    start = time.time()
    status = -1
    retry_times = 3
    download_handler = downloadufile.DownloadUFile(public_key=public_key, private_key=private_key)
    url = download_handler.private_download_url(bucket_name, key)
    if not url:
        return None
    while status != 200 and retry_times >= 0:
        retry_times -= 1
        try:
            resp = requests.get(url)
            status = resp.status_code
        except Exception as exc:
            logger.exception(msg="[download file error]", exc_info=exc)
            status = -1
    if status == 200:
        logger.debug("[Succeed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                          time.time() - start))
        file_info = FileInfo()
        d_time = datetime.datetime.strptime(resp.headers['Last-Modified'], "%a, %d %b %Y %X GMT")
        file_info.st_mtime = time.mktime(d_time.timetuple())
        file_info.content_type = resp.headers['Content-Type']
        return resp.content, file_info
    else:
        logger.debug("[Failed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                         time.time() - start))
        return None


def upload_stream(key, data):
    start = time.time()
    status = -1
    retry_times = 3
    while status != 200 and retry_times >= 0:
        retry_times -= 1
        try:
            upload_handler = putufile.PutUFile(public_key=public_key, private_key=private_key)
            ret, resp = upload_handler.putstream(bucket_name, key, data)
            status = resp.status_code
        except Exception as exc:
            logger.exception(msg="[upload file error]", exc_info=exc)
            status = -1
    if status == 200:
        logger.debug("[Succeed][upload file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                        time.time() - start))
        return True
    else:
        logger.debug("[Failed][upload file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, key,
                                                                                       time.time() - start))
        return False


if __name__ == '__main__':
    # print(upload_stream('test', json.dumps({'status': 'OK', 'data': 'Hello World', 'test': '中文测试'})))
    # print(has_file('service_platform_cdfdb55def0b654eadba37812bfc66bd'))
    pass
    # print(delete_ufile('test'))
    # print(get_ufile('test'))
    # print(get_file_info('test'))
