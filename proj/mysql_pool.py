#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:40
# @Author  : Hou Rong
# @Site    : 
# @File    : mysql_pool.py
# @Software: PyCharm
import mysql.connector

db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='ServicePlatform'
)
service_platform_conn = mysql.connector.connect(pool_name="service-platform-pool",
                                                pool_size=15,
                                                **db_config)

# mysql connect pool
db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='base_data'
)
base_data_conn = mysql.connector.connect(pool_name="base-data-pool",
                                         pool_size=15,
                                         **db_config)
