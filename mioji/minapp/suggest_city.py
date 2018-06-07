#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月20日

  标注匹配程序

@author: dujun
'''

import json

from mioji.dao import hotel_suggest_city_dao
from mioji.models.city_models import city_dic

def ai_by_iglastlatter(source='booking'):
    item_list = hotel_suggest_city_dao.get_annotation_suggest(source, 1)
#     item_list = item_list[0:2]
    eq_list = []
    ccc = []
    for item in item_list:
        sug_list = json.loads(item[3])
        m_city_info = city_dic.get(item[1], None)
        if not m_city_info:
            continue
        
        annotation = -1
        select_index, s_select = ai_select_sug(source, sug_list, m_city_info)
        if len(s_select) == 1:
            annotation = 1
            
        if len(s_select) > 1:
            select_index = s_select[0]
            annotation = 100
        if select_index != item[4] and annotation != item[5]:
            pass
#             hotel_suggest_city_dao.update_suggests(item[1], source, None, select_index, annotation, None)
    
#     print eq_list
    print 'eq count:', len(eq_list), len(ccc)  
    
def ai_select_sug(source, sug_list, m_city_info):
    index = 0
    select_index = -1
    s_select = []
    for sug in sug_list:
        city, country = bind_fun[source](sug)
        m_city, m_county = m_city_info[1], m_city_info[3]
        index += 1
        if country and m_county != country:
            continue
        if ai_city_eq_2(city, m_city, country):
            select_index = index
            s_select.append(index)
    
            
    return select_index, s_select


def ai_city_eq_2(city, m_city, country):
    last_ = ['市', '町', '岛' ]
    def ig_last(src):
#         src = src.replace(country, '')
        if not src:
            return src
        if src[-1] in last_:
            return src[0:-1]
        else:
            return src
        
    city = ig_last(city)
    m_city = ig_last(m_city)
    return city == m_city

def ai_booking_city_eq(city, m_city):
    pass

def agoda_label(sug):
    city = sug.get('Name', '')
    country = None
    return city, country

def book_label(sug):
    labels = sug.get('labels', [])
    city = labels[0].get('text')
    country = labels[-1].get('text')
    return city, country

def elong_label(sug):
    city = sug.get('regionNameCn', '')
    country = sug.get('countryNameCn', '')
    return city, country

def expedia_label(sug):
    city = sug.get('regionNames', {}).get('lastSearchName', '').split(',')[0]
    country = sug.get('hierarchyInfo', {}).get('country', {}).get('name', '')
    return city, country

def hotels_label(sug):
    city = sug.get('name', '')
    s_country = sug['caption'].split(',')
    country = s_country[-1].strip() if s_country else None
    return city, country

def hoteltravel_label(sug):
    city = sug.get('cityname', None)
    country = sug.get('countryname', '')
    return city, country


bind_fun = {'booking':book_label,
            'agoda':agoda_label,
            'elong':elong_label,
            'expedia':expedia_label,
            'hotels':hotels_label,
            'hoteltravel':hoteltravel_label}
bing_eq_fun = {'2':ai_city_eq_2}

if __name__ == '__main__':
#     source = ['elong','expedia','hotels','hoteltravel']
#     for s in source:
#         ai_by_iglastlatter(s)
    ai_by_iglastlatter('booking')
