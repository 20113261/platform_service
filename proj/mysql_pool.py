#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:40
# @Author  : Hou Rong
# @Site    : 
# @File    : mysql_pool.py
# @Software: PyCharm
import pymysql
from DBUtils.PooledDB import PooledDB


def init_pool(host, user, password, db, max_connections=10):
    mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=max_connections,
                             host=host, port=3306, user=user, passwd=password,
                             db=db, charset='utf8', use_unicode=False, blocking=True)
    return mysql_db_pool


db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='ServicePlatform'
)
service_platform_pool = init_pool(**db_config)

# mysql connect pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
base_data_pool = init_pool(**db_config)
