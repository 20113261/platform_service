#!/usr/bin/python
# -*- coding: UTF-8 -*-

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.task_info import Task
from mioji.common.parser_except import ParserException
from utils import RoundFlightParser
cabin_dict = {'E': 'economy', 'B': 'business', 'F': 'first', 'P': 'premiumeconomy'}


seat_dict = {'ECO': '经济舱', 'BUS': '商务舱', 'FST': '头等舱', 'PEC': '超级经济舱'}
class_code_dict = {'E': 'ECO', 'B': 'BUS', 'F': 'FST', 'P': 'PEC'}

HOST = 'https://www.skyscanner.com'

SUGGEST_URL = HOST + '/dataservices/geo/v2.0/autosuggest/US/en-US/{0}?' \
                     'isDestination=false&ccy=CNY&limit_taxonomy=City,Airport'
'/dataservices/geo/v2.0/autosuggest/US/en-US/pvg?isDestination=false&ccy=CNY'
MAIN_URL = HOST + '/transport/flights/{p1}/{p2}/{t1}/{t2}?adults={adults}&children=0&adultsv2={adults}&childrenv2=' \
                  '&infants=0&cabinclass={cabin}&ref=home&currency=CNY&market=US'
DATA_URL = HOST + '/dataservices/flights/pricing/v3.0/search/?geo_schema=skyscanner&carrier_schema=skyscanner' \
                  '&response_include=query;deeplink;segment;stats;fqs;pqs;_flights_availability'


def first_header():
    return {
        'Host': 'www.skyscanner.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',

        'Connection': 'keep-alive'}


def price_api_header():
    return {
        'Host': 'www.skyscanner.com',
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


class SkyscannerRoundFlightSpider(Spider):
    source_type = "skyscannerRoundFlight"
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }
    old_spider_tag = {
        'skyscannerRoundFlight': {'required': ['RoundFlight']}
    }

    def __init__(self, task=None):
        super(SkyscannerRoundFlightSpider, self).__init__(task)
        self.task = task

    @property
    def task(self):
        return self.__task

    @task.setter
    def task(self, task):
        self.__task = task

    def process_task(self):
        content = self.task.content
        ticket_info = self.task.ticket_info

        outbound_loc, inbound_loc, dept_day, return_day = content.split('&')

        self.cabin = cabin_dict[ticket_info.get('v_seat_type', 'E')]
        self.adults = ticket_info.get('v_count', 1)
        self.user_datas['p1'] = outbound_loc
        self.user_datas['p2'] = inbound_loc

        self.user_datas['t1'] = dept_day[2:]
        self.user_datas['t2'] = return_day[2:]


        self.dept_day = '-'.join([dept_day[:4], dept_day[4:6], dept_day[6:]])
        self.return_day = '-'.join([return_day[:4], return_day[4:6], return_day[6:]])

        self.poll_condition = True


    def targets_request(self):
        self.process_task()

        @request(retry_count=5, proxy_type=PROXY_REQ, async=True)
        def suggest_request():
            return [
                {'req': {'url': SUGGEST_URL.format(self.user_datas[key])},
                 'req_id': {'place_id': key, 'query_key': self.user_datas[key]},
                 'user_handler': [self.place_convert],
                 'data': {'content_type': 'json'},
                 }
                for key in ['p1', 'p2']]

        @request(retry_count=5, proxy_type=PROXY_FLLOW)
        def first_request():
            """
            :return:
            """
            main_page_url = MAIN_URL.format(p1=self.user_datas['p1'], p2=self.user_datas['p2'],
                                            t1=self.user_datas['t1'],
                                            t2=self.user_datas['t2'],
                                            cabin=self.cabin, adults=self.adults).strip()
            self.user_datas['url_first'] = main_page_url
            header = first_header()
            return {'req': {'url': main_page_url, 'headers': header, 'method': 'get'},
                    'data': {'content_type': 'string'},
                    'user_handler': [self.__get_info_from_first_page]
                    }

        @request(retry_count=5, proxy_type=PROXY_FLLOW, binding=['RoundFlight'])
        def second_request():
            params = {"market": "US", "currency": "CNY", "locale": "en-US",
                      "cabin_class": self.cabin, "prefer_directs": False,
                      "trip_type": "return",
                      "legs":
                          [
                              {
                                  "origin": self.user_datas['p1'],
                                  "destination": self.user_datas['p2'],
                                  "date": self.dept_day,
                                  "return_date": self.return_day
                              }
                          ],
                      "adults": self.adults, "child_ages": [],
                      "options": {
                          "include_unpriced_itineraries": True,
                          "include_mixed_booking_options": False
                      }
                      }
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

            return {'req':
                        {
                            'url': DATA_URL,
                            'headers': header,
                            'method': 'POST',
                            'data': post_data
                        },
                    'data':
                        {
                            'content_type': 'json'
                        },
                    'user_handler': [self.assert_resp]
                    }

        yield suggest_request
        yield first_request
        if self.user_datas.get('scanner') == '' or self.user_datas.get('ssab') == '':
            raise Exception
        else:
            #while self.poll_condition:
            yield second_request

    def assert_resp(self, req, data):
        total = data.get('stats', {}).get('itineraries', {}).get('total', {}).get('count', 0)
        if total <= 0:
            raise ParserException(ParserException.EMPTY_TICKET)
        load_count = len(data.get('itineraries', []))
        if load_count < total:
            raise ParserException(ParserException.PROXY_INVALID)

    def parse_RoundFlight(self, req, data):
        # with open('raw', 'w') as fp:
        #     fp.write(json.dumps(data, indent=2, ensure_ascii=False))
        try:
            parse_obj = RoundFlightParser(data, self.task)
            return parse_obj.parse()
        except:
            import traceback
            traceback.print_exc()
            return []

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
        assert cookies != []
        for each_cookie in cookies:
            self.user_datas[each_cookie[0]] = each_cookie[1]


if __name__ == '__main__':
    task = Task()
    task.content = 'BJS&CHI&20171002&20171015'
    task.source = 'skyscannerround'
    from mioji.common.task_info import Task

    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    spider.get_proxy = simple_get_socks_proxy

    # spider.get_proxy = simple_get_http_proxy

    task.ticket_info = {'v_count': 2, 'v_seat_type': 'P'}

    # 执行流程：
    # 1. 配置好task, Spider根据task初始化相应的参数
    # 2. 重写targets_request方法
    #   2.1 定义抓取链，并返回
    # 3. 调用基类crawl进行抓取seat_type
    #   3.1
    spider = SkyscannerRoundFlightSpider(task)
    print 'code', spider.crawl()
    print spider.result['RoundFlight'][:20]
