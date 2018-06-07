#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.mioji_db import online_db

def all_city_name():
    with online_db as connect:
        with connect as cursor:
            cursor.execute('select name FROM city')
            all_city_name_list = [r[0] for r in cursor.fetchall()]
    return all_city_name_list


def all_city():
    with online_db as connect:
        with connect as cursor:
            cursor.execute("SELECT id,name,name_en,country,map_info,tri_code,alias,continent,region,time_zone,summer_zone,summer_start,summer_end,grade,dur,transit_visa,visit_num,region_1,schengen,newProduct_status,is_park FROM city " + \
                           "where newProduct_status != 'Close'")
            city_list = cursor.fetchall()
            return city_list

def all_country():
    with online_db as connect:
        with connect as cursor:
            cursor.execute("SELECT mid,name,name_en,alias FROM country")
            country_list = cursor.fetchall()
            return country_list


def get_labed_city(source):
    from mioji.models.city_models import city_dic
    from mioji.dao import hotel_suggest_city_dao
    all_l = hotel_suggest_city_dao.get_label_suggest(source, 0)
    need_workload = []
    for r in all_l:
        item = city_dic.get(r[1], None)
        if item:
            need_workload.append(item)
    return need_workload

            
if __name__ == '__main__':
#     print 'need', len(get_not_crawled_city('booking'))
    print len(get_labed_city('booking'))
