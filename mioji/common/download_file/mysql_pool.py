#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:40
# @Author  : Hou Rong
# @Site    : 
# @File    : mysql_pool.py
# @Software: PyCharm
import pymysql
from DBUtils.PooledDB import PooledDB


def init_pool(host, user, password, database, max_connections=5):
    mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=max_connections,
                             host=host, port=3306, user=user, passwd=password,
                             db=database, charset='utf8', use_unicode=False, blocking=True)
    return mysql_db_pool


db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='ServicePlatform'
)
service_platform_pool = init_pool(**db_config)

db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='BaseDataFinal'
)
base_data_final_pool = init_pool(**db_config)

# mysql connect pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
base_data_pool = init_pool(**db_config)

# spider db devdb pool
# db_config = dict(
#     user='writer',
#     password='miaoji1109',
#     host='10.10.154.38',
#     database='devdb'
# )
# spider_db_devdb_pool = init_pool(**db_config)

# spider data poi pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='poi'
)
spider_data_poi_pool = init_pool(**db_config)

# test base data pool
db_config = dict(
    user='reader',
    password='miaoji1109',
    host='10.10.69.170',
    database='base_data'
)
base_data_test_pool = init_pool(**db_config)

# spider data base data
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
spider_data_base_data_pool = init_pool(**db_config)
