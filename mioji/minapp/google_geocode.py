#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月14日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji import spider_factory
from mioji.common.task_info import Task
from mioji.common.utils import simple_get_http_proxy

from mioji.dao.mioji_dao import all_city
from mioji.models import city_models
from mioji.dao import file_dao

# 初始化工作 （程序启动时执行一次即可）
insert_db = None
get_proxy = simple_get_http_proxy
debug = True
spider_factory.config_spider(insert_db, get_proxy, debug)

from mioji.spider.google.geocode_spider import search
# def search(key):
#     task = Task()
#     task.extra['key'] = key
#     spider = spider_factory.factory.get_spider('google', 'geocode', required_targets=None)
#     spider.task = task
#     try:
#         rs = spider.crawl()[0]['address_info']
#         return key, {'error':{'code':0}, 'data':rs}
#     except Exception, e:
#         return key, {'error':{'code':-1, 'msg':str(e)}, 'data':[]}

def init_agoda_city():
    from mioji.common.pool import pool
    from mioji.dao import google_format_city_dao
    import gevent, json
    
    key_list = all_city()
#     key_list = key_list[0:60]
    print len(key_list)
    gs = []
    key_list = google_format_city_dao.get_unformat_id()
#     key_list = key_list[0:50]
    for k in key_list:
        print k
        g = pool.apply_async(search, args=(k,))
#         g = gevent.spawn(search, k[0])
        gs.append(g)
     
    gevent.joinall(gs)
    
    result = {}
    rows = []
    db_rows = []
    
    batch = '20170215a'
    for g in gs:
        google_format = None
        data = None
        shot_name = None
        place_id = None
        if g.value[1]['data']:
            data = g.value[1]['data'][0]
            google_format = data.get('formatted_address', None)
            shot_name = data.get('address_components', [{}])[0].get('short_name', None)
            place_id = data.get('place_id', None)
            
        m_city = city_models.city_dic[g.value[0]]
        
        data = json.dumps(data, ensure_ascii=False)
        rows.append((g.value[0], m_city[1], m_city[3] , shot_name, google_format, data, g.value[1]['error']))
        
        # city_id,short_name,format_name,place_id,data,error,batch)
        db_rows.append((g.value[0], shot_name, google_format, place_id, data, json.dumps(g.value[1]['error'], ensure_ascii=False), batch))
        result[g.value[0]] = g.value[1]
    
    google_format_city_dao.store_format_address_rows(db_rows)
    headers = ['key', 'm_city', 'm_country', 'google_short_name', 'google_format', 'data', 'error']
    file_dao.store_as_csv('goocode/google_geocode_zh_{0}.csv', headers, rows, row_count_cut=1000)
    
if __name__ == '__main__':
    init_agoda_city()
