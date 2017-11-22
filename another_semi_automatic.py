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
import json

def cache_city2_country():
    conn_c = pymysql.connect(host='10.10.69.170', user='reader', password='miaoji1109', charset='utf8', db='base_data')
    cursor_c = conn_c.cursor()
    cursor_c.execute('select id, country_id from city;')
    city_country = {city_id: country_id for city_id, country_id in cursor_c.fetchall()}
    cursor_c.close()
    conn_c.close()
    return city_country



def prepare_data_hotel_list_old(source, part, priority, cities=[]):
    """
    准备hotel老源数据
    需要的字段 source, suggestions, select_index, country_id, suggest_type, is_new_type, part
    :param source:
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    city_country = cache_city2_country()
    conn_s = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_s = conn_s.cursor()
    sql = """SELECT city_id, source, suggestions, select_index, is_new_type FROM source_info.hotel_suggestions_city where source = '%s' and annotation > -1 and select_index > -1"""
    if flag:
        sql += " and city_id in %s" % str(cities)
    print sql
    cursor_s.execute(sql % source)

    datas = []
    temp_old = []
    suggest_type = 1
    for city_id, source, suggestions, select_index, is_new_type in cursor_s.fetchall():
        try:
            if flag:
                temp_old.append(int(city_id))
            datas.append((city_id, source, suggestions, select_index, city_country[city_id], suggest_type, is_new_type, part))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_s.close()
    conn_s.close()

    if flag:
        old_set = set(cities) ^ set(temp_old)
        print '老源不存在的城市  %s, %d 个, %s' % (source, len(old_set), str(old_set))

    task_name = 'list_hotel_' + source + '_' + part
    print task_name
    list_task(task_name, datas, priority)

def prepare_data_hotel_list_new(source, part, priority=3, cities=[]):
    """
    准备hotel新源数据
    需要的字段 city_id, source, suggestions, select_index, country_id, suggest_type, is_new_type, part
    :param source:
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    conn_s = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_s = conn_s.cursor()
    sql = """SELECT city_id, source, suggest, country_id, suggest_type FROM source_info.ota_location where source = '%s'"""
    if flag:
        sql += " and city_id in %s" % str(cities)
    print sql
    cursor_s.execute(sql % source)

    datas = []
    temp_new = []
    is_new_type = 1
    select_index = None
    for city_id, source, suggest, country_id, suggest_type in cursor_s.fetchall():
        if flag:
            temp_new.append(int(city_id))
        datas.append((city_id, source, suggest, select_index, country_id, suggest_type, is_new_type, part))

    cursor_s.close()
    conn_s.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print '新源不存在的城市  %s, %d 个, %s' % (source, len(new_set), str(new_set))

    task_name = 'list_hotel_' + source + '_' + part
    print task_name
    list_task(task_name, datas, priority)

def prepare_data_daodao_list_SuggestName(poi_type, part, priority=3, cities=[]):
    """
    准备 daodao DaodaoSuggestCityUrl源数据
    :param poi_type: rest attr
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    city_country = cache_city2_country()
    conn_c = pymysql.connect(host='10.10.180.145', user='hourong', password='hourong', charset='utf8', db='SuggestName')
    cursor_c = conn_c.cursor()

    sql = """select city_id, daodao_url from SuggestName.DaodaoSuggestCityUrl"""
    if flag:
        sql += " where city_id in %s" % str(cities)
    print sql
    cursor_c.execute(sql)

    datas = []
    temp_new = []
    for city_id, daodao_url in cursor_c.fetchall():
        try:
            if flag:
                temp_new.append(int(city_id))
            datas.append((city_id, daodao_url, city_country[str(city_id)], part))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_c.close()
    conn_c.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print 'DaodaoSuggestCityUrl不存在的城市  %s, %d 个, %s' % ('daodao', len(new_set), str(new_set))

    task_name = 'list_' + poi_type + '_daodao_' + part
    print task_name
    list_task(task_name, datas, priority)


def prepare_data_daodao_list_ota_location(poi_type, part, priority=3, cities=[]):
    """
    准备 daodao ota_location源数据
    :param poi_type: rest attr
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    sql = """SELECT  city_id, suggest, country_id FROM source_info.ota_location where source = 'daodao'"""
    if flag:
        sql += " and city_id in %s" % str(cities)
    print sql
    cursor_c.execute(sql)

    datas = []
    temp_new = []
    for city_id, suggest, country_id in cursor_c.fetchall():
        if flag:
            temp_new.append(int(city_id))
        datas.append((city_id, suggest, country_id, poi_type))

    cursor_c.close()
    conn_c.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print 'ota_location不存在的城市  %s, %d 个, %s' % ('daodao', len(new_set), str(new_set))

    task_name = 'list_' + poi_type + '_daodao_' + part
    print task_name
    list_task(task_name, datas, priority)


