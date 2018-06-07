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
            hotel_name = str(self.task.content[0][0])
            id = str(self.task.content[0][1])
            return {
                        'req': {
                                'req': id,
                                'url': 'https://www.google.com.hk/search?newwindow=1&safe=strict&ei=xQm7WsTQIMi18QW4vqz4BQ&hotel_occupancy=&q=' + hotel_name + '&oq=%E6%96%B0%E5%8A%A0%E5%9D%A1%E9%A6%99%E6%A0%BC%E9%87%8C%E6%8B%89%E5%A4%A7%E9%85%92%E5%BA%97+%28Shangri-la+Hotel+Singapore%29&gs_l=psy-ab.12...0.0.0.12258.0.0.0.0.0.0.0.0..0.0....0...1c..64.psy-ab..0.0.0....0.QSpaas2J-pE',
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
        res2 = data.xpath('//div[@class="lhpr-content-item"]')
        print res2,'temp_res',req['req']['req']
        dic = {}
        for j in res2[:-1]:
            res3 = j.xpath('div/a/@href')[0]
            source = j.xpath('div/a/img/@alt')[0]
            dic[source] = res3
            print source, res3
        dic2 = json.dumps(dic)
        print dic2
        sql = 'update hotelinfo_jac_2018_03_20 set url=%s where id =%s'
        cur2.execute(sql,(dic2,req['req']['req']))
        db.commit()


def map():
    pool = Pool(100)
    db = MySQLdb.connect(host='10.10.230.206', user='mioji_admin', passwd='mioji1109', db='source_info',charset='utf8')
    cur = db.cursor()
    try:
        cur.execute('select hotel_name,id from hotelinfo_jac_2018_03_20 where url is null')
        r = cur.fetchall()
        print len(r)
    except Exception as e:
        print 'err',e
        db.rollback()
    finally:
        cur.close()
        db.close()
    pool.map(map2, r)
    pool.join()


def map2(*args):
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
