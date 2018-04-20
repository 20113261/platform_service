#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.models.city_models import get_suggest_city
from mioji.common import parser_except
import datetime
import re
from datetime import timedelta
import hotellist_parse
from urlparse import unquote
import urllib
import urlparse
import json

DATE_F = '%Y-%m-%d'
URL = 'https://zh.hotels.com/search/listings.json'
PAGE_URL = 'https://zh.hotels.com/search.do?'


def crate_params(task_p, self_p):
    param = {
        'destination-id': '{p[destinationId]}'.format(p=self_p),
        'q-check-in': task_p.format_check_in(DATE_F),
        'q-check-out': task_p.format_check_out(DATE_F),
        'q-destination': '{p[caption]}'.format(p=self_p),
        'resolved-location': 'CITY:{p[destinationId]}:UNKNOWN:UNKNOWN'.format(p=self_p),
        'q-rooms': task_p.rooms_count,
        'pg': 1}

    rooms_info = task_p.rooms_required

    for index in xrange(0, task_p.rooms_count):
        pre = 'q-room-{0}-'.format(index)
        param[pre + 'adults'.format(index)] = rooms_info[index].adult
        param[pre + 'children'.format(index)] = rooms_info[index].child
        for c_indx in xrange(0, rooms_info[index].child):
            param[pre + 'child-{0}-age'.format(c_indx)] = rooms_info[index].child_age[c_indx]
    return param


