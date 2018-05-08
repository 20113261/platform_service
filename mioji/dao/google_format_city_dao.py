#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月14日

@author: dujun
'''

from mioji.common.mioji_db import new_spider_db

INSERT_SQL = '''insert INTO `google_format_city`(city_id,`short_name`,format_name,place_id,data,error,batch)''' + \
''' VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE ''' + \
'''`short_name`=VALUES(`short_name`),format_name=VALUES(format_name),place_id=VALUES(place_id),data=VALUES(data),''' + \
'''error=VALUES(error),batch=VALUES(batch)'''

def get_unformat_id():
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute('select city_id from google_format_city where place_id is NULL')
            res = cursor.fetchall()
            return [r[0] for r in res]
        
def all_format_address():
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute('select * from google_format_city where place_id is not NULL')
            res = cursor.fetchall()
    return res

def all_unformat_address():
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute('select * from google_format_city where place_id is NULL')
            res = cursor.fetchall()
    return res

def all_address():
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute('select * from google_format_city order by format_name')
            res = cursor.fetchall()
    return res
    
def store_format_address_rows(rows):
    '''
    city_id,source,suggestions, select, annotation, error
    '''
    with new_spider_db as connect:
        with connect as cursor:
            cursor.executemany(INSERT_SQL, rows)

def store_format_address(city_id, short_name, format_name, place_id, data, error, batch):
    with new_spider_db as connect:
        with connect as cursor:
            cursor.execute(INSERT_SQL, (city_id, short_name, format_name, place_id, data, error, batch))
            
if __name__ == '__main__':
#     res = get_unformat_id()
#     print res
#     print len(res)            
    store_format_address('10050', None, None, None, None, '{"code": 0}', 'test')