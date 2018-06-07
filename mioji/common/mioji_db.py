#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''
from common.conf_manage import ConfigHelper
from db_helper import DbHelper


conf = ConfigHelper()

online_db = DbHelper(host=conf.mysql_host, user=conf.mysql_user, password=conf.mysql_passwd, db='onlinedb')

# 董凯提供城市数据

new_spider_db = DbHelper(host=conf.spiderbase_host,
                         user=conf.spiderbase_user,
                         password=conf.spiderbase_passwd,
                         db=conf.spiderbase_db)    # 迁移 到 spiderBase

spider_db = online_db
#spider_devdb = DbHelper(host=conf.mysql_host, user=conf.mysql_user, password=conf.mysql_passwd, db='devdb')
# spider_workload_db = DbHelper(host='10.10.154.38', user='reader', password='miaoji1109', db='workload')   # 删除


if __name__ == '__main__':
    with new_spider_db as connect:
        print 'ss'
