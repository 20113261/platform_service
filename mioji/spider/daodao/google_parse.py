#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey;
monkey.patch_all()
from gevent.pool import Pool
import re
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from lxml.html import tostring
import MySQLdb
import json


#

class TestSpider(Spider):
    source_type = 'agodaCityPosition'
    targets = {
        "position": {}
    }
    count = 0
    temp0 = []

    def __init__(self, task):
        super(TestSpider, self).__init__(task)

    def targets_request(self):
        @request(retry_count=12, proxy_type=PROXY_REQ, binding=self.parse_position)
        def tasker():
            source = str(self.task.content[0])
            url = self.task.content[2]
            id = str(self.task.content[1])
            if source == 'Expedia':
                data = url
                url = 'https://www.expedia.com.vn/Hotel-Search-Data?'
                return {
                    'req': {
                        'source': source,
                        'id': id,
                        'url': url,
                        'data':data,
                        'headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'},
                        'method': 'POST',
                    },
                    'data': {'content_type': 'text'}}
            else:
                return {
                            'req': {
                                    'source': source,
                                    'id': id,
                                    'url': url,
                                    'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'},
                                    'method': 'get',
                                    },
                            'data': {'content_type': 'html'}
                        }
        yield tasker

    def parse_position(self, req, data):
        db = MySQLdb.connect(host='10.10.230.206', user='mioji_admin', passwd='mioji1109', db='source_info',
                             charset='utf8')
        cur2 = db.cursor()
        source = req['req']['source']
        #print 'pp0', source, req['req']['id'], data
        if source == 'Agoda':
            res2 = data.xpath('/html/head/meta[10]/@content')[0]
            #print source, res2,'temp_agoda',req['req']['id']
            sql = 'update hotelinfo_jac_2018_03_20 set agoda=%s where id =%s'
            cur2.execute(sql, (res2,req['req']['id']))
            db.commit()

        elif source == 'Booking':
            temp_dic = {}
            res2 = 'https://www.booking.com' + data.xpath('//*[@id="hotellist_inner"]/div[1]/div[2]/div[1]/div[1]/h3/a/@href')[0].replace('\n','')
            #print source, res2, 'temp_booking', req['req']['id']
            temp_dic['booking'] = res2
            tem = json.dumps(temp_dic)
            sql = 'update hotelinfo_jac_2018_03_20 set book=%s where id =%s'
            cur2.execute(sql, (tem, req['req']['id']))
            #print source, res2, req['req']['id']
            db.commit()
        elif source == 'Hotels':
            temp_dic = {}
            res2 = 'https://zh.hotels.com' + data.xpath('//*[@id="listings"]/ol/li[1]/article/div/div[1]/h3/a/@href')[0]
            #print source, res2, 'temp_hotels', req['req']['id']
            temp_dic['hotels'] = res2
            tem = json.dumps(temp_dic)
            sql = 'update hotelinfo_jac_2018_03_20 set hotels=%s where id =%s'
            cur2.execute(sql, (tem, req['req']['id']))
            #print source, res2, req['req']['id']
            db.commit()
        elif source == 'Expedia':
            #print 'pp1',source, req['req']['id'],data
            dt = json.loads(data)
            ep_url = dt['searchResults']['retailHotelModels'][0]['infositeUrl']
            temp_dic = {}
            temp_dic['hotels'] = ep_url
            tem = json.dumps(temp_dic)
            #print 'pp2', source, req['req']['id'], data
            sql = 'update hotelinfo_jac_2018_03_20 set expedia=%s where id =%s'
            cur2.execute(sql, (tem, req['req']['id']))
            #print source, ep_url, req['req']['id']
            db.commit()


def map():
    pool = Pool(100)
    db = MySQLdb.connect(host='10.10.230.206', user='mioji_admin', passwd='mioji1109', db='source_info',charset='utf8')
    cur = db.cursor()
    try:
        cur.execute('select url,id from hotelinfo_jac_2018_03_20 where url is not null')
        r = cur.fetchall()
        #print len(r)
    except Exception as e:
        #print 'err',e
        db.rollback()
    finally:
        cur.close()
        db.close()
    lis = []
    for url,id in r:
        dic = json.loads(url)
        if 'Agoda' in dic:
            lis.append(('Agoda',id,dic['Agoda']))
        if 'Booking.com' in dic:
            lis.append(('Booking',id,dic['Booking.com']))
        if 'Hotels.com' in dic:
            lis.append(('Hotels', id, dic['Hotels.com']))
        if 'Expedia.com' in dic:
            lis.append(('Expedia', id, dic['Expedia.com']))
            #print 'cs',type(dic['Expedia.com']),dic['Expedia.com']
    #print 'lenlis',len(lis)
    pool.map(map2, lis)
    pool.join()


def map2(args):
    import mioji.common.spider
    import mioji.common.pool
    mioji.common.spider.NEED_FLIP_LIMIT = False
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    mioji.common.pool.pool.set_size(1024)
    spider.slave_get_proxy = simple_get_socks_proxy
    spider.get_proxy = simple_get_socks_proxy
    task = Task(source='position')
    task.content = args
    positions = TestSpider(task)
    positions.task = task
    positions.crawl()


if __name__ == '__main__':
    map()
