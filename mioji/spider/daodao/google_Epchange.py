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
            dic = self.task.content[2]
            url = str(self.task.content[2].get('Expedia.com.vn',''))
            if not url:
                url = str(self.task.content[2].get('Expedia.com.tw'))
            print 'url_0:',url
            id = str(self.task.content[1])
            return {
                        'req': {
                                'dic': dic,
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
        dic = req['req']['dic']
        if source == 'Expedia':
            url = req['resp'].url
            print 'url_1:',url
            res = url.split('&')
            temp_dic = {}
            temp_dic['responsive'] = 'true'
            temp_dic['hsrIdentifier'] = 'HSR'
            temp_dic[res[0].split('?')[1].split('=')[0].encode('utf-8')] = res[0].split('?')[1].split('=')[1].encode('utf-8')
            for i in res[1:]:
                temp_dic[i.split('=')[0].encode('utf-8')] = i.split('=')[1].encode('utf-8')
            print temp_dic
            dic['Expedia.com'] = temp_dic
            res2 = json.dumps(dic)
            sql = 'update hotelinfo_jac_2018_03_20 set url=%s where id =%s'
            cur2.execute(sql, (res2,req['req']['id']))
            db.commit()


def map():
    pool = Pool(100)
    db = MySQLdb.connect(host='10.10.230.206', user='mioji_admin', passwd='mioji1109', db='source_info',charset='utf8')
    cur = db.cursor()
    try:
        cur.execute('select url,id from hotelinfo_jac_2018_03_20 where url is not null limit 21,1000')
        r = cur.fetchall()
        print len(r)
    except Exception as e:
        print 'err',e
        db.rollback()
    finally:
        cur.close()
        db.close()
    lis = []
    for url,id in r:
        dic = json.loads(url)
        if ('Expedia.com.vn' in dic) or ('Expedia.com.tw' in dic):
            lis.append(('Expedia',id,dic))
    print len(lis)
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
