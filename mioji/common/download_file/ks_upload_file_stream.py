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
import hashlib
# from toolbox.Hash import file_hash
from logger import get_logger, func_time_logger
from ks3.connection import Connection

logger = get_logger('ks_uploader')

ak = 'K0fJOlnF++ck5LznhuNZ'
sk = 'o4D5wjs6r02dxLDLyLbTTUenTvpmKgrBItra6qgb'

connection = Connection(ak, sk, host='kss.ksyun.com')


def get_stream_md5(stream):
    stream.seek(0)
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: stream.read(4096), b""):
        hash_md5.update(chunk)
    stream.seek(0)
    return hash_md5.hexdigest()


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
def download(bucket_name, file_name, file_path, new_file_name=''):
    start = time.time()
    bucket = connection.get_bucket(bucket_name)
    obj = bucket.get_key(file_name)
    if new_file_name == '':
        new_file_name = file_name

    status = -1
    retry_times = 3
    while status == -1 and retry_times >= 0:
        retry_times -= 1
        try:
            obj.get_contents_to_filename(os.path.join(file_path, new_file_name))
            status = 0
        except Exception as exc:
            logger.exception(msg="[download file error]", exc_info=exc)
            status = -1
    if status == 0:
        logger.debug(
            "[Succeed][download file][bucket: {0}][key: {1}][new_file_name: {2}][takes: {3}]".format(bucket_name,
                                                                                                     file_name,
                                                                                                     new_file_name,
                                                                                                     time.time() - start))
        return True
    else:
        logger.debug(
            "[Failed][download file][bucket: {0}][key: {1}][new_file_name: {2}][takes: {3}]".format(bucket_name,
                                                                                                    file_name,
                                                                                                    new_file_name,
                                                                                                    time.time() - start))
        return False


@func_time_logger
def download_content(bucket_name, file_name, need_md5=False):
    start = time.time()
    bucket = connection.get_bucket(bucket_name)
    obj = bucket.get_key(file_name)

    status = -1
    retry_times = 3
    content = None
    while status == -1 and retry_times >= 0:
        retry_times -= 1
        try:
            content = obj.get_contents_as_string()
            if need_md5:
                md5 = str(obj.etag.replace('"', ''))
            status = 0
        except Exception as exc:
            logger.exception(msg="[download file error]", exc_info=exc)
            status = -1
    if status == 0:
        logger.debug("[Succeed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, file_name,
                                                                                          time.time() - start))
        if need_md5:
            return content, md5
        else:
            return content
    else:
        logger.debug("[Failed][download file][bucket: {0}][key: {1}][takes: {2}]".format(bucket_name, file_name,
                                                                                         time.time() - start))
        if need_md5:
            return None, None
        else:
            return None


@func_time_logger
def check_key(bucket_name, file_name):
    bucket = connection.get_bucket(bucket_name)
    obj = bucket.get_key(file_name)

    if not obj:
        pass
    print("Hello World")


# def test_img_p_hash_download():
#     from proj.my_lib.Common.img_hash import img_p_hash
#     from StringIO import StringIO
#
#     content = download_stream('mioji-hotel', 'a24af36faf3e2f67a0816e8793c89973.jpg')
#     print(img_p_hash(StringIO(content)))


if __name__ == '__main__':
    check_key('mioji-shop', '24274ec3d9216ed7dce0f6e70691a44b.jpg')
    check_key('mioji-shop', '451c4fc0f9653a02596600e5b2d4eaa1')
    # f = open('/tmp/1b78877b728d4bd6e8445d2d1102044c.png', 'rb')
    # md5 = get_stream_md5(f)
    # print(md5)
    # f.seek(0)
    # f = open('/tmp/c0b9378743defc0c81ff308b112542a0.jpg', 'rb')
    # f = StringIO(content)
    # f_hash = file_hash(f)
    # print(f_hash)
    # import StringIO

    # 'Content-Type': 'application/octet-stream'
    # s = StringIO.StringIO(f.read())
    # upload_ks_file_stream('mioji-wanle', 'huantaoyou/hello_world', f, hash_check=md5)
    # test_img_p_hash_download()
