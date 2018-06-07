#!/usr/bin/python
#-*-coding:utf-8 -*-

"""
    :抓取携程国内酒店列表
"""
import sys
import re
import json
import traceback
from urlparse import urljoin
from datetime import datetime
from datetime import timedelta
from mioji.common.spider import Spider,PROXY_REQ,request
from mioji.common.task_info import Task
from collections import defaultdict
from mioji.common.logger import logger
from mioji.common.func_log import current_log_tag
from mioji.common.class_common import Room
from mioji.models.city_models import get_suggest_city


class CountryListHotelSpider(Spider):

    source_type = "ctripTWHotel"
    targets = {"hotel": {}}
    old_spider_tag = {'ctripcnListHotel': {'required': ['hotel']}}
    targets = {
        'hotel':{}
    }

    def __init__(self):
        super(CountryListHotelSpider, self).__init__()
        self.post_data = defaultdict(dict)
        self.headers = {
            "Origin": "http://hotels.ctrip.com",
            "Referer": "http://hotels.ctrip.com/hotel/paris192",
            "Host": "hotels.ctrip.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        self.base_url = 'http://hotels.ctrip.com/Domestic/Tool/AjaxHotelList.aspx'
        self.hotel_base_url = 'http://hotels.ctrip.com/hotel'

    def get_post_data(self):
        task_content = self.task.content
        self.cityId, room_num, nights, check_in = task_content.split('&')
        self_p = get_suggest_city('ctripcn', str(self.cityId)).split('|')
        self.check_in = str(datetime(int(check_in[:4]),int(check_in[4:6]),int(check_in[6:])))[:10]
        self.check_out = str(datetime(int(check_in[:4]),int(check_in[4:6]),int(check_in[6:]))+timedelta(int(nights)))[:10]
        self.city_id = self_p[2]
        self.room = room_num
        self.post_data['checkIn'],self.post_data['checkOut'],self.post_data['cityId'],self.post_data['RoomNum'],self.post_data['StartTime'], \
        self.post_data['DepTime'] = self.check_in,self.check_out,self.city_id,self.room,self.check_in,self.check_out
        self.post_data['page'] = 1

    def targets_request(self):
        self.get_post_data()

        @request(retry_count=5, proxy_type=PROXY_REQ, )
        def get_page_num():
            return {
                'req': {
                    'url':  self.base_url,
                    'method': 'post',
                    'data': self.post_data,
                    'headers': self.headers
                },
                'data': {'content_type': 'string'},
                'user_handler': [self.parse_page_num]
            }
        yield get_page_num

        @request(retry_count=5,proxy_type=PROXY_REQ,async=True,binding=['hotel'])
        def hotel_list():
            pages = []
            from copy import deepcopy
            for page in range(self.pages):
                self.post_data['page'] = page + 1
                pages.append({
                    'req': {
                        'url':  self.base_url,
                        'method': 'post',
                        'data': deepcopy(self.post_data),
                        'headers': self.headers
                    },
                    'data': {'content_type': 'json'},
                })
            return pages
        yield hotel_list

    def process_price(self, price_info):
        prices = {}
        price_info = json.loads(price_info)
        for price in price_info:
            city_id_key,price_key = price.keys()
            prices.update({price[city_id_key]:price[price_key]})
        return prices

    def parse_page_num(self,req,data):
        # prices_info = data['HotelMaiDianData']['value']['htllist']
        # prices_info = json.loads(prices_info)
        # print "数据类型：",type(prices_info)
        try:
            page_num = re.search(r'data-pagecount=([\d]+)',data).group(1)
            self.pages = int(page_num)
            print "分页数量：",page_num
        except:
            logger.debug(current_log_tag()+'【获取酒店分页数目失败】')

    def parse_hotel(self, req, data):
        # with open('resutl.json','w+') as result:
        #     result.write(json.dumps(data))
        try:
            hotels = []
            hotels_list = data['hotelPositionJSON']
            print "hotels_list:",len(hotels_list)
            prices_info = data['HotelMaiDianData']['value']['htllist']
            prices = self.process_price(prices_info)
            for hotel in hotels_list:
                hotel_info = Room()
                hotel_info.hotel_name = hotel['name']
                hotel_info.city = self.city_id
                hotel_info.source = 'ctrip'
                hotel_info.check_in = self.check_in
                hotel_info.check_out = self.check_out
                hotel_id = hotel['id']
                hotel_info.source_hotelid = hotel_id
                hotel_info.price = prices.get(hotel_id)
                hotel_info.currency = 'CNY'
                hotel_info.hotel_url = urljoin(self.hotel_base_url,hotel['url'])
                hotel_info.source_roomid = ''
                hotel_info.real_source = ''
                hotel_info.room_type = ''
                hotel_info.occupancy = ''
                hotel_info.bed_type = ''
                hotel_info.size = ''
                hotel_info.floor = ''
                hotel_info.rest = ''
                hotel_info.tax = ''
                hotel_info.pay_method = ''
                hotel_info.is_cancel_free = ''
                hotel_info.extrabed_rule = ''
                hotel_info.return_rule = ''
                hotel_info.change_rule = ''
                hotel_info.room_desc = ''
                hotel_info.others_info = ''
                hotel_info.guest_info = ''
                roomtuple = (hotel_info.hotel_name, hotel_info.city, hotel_info.source, hotel_info.source_hotelid, \
                 hotel_info.source_roomid, hotel_info.real_source, hotel_info.room_type, hotel_info.occupancy,
                 hotel_info.bed_type, hotel_info.size, \
                 hotel_info.floor, hotel_info.check_in, hotel_info.check_out, hotel_info.rest, hotel_info.price,
                 hotel_info.tax, hotel_info.currency, hotel_info.pay_method, \
                 hotel_info.is_extrabed, hotel_info.is_extrabed_free, hotel_info.has_breakfast,
                 hotel_info.is_breakfast_free, \
                 hotel_info.is_cancel_free, hotel_info.extrabed_rule, hotel_info.return_rule,
                 hotel_info.change_rule, hotel_info.room_desc, \
                 hotel_info.others_info, hotel_info.guest_info, hotel_info.hotel_url)
                hotels.append(roomtuple)
        except:
            logger.debug(current_log_tag()+'【解析错误】')
            print traceback.format_exc()
        return hotels


if __name__ == "__main__":
    # from mioji.common.utils import simple_get_http_proxy
    # from mioji.common import spider
    # spider.get_proxy = simple_get_http_proxy
    spider = CountryListHotelSpider()
    task = Task()
    task.content = '20043&1&3&20170830'
    task.ticket_info = {'cid':1,'occ':2}
    spider.task = task
    print spider.crawl()
    print len(spider.result['hotel'])
    # print spider.result['hotel']
    # for hotel in spider.result['hotel']:
    #     print hotel[0],hotel[14],hotel[15]

