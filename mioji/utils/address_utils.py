#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月9日

@author: dujun
'''
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.models.city_models import country_dic

def name_eq(name, other_name):
    print 'eq==', name, other_name
    l_name = name.lower()
    ol_name = other_name.lower()
    ol_name = ol_name.replace('（', '(')
    ol_name = ol_name.replace('）', ')')
    
    index = ol_name.find('(')
    if index != -1 and ol_name.endswith(')'):
        o_names = [ol_name[0:index].strip(), ol_name[index + 1:-1].strip()]
        print 'eq==', name, o_names
        o_names = [o.lower() for o in o_names]
        return l_name in o_names
    else:
        return l_name == ol_name
    

def name_eq_elong(name, other_name):
    if name_eq(name, other_name):
        return True
    elif name == other_name.replace('及周边', ''):
        return True
    elif name == other_name.split('-')[0]:
        return True


def country_eq_byzh(name, r_name):
    print country_dic
    print country_dic.get(name, {})
    country_names = country_dic.get(name, {}).get('alias', [])
    print name, r_name, country_names
    return r_name in country_names

def mioji_map_to_latlng(src, default=None):
    if not src:
        return None
#         raise Exception('map_info={0} error must like xx,xx')
    m_latlngs = src.split(',')
    if len(m_latlngs) != 2:
        return None
#         raise Exception('map_info={0} error must like xx,xx'.format(src))
    latlng = m_latlngs[1] + ',' + m_latlngs[0]
    return latlng
    
    
if __name__ == '__main__':
    a= [1,2,3]
    print a[-3]
    
