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


F_URL = 'http://www.booking.com/autocomplete_2?v=1&lang=zh-cn&sid=856b717ff095a5294d897d227d9e7ef4&aid=376390&pid=9bb13ce9aca502d0&stype=1&src=index&eb=4&e_obj_labels=1&at=1&e_tclm=1&e_smmd=2&e_ms=1&e_msm=1&e_themes_msm_1=1&add_themes=1&themes_match_start=1&include_synonyms=1&sort_nr_destinations=1&gpf=1&term={key}'

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
        
        @request(retry_count=3, proxy_type=PROXY_REQ,binding = self.parse_citySearch_city)
        def search():
            return {'req':{'url':url},
                    'data':{'content_type':self.convert_data} }
        
        return [search]
    
    def convert_data(self, req, data):
        r = data[data.index('{'):data.rindex('}') + 1]
        return json.loads(r)
    
    def cache_check(self, req, data):
        if data and data.get('sr', []):
            return True
        return False
        
    def parse_citySearch_city(self, req, data):
        print '<parse——parse citySearch city>'
        sug_list = []
        ai = 0
        ai_sug = None
        key = self.task.extra['key']
        data = data.get('city',[])
        al = 0
        index = -1
        for sug in data:
            if key==sug['label'] :
                al+=1
                index = data.index(sug)+1
        if al>1:
            index= -2

        return [data,index,self.task.source]


    def __init__(self):
        Spider.__init__(self)
        self.source = 'booking'
        self.host = 'https://www.booking.com'

def search(key, en, country):
    task = Task()
    key = key+','+en+','+country
    task.extra['key'] = key
    spider = CitySpider()
    spider.task = task
    try:
        spider.crawl()
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
    print 'over - -',city[0]
    try:
        cur.execute(sql,(city[0],'booking',json.dumps(data[1]['data'][0]),data[1]['data'][1],ann,str(data[1]['error']),'20170825'))
    except:
        cur.execute(sql_err,(city[0],'booking','20170825'))
    print '<>------------<>-------------------<>------------------<finash insert db>'
    db.commit()
    db.close()

def get_new_city():
    citys = []
    with open('booking') as csvf:
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
