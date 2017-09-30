# !/usr/bin/python
# -*- coding: UTF-8 -*-
""""
    task_name
    list - hotel - agoda|booking|ctrip|elong|expedia|hotels|hoteltravel|hrs|cheaptickets|orbitz|travelocity|ebookers|tripadvisor|ctripcn|hilton - tag
    list - rest|attr - daodao - tag
    list - total - qyer - tag
    tag 为 test是特殊的，不被识别   eg:20170919a
"""
from semi_automatic_send_task import list_task

import pymysql
from uuid import uuid4
import json

"""
9月29日十点发四个源
elong
ctrip
hotels
booking
"""
HOTEL_SOURCE = 'hotels'
HOTEL_TAG = '20170929a'

POI_TYPE = 'rest'
POI_TAG = '20170928a'

QYER_TAG = '20170928a'

FUNC_TO_TASKNAME = {
    'prepare_data_daodao_list_ota_location': 'list_'+POI_TYPE+'_'+POI_TAG,
    'prepare_data_daodao_list_SuggestName': 'list_'+POI_TYPE+'_'+POI_TAG,
    'prepare_data_daodao_list_hotel_suggestions_city': 'list_'+POI_TYPE+'_'+POI_TAG,

    'prepare_data_hotel_list_old': 'list_hotel_'+HOTEL_SOURCE+'_'+HOTEL_TAG,
    'prepare_data_hotel_list_new': 'list_hotel_'+HOTEL_SOURCE+'_'+HOTEL_TAG,

    'prepare_data_qyer_list_ota_location': 'list_total_qyer'+'_'+QYER_TAG,
    'prepare_data_qyer_list_QyerSuggestCityUrl': 'list_total_qyer'+'_'+QYER_TAG,
}

def must_be(func):
    def after(*args, **kwargs):
        datas = func(*args, **kwargs)
        task_name = FUNC_TO_TASKNAME[func.func_name]
        list_task(task_name, datas)
    return after

def cache_city2_country():
    conn_c = pymysql.connect(host='10.10.69.170', user='reader', password='miaoji1109', charset='utf8', db='base_data')
    cursor_c = conn_c.cursor()
    cursor_c.execute('select id, country_id from city;')
    city_country = {city_id: country_id for city_id, country_id in cursor_c.fetchall()}
    cursor_c.close()
    conn_c.close()
    return city_country



@must_be
def prepare_data_hotel_list_old():
    city_country = cache_city2_country()
    typ1, typ2, source, tag = FUNC_TO_TASKNAME['prepare_data_hotel_list_old'].split('_')
    PART = tag
    conn_s = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_s = conn_s.cursor()
    cursor_s.execute(
        """SELECT city_id, source, suggestions, select_index, is_new_type FROM source_info.hotel_suggestions_city where source = '%s' and annotation > -1 and select_index > -1""" % source)

    datas = []
    #source, suggestions, select_index, country_id, suggest_type, is_new_type, part
    suggest_type = 1
    for city_id, source, suggestions, select_index, is_new_type in cursor_s.fetchall():
        try:
            datas.append((city_id, source, suggestions, select_index, city_country[city_id], suggest_type, is_new_type, PART))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    return datas

@must_be
def prepare_data_hotel_list_new():
    typ1, typ2, source, tag = FUNC_TO_TASKNAME['prepare_data_hotel_list_new'].split('_')
    PART = tag
    conn_s = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_s = conn_s.cursor()
    cursor_s.execute(
        """SELECT city_id, source, suggest, country_id, suggest_type FROM source_info.ota_location where source = '%s'""" % source)

    datas = []
    #city_id, source, suggestions, select_index, country_id, suggest_type, is_new_type, part
    is_new_type = 1
    select_index = None
    for city_id, source, suggest, country_id, suggest_type in cursor_s.fetchall():
        datas.append((city_id, source, suggest, select_index, country_id, suggest_type, is_new_type, PART))

    return datas

@must_be
def prepare_data_daodao_list_SuggestName():
    city_country = cache_city2_country()
    conn_c = pymysql.connect(host='10.10.180.145', user='hourong', password='hourong', charset='utf8', db='SuggestName')
    cursor_c = conn_c.cursor()

    sql = """select city_id, daodao_url from SuggestName.DaodaoSuggestCityUrl"""
    cursor_c.execute(sql)
    datas = []
    for city_id, daodao_url in cursor_c.fetchall():
        try:
            datas.append((city_id, daodao_url, city_country[str(city_id)], POI_TYPE))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_c.close()
    conn_c.close()

    return datas

@must_be
def prepare_data_daodao_list_ota_location():
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    sql = """SELECT  city_id, suggest, country_id FROM source_info.ota_location where source = 'daodao'"""
    cursor_c.execute(sql)
    datas = []
    for city_id, suggest, country_id in cursor_c.fetchall():
        datas.append((city_id, suggest, country_id, POI_TYPE))

    cursor_c.close()
    conn_c.close()

    return datas

@must_be
def prepare_data_daodao_list_hotel_suggestions_city():
    city_country = cache_city2_country()
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    sql = """select city_id, source, suggestions, select_index from source_info.hotel_suggestions_city where source = 'daodao' and select_index > -1 and annotation > -1;"""
    cursor_c.execute(sql)

    datas = []
    for city_id, source, suggestions, select_index in cursor_c.fetchall():
        url = json.loads(suggestions)[select_index - 1]['url']
        try:
            datas.append((city_id, url, city_country[city_id], POI_TYPE))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_c.close()
    conn_c.close()

    return datas

@must_be
def prepare_data_qyer_list_ota_location():
    typ1, typ2, source, tag = FUNC_TO_TASKNAME['prepare_data_hotel_list_old'].split('_')
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    datas = []

    sql = """SELECT city_id, country_id, suggest FROM source_info.ota_location where source = 'qyer'"""
    cursor_c.execute(sql)
    for city_id, country_id, suggest in cursor_c.fetchall():
        datas.append((city_id, country_id, suggest, tag))

    return datas

@must_be
def prepare_data_qyer_list_QyerSuggestCityUrl():
    city_country = cache_city2_country()
    typ1, typ2, source, tag = FUNC_TO_TASKNAME['prepare_data_hotel_list_old'].split('_')
    conn_c = pymysql.connect(host='10.10.180.145', user='hourong', password='hourong', charset='utf8', db='SuggestName')
    cursor_c = conn_c.cursor()

    datas = []

    sql = """select city_id, city_link from SuggestName.QyerSuggestCityUrl"""
    cursor_c.execute(sql)
    for city_id, city_link in cursor_c.fetchall():
        try:
            datas.append((city_id, city_country[str(city_id)], city_link, tag))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    return datas

if __name__ == '__main__':
    # prepare_data_daodao_list_hotel_suggestions_city()
    # prepare_data_daodao_list_ota_location()
    # prepare_data_daodao_list_SuggestName()
    #***************************************************************************************
    prepare_data_hotel_list_old()
    prepare_data_hotel_list_new()
    # ***************************************************************************************
    # prepare_data_qyer_list_ota_location()
    # prepare_data_qyer_list_QyerSuggestCityUrl()