class HotelListSpider(Spider):
    source_type = 'hotelsListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room4'},
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'hotelsListHotel': {'required': ['room']}
    }

    def process_url(self,hotel_url):
        query = urlparse.parse_qs(urlparse.urlsplit(hotel_url).query)
        self.user_datas['destination-id'] = query.get('destination-id', [''])[0]
        # if self.user_datas['destination-id']:
        self.user_datas['q-destination'] = query.get('q-destination', [''])[0].decode('utf8')
        self.user_datas['resolved-location'] = query.get('resolved-location', [''])[0]
        self.user_datas['sort-order'] = query.get('sort-order', [''])[0]

        def creat_Params():
            param = {
                'destination-id': self.user_datas['destination-id'],
                'q-check-in': self.user_datas['check_in'],
                'q-check-out': self.user_datas['check_out'],
                'q-destination': '{p[q-destination]}'.format(p=self.user_datas),
                # 'resolved-location': 'CITY:{p[destination-id]}:UNKNOWN:UNKNOWN'.format(p=self.user_datas),
                'resolved-location': self.user_datas['resolved-location'],
                'q-rooms': self.user_datas['night'],
                'pg': 1}
            return param

        params = creat_Params()

        if not self.user_datas['destination-id']:
            del params['destination-id']
            params.update(
                {
                    'resolved-location': self.user_datas['resolved-location'],
                    'sort-order': self.user_datas['sort-order']
                }
            )
        return params
    def targets_request(self):

        if self.task.ticket_info.get('is_new_type'):

            night = self.task.ticket_info.get('stay_nights')
            self.user_datas['night'] = night
            check_in = self.task.ticket_info.get('check_in')
            self.user_datas['check_in'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10]
            self.user_datas['check_out'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + timedelta(int(night)))[
                                           :10]
            self.user_datas['night'] = night
            self.user_datas['mjcity_id'] = 'NULL'
            self.user_datas['adult'] = self.task.ticket_info.get('occ')
            if self.task.ticket_info.get('suggest_type') == 1:
                hotel_url = self.task.ticket_info.get('suggest')
                params = self.process_url(hotel_url)
            else:
                suggest_json = json.loads(self.task.ticket_info.get('suggest'))
                params = {
                    'destination-id': '{p[destinationId]}'.format(p=suggest_json),
                    'q-check-in': self.user_datas['check_in'],
                    'q-check-out': self.user_datas['check_out'],
                    'q-destination': '{p[caption]}'.format(p=suggest_json),
                    'resolved-location': 'CITY:{p[destinationId]}:UNKNOWN:UNKNOWN'.format(p=suggest_json),

                    'pg': 1}
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]

                task_p = creat_hotelParams(self.task.content)
                self.user_datas['mjcity_id'] = mjcity_id
                suggest_city = get_suggest_city('hotels',mjcity_id)
                is_new_type = suggest_city.get('is_new_type')
                self_p = suggest_city.get('suggest')
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            if is_new_type == 0:
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
                params = crate_params(task_p, self_p)
                self.user_datas['night'] = task_p.night
                self.user_datas['adult'] = task_p.adult

            else:
                hotel_url = self_p.get('url')
                self.user_datas['night'] = task_p.night
                self.user_datas['adult'] = task_p.adult
                self.user_datas['check_in'] = str(task_p.check_in)[:10]
                self.user_datas['check_out'] = str(task_p.check_out)[:10]
                params = self.process_url(hotel_url)
            self.user_datas['check_in'] = task_p.check_in
            self.user_datas['check_out'] = task_p.check_out


        @request(retry_count=3, proxy_type=PROXY_REQ, binding=["hotel", 'room'])
        def first_page():
            return {'req': {'url': URL, 'params': params},
                    'data': {'content_type': 'json'},
                    'user_handler': [self.parse_next_page]}

        yield first_page

        if self.user_datas['has_next']:
            @request(retry_count=3, proxy_type=PROXY_REQ, binding=["hotel", 'room'])
            def next_pages():
                while self.user_datas['has_next'] and self.user_datas['next_page']:
                    print "next_page:", self.user_datas['next_page']
                    yield {
                        'req': {"url": URL + self.user_datas['next_page']},
                        'data': {'content_type': 'json'},
                        'user_handler': [self.parse_next_page]
                    }

            yield next_pages

    def parse_next_page(self, req, data):
        # print "请求数据：",data
        if "error" in data['data']['body'] and "暫時無法載入更多酒店" in data['data']['body']['error']['message']:
            raise parser_except.ParserException(22, "暫時無法載入更多酒店")
        group_type = data.get('data', {}).get('body', {}).get('searchResults').get('pagination', {}) \
            .get('pageGroup', None)
        if not cmp(group_type, 'EXPEDIA_IN_POLYGON'):

            self.user_datas['next_page'] = data.get('data', {}).get('body', {}) \
                .get('searchResults', {}).get('pagination', {}).get('nextPageUrl', None)
            self.user_datas['has_next'] = self.user_datas['next_page'] != None

        else:
            self.user_datas['next_page'] = None

    def parse_hotel(self, req, data):
        # group_type = data.get('data', {}).get('body', {}).get('searchResults').get('pagination', {}) \
        #     .get('pageGroup', None)
        # 解析部分错误过滤，已修正
        return hotellist_parse.parse_hotelList_hotel(data)
        # if not cmp(group_type, 'EXPEDIA_IN_POLYGON'):
        #     return hotellist_parse.parse_hotelList_hotel(data)
        # else:
        #     pass

    def parse_room(self, req, data):
        group_type = data.get('data', {}).get('body', {}).get('searchResults').get('pagination', {}) \
            .get('pageGroup', None)
        if not cmp(group_type, 'EXPEDIA_IN_POLYGON'):
            return hotellist_parse.parse_hotelList_room(data, self.user_datas['check_in'], self.user_datas['check_out'],
                                                        self.user_datas['night'], self.user_datas['adult'],
                                                        self.user_datas['mjcity_id'])
        else:
            pass


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import json

    task = Task()
    task.content = '60443&2&1&20180401'
    # data_j = json.loads(
    #     """{"name": "罗马", "redirectPage": "DEFAULT_PAGE", "longitude": 12.479289444295746, "caption": "<span class='highlighted'>罗马</span>, <span class='highlighted'>意大利</span>", "destinationId": "712491", "latitude": 41.90378883593621, "landmarkCityDestinationId": null, "type": "CITY", "geoId": "1000000000000003023"}""")
    # data_j = json.loads('''[{"url": "https://www.hotels.cn/search.do?resolved-location=CITY:10414535:UNKNOWN:UNKNOWN&destination-id=10414535&q-destination=\u51b2\u6c38\u826f\u90e8\u5c9b, \u65e5\u672c"}]''')
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy

    import mioji.common.pages_store

    mioji.common.pages_store.STORE_TYPE = 'ufile'

    spider.slave_get_proxy = simple_get_socks_proxy
    # task.extra['hotel'] = {'check_in':'20170505', 'nights':1, 'rooms':[{}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2, 'child_age':[0, 6]}] * 2}
    # print json.dumps(task.extra['hotel'])
    # task.content = u'60087&2&1&20170801'

    spider = HotelListSpider()
    spider.task = task
    print spider.crawl(cache_config={'enable': False})
    print len(spider.result['hotel'])
    print spider.result, spider.code
    # print spider.first_url()
    # spider@Mioji
