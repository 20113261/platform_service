#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月20日

@author: dujun
'''
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
from mioji.dao.mioji_dao import all_city, all_country
from mioji.dao.hotel_suggest_city_dao import get_label_suggest
from mioji.dao import google_format_city_dao

all_city_list = all_city()
city_dic = {}
city_dic_idkey = {}
country_dic = {}

for c in all_city_list:
    city_dic[c[0]] = c

for c in all_country():
    alias = c[3].split('|') if c[3] else []
    alias += [c[2], c[1]]
    country_dic[c[1]] = {'id': c[0], 'name': c[1], 'name_en': c[2], 'alias': alias}


def __init_suggest_city():
    init_source = ['agoda', 'booking', 'elong', 'expedia', 'hotels', 'hoteltravel', 'ctrip', 'ctripcn']
    # init_source = ['ctrip']
    # init_source = []
    s = {}
    for source in init_source:
        s[source] = __suggest_dict(source)
    return s


def __suggest_dict(source):
    s = {}
    for sug in get_label_suggest(source):
        try:
            sug_dic = {'id': sug[0], 'mcity_id': sug[1], 'suggest': json.loads(sug[3])[int(sug[4]) - 1],'is_new_type':sug[8]}
            s[sug[1]] = sug_dic
        except Exception as e:
            sug_dic = {'id': sug[0], 'mcity_id': sug[1], 'suggest': json.loads(sug[3].decode('string_escape'))[int(sug[4]) - 1],'is_new_type':sug[8]}
            s[sug[1]] = sug_dic


    return s


def get_suggest_city(source, mcity_id):
    '''
    获取标注。
    :param source: 源名称
    :param mcity_id: mioji city id
    '''
    return SUGGEST.get(source, {}).get(mcity_id, {})


SUGGEST = __init_suggest_city()

if __name__ == '__main__':
    #     print city_dic['10030']
    #     print get_suggest_city('booking', '11958')
    #     print get_suggest_city('hoteltravel', '10001')
    print country_dic[u'白俄罗斯']
