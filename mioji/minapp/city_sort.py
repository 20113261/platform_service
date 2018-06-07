#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月14日

@author: dujun
'''

from mioji.dao import google_format_city_dao
from mioji.models.city_models import city_dic
from mioji.utils import address_utils
from mioji.dao import file_dao

import json, difflib


def output_group_city():
    all_city = google_format_city_dao.all_format_address()
    format_dict = {}
    for a in all_city:
        city_info = format_dict.get(a[3], {'mcity_id':[], 'data':a[4]})
        format_dict[a[3]] = city_info
        city_info['mcity_id'].append(a[0])
    
    rows = []
    format_dict_s = {}
    
    count = 0
    all_c = 0
    for k, v in format_dict.items():
        if len(v['mcity_id']) > 1:
            count += 1
            all_c += len(v['mcity_id'])
            format_dict_s[k] = v
            g_js = json.loads(v['data'])
            google_format = g_js.get('formatted_address', None)
            shot_name = g_js.get('address_components', [{}])[0].get('short_name', None)
            place_id = g_js.get('place_id', None)
            country = g_js.get('address_components', [{}])[-1].get('long_name', None)
            
            for mid in v['mcity_id']:
                m_city = city_dic[mid]
                rows.append([mid, m_city[1], m_city[3], m_city[2], address_utils.mioji_map_to_latlng(m_city[4])] + list(m_city[5:21]) + [shot_name, country, google_format])
                
            rows.append((None,))
            
    # file_dao.store_dict(format_dict_s, 'google_sort')
    m_header = ['tri_code', 'alias', 'continent', 'region', 'time_zone', 'summer_zone', 'summer_start', 'summer_end', 'grade', 'dur', 'transit_visa', 'visit_num', 'region_1', 'schengen', 'newProduct_status', 'is_park']
    headers = ['mcity_id', 'mcity', 'mcountry', 'men', 'm_map'] + m_header + ['google_short_name', 'google_country', 'google_format_name']
    file_dao.store_as_csv('city_sort/google_sort_city{0}.csv', headers, rows, row_count_cut=500)
    print count, all_c

def output_address(type='all', filter=None):
    '''
    '''
    index = 0
    config = [{'func':google_format_city_dao.all_address, 'name':'city_sort/google_address_city{0}.csv'},
           {'func':google_format_city_dao.all_unformat_address, 'name':'city_sort/google_unformataddress_city{0}.csv'}]
    
    all_city = config[index]['func']()
    
    m_header = ['tri_code', 'alias', 'continent', 'region', 'time_zone', 'summer_zone', 'summer_start', 'summer_end', 'grade', 'dur', 'transit_visa', 'visit_num', 'region_1', 'schengen', 'newProduct_status', 'is_park']
    headers = ['mcity_id', 'mcity', 'mcountry', 'men', 'm_map'] + \
    m_header + \
    ['google_short_name', 'google_country', 'google_format_name', 'error', 'type']
    rows = []
    
    for c in all_city:
        shot_name, country, google_format = None, None, None
        s_type = 0
        m_city = city_dic[c[0]]
        if c[4] and c[4].lower() != 'null':
            g_js = json.loads(c[4])
            google_format = g_js.get('formatted_address', None)
            shot_name = g_js.get('address_components', [{}])[0].get('short_name', None)
            country = get_country(g_js)
        
        if shot_name:
            m_alias = m_city[6]
            alias = m_alias.split('|') if m_alias and m_alias != 'NULL' else []
            s_type = simple_filter(shot_name, [m_city[1], m_city[2]] + alias)
            
        rows.append([c[0], m_city[1], m_city[3], m_city[2], address_utils.mioji_map_to_latlng(m_city[4])] + \
                     list(m_city[5:21]) + \
                     [shot_name, country, google_format, json.dumps(c[5], ensure_ascii=False), s_type])
    
    file_dao.store_as_csv(config[index]['name'], headers, rows, row_count_cut=1000)

def simple_filter(short_name, m_names):
    short_name = short_name.lower()
    dif_ratio = 0
    
    if short_name == 'hn':
        print 'ssss', short_name, m_names
    for n in m_names:
        n = n.lower()
        if not n:
            continue
        
        if short_name == n:
            return 1
        elif short_name in n:
            return 2
        elif n in short_name:
            return 3
        else:
            dif_ratio = max(dif_ratio, difflib.SequenceMatcher(None, short_name, n).ratio())
            
    return dif_ratio
    

def get_country(src):
    l = src.get('address_components', [{}])
    for i in xrange(0, len(l)):
        if 'country' in l[-(i + 1)].get('types', []):
            return l[-(i + 1)].get('long_name', None)
        

# print json.dumps(format_dict_s)

if __name__ == '__main__':
#     output_error_format_address()
#     output_group_city()
    output_address()
