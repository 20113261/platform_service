#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/21 上午11:36
# @Author  : Hou Rong
# @Site    : 
# @File    : RespStore.py
# @Software: PyCharm
import os
import zlib
import time
import json
import pickle
import datetime
import proj.my_lib.Common.Utils
import proj.my_lib.Common.UFileHandler
from os import path
from proj.my_lib.logger import get_logger

# from proj.my_lib.Common.UFileHandler import upload_stream, get_ufile_and_info, delete_ufile, has_file

logger = get_logger('RespStore')

cache_dir = path.abspath(path.join('/data/nfs/page_saver', 'resp_cache'))

STORE_TYPE = 'ufile'


def has_dir():
    return path.isdir(cache_dir)


def has_cache(md5):
    if STORE_TYPE == 'file':
        return path.exists(path.join(cache_dir, md5))
    elif STORE_TYPE == 'ufile':
        return proj.my_lib.Common.UFileHandler.has_file("service_platform_{}".format(md5))
    else:
        raise TypeError('Unknown Type {}'.format(STORE_TYPE))


def delete_cache(md5):
    if STORE_TYPE == 'file':
        if not has_cache(md5):
            return None
        os.remove(path.join(cache_dir, md5))
        logger.info('delete cache md5: {0}'.format(md5))
    elif STORE_TYPE == 'ufile':
        return proj.my_lib.Common.UFileHandler.delete_ufile("service_platform_{}".format(md5))
    else:
        raise TypeError('Unknown Type {}'.format(STORE_TYPE))


def put_by_md5(md5, resp):
    if STORE_TYPE == 'file':
        if not has_dir():
            os.makedirs(cache_dir)

        fo = open(path.join(cache_dir, md5), "wb")
        res = pickle.dumps(resp)
        length1 = len(res)
        res = zlib.compress(res)
        length2 = len(res)
        logger.info(
            "[cache zipped][len1: {0}][len2: {1}][ration: {2}]".format(length1, length2, length2 / float(length1)))
        fo.write(res)
        fo.close()
        return md5
    elif STORE_TYPE == 'ufile':
        res = pickle.dumps(resp)
        length1 = len(res)
        res = zlib.compress(res)
        length2 = len(res)
        logger.info(
            "[cache zipped][len1: {0}][len2: {1}][ration: {2}]".format(length1, length2, length2 / float(length1)))
        proj.my_lib.Common.UFileHandler.upload_stream("service_platform_{}".format(md5), data=res)
        return md5
    else:
        raise TypeError("Unknown Type {}".format(STORE_TYPE))


def get_by_md5(md5, expire_time=3600):
    if STORE_TYPE == 'file':
        if not has_dir():
            return
        if not has_cache(md5):
            return
        fo = open(cache_dir + '/' + md5, "r+")
        res = fo.read()
        length1 = len(res)
        fo.close()
        file_info = os.stat(cache_dir + '/' + md5)
        res = zlib.decompress(res)
        length2 = len(res)
        resp = pickle.loads(res)
        logger.info(
            "[cache unzipped][len1: {0}][len2: {1}][ration: {2}]".format(length1, length2, length1 / float(length2)))
        if time.time() - file_info.st_mtime < expire_time:
            logger.info(
                '[ get cache ][md5: {0}][expire: {1}][ save_time: {2}]'.format(md5, expire_time, file_info.st_mtime))
            return resp
        else:
            delete_cache(md5)
            logger.info('[ delete expired response cache {0} ]'.format(md5))
            return None
    elif STORE_TYPE == 'ufile':
        if not has_cache(md5):
            return None
        returned = proj.my_lib.Common.UFileHandler.get_ufile_and_info("service_platform_{}".format(md5))
        if not returned:
            return None
        else:
            res, file_info = returned
        length1 = len(res)
        res = zlib.decompress(res)
        length2 = len(res)
        resp = pickle.loads(res)
        cache_date = datetime.datetime.fromtimestamp(
            int(file_info.st_mtime)
        ).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(
            "[cache unzipped][len1: {0}][len2: {1}][ration: {2}]".format(length1, length2, length1 / float(length2)))
        if time.time() - file_info.st_mtime < expire_time:
            logger.info(
                '[ get cache ][md5: {0}][expire: {1}][ save_time: {2}][ date: {3} ]'.format(md5, expire_time,
                                                                                            file_info.st_mtime,
                                                                                            cache_date))
            return resp
        else:
            logger.info('[ cache file has expired ][ cache {0} ][ date: {1} ]'.format(md5, cache_date))
            return None
    else:
        raise TypeError('Unknown Type {}'.format(STORE_TYPE))


def calculate_md5(req):
    md5_name = proj.my_lib.Common.Utils.get_md5(json.dumps(req, sort_keys=True))
    logger.info('[md5: {0}][req: {1}]'.format(md5_name, req))
    return md5_name


# def file_path(req):
#     md5_name = proj.my_lib.Common.Utils.get_md5(json.dumps(req, sort_keys=True))
#     logger.info('[md5: {0}][req: {1}]'.format(md5_name, req))
#     return path.join(cache_dir, md5_name), md5_name


def get_by_req(req, expire_time=3600):
    md5 = calculate_md5(req)
    if not has_cache(md5):
        return None
    return get_by_md5(md5, expire_time=expire_time)


if __name__ == '__main__':
    resp = get_by_md5('cdfdb55def0b654eadba37812bfc66bd')
    print(resp.text)
    print(resp.url)