def prepare_data_daodao_list_hotel_suggestions_city(poi_type, part, priority=3, cities=[]):
    """
    准备 daodao hotel_suggestions_city源数据
    :param poi_type: rest attr
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    city_country = cache_city2_country()
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    sql = """select city_id, source, suggestions, select_index from source_info.hotel_suggestions_city where source = 'daodao' and select_index > -1 and annotation > -1"""
    if flag:
        sql += " and city_id in %s" % str(cities)
    print sql
    cursor_c.execute(sql)

    datas = []
    temp_new = []
    for city_id, source, suggestions, select_index in cursor_c.fetchall():
        url = json.loads(suggestions)[select_index - 1]['url']
        try:
            if flag:
                temp_new.append(int(city_id))
            datas.append((city_id, url, city_country[city_id], poi_type))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_c.close()
    conn_c.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print 'ota_location不存在的城市  %s, %d 个, %s' % ('daodao', len(new_set), str(new_set))

    task_name = 'list_' + poi_type + '_daodao_' + part
    print task_name
    list_task(task_name, datas, priority)


def prepare_data_qyer_list_ota_location(part, priority=3, cities=[]):
    """
    准备 qyer ota_location源数据
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    conn_c = pymysql.connect(host='10.10.230.206', user='mioji_admin', password='mioji1109', charset='utf8',
                             db='source_info')
    cursor_c = conn_c.cursor()

    temp_new = []
    datas = []
    task_name = 'list_total_qyer' + '_' + part

    sql = """SELECT city_id, country_id, suggest FROM source_info.ota_location where source = 'qyer'"""
    if flag:
        sql += " and city_id in %s" % str(cities)
    print sql
    cursor_c.execute(sql)

    for city_id, country_id, suggest in cursor_c.fetchall():
        if flag:
            temp_new.append(int(city_id))
        datas.append((city_id, country_id, suggest, part))

    cursor_c.close()
    conn_c.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print 'ota_location不存在的城市  %s, %d 个, %s' % ('qyer', len(new_set), str(new_set))

    print task_name
    list_task(task_name, datas, priority)


def prepare_data_qyer_list_QyerSuggestCityUrl(part, priority=3, cities=[]):
    """
    准备 qyer QyerSuggestCityUrl源数据
    :param part: tag号
    :param priority: 任务优先级 默认为3
    :param cities: 为空发送全部任务
    :return:
    """
    flag = len(cities) > 0
    city_country = cache_city2_country()

    conn_c = pymysql.connect(host='10.10.180.145', user='hourong', password='hourong', charset='utf8', db='SuggestName')
    cursor_c = conn_c.cursor()

    temp_new = []
    datas = []
    task_name = 'list_total_qyer' + '_' + part

    sql = """select city_id, city_link from SuggestName.QyerSuggestCityUrl"""
    if flag:
        sql += " where city_id in %s" % str(cities)
    print sql
    cursor_c.execute(sql)

    for city_id, city_link in cursor_c.fetchall():
        try:
            if flag:
                temp_new.append(int(city_id))
            datas.append((city_id, city_country[str(city_id)], city_link, tag))
        except KeyError as e:
            print u'city 不存在 : %s' % city_id

    cursor_c.close()
    conn_c.close()

    if flag:
        new_set = set(cities) ^ set(temp_new)
        print 'QyerSuggestCityUrl不存在的城市  %s, %d 个, %s' % ('qyer', len(new_set), str(new_set))

    print task_name
    list_task(task_name, datas, priority)


if __name__ == '__main__':
    pass
    # prepare_data_daodao_list_hotel_suggestions_city()
    # prepare_data_daodao_list_ota_location()
    # prepare_data_daodao_list_SuggestName()
    #***************************************************************************************
    # prepare_data_hotel_list_old()
    # prepare_data_hotel_list_new()
    # ***************************************************************************************
    # prepare_data_qyer_list_ota_location()
    # prepare_data_qyer_list_QyerSuggestCityUrl()

