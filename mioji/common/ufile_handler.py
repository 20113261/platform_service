#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Created on 2017年04月18日

@author: Hou Rong
"""

import json
import zlib
import requests
import logging
from ucloud.ufile import putufile, downloadufile, postufile, multipartuploadufile
from ucloud.compact import BytesIO
from pool import file_upload_pool
from func_log import func_time_logger

logger = logging.getLogger("UCLOUD")
logger.setLevel(logging.ERROR)
# public_key = 'vCuKhG6UcHvB1UswK/q5zjMMHxt7PjKIu3/6q1JtxiZHtAuv'
# private_key = 'fdfbdf9cb0ebfeed522f664efc44f752694b15f6'
public_key = 'M7jIsudUE4Nvn6zQGjNMWxReCrSpc8HcWdBztizB38qvbXkS'
private_key = '3fe4dbb2f16a86a8a58c6c9aac061d83c43ff468'

put_handler = putufile.PutUFile(public_key, private_key)
bucket = "verify-case"


def upload_file_post(key, file_name):
    post_handler = postufile.PostUFile(public_key, private_key)
    ret, resp = post_handler.postfile(bucket, key, file_name)
    assert resp.status_code == 200, '错误'


def upload_file(key, data):
    stream = BytesIO(zlib.compress(json.dumps(data)))
    ret, resp = put_handler.putstream(bucket, key, stream, mime_type='text/plain')
    if resp.status_code == 200:
        return True
    else:
        return False


def download_file(key):
    download_handler = downloadufile.DownloadUFile(public_key, private_key)
    download_url = download_handler.private_download_url(bucket, key)
    print download_url
    page = requests.get(download_url)
    return zlib.decompress(page.content)


def multi_part_upload_stream(key, data):
    file_upload_pool.apply_async(_multi_part_upload_stream, args=(key, data))
    return True


@func_time_logger
def _multi_part_upload_stream(key, data):
    handler = multipartuploadufile.MultipartUploadUFile(public_key, private_key)
    stream = BytesIO(zlib.compress(data))
    ret, resp = handler.uploadstream(bucket, key, stream)

    # 出问题重试 2 次
    retry_times = 2
    while resp.status_code != 200 and retry_times:
        retry_times -= 1
        ret, resp = handler.resumeuploadstream()
        if resp.status_code == 200:
            return True
    else:
        return False


if __name__ == '__main__':
    if multi_part_upload_stream('hello_world', json.dumps({'status': 'OK', 'data': 'Hello World', 'test': '中文测试'})):
       print 'OK'
    else:
       print 'Error'
    # file_names = ['4ef120ce68aa015cfd4b754435e80156', '28ac4f5b26340aac67ed46d857887e6e',
    #               '8ef6421c0b4f450f14fe214e60f7142d', '0875f5fd094ce074b03af6d8f8d37749',
    #               '3fa728fc4bef9aa9de0bdbffa31aa087', 'b9a0a995a06cc344da23b69c4dfb7fb9']
    #
    # for file_name in file_names:
    #     f = open('/Users/hourong/Downloads/abcdef/' + file_name, 'w')
    #     f.write(download_file(file_name))
    #     f.close()
