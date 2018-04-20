#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月16日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from mioji import spider_factory
from mioji.dao import mioji_dao
from mioji.common.task_info import Task
from mioji.utils import address_utils, google_address_utils
from mioji.common.utils import simple_get_http_proxy
from mioji.dao import file_dao
from mioji.common.pool import pool

import gevent, json, difflib

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = None
debug = True
spider_factory.config_spider(insert_db, get_proxy, debug)

from mioji.spider.google.address_format_spider import format_city_by_name, format_city_by_latlng
region_dic = {}


def task_names():
    country = ['United States']
    all_c = file_dao.load_dict('agoda/citylist_en.json')
    citys = []
    for c in all_c:
        if c[0] in country:
            citys.append(c)
    return citys

def city_5525():
    task_list = []
    for c in mioji_dao.all_city():
        ts = []
        if c[2]:
            ts.append(c[2])
        else:
            ts.append(c[1])
        
        if c[8] and c[8] != 'NULL':
            ts.append(c[8])
        ts.append(c[3])
        
        task_list.append(','.join(ts))
    
    return [c[3] + ',' + c[1] for c in mioji_dao.all_city()]

def group_name_task(citys):

    city_region = file_dao.load_dict('online/city_region.json')
    exist_dict = file_dao.load_dict('city_label_test/mioji_exit_macth.json')
    
    gs = []
    for c in citys:
        ex_row = exist_dict.get(c[0], None)
        
        if not ex_row or ex_row[-2] == 1:
            continue
        
        keys = []
        if c[2] and c[2] != 'NULL':
            keys.append(c[2])
        else:
            keys.append(c[1])
        
#         region = city_region.get(c[0], None)
#         if region:
#             keys.append(region)
#         elif c[8] and c[8] != 'NULL':
#             keys.append(c[8])
        
        keys.append(c[3])
        
        g = pool.apply_async(format_city_by_name, args=(','.join(keys),), kwds={'extra':c})
        gs.append(g)
        
    gevent.joinall(gs)
    
    rows = []
    res_dic = {}
    new_com_dict = {}
    
    for g in gs:
        city_info = g.value.kw['extra']
        m_alias = city_info[6]
#         ex_row = exist_dict.get(city_info[0])
        
        alias = m_alias.split('|') if m_alias and m_alias != 'NULL' else []
        g_region = city_region.get(city_info[0], None)
        short_name, f_address, place_id, types = None, None, None, None
        max_ratio = -1
        if g.value.isok():
            res = g.value.result[0].get('address_info', [])
            if res:
                f_address = res[0].get('formatted_address', None)
                place_id = res[0].get('place_id', None)
                types = ' | '.join(res[0].get('types', []))
                short_name = res[0]['address_components'][0]['short_name']
                res_dic[city_info[0]] = res
                max_ratio = max_close(short_name, [city_info[1], city_info[2]] + alias)
                  
            row = [city_info[0], g.value.args[0], city_info[1], city_info[2], '\n'.join(alias), city_info[3], address_utils.mioji_map_to_latlng(city_info[4], None), \
                   city_info[8], g_region, short_name, f_address, place_id, types, max_ratio, None]
            new_com_dict[city_info[0]] = row
            rows.append(row)
        else:
            row = [city_info[0], g.value.args[0], city_info[1], city_info[2], '\n'.join(alias), city_info[3], address_utils.mioji_map_to_latlng(city_info[4], None), \
                   city_info[8], g_region, short_name, f_address, place_id, types, max_ratio, g.value.error]
            rows.append(row)
        
    headers = ['city_id', 'search_key', 'name', 'name_en', 'alias', 'country', 'map_info', 'region_name', 'g_region', \
               'short_name', 'f_address', 'place_id', 'types', 'max_ratio', 'error'] 
    file_dao.store_as_csv('online/city_region_search_address_all_2.csv', headers, rows, row_count_cut=-1)
#     file_dao.store_dict(new_com_dict, 'city_label_test/mioji_exit_macth.json')
#     file_dao.store_dict(res_dic, 'city_label_test/city_address.json')

def find_group():
    city_address = file_dao.load_dict('city_label_test/city_address.json')
    
    sort_dict = {}
    
    for k, v in city_address.iteritems():
        p_id = v[0].get('place_id', None)
        exi = sort_dict.get(p_id, [])
        sort_dict[p_id] = exi
        exi.append(k)
    
    rows = []
    for k, v in sort_dict.iteritems():
        if len(v) > 1:
            rows.append((k, v))
    print rows
        

