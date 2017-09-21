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
from os import path
from proj.my_lib.Common.Utils import get_md5
from proj.my_lib.logger import get_logger

logger = get_logger('RespStore')

cache_dir = path.abspath(path.join('/data/nfs/page_saver', 'resp_cache'))


def has_dir():
    return path.isdir(cache_dir)


def has_cache(md5):
    return path.exists(path.join(cache_dir, md5))


def delete_cache(md5):
    if not has_cache(md5):
        return None
    os.remove(path.join(cache_dir, md5))
    logger.info('delete cache md5: {}'.format(md5))


def put_by_md5(md5, resp):
    if not has_dir():
        os.makedirs(cache_dir)

    fo = open(path.join(cache_dir, md5), "wb")
    res = pickle.dumps((resp, time.time()))
    length1 = len(res)
    res = zlib.compress(res)
    length2 = len(res)
    logger.info("[cache zipped][len1: {}][len2: {}][ration: {}]".format(length1, length2, length2 / float(length1)))
    fo.write(res)
    fo.close()
    return md5


def get_by_md5(md5, expire_time=3600):
    if not has_dir():
        return
    if not has_cache(md5):
        return
    fo = open(cache_dir + '/' + md5, "r+")
    res = fo.read()
    length1 = len(res)
    fo.close()
    res = zlib.decompress(res)
    length2 = len(res)
    resp, save_time = pickle.loads(res)
    logger.info("[cache unzipped][len1: {}][len2: {}][ration: {}]".format(length1, length2, length1 / float(length2)))
    if time.time() - save_time < expire_time:
        logger.info('[ get cache ][md5: {}][expire: {}][ save_time: {}]'.format(md5, expire_time, save_time))
        return resp
    else:
        delete_cache(md5)
        logger.info('[ delete expired response cache {} ]'.format(md5))
        return None


def file_path(req):
    md5_name = get_md5(json.dumps(req, sort_keys=True))
    logger.info('md5', md5_name, 'req', req)
    return path.join(cache_dir, md5_name), md5_name


def get_by_req(req, expire_time=3600):
    file_path_str, md5 = file_path(req)
    if not has_cache(md5):
        return None
    return get_by_md5(md5, expire_time=expire_time)


if __name__ == '__main__':
    resp = get_by_md5('cdfdb55def0b654eadba37812bfc66bd')
    print(resp.text)
    print(resp.url)
