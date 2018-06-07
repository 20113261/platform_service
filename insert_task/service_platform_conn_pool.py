#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/14 上午11:06
# @Author  : Hou Rong
# @Site    : 
# @File    : service_platform_conn_pool.py
# @Software: PyCharm
import pymysql
import pymysql.cursors
from DBUtils.PooledDB import PooledDB


def init_pool(host, user, password, database, max_connections=20):
    mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=max_connections,
                             host=host, port=3306, user=user, passwd=password,
                             db=database, charset='utf8mb4', blocking=True)
    return mysql_db_pool


service_platform_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='ServicePlatform'
)

service_platform_pool = init_pool(**service_platform_config)

db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='BaseDataFinal',
)

base_data_final_pool = init_pool(**db_config)

db_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.228.253',
    database='poi_merge',
)

poi_ori_pool = init_pool(**db_config)

base_data_config = dict(
    user='reader',
    password='miaoji1109',
    host='10.10.69.170',
    database='base_data',
)

base_data_pool = init_pool(max_connections=30, **base_data_config)
# base_data_str = 'mysql+pymysql://reader:miaoji1109@10.10.69.170/base_data?charset=utf8'
#
# db_config = dict(
#     user='root',
#     password='shizuo0907',
#     host='10.10.242.173',
#     database='data_process',
# )
#
# data_process_pool = init_pool(**db_config, max_connections=30)
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='Report',
# )
#
# report_pool = init_pool(**db_config, max_connections=30)
#
# db_config = dict(
#     user='reader',
#     password='miaoji1109',
#     host='10.10.94.198',
#     database='private_data',
# )
#
# private_data_test_pool = init_pool(**db_config, max_connections=30)

source_info_config = dict(
    user='mioji_admin',
    password='mioji1109',
    host='10.10.230.206',
    database='source_info',
)

source_info_pool = init_pool(max_connections=30, **source_info_config)
# source_info_str = 'mysql+pymysql://mioji_admin:mioji1109@10.10.230.206/source_info?charset=utf8'
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.230.206',
#     database='verify_info',
# )
#
# verify_info_pool = init_pool(**db_config, max_connections=30)
#
# # spider db devdb pool
# db_config = dict(
#     user='writer',
#     password='miaoji1109',
#     host='10.10.154.38',
#     database='devdb'
# )
# spider_db_devdb_pool = init_pool(**db_config)
#
# # task db spider_db pool
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.238.148',
#     database='spider_db'
# )
#
# task_db_spider_db_pool = init_pool(**db_config)
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='poi'
# )
#
# poi_face_detect_pool = init_pool(**db_config)
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='base_data'
# )
#
# spider_data_base_data_pool = init_pool(**db_config)
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='poi_merge_base_data_test'
# )
#
# poi_merge_base_data_test_pool = init_pool(**db_config)
#
# db_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='poi_merge_data_process'
# )
#
# poi_merge_data_process_pool = init_pool(**db_config)
#
# hotel_api_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='hotel_api'
# )
#
# hotel_api_pool = init_pool(**hotel_api_config)
#
# spider_data_tmp_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     database='tmp'
# )
#
# spider_data_tmp_pool = init_pool(**spider_data_tmp_config)
#
# spider_data_tmp_str = "mysql+pymysql://mioji_admin:mioji1109@10.10.228.253/tmp?charset=utf8"
#
# spider_base_tmp_wanle_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.230.206',
#     database='tmp_wanle'
# )
# spider_base_tmp_wanle_pool = init_pool(**spider_base_tmp_wanle_config)
# spider_base_tmp_wanle_str = "mysql+pymysql://mioji_admin:mioji1109@10.10.230.206/tmp_wanle?charset=utf8"
#
# spider_base_tmp_wanle_test_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.230.206',
#     database='tmp_wanle_test'
# )
# spider_base_tmp_wanle_test_pool = init_pool(**spider_base_tmp_wanle_config)
# spider_base_tmp_wanle_test_str = "mysql+pymysql://mioji_admin:mioji1109@10.10.230.206/tmp_wanle_test?charset=utf8"
#
# spider_task_tmp_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.238.148',
#     database='tmp'
# )
#
# spider_task_tmp_pool = init_pool(**spider_task_tmp_config)
#
# verify_info_new_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.19.153.98',
#     # database='verify_info',
#     database='ServicePlatform'
# )
#
# verify_info_new_pool = init_pool(**verify_info_new_config, max_connections=30)
#
# new_station_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.10.228.253',
#     # database='verify_info',
#     database='NewStation'
# )
#
# new_station_pool = init_pool(**new_station_config, max_connections=30)
#
# new_service_platform_config = dict(
#     user='mioji_admin',
#     password='mioji1109',
#     host='10.19.153.98',
#     # database='verify_info',
#     database='ServicePlatform'
# )
#
# new_service_platform_pool = init_pool(**new_service_platform_config, max_connections=30)
#
# poi_ori_new_config = dict(
#     user='reader',
#     password='miaoji1109',
#     host='10.10.169.10',
#     database='poi_merge',
# )
#
# poi_ori_new_pool = init_pool(**poi_ori_new_config)
#
#
# def fetchall(conn_pool, sql, is_dict=False):
#     conn = conn_pool.connection()
#     if is_dict:
#         cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
#     else:
#         cursor = conn.cursor()
#     cursor.execute('''SET SESSION sql_mode = (SELECT REPLACE(@@sql_mode, 'ONLY_FULL_GROUP_BY', ''));''')
#     cursor.execute(sql)
#     for line in cursor.fetchall():
#         yield line
#     cursor.close()
#     conn.close()
