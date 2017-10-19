#!/usr/bin/env python
# -*- coding: utf-8 -*-

from proj.my_lib.models.column import Column, String, Integer, Datetime, Text, Map, JSON
from proj.my_lib.Common.KeyMatch import key_is_legal
from proj.my_lib.Common.Utils import Coordinate

import datetime
import json

class BaseModel(object):
    __sql = ''
    __columns_dict = {}
    def __new__(cls, *args, **kwargs):
        for item in dir(cls):
            if item.startswith('_BaseModel__') or item.startswith('__'): continue
            column = getattr(cls, item, None)
            if isinstance(column, Column):
                cls._BaseModel__columns_dict[item] = column
                setattr(cls, item, column._default)

        return object.__new__(cls, *args, **kwargs)

    def __setattr__(self, key, value):
        if key == '_BaseModel__columns_dict':return
        column = self._BaseModel__columns_dict.get(key, None)
        if not column:
            raise KeyError(str(key))
        if not column.judgement_type(value):
            raise TypeError('%s must be %s' % (value, column._typ))
        if not key_is_legal(value):
            self.__dict__[key] = column._default

        self.__dict__[key] = value

    # def __delattr__(self, key):
    #     column = getattr(self, key, None)
    #     if not column:
    #         raise KeyError(str(key))
    #     column._value = None
    #     del self.__instance_dict[key]

    def generation_sql(self):
        self._completion_obj()
        attribute = self.__dict__
        keys = attribute.keys()
        sql = self._keys_to_sql(keys)
        print sql
        return sql

    def _completion_obj(self):
        keys = []
        for item in dir(self):
            if item.startswith('__'):continue
            column = self._BaseModel__columns_dict.get(item, None)
            if column is None:continue
            if isinstance(column, Column):
                keys.append(item)
        for key in keys:
            if self.__dict__.has_key(key):
                continue
            column = self._BaseModel__columns_dict.get(key, None)
            self.__dict__[key] = column._default

    def values(self, backdict=False):
        self._completion_obj()
        if backdict:
            return self.__dict__
        return tuple(self.__dict__.values())

    # def load_sql(self):
    #     for item in dir(self):
    #         if item.startswith('__') or item.startswith('_Base__'):continue
    #         column = getattr(self, item, None)
    #         if column is None:continue
    #         if isinstance(column, Column):
    #             setattr(self, item, column._default)
    #
    #     self.__sql = self.generation_sql()

    def _keys_to_sql(self, keys):
        sql = "replace into {table_name} "
        params = ""
        values = ""
        for key in keys:
            params += key + ", "
            column = self._BaseModel__columns_dict.get(key, None)
            if isinstance(column._typ, Integer):
                values += "%s, "
            else:
                values += "%s, "
        return sql + "(" + params[:-2] + ") values (" + values[:-2] + ")"

    def __str__(self):
        return str(self.__dict__)

class Hotel_model(BaseModel):
    hotel_name = Column(String(512), default='NULL')
    hotel_name_en = Column(String(512), default='NULL')
    source = Column(String(64), default='NULL')
    source_id = Column(String(128), default='NULL')
    brand_name = Column(String(512), default='NULL')
    map_info = Column(Map(512), default='NULL')
    address = Column(String(512), default='NULL')
    city = Column(String(512), default='NULL')
    country = Column(String(512), default='NULL')
    city_id = Column(String(11), default='NULL')
    postal_code = Column(String(512), default='NULL')
    star = Column(Integer(20), default='-1.0')
    grade = Column(Integer(256), default='NULL')
    review_num = Column(String(20), default='NULL')
    has_wifi = Column(String(20), default='NULL')
    is_wifi_free = Column(String(20), default='NULL')
    has_parking = Column(String(20), default='NULL')
    is_parking_free = Column(String(20), default='NULL')
    service = Column(Text(5000), default='NULL')
    img_items = Column(Text(5000), default='NULL')
    description = Column(Text(5000), default='NULL')
    accepted_cards = Column(String(512), default='NULL')
    check_in_time = Column(String(128), default='NULL')
    check_out_time = Column(String(128), default='NULL')
    hotel_url = Column(String(1024), default='NULL')
    update_time = Column(Datetime(6), default=datetime.datetime.now)
    continent = Column(String(96), default='NULL')
    other_info = Column(JSON(1000), default='NULL')

    @staticmethod
    def load_data():
        Hotel_model.load_sql(Hotel_model)
        print 'asdfasdf'

# Hotel_model.load_data()

if __name__ == '__main__':
    h = Hotel_model()
    h.hotel_name = '华龙酒店'
    h.hotel_name_en = 'china dragon hotel'
    h.source = 'elong'
    h.source_id = '2222222'
    h.brand_name = 'pipipipi'
    h.map_info = Coordinate(longitude='120.2345', latitude='80.4321')
    # h.map_info = '120.2345,80.4321'
    h.address = '中国河南省林州市'
    h.city = '林州市'
    h.country = 1022
    h.city_id = '6666'
    h.postal_code = '13'
    h.star = 88
    h.grade = 10
    # h.review_num = '100'
    # h.has_wifi = '0'
    # h.is_wifi_free = '1'
    # h.has_parking = '1'
    # h.is_parking_free = '0'
    # h.service = '只有床'
    # h.img_items = "https://www.'baidu.com|https:'//www.baidu.com"
    # h.description = '0.5星级酒店'
    # h.accepted_cards = 'AAA'
    # h.check_in_time = '2017-09-09 12:23:45'
    # h.check_out_time = '2017-09-09 18:23:45'
    # h.hotel_url = 'https://map.baidu.com'
    h.update_time = datetime.datetime.now()
    # h.continent = 'NULL'
    h.other_info = json.dumps({'json':'个性不'})

    print h
    sql = h.generation_sql()
    values = h.values()
    print values
    sql = sql.format(table_name='aaaa')
    # sql = sql % values
    print sql
    from proj.mysql_pool import service_platform_pool
    service_platform_conn = service_platform_pool.connection()
    cursor = service_platform_conn.cursor()
    cursor.execute(sql, values)

    cursor.close()
    service_platform_conn.close()
    # c = Coordinate()
    # c.latitude = '123.12343'
    # c.longitude = '2345.4123'
    # print c

