#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
@Time : 17/5/24 下午3:38
@Author : Li Ruibo

'''
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re, json, urllib, random, time, datetime
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.task_info import Task
from mioji.common.parser_except import ParserException
from utils import FlightParser, seat_type_to_queryparam

seat_dict = {'ECO': '经济舱', 'BUS': '商务舱', 'FST': '头等舱', 'PEC': '超级经济舱'}
class_code_dict = {'E': 'ECO', 'B': 'BUS', 'F': 'FST', 'P': 'PEC'}

HOST = 'https://www.skyscanner.net'

SUGGEST_URL = HOST + '/dataservices/geo/v2.0/autosuggest/UK/en-GB/{0}?' \
                     'isDestination=false&ccy=GBP&limit_taxonomy=City,Airport'
MAIN_URL = HOST + '/transport/d/{p1}/{t1}/{p2}/{p3}/{t2}/{p4}?adults={adults}&children=0&adultsv2=1&childrenv2=' \
                  '&infants=0&cabinclass={cabin}&ref=home&currency=CNY#results'
DATA_URL = HOST + '/dataservices/flights/pricing/v3.0/search/?geo_schema=skyscanner&carrier_schema=skyscanner' \
                  '&response_include=query;deeplink;segment;stats;fqs;pqs;_flights_availability'


def first_header():
    return {
        'Host': 'www.skyscanner.net',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'}


def price_api_header():
    return {
        'Host': 'www.skyscanner.net',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'ADRUM': 'isAjax:true',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json; charset=utf-8',
        'X-Skyscanner-ChannelId': 'website',
        'X-Distil-Ajax': 'azezcavtdrrxfqrtbw',
        'X-Skyscanner-TrackId': 'null',
        'X-Skyscanner-Traveller-Context': 'null',
        'X-Skyscanner-DeviceDetection-IsMobile': 'false',
        'X-Skyscanner-DeviceDetection-IsTablet': 'false',
        'X-Skyscanner-MixPanelId': '6fe6a359-ba53-4bfd-b92d-ba426e5c6d3b',
        'X-Skyscanner-ViewId': '6fe6a359-ba53-4bfd-b92d-ba426e5c6d3b',
        'X-Requested-With': 'XMLHttpRequest'}


class SkyscannerMultiFlightSpider(Spider):

    source_type = "skyscannerMultiFlight"
    targets = {
        'Flight': {'version': 'InsertMultiFlight'}
    }
    old_spider_tag = {
        'skyscannerMultiFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        super(SkyscannerMultiFlightSpider, self).__init__(task)

    def targets_request(self):

        con1, con2 = self.task.content.split('|')
        infos1 = con1.split('&')
        infos2 = con2.split('&')
        self.user_datas['p1'] = infos1[0]
        self.user_datas['p2'] = infos1[1]
        self.user_datas['p3'] = infos2[0]
        self.user_datas['p4'] = infos2[1]

        ticket_info = self.task.ticket_info
        cabin = seat_type_to_queryparam(ticket_info.get('v_seat_type', 'E'))
        adults = ticket_info.get('v_count', 1)

        t1 = infos1[2]
        t1 = '-'.join([t1[:4], t1[4:6], t1[6:]])
        self.user_datas['t1'] = t1
        t2 = infos2[2]
        t2 = '-'.join([t2[:4], t2[4:6], t2[6:]])
        self.user_datas['t2'] = t2

        @request(retry_count=5, proxy_type=PROXY_REQ, async=True)
        def suggest_request():

            return [
                {'req': {'url': SUGGEST_URL.format(self.user_datas[key])},
                 'req_id': {'place_id': key, 'query_key': self.user_datas[key]},
                 'user_handler': [self.place_convert],
                 'data': {'content_type': 'json'},
                 }
                for key in ['p1', 'p2', 'p3', 'p4']]

        @request(retry_count=5, proxy_type=PROXY_FLLOW)
        def first_request():
            """
            task.content 'PEK&YYZ&20170610|YVR&PEK&20170620'
            :return: 
            """
            main_page_url = MAIN_URL.format(p1=self.user_datas['p1'], p2=self.user_datas['p2'],
                                            p3=self.user_datas['p3'],
                                            p4=self.user_datas['p4'], t1=self.user_datas['t1'],
                                            t2=self.user_datas['t2'],
                                            cabin=cabin, adults=adults).strip()
            self.user_datas['url_first'] = main_page_url
            header = first_header()
            return {'req': {'url': main_page_url, 'headers': header, 'method': 'get'},
                    'data': {'content_type': 'string'},
                    'user_handler': [self.__get_info_from_first_page]
                    }

        @request(retry_count=5, proxy_type=PROXY_FLLOW, binding=['Flight'])
        def second_request():
            params = {"market": "UK", "currency": "CNY", "locale": "en-GB",
                      "cabin_class": cabin, "prefer_directs": False,
                      "trip_type": "multi-destination",
                      "legs":
                          [{"origin": self.user_datas['p1'], "destination": self.user_datas['p2'],
                            "date": self.user_datas['t1']},
                           {"origin": self.user_datas['p3'], "destination": self.user_datas['p4'],
                            "date": self.user_datas['t2']}],
                      "adults": adults, "child_ages": [],
                      "options": {"include_unpriced_itineraries": True, "include_mixed_booking_options": False}}
            post_data = json.dumps(params)

            cookie = 'X-Mapping-fpkkgdlh={X_Mapping_fpkkgdlh}; ' \
                     'scanner={scanner};' \
                     'ssab={ssab};' \
                     'ssculture={ssculture};' \
                     'ssassociate=; ' \
                     'abgroup={abgroup}; ' \
                     'X-Mapping-rrsqbjcb={X_Mapping_rrsqbjcb}' \
                .format(X_Mapping_rrsqbjcb=self.user_datas['X-Mapping-rrsqbjcb'],
                        abgroup=self.user_datas['abgroup'],
                        X_Mapping_fpkkgdlh=self.user_datas['X-Mapping-fpkkgdlh'],
                        scanner=self.user_datas['scanner'],
                        ssab=self.user_datas['ssab'],
                        ssculture=self.user_datas['ssculture'])

            header = price_api_header()
            header['Cookie'] = cookie
            header['Referer'] = self.user_datas['first_url']

            return {'req': {'url': DATA_URL, 'headers': header, 'method': 'POST', 'data': post_data},
                    'data': {'content_type': 'json'}}

        yield suggest_request
        yield first_request
        if self.user_datas.get('scanner') == '' or self.user_datas.get('ssab') == '':
            raise Exception
        else:
            yield second_request

    def parse_Flight(self, req, data):
        total = data.get('stats', {}).get('itineraries', {}).get('total', {}).get('count', 0)
        if "itineraries" not in str(data):
        # 如果没找到联程行程信息，就抛22错误
            raise ParserException(ParserException.PROXY_INVALID)
        if total <= 0:
            raise ParserException(ParserException.EMPTY_TICKET)
        load_count = len(data.get('itineraries', []))
        if load_count < total:
            # 先使用抛22 达到poll的方式
            raise ParserException(ParserException.PROXY_INVALID)

        parser = FlightParser(data, self.task)
        return parser.parse()

    def place_convert(self, req, data):
        req_id = req['req_id']
        query_key = req_id['query_key']
        for item in data:
            r_place_id = item['PlaceId']
            if r_place_id.startswith(query_key):
                self.user_datas[req_id['place_id']] = r_place_id.lower()
                break

    def __get_info_from_first_page(self, req, data):
        self.user_datas['first_url'] = req['req']['url']
        cookies = req['resp'].cookies.items()
        for each_cookie in cookies:
            self.user_datas[each_cookie[0]] = each_cookie[1]


if __name__ == '__main__':
    task = Task()
    task.content = 'BJS&PAR&20170710|LON&BJS&20170718'
    task.source = 'skyscannermulti'
    import httplib
    from mioji.common.task_info import Task
    from mioji.common import spider
    from mioji.common.utils import simple_get_http_proxy

    # spider.get_proxy = simple_get_http_proxy

    task.source = "skyscannerround"
    task.ticket_info = {'v_count': 2, 'v_seat_type': 'F'}

    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    # 执行流程：
    # 1. 配置好task, Spider根据task初始化相应的参数
    # 2. 重写targets_request方法
    #   2.1 定义抓取链，并返回
    # 3. 调用基类crawl进行抓取seat_type
    #   3.1
    spider = SkyscannerMultiFlightSpider(task)
    print 'code', spider.crawl()
    print spider.result['Flight'][:20]
