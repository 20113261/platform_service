#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

import xmltodict, types

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR
from mioji.utils import address_utils

F_URL = 'http://www.hoteltravel.com/search/autoComplete.aspx?search={key}&lng=en&noRec=3&indexcitycode= &indexcountrycode= &noRecHotel=10&noRecAttr=5&pageName=HOMEPAGE'

USE_EQ_KEY = 'key_en'
USE_EQ_COUNTRY_KEY = 'country'
USE_SEARCH_KEY = 'key_en'

class CitySpider(Spider):
    
    __type = 'citySearch'
    # 基础数据城市酒店列表 & 例行城市酒店
    __targets_version = {
        'citySearch_city':{},
        }
    
    __targets = __targets_version.keys()
    # 关联原爬虫
    #   对应多个原爬虫
    __old_spider_tag = { }
    
    def old_spider_tag(self):
        return CitySpider.__old_spider_tag
    
    def crawl_type(self):
        return CitySpider.__type
    
    def targets_parser(self):
        return CitySpider.__targets
    
    def parser_targets_version(self):
        return CitySpider.__targets_version

    def targets_request(self):
        task = self.task
        key = task.extra.get(USE_SEARCH_KEY, None)
        if not key:
            raise ParserException(TASK_ERROR, 'task.extra must has "key"')
        
        url = F_URL.format(key=key)
        
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def search():
            return {'req':{'url':url},
                    'data':{'content_type':self.convert_search_res_xml_json}, }
        
        return [search]
    
    def convert_search_res_xml_json(self, req, data):
        return xmltodict.parse(data)
    
    def cache_check(self, req, data):
        if data:
            cache_is_ok = True
        else:
            cache_is_ok = False
        return cache_is_ok
        
    def parse_citySearch_city(self, req, data):
        sug_list = []
        ai = 0
        ai_sug = None
        print 'ddd', data
        ds = data.get('ret', {})
        if ds:
            ds = ds.get('Destination', [])
        else:
            ds = []
        if ds and not isinstance(ds, types.ListType):
            ds = [ds]
        
        
        country = self.task.extra[USE_EQ_COUNTRY_KEY]
        
        index = 0
        select = -1
        select_s = []    
        for sug in ds:
            sug_list.append(sug)
            index += 1
            if address_utils.name_eq(self.task.extra[USE_EQ_KEY] , sug.get('name', '').split('*')[0])\
            and address_utils.country_eq_byzh(country, sug.get('countryname', '')):
                ai = 1
                ai_sug = sug
                select = index
                select_s.append(index)
        
        if len(select_s) > 1:
            select = select_s[0]
            ai = 100 
                
        return [[sug_list, ai_sug, ai, select]]

def search(key, en, country):
    task = Task()
    task.extra['key'] = key
    task.extra['key_en'] = en
    task.extra['country'] = country
    spider = CitySpider(task)
    try:
        rs = spider.crawl()[0]['citySearch_city']
        return key, {'error':{'code':0}, 'data':rs}
    except Exception, e:
        return key, {'error':{'code':-1, 'msg':str(e)}, 'data':[]}

if __name__ == '__main__':
    import json
    print json.dumps(search(u'布拉德福德', 'Bradford', u'英国')[1])
