#!/usr/bin/env python
# encoding:utf-8

import MySQLdb
import time


class PicModel(object):
    """docstring for PicModel"""

    def __init__(self, *args, **kwargs):
        super(PicModel, self).__init__()
        self.args = args
        self.kwargs = kwargs
        self._connect()

    def _connect(self):
        self.db_client = MySQLdb.connect(*self.args, **self.kwargs)
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

    def insert_pic_many(self, table_name, field_list, data_list):
        """
        """
        fields_str = ",".join(["`%s`" % x for x in field_list])
        values_str = ",".join(["%s"] * len(field_list))
        sql = "INSERT INTO `{0}`({1}) VALUE({2})".format(table_name,
                                                         fields_str,
                                                         values_str)
        self._re_connect()
        self.db_cursor.executemany(sql, data_list)
        self.db_client.commit()
