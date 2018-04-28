# -*- coding:utf-8 -*-

"""
@author: fengyufei
@date: 2018-01-30
@purpose: ctrip POI 景点，餐厅，购物 列表页
"""
from mioji.common.logger import logger
from mioji.common import parser_except
from mioji.common.func_log import current_log_tag
from mioji.common.task_info import Task
from mioji.common.parser_except import PROXY_INVALID, PROXY_FORBIDDEN
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from lxml import html
from collections import defaultdict
from urlparse import urljoin
import traceback
import re

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
}


class CtripViewSpider(Spider):
    source_type = "PoiListInfo"
    page_sight_url = "http://you.ctrip.com/sight/{}.html"
    page_restaurant_url = "http://you.ctrip.com/restaurantlist/{}.html"
    page_shop_url = "http://you.ctrip.com/shoppinglist/{}.html"
    three_page_url = [page_sight_url, page_restaurant_url, page_shop_url]

    # 抓取数据： 景点，餐厅，购物列表
    targets = {
        'POIlist': {},
    }

    old_spider_tag = {
        'ctripPoi_list': {'required': ['POIlist']}
    }

    def __init__(self):
        super(CtripViewSpider, self).__init__()
        self.header = headers
        self.sight_url = None
        self.restaurant_url = None
        self.shop_url = None
        self.page_num = []
        self.finished = False
        self.nowurl = ''
        self.nowindex = 0
        self.page = 1

    def targets_request(self):
        tid = 'demo'
        used_times =3

        @request(retry_count=5, proxy_type=PROXY_REQ,store_page_name="num_first_{}_{}".format(tid, used_times))
        def num_first():
            cont = self.task.content
            url1 = self.page_sight_url.format(cont)
            url2 = self.page_restaurant_url.format( cont)
            url3 = self.page_shop_url.format(cont)
            three_url = [url1,url2,url3]
            #print three_url
            urls = [{
                'req': {'url': url},
                'data': {'content_type': 'html'},
                'user_handler': [self.get_sight_page_num]
            } for url in three_url]
            return urls
        yield num_first

        @request(retry_count=5, binding=['POIlist'],proxy_type=PROXY_REQ,async = True,store_page_name="get_info_{}_{}".format(tid, used_times))
        def get_info():
            all_page = []
            num = int(self.page)
            for i in range(num,num+10):
                if self.finished or self.page > int(self.page_num[self.nowindex]):
                    self.finished = True
                    return []
                all_page.append({
                    'req': {'url':self.nowurl.format(self.task.content + '/s0-p' + str(i)) },
                    'data': {'content_type': 'html'},
                    })
            self.page += 10   
            return all_page

        for i in range(len(self.page_num)):
            self.nowurl = self.three_page_url[i]
            self.nowindex = i
            self.finished = False
            while self.finished==False:
                #print '-------VON-----',i
                yield get_info



    def get_sight_page_num(self, req, data):
        root = data
        try :
            pages = data.xpath("//b[@class='numpage']")[0].text_content()
            self.page_num.append(pages)
        except Exception as e:
            self.page_num.append('1')
            print e

    def parse_POIlist(self, req, data):
        url = 'http://you.ctrip.com'
        root = data
        temp_list = set()
        max_num = 1
        try:
            max_num = root.xpath("//b[@class='numpage']")[0].text_content()
        except :
            self.page = 1
            self.finished = True
        try:
            lists = root.xpath('//div[@class="list_mod2"]')
            for lis in lists:
                href = lis.xpath('div[@class="leftimg"]/a/@href')[0]
                sp = href.split('/')
                poi_id = sp[-1].split('.')[0]
                ptype = sp[1]
                temp_list.add(
                        (poi_id, ptype, url+href )
                        )

            print "抓取到数据的数量：", len(temp_list)
            return list(temp_list)
        except:
            logger.debug(
                current_log_tag() + '【{0}解析错误】{1}'.format(self.parse_POIlist.__name__, parser_except.PARSE_ERROR))



if __name__ == "__main__":
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    from mioji.common.pool import pool

    # spider.slave_get_proxy = simple_get_socks_proxy
    spider.NEED_FLIP_LIMIT = False
    pool.set_size(104)
    task = Task()
    spider = CtripViewSpider()
    task.content = 'newyork248'
    task.content = 'salamanca1956'

    spider.task = task
    spider.crawl()
    print spider.code
    print spider.result
    print spider.page_num
    print len(spider.result['POIlist'])
