#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/31 下午7:34
# @Author  : Hou Rong
# @Site    : 
# @File    : img_hash.py
# @Software: PyCharm
import imagehash
from PIL import Image
from proj.my_lib.logger import get_logger, func_time_logger

logger = get_logger("img_hash")


@func_time_logger
def _img_p_hash(f_obj):
    f_obj.seek(0)
    try:
        img_obj = Image.open(f_obj)
    except Exception as exc:
        logger.exception(msg="[error img]", exc_info=exc)
        return None

    try:
        _hash = imagehash.phash(img_obj)
    except Exception as exc:
        logger.exception(msg="[could not calculate phash]", exc_info=exc)
        return None
    f_obj.seek(0)
    return _hash


def img_p_hash(f_obj):
    _retry_times = 4
    while _retry_times:
        _retry_times -= 1
        _res = _img_p_hash(f_obj)
        if _res:
            return _res
    return None


if __name__ == '__main__':
    f = open('/tmp/1/035211ab53d76b051376f9292ca9623d.jpg')
    print(img_p_hash(f))
    print(img_p_hash(f))
    print(img_p_hash(f))
    print(img_p_hash(f))
    print(img_p_hash(f))

    f = open('/tmp/1/b8c88852a915cf32e1eeed20ec7d3cc7.jpg')
    print(img_p_hash(f))
