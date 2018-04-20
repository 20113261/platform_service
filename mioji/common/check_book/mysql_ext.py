#!/usr/bin/env python
# encoding:utf-8

try:
    import MySQLdb
except:
    import pymysql
    pymysql.install_as_MySQLdb()
    import MySQLdb
import time


class MySQLExt(object):
    """
    docstring for MySQLExt
    """

    def __init__(self, *args, **kwargs):
        super(MySQLExt, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self._connect()

    def _connect(self):
        self.db_client = MySQLdb.connect(*self.args, **self.kwargs)
        self.db_client.autocommit(True)
        self.db_cursor = self.db_client.cursor()

    def _re_connect(self):
        flag = 5
        while flag > 0:
            try:
                self.db_client.ping(True)
                break
            except Exception:
                time.sleep(flag)
                self._connect()
                flag -= 1

    def exec_sql(self, sql, data=[]):
        """
        直接执行 sql。 返回内容为 sql 语句的返回
        sql:
            string
        data:
            list or tuple. default is []
        """
        self.db_cursor.execute(sql, data)
        ret = self.db_cursor.fetchall()
        return ret

    def execmany_sql(self, sql, data=[]):
        """
        调用 execmany 单条 sql。执行多次。
        sql:
            string.
        data:
            list or tuple,default []
        """
        self.db_cursor.execmany(sql, data)
        ret = self.db_cursor.fetchall()
        return ret

    def close(self):
        try:
            self.db_cursor.close()
            self.db_client.close()
        except Exception as why:
            print why

if __name__ == "__main__":
    from conf.config import lv_pi_data_conf
    _mysql = MySQLExt(**lv_pi_data_conf)
    a = _mysql.exec_sql("SHOW TABLES")
    for i in a:
        print i
    _mysql.close()
