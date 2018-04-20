#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR
import pymysql
from DBUtils.PooledDB import PooledDB
import json
#from mioji.utils import address_utils

F_URL ='http://ihotel.elong.com/ajax/sugInfo?datatype=Region&keyword={0}' 
city_url = 'http://ihotel.elong.com/region_'

USE_EQ_KEY = 'key'
USE_EQ_COUNTRY_KEY = 'country'
USE_SEARCH_KEY = 'key'

#db -
base_ip = '10.10.230.206'
base_user = 'mioji_admin'
base_pwd = 'mioji1109'
base_db = 'source_info'
mysql_db_pool = PooledDB(creator=pymysql, mincached=1, maxcached=2, maxconnections=100, host=base_ip, port=3306,user=base_user, passwd=base_pwd, db=base_db, charset='utf8', use_unicode=False, blocking=True) 

class CitySpider(Spider):

    source_type = 'citySearch'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'citySearch_city':{},
        }
    
    #__targets = __targets_version.keys()
    # 关联原爬虫
    #   对应多个原爬虫
    #__old_spider_tag = { }
    old_spider_tag= {  }
    
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
        print key 
        if not key:
            raise ParserException(TASK_ERROR, 'task.extra must has "key"')
        
        url = F_URL.format(key)
        
        print 'WTF start targets request'
        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_citySearch_city)
        def search():
            return {'req':{'url':url},
                    'data':{'content_type':'json'}, }
        
        return [search]
    
    def cache_check(self, req, data):
        if data and data.get('region', []):
            cache_is_ok = True
        else:
            cache_is_ok = False
            
        return cache_is_ok
        
    def parse_citySearch_city(self, req, data):
        print '<parse——parse citySearch city>'
        sug_list = []
        ai = 0
        ai_sug = None
        
        #---feng--
        key = self.task.extra['key']
        key_en =self.task.extra['key_en']
        country = self.task.extra[USE_EQ_COUNTRY_KEY]
        data = data['data']
        data = data.get('city',[])
        print 'data',data
        al = 0
        index = -1
        for sug in data:
            if key==sug['name_cn'] and key_en==sug['name_en'] and country== sug['region_info']['province_name_cn']:
                al+=1
                index = data.index(sug)+1
        if al>1:
            index= -2

        return [data,index,self.task.source]  
        '''
        for sug in data.get('region_info', []):
            print '<><<sug>><>',sug
            sug['m_url'] = city_url + sug.get('regionId', 'NULL')
            sug_list.append(sug)
            index += 1
            if address_utils.name_eq_elong(self.task.extra[USE_EQ_KEY] , sug.get('regionNameCn', '')) \
            and address_utils.country_eq_byzh(country, sug.get('countryNameCn', '')):
                ai_sug = sug
                ai = 1
                select = index
                select_s.append(index)
        if len(select_s) > 1:
            select = select_s[0]
            ai = 100
        return [[sug_list, ai_sug, ai, select]]
        '''

    def __init__(self,task=None):
        Spider.__init__(self)
        self.source = 'elong'
        self.host = 'https://www.elong.com'

def search(key, en, country):
    task = Task()
    task.extra['key'] = key
    task.extra['key_en'] = en
    task.extra['country'] = country
    spider = CitySpider()
    spider.task = task
    try:
        rs_code =spider.crawl()
        rs = spider.result['citySearch_city']
        return key, {'error':{'code':0}, 'data':rs}
    except Exception, e:
        return key, {'error':{'code':-1, 'msg':str(e)}, 'data':[]}


def insert_db(city,data):
    db =mysql_db_pool.connection()
    cur = db.cursor()
    ann = 1
    try:
        if data[1]['data'][1]<0:
            ann = -1
    except:
        ann = -2
    sql = """INSERT INTO tmp(
    city_id,source,suggestions,select_index,annotation,error,label_batch)
    VALUES (%s,%s,%s,%s,%s,%s,%s)"""
    sql_err = """INSERT INTO tmp(
    city_id,source,label_batch)
    VALUES (%s,%s,%s)"""
    try:
        cur.execute(sql,(city[0],'elong',json.dumps(data[1]['data'][0]),data[1]['data'][1],ann,str(data[1]['error']),'20170824'))
    except:
        cur.execute(sql_err,(city[0],'elong','20170824'))
    print '<>------------<>-------------------<>------------------<finash insert db>'
    db.commit()
    db.close()

def get_new_city():
    citys = []
    with open('elong') as csvf:
        fcsv = csvf.readlines() 
        for c in fcsv:
            c = c[:-1]
            citys.append(c.split(','))
    return citys

if __name__ == '__main__':
    citys = get_new_city()

    for city in citys:
        search_data =  search(city[2],city[3],city[4])
        print search_data
        #insert_db(city,search_data)