def get_region(citys):
    gs = []
    for c in citys:
        g = pool.apply_async(format_city_by_latlng, args=(address_utils.mioji_map_to_latlng(c[4], None),), kwds={'extra':c})
        gs.append(g)
        
    gevent.joinall(gs)
    
    save_values = []
    city_region = []
    
    region_dic = {}
    
    for g in gs:
        city_info = g.value.kw['extra']
        r_long, r_short, r_type, r_data = None, None, None, None
        if g.value.isok():
            address = g.value.result[0].get('address_info', [])
            if address:
                region_node = address[0]
                node = google_address_utils.find_google_region_by_addressnode(region_node)
                region_node = google_address_utils.find_google_region(g.value.result[0].get('address_info', []))
                if region_node:
                    node = region_node['address_components'][0]
#                 if not node:
                    
                if node:
#                 r_name = region_node['formatted_address']
                    r_long = node.get('long_name', None)
                    r_short = node.get('short_name', None)
                    r_type = '|'.join(node['types'])
                    
                if region_node: 
                    r_data = json.dumps(region_node, ensure_ascii=False)
            
            row = [city_info[0], city_info[1], city_info[2], city_info[3], address_utils.mioji_map_to_latlng(city_info[4], None), \
                   city_info[8], r_long, r_short, r_type, r_data, None ]
            region_dic[city_info[0]] = r_long
            city_region.append(row)
        else:
            row = [city_info[0], city_info[1], city_info[2], city_info[3], address_utils.mioji_map_to_latlng(city_info[4], None), \
                   city_info[8], r_long, r_short, r_type, r_data , g.value.error ]
            city_region.append(row)
            
#         save_values.append(g.value)
    
    file_dao.store_dict(region_dic, 'online/city_region.json')
    headers = ['city_id', 'name', 'name_en', 'country', 'map_info', 'region_name', 'g_region_long', 'g_region_short', 'g_region_type', 'g_rmin_data', 'error']        
    file_dao.store_as_csv('online/region_info_{0}.csv', headers, city_region, row_count_cut=-1)

def format_agoda_cityaddress():
    agoda_citys = task_names()[0:10]
    gs = []
    for c in agoda_citys:
        g = pool.apply_async(format_city_by_name, args=(','.join(c),), kwds={'extra':c})
        gs.append(g)
    gevent.joinall(gs)
    
    
    agoda_address_dict = {}
    rows = []
    for g in gs:
        city_info = g.value.kw['extra']
        short_name, f_address, place_id, types = None, None, None, None
        if g.value.isok():
            res = g.value.result[0].get('address_info', [])
            if res:
                f_address = res[0].get('formatted_address', None)
                place_id = res[0].get('place_id', None)
                types = ' | '.join(res[0].get('types', []))
                short_name = res[0]['address_components'][0]['short_name']
                agoda_address_dict[g.value.args[0]] = place_id 
        else:
            pass
    
    file_dao.store_dict(agoda_address_dict, 'city_label_test/agoda_address_format.json')
               

def do():
    # print format_city_by_name('阿伯丁(MS)')
#     names = task_names()
    citys = mioji_dao.all_city()
    address_list = get_region(citys)
    
    rows = []
#     for a in address_list:
#         if a.isok():
#             row = (a.args[0], a.result[0].get('address_info', [{}])[0].get('formatted_address', None), a.result[0].get('address_info', [{}])[0].get('types', []), None)
#         else:
#             row = (a.args[0], None, None, a.error)
#         rows.append(row)
    
#     headers = ['s_name', 'g_format_name', 'types', 'error']        
#     file_dao.store_as_csv('online/region_2_{0}.csv', headers, rows, row_count_cut=2000)
    
def max_close(short_name, names):
    short_name = short_name.lower()
    max_ratio = 0
    for n in names:
        if not n:
            continue
        n = n.lower()
        max_ratio = max(max_ratio, difflib.SequenceMatcher(None, short_name, n).ratio())
    
    return max_ratio
    
if __name__ == '__main__':
#     city_region = file_dao.load_dict('online/city_region.json')
#     print city_region['50146']
    citys = mioji_dao.all_city()
    group_name_task(citys)
#     print len(task_names())
#     format_agoda_cityaddress()
