#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午6:26
# @Author  : Hou Rong
# @Site    : 
# @File    : upload_case_file.py
# @Software: PyCharm
import os
import hashlib
from logging import getLogger
from mioji.common.ufile_handler import upload_file

public_key = 'vCuKhG6UcHvB1UswK/q5zjMMHxt7PjKIu3/6q1JtxiZHtAuv'
private_key = 'fdfbdf9cb0ebfeed522f664efc44f752694b15f6'

logger = getLogger('upload_file_logger')


def get_file_md5(f_name):
    hash_md5 = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


if __name__ == '__main__':
    logger.debug('Upload All Cases')
    for f_name in os.listdir('./cases'):
        f_absolute_path = os.path.join('./cases', f_name)
        f_key = get_file_md5(f_absolute_path)
        logger.debug("[Start] uploading file_name: {0}, file_key: {1}".format(f_name, f_key))
        try:
            if upload_file(f_key, {'data': open(f_absolute_path).read()}):
                logger.debug("[Succeed] uploading file_name: {0}, file_key: {1}".format(f_name, f_key))
            else:
                logger.debug("[Failed] uploading file_name: {0}, file_key: {1}".format(f_name, f_key))
        except Exception as e:
            logger.debug("[Error] uploading file_name: {0}, file_key: {1}".format(f_name, f_key))
            logger.exception(msg="[ErrorInfo]", exc_info=e)
