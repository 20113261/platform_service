#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re, json
from urlparse import urljoin
from mioji.common import parser_except
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.models.city_models import get_suggest_city

from utils import generate_page_post_data
import hotellist_parse
import datetime
from datetime import timedelta
import re

host = 'https://www.agoda.com'
page_url = 'https://www.agoda.com/api/zh-cn/Main/GetSearchResultList'
DATE_F = '%Y-%m-%d'


def create_param(task_p, self_p):
    param = {"pagetypeid": "1", "origin": "CN",
             "cid": "-1", "tag": "", "gclid": "", "aid": "130243", "userId": "60f86c50-206a-47e4-93c1-e9007045a669",
             "languageId": "8", "sessionId": "j0qg12urhmuz0nh0oje3sjof", "htmlLanguage": "zh-cn",
             "checkIn": task_p.format_check_in(DATE_F), "checkOut": task_p.format_check_out(DATE_F),
             "los": "1",  "adults": task_p.adult, "children": "0",
             "priceCur": "CNY", "hotelReviewScore": "5", "ckuid": "60f86c50-206a-47e4-93c1-e9007045a669"}
    return param


class HotelListSpider(Spider):
    source_type = 'agodaListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room4'}
    }

    # 设置上不上线 unable
    # unable = True

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'agodaListHotel': {'required': ['room']}
    }

    def targets_request(self):
        if self.task.ticket_info.get('is_new_type'):
            hotel_url = self.task.ticket_info.get('suggest')
            night = self.task.ticket_info.get('stay_nights')
            check_in = self.task.ticket_info.get('check_in')
            adult = self.task.ticket_info.get('occ')
            self.user_datas['check_in'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10]
            self.user_datas['check_out'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + timedelta(int(night)))[
                                           :10]
            if self.task.ticket_info.get('suggest_type') == 1:
                hotel_url = re.sub(r'(checkIn=)[0-9]+-[0-9]+-[0-9]+', '\g<1>' + self.user_datas['check_in'], hotel_url)
                hotel_url = re.sub(r'(checkOut=)[0-9]+-[0-9]+-[0-9]+', '\g<1>' + self.user_datas['check_out'], hotel_url)
                url = re.sub(r'(adults=)[0-9]+', '\g<1>' + adult, hotel_url)
                param = ''
            else:
                suggest_json = json.loads(self.task.ticket_info.get('suggest'))
                param = {"pagetypeid": "1", "origin": "CN",
                         "cid": "-1", "tag": "", "gclid": "", "aid": "130243",
                         "userId": "60f86c50-206a-47e4-93c1-e9007045a669",
                         "languageId": "8", "sessionId": "j0qg12urhmuz0nh0oje3sjof", "htmlLanguage": "zh-cn",
                         "checkIn": self.user_datas['check_in'], "checkOut": self.user_datas['check_out'],
                         "los": "1", "adults": adult, "children": "0",
                         "priceCur": "CNY", "hotelReviewScore": "5", "ckuid": "60f86c50-206a-47e4-93c1-e9007045a669"}
                url = urljoin(host,suggest_json['Url'])
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]
                task_p = creat_hotelParams(self.task.content)
                self.user_datas['mjcity_id'] = mjcity_id
                suggest_city = get_suggest_city('agoda',mjcity_id)
                self_p = suggest_city.get('suggest')
                is_new_type = suggest_city.get('is_new_type')
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            if is_new_type == 0:
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
                param = create_param(task_p, self_p)

                if self_p.get('Url'):
                    url = host + self_p['Url']
                elif self_p.get('ResultUrl'):
                    url = host + self_p['ResultUrl']
            else:
                self.user_datas['check_in'] = str(task_p.check_in)[:10]
                self.user_datas['check_out'] = str(task_p.check_out)[:10]
                adult = str(task_p.adult)
                hotel_url = self_p.get('url')
                hotel_url = re.sub(r'(checkIn=)[0-9]+-[0-9]+-[0-9]+', '\g<1>' + self.user_datas['check_in'], hotel_url)
                hotel_url = re.sub(r'(checkOut=)[0-9]+-[0-9]+-[0-9]+', '\g<1>' + self.user_datas['check_out'],
                                   hotel_url)
                url = re.sub(r'(adults=)[0-9]+', '\g<1>' + adult, hotel_url)
                param = ''

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            return {'req': {'url': url, 'params': param},
                    'data': {'content_type': self.convert_first_page_as_json},
                    'user_handler': [self.parse_pages_info]}

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=["hotel", 'room'])
        def pages_reqtues():
            count = self.user_datas.get('pageCount', 1)
            page_param = self.user_datas['page_param']
            pages = []
            for p in xrange(1, count + 1):
                page_p = dict(page_param)
                page_p['PageNumber'] = p
                pages.append({'req': {'method': 'post', 'url': page_url, 'data': page_p},
                              'data': {'content_type': 'json'}})
            return pages

        return [first_page, pages_reqtues]

    def convert_first_page_as_json(self, req, data):
        pattern = re.compile(
            r'<script type="text/javascript" data-selenium="script-initparam">.*?var initialResults = (.*?)};', re.S)
        json_data = pattern.findall(data)[0] + '}'
        return json.loads(json_data)

    def parse_pages_info(self, req, data):
        self.user_datas['pageCount'] = data.get('TotalPage', 1)
        self.user_datas['page_param'] = generate_page_post_data(data)

    def parse_hotel(self, req, data):
        return hotellist_parse.parse_hotels_hotel(data)

    def parse_room(self, req, data):
        return hotellist_parse.parse_hotels_room(self.user_datas['mjcity_id'], data)


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy
    task.content = '51510&3&1&20181217'
    data_j = json.loads(
        """{"Url": "/zh-cn/pages/agoda/default/DestinationSearchResult.aspx?asq=u2qcKLxwzRU5NDuxJ0kOFxqHdHTGnNdI9yWnaEfnwQcQJD2%2fNHszlFMi2tp4vVOB8mVK8fkSAOx2ZIHnX2Ag5V8bUIEYWE8tV3keNC66CWTK47iOh8Nf24dVym2HIYcvl%2fcp%2f5TrCM%2bEGhl2nfdvCE2wRRv2HOYfYs2mYaqGSsLX4QMXCYJiePqgMRkEIu76eDBwFQdoJlrlBlQ7ke3qCXfmG1btJ4rXIGquB6HLlWMk%2b9Gkq6xP6zPgJW3WR8nz&city=15470&tick=636258690000", "ObjectTypeID": 5, "SuggestionType": 2, "Name": "巴黎", "ObjectID": 15470}""")
    task.ticket_info = {
        'is_new_type': False,
        'suggest_type': 2,
        'suggest': json.dumps(data_j),
        'check_in': '20170930',
        'stay_nights': '2',
        'occ': '2'
    }
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{}] }
    spider = HotelListSpider(task)

    res = spider.crawl()
    print spider.result
    print res