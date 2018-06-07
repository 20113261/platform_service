#!/usr/bin/env python
# -*- coding:utf-8 -*-

from mioji.common.spider import Spider,request
import execjs
import re
from collections import defaultdict
from mioji.common.spider import PROXY_REQ
from mioji.common.task_info import Task
import os
from toolbox import Common
import requests
from lxml import html
import sys
import json
source_map = {
    'agoda': 'agoda',
    'ctripintdaodao': 'ctrip',
    'bookingcn': 'booking',
    'hotelscom2': 'hotels',
    'elongintdaodaob2v': 'elong',
    'ctripdaodao': 'ctrip',
    'elongdaodao': 'elong'

}
sources = ['agoda','booking','ctrip','elong','expedia','hotels']
class CrawlHotelUrl(Spider):

    source_type = "daodaoListHotel"
    targets = {
        'hotel': {},
        'travelzoolist': {}
    }
    old_spider_tag = {
        'daodaoListHotel': {'required': 'hotel'}
    }
    def __init__(self):
        super(CrawlHotelUrl, self).__init__()

    def targets_request(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate, br',
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        @request(retry_count=5,async=False,)
        def first_req():

            url = self.task.ticket_info['url']
            return {
                'req':{'url':url,'headers':headers,'method':'get'},
                'data':{'content_type':'html'},
                'user_handler': [self.get_max_page]
            }

        yield first_req

        @request(retry_count=10,async=True,user_retry_count=10,proxy_type=PROXY_REQ)
        def second_req():
            max_page = self.user_datas['max_page']
            saves = []
            for page in xrange(0,max_page):
                url = self.task.ticket_info['url']
                url_list = url.split('-')
                insert_str = "oa{0}".format(page*30)
                url_list.insert(2,insert_str)
                url = '-'.join(url_list)
                saves.append(
                    {
                        'req': {'url': url,'method':'get','headers':headers},
                        'data': {'content_type': 'html'},
                        'user_handler': [self.get_location_position]
                    }
                )
            return saves

        yield second_req

        @request(retry_count=10,async=True,user_retry_count=10,proxy_type=PROXY_REQ,binding=['travelzoolist',])
        def three_req():
            urls = self.user_datas['ajax_url']
            saves = []
            for url in urls:
                saves.append(
                    {
                        'req': {'url':url[0],'method':'get','headers':headers},
                        'data': {'content_type': 'html'},
                        'hotel_name':url[1]
                    }
                )
            return saves
        yield three_req

        @request(retry_count=10, async=True, user_retry_count=10, proxy_type=PROXY_REQ, binding=['hotel', ])
        def four_req():
            hotels = self.result['travelzoolist']
            saves = []
            for seq, hotel in enumerate(hotels):
                for key, url in hotel.items():
                    if key in sources:
                        url = url.replace('www.tripadvisor.cn', 'www.tripadvisor.com')
                        saves.append(
                            {
                                'req': {'url': url, 'method': 'get', 'headers': headers},
                                'data': {'content_type': 'string'},
                                'source': key,
                                'sequence': seq,
                            }
                        )
            return saves

        yield four_req

    def get_max_page(self, req, data):
        root = data
        a_tag = root.xpath('//a[contains(@class,"pageNum last")]/text()')
        max_page = 1
        if a_tag:
            max_page = int(a_tag[0])
        self.user_datas['max_page'] = max_page

    def get_location_position(self, req, data):
        root = data
        results = []
        div_list = root.xpath('//div[contains(@class,"meta_listing ui_columns")]')
        for div in div_list:
            try:
                hotel_name = div.xpath('./div//div[@class="listing_title"]/a/text()')[0]
            except:
                try:
                    hotel_name = div.xpath('./div//div[contains(@class,"listing_title")]/div/a/text()')[0]
                except:
                    hotel_name = 'NULL'
            url = 'https://www.tripadvisor.cn/OverlayWidgetAjax?Mode=HOTELS_VIEW_ALL_OFFERS&metaReferer=Hotels&listPos={0}&locationId={1}'
            location_id = div.attrib.get('data-locationid')
            position = div.attrib.get('data-index')
            url = url.format(str(position).strip(),str(location_id).strip())
            results.append((url,hotel_name))
        self.user_datas['ajax_url'].extend(results)

    def parse_travelzoolist(self, req, data):
        hotel_name = req['hotel_name']
        root = data
        base_url = 'https://www.tripadvisor.cn'
        results = {}
        judge = Common.has_any(hotel_name,Common.is_chinese)
        if judge:
            results['hotel_name'] = hotel_name
        else:
            results['hotel_name_en'] = hotel_name
        div_list = root.xpath('//div/div')
        for div in div_list:
            source = div.attrib.get('data-provider','').strip().lower()
            if source_map.get(source):
                source = source_map[source]
            token_str = div.attrib.get('data-clicktoken','')
            if not token_str:
                continue
            source_url = get_source_url(token_str)
            url = ''.join([base_url,source_url])
            results[source] = url
        return results

    def parse_hotel(self, req, resp):
        source = req['source']
        sequence = req['sequence']
        real_url = None
        try:
            if source == 'agoda':
                agoda_json = re.search(r'window.searchBoxReact = (.*)(?=;)', resp).group(1)
                agoda_json = json.loads(agoda_json)
                url = agoda_json.get('recentSearches', [])[0].get('data', {}).get('url')
                base_url = 'https://www.agoda.com'
                real_url = ''.join([base_url, url])
            elif source == 'booking':
                root = html.fromstring(resp)
                real_url = root.xpath('//link[@rel="canonical"]/@href')[0]
            elif source == 'ctrip':
                ctrip_json = re.search(r'hotelPositionJSON: (.*)(?=,)', resp).group(1)
                ctrip_json = json.loads(ctrip_json)
                url = ctrip_json[0].get('url')
                base_url = "http://hotels.ctrip.com"
                real_url = ''.join([base_url, url])
            elif source == 'elong':
                hotel_id = re.search(r'hotelId":"([0-9]+)"', resp).group(1)
                real_url = 'http://ihotel.elong.com/{0}/'.format(hotel_id)

            elif source == 'hotel':
                root = html.fromstring(resp)
                hotel_id = root.xpath('//div[@id="listings"]//li')[0].attrib.get('data-hotel-id')
                real_url = "https://ssl.hotels.cn/ho{0}/?pa=1&q-check-out=2018-04-16&tab=description&q-room-0-adults=2&YGF=7&q-check-in=2018-04-15&MGT=1&WOE=1&WOD=7&ZSX=0&SYE=3&q-room-0-children=0".format(hotel_id)
        except:
            real_url = None

        self.result['travelzoolist'][sequence][source] = real_url

        return self.result['travelzoolist'][sequence]



def get_source_url(token_str):
    current_path = os.path.abspath(os.path.dirname(__file__))
    path = '/'.join([current_path,'decode_node.js'])
    with open(path) as f:
        js_str = f.read()
    phantomjs = execjs.get('PhantomJS')
    url = phantomjs.compile(js_str).call('decode',token_str)
    return url

if __name__ == "__main__":

    from mioji.common import spider
    from mioji.common.utils import simple_get_proxy
    spider.slave_get_proxy = simple_get_proxy
    crawl = CrawlHotelUrl()
    task = Task()
    task.ticket_info['url'] = 'https://www.tripadvisor.cn/Hotels-g28970-Washington_DC_District_of_Columbia-Hotels.html'
    crawl.task = task
    crawl.crawl()
    print crawl.result



