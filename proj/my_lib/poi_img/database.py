#!/usr/bin/env python
# coding=UTF-8
"""
    Created on 2014-03-08
    @author: devin
    @desc:
        数据访问
"""
import sys

import MySQLdb
from MySQLdb.cursors import DictCursor
from logger import logger

reload(sys)
sys.setdefaultencoding('utf-8')

# MySQL 连接信息
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'hourong'
MYSQL_PWD = 'hourong'
MYSQL_DB = 'chat_poi'


def GetConnection():
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PWD, \
                           db=MYSQL_DB, charset="utf8")
    return conn


def Connect():
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PWD, \
                           db=MYSQL_DB, charset="utf8")

    return conn


def ExecuteSQL(sql, args=None):
    '''
        执行SQL语句, 正常执行返回影响的行数，出错返回Flase
    '''
    ret = 0
    try:
        conn = GetConnection()
        cur = conn.cursor()

        ret = cur.execute(sql, args)
        conn.commit()
        cur.close()
        conn.close()
    except MySQLdb.Error, e:
        logger.error("ExecuteSQL error: %s" % str(e))
        return False
    '''
    finally:
        cur.close()
        conn.close()
    '''

    return ret


def ExecuteSQLs(sql, args=None):
    '''
        执行多条SQL语句, 正常执行返回影响的行数，出错返回Flase
    '''
    ret = 0
    try:
        conn = GetConnection()
        cur = conn.cursor()

        ret = cur.executemany(sql, args)
        conn.commit()
        cur.close()
        cur.close()
    except MySQLdb.Error, e:
        logger.error("ExecuteSQLs error: %s" % str(e))
        return False

    return ret


def QueryBySQL(sql, args=None, size=None):
    '''
        通过sql查询数据库，正常返回查询结果，否则返回None
    '''
    results = []
    try:
        conn = GetConnection()
        cur = conn.cursor(cursorclass=DictCursor)

        cur.execute(sql, args)
        rs = cur.fetchall()
        for row in rs:
            results.append(row)
    except MySQLdb.Error, e:
        logger.error("QueryBySQL error: %s" % str(e))
        return None
    finally:
        cur.close()
        # conn.close()

    return results
