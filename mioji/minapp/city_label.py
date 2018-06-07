#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月20日

@author: dujun
'''

from mioji.common import utils
utils.setdefaultencoding_utf8()

import difflib, traceback
from mioji.dao import file_dao, hotel_suggest_city_dao, mioji_dao
from mioji.spider.google.address_format_spider import format_city_by_name


def utf(src):
    if src.endswith('\\'):
        src = src[0:-1]
    return src.decode('unicode_escape')

def com_close():
    agoda_all_city = file_dao.load('agoda/citylist.json')
    region_dic = file_dao.load_dict('online/city_region.json')

    agoda_unlabel_city = hotel_suggest_city_dao.get_annotation_suggest('agoda', -1)
    unlabel_ids = []
    for c in agoda_unlabel_city:
        unlabel_ids.append(c[1])
        
    agoda_country_city = {}    
    for c in agoda_all_city:
        country = utf(c[0])
        name = utf(c[2])
        citys = agoda_country_city.get(country, [])
        citys.append(name)
        agoda_country_city[country] = citys
    
    city_dic = {}
    for c in mioji_dao.all_city():
#         if c[3] in ['美国'] and c[0] in unlabel_ids:
            city_dic[c[0]] = c
    
    match_dic = {}
    match_rows = []
    for c_id, c_info in city_dic.iteritems():
        try:
            m = difflib.get_close_matches(c_info[1], agoda_country_city[c_info[3]])
            row = (c_info[0], c_info[1], c_info[2], c_info[3], c_info[8], region_dic.get(c_info[0], None), '\n'.join(m))
            match_rows.append(row)
            match_dic[c_info[0]] = m
        except:
            print traceback.format_exc()
        
    headers = ['id', 'name', 'name_en', 'country', 'region', 'g_region', 'close']    
    file_dao.store_as_csv('agoda/close_match.csv', headers, match_rows)   
    file_dao.store_dict('agoda/close_match.json', name)

if __name__ == '__main__':
    com_close()

