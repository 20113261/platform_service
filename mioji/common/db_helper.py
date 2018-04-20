#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年10月27日

@author: dujun
'''
from logger import logger

import MySQLdb

debug = True


class DbHelper(object):
    '''
    mysql database open helper
    '''

    def __init__(self, host, user, password, db, port=3306, charset="utf8", pool=None):
        '''
        Constructor
        '''
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__charset = charset
        self.__db = db
        self.__connect = None
        self.__pool = pool

    def open(self):
        connect = MySQLdb.connect(host=self.__host, port=self.__port,
                                  user=self.__user, passwd=self.__password,
                                  db=self.__db, charset="utf8")
        self.__connect = connect
        return self.__connect

    def close(self):
        if self.__connect:
            self.__connect.close()

    def __enter__(self):
        '''
        '''
        connect = MySQLdb.connect(host=self.__host, port=self.__port,
                                  user=self.__user, passwd=self.__password,
                                  db=self.__db, charset="utf8")
        if self.__pool:
            # 后续可使用连接池管理链接进行优化
            # like DBUtils
            pass

        self.__connect = connect
        if debug:
            logger.debug('---db_helper connect %s', self.__db)

        return self.__connect

    def __exit__(self, exc_type, exc_value, exc_traceback):

        if self.__connect:
            self.__connect.close()
            if debug:
                logger.debug('---db_helper %s connect release %s', exc_value, self.__db)

        # 如果块代码执行异常，抛出由上层处理
        return False


def from_config(config, config_section):
    host = config.get(config_section, 'host')
    port = int(config.get(config_section, 'port').strip())
    user = config.get(config_section, 'user').strip()
    password = config.get(config_section, 'passwd').strip()
    db = config.get(config_section, 'database').strip()
    return DbHelper(host=host, port=port, user=user, password=password, db=db)


if __name__ == '__main__':

    a = [1, 3]
    a += [3, 45]

    print 1 not in a

    TABLE = 'chat_statistic'
    MYSQL_HOST = '10.10.22.126'
    MYSQL_PORT = 3306
    MYSQL_USER = 'writer'
    MYSQL_PWD = 'miaoji1109'
    MYSQL_DB = 'statistic_chat'

    db_test = DbHelper(host=MYSQL_HOST, port=MYSQL_PORT,
                       user=MYSQL_USER, password=MYSQL_PWD,
                       db=MYSQL_DB, charset="utf8")

    # 一次db open
    with db_test as connect:
        # 一次session
        with connect as cursor:
            sql = 'select count(*) from chat_statistic'
            cursor.execute(sql)
            rs = cursor.fetchall()
            print rs

        with connect as cursor:
            cursor.execute(sql)
            rs = cursor.fetchall()
            print rs

        # test error
        try:
            with connect as cursor:
                update_sql = 'INSERT INTO ' + TABLE + '''(sjid, date, c_user,
                     s_all, s_text, s_image, s_widget, s_order,
                     r_all, r_text, r_image, r_widget, r_order, r_server)
                     VALUES (%s,%s,%s,
                     %s,%s,%s,%s,%s,
                     %s,%s,%s,%s,%s,%s) 
                     ON DUPLICATE KEY UPDATE sjid=VALUES(sjid), date=VALUES(date)'''
                rows = []
                cursor.executemany(update_sql, rows)
                new_row = ()
                cursor.execute(update_sql, new_row)
        except:
            logger.debug('insert data error')

    print 'done'
