#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import urllib
import json
import random
import time
import re
import traceback
from fliggy_flight_parse import Fliggy_flight_parse
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common.logger import logger
from copy import deepcopy
from functools import partial

cabintask = {'E': 0, 'P': 4, 'B': 2, 'F': 3}


class FliggyMultiFlightSpider(Spider):
    source_type = 'fliggyMultiFlight'
    targets = {'Flight': {'version': 'InsertMultiFlight'}}
    old_spider_tag = {'fliggyMultiFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.task_info = {}
        self.tickets = []
        self.task_info = None
        self.flight_numbers = []
        self.flight_operating_no = []
        self.mflight = None
        self.flag = False
        self.retry = 5
        self.retry_list = []
        self.s_retry = 5
        self.search_index = "https://www.fliggy.com/ijipiao"
        self.search_result = ('https://sijipiao.fliggy.com/ie/flight_search_result.htm?'
                              '&searchBy=1278'
                              '&searchJourney=[{"arrCityCode":"%s",'
                              '"depCityCode":"%s","depDate":"%s","selectedFlights":[]},'
                              '{"arrCityCode":"%s","depCityCode":"%s","depDate":"%s",'
                              '"selectedFlights":[]}]&tripType=2')

    def targets_request(self):
        # 处理这些信息
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')
        flights = self.task.content.split('|')
        dept_flight = flights[0].split('&')
        dc1 = dept_flight[0]
        ac1 = dept_flight[1]
        dt1 = dept_flight[2][0:4] + '-' + dept_flight[2][4:6] + '-' + dept_flight[2][6:8]
        dest_flight = flights[1].split('&')
        dc2 = dest_flight[0]
        ac2 = dest_flight[1]
        dt2 = dest_flight[2][0:4] + '-' + dest_flight[2][4:6] + '-' + dest_flight[2][6:8]
        print dc1, ac1, dt1, dc2, ac2, dt2

        @request(retry_count=3, proxy_type=PROXY_REQ, async=False,
                 new_session=True)
        def visit_search_index():
            """访问航班搜索页面"""
            search_entrance = [
                "https://www.baidu.com/s?ie=utf-8&wd=%E9%A3%9E%E7%8C%AA",
                "https://www.sogou.com/web?query=%E9%A3%9E%E7%8C%AA",
                "https://www.so.com/s?ie=utf-8&fr=so.com&src=home_so.com&q=%E9%A3%9E%E7%8C%AA"
            ]
            page = {
                "req": {
                    "url": self.search_index,
                    "method": "get",
                    "headers": {
                        "referer": random.choice(search_entrance)
                    }
                },
            }
            return [page]

        def get_result_url():
            return self.search_result % (ac1, dc1, dt1, ac2, dc2, dt2)

        yield visit_search_index

        base_url = 'https://sijipiao.fliggy.com/ie/flight_search_result_poller.do?src=filter&supportMultiTrip=true&searchBy=1280&searchJourney='

        fex = '[{"arrCityCode":"%s","depCityCode":"%s","depDate":"%s","selectedFlights":[]},{"arrCityCode":"%s","depCityCode":"%s","depDate":"%s"}]' % (ac1, dc1, dt1, ac2, dc2, dt2)
        # searchCabinType : 0: 全部    1：经济     2：商务/头等
        cabin = self.task.ticket_info.get('v_seat_type', 0)
        if cabin == 'E': cabin = 1
        elif cabin == 'F' or cabin == 'B': cabin = 2
        fex2 = '&tripType=2&searchCabinType={}&agentId=-1&searchMode=0&b2g=0&formNo=-1&cardId=&needMemberPrice='.format(cabin)
        query_url = base_url + urllib.quote(fex) + fex2
        _referer = get_result_url()
        @request(retry_count=4, proxy_type=PROXY_REQ)
        def get_first_flight():
            """获取搜索结果"""
            page = {
                'req': {'url': query_url,
                        'method': 'get',
                        'headers': {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
                            "referer": _referer
                        }},
                'user_handler': [self.parse_first_Flight]
            }
            return page

        yield get_first_flight
        while self.flag and self.retry > 0:
            logger.error('被封禁，剩余重试次数' + str(self.retry))
            yield get_first_flight
            self.retry -= 1
        if self.retry == 0 and self.flag:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, '代理被封禁')

        flight_no = self.task.ticket_info.get('flight_no', None)
        if not flight_no:
            self.first_flight = sorted(self.first_data, key=lambda _: _.price + _.tax)[:5]
        else:
            if '&' in flight_no:
                first, second = flight_no.split('&')
            else:
                first = self.task.ticket_info.get('flight_no', None)
                second = self.task.ticket_info.get('ret_flight_no', None)
            for f in self.first_data:
                if first in '_'.join(_.flight_no for _ in f.legs[0].segments):
                    self.first_flight = [f]

        @request(retry_count=4, proxy_type=PROXY_REQ, async=True, binding=self.parse_Flight)
        def get_second_flight():
            pages = []
            fex3 = '&tripType=2&searchCabinType={}&agentId=-1&searchMode=1&b2g=0&formNo=-1&cardId=&needMemberPrice=true'.format(
                cabin)
            for f in self.first_flight:
                selected = []
                for seg in f.legs[0].segments:
                    _ = {"marketFlightNo":seg.flight_no,"flightTime":str(seg.dept_date),"depAirportCode":seg.dept_id,"arrAirportCode":seg.dest_id,"marketingAirlineCode":seg.flight_corp,"codeShare":False,"depTerm":"","arrTerm":""}
                    selected.append(_)
                selected = json.dumps(selected)
                # selected = '[{"marketFlightNo":"PC294","operatFlightNo":"","flightTime":"2018-01-24 16:05:00","depCityCode":"SJJ","arrCityCode":"IST","depAirportCode":"SJJ","arrAirportCode":"SAW","marketingAirlineCode":"PC","operatingAirlineCode":"","codeShare":false,"depTerm":"","arrTerm":""},{"marketFlightNo":"PC331","operatFlightNo":"","flightTime":"2018-01-25 10:25:00","depCityCode":"IST","arrCityCode":"BUD","depAirportCode":"SAW","arrAirportCode":"BUD","marketingAirlineCode":"PC","operatingAirlineCode":"","codeShare":false,"depTerm":"","arrTerm":""}]'
                fex = '[{"arrCityCode":"%s","depCityCode":"%s","depDate":"%s","selectedFlights":%s},{"arrCityCode":"%s","depCityCode":"%s","depDate":"%s","selectedFlights":[]}]' % (ac1, dc1, dt1, selected, ac2, dc2, dt2)
                query_url = base_url + urllib.quote(fex) + fex3
                pages.append({
                    'req': {'url': query_url,
                            'method': 'get',
                            'headers': {
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
                                              "referer": _referer
                            },
                            'flight': f
                    },
                })
            return pages
        yield get_second_flight
        while self.retry_list and self.s_retry > 0:
            url, flight = self.retry_list.pop()

            @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=self.parse_Flight)
            def retry_parse():
                return {
                    'req': {'url': url,
                            'method': 'get',
                            'headers': {
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0'},
                            'flight': flight
                            }
                }

            yield retry_parse
            self.s_retry -= 1
        if self.s_retry == 0 and self.retry_list:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, '代理被封禁')


    def parse_first_Flight(self, req, resp):
        resp = resp.decode('unicode_escape')
        resp = str(resp)
        # resp = resp.replace('{0:', '{"0":', 1000)
        # resp = resp.replace(',1:', ',"1":', 1000)
        response = re.compile(r"{.*}").findall(resp)[0].decode('string_escape')
        resp = response.replace(r'{0:', '{"0":').replace(r',1:', ',"1":')
        cabin = self.task.ticket_info.get('v_seat_type', 'E')
        try:
            resp = json.loads(resp)
        except:
            self.flag = True
            return
        if not resp:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, '代理无效')
        if 'url' in resp:
            # 被封禁了
            self.flag = True
            return
        self.first_request_success = 1
        try:
            parser = Fliggy_flight_parse()
        except KeyError:
            self.retry_list.append((req['req']['url'], req['req']['flight']))
            return
        # parse_result = parser.parse_flight_no_dt(resp, cabin, flight_no_list)
        self.first_data = parser.parse_multi_first(resp, setype=cabin)
        self.flag = False

    def parse_Flight(self, req, resp):
        all_flights = []
        try:
            parser = Fliggy_flight_parse()
        except KeyError:
            self.retry_list.append((req['req']['url'], req['req']['flight']))
            return
        resp = resp.decode('unicode_escape')
        resp = str(resp)
        # resp = resp.replace('{0:', '{"0":', 1000)
        # resp = resp.replace(',1:', ',"1":', 1000)
        response = re.compile(r"{.*}").findall(resp)[0].decode('string_escape')
        resp = response.replace(r'{0:', '{"0":').replace(r',1:', ',"1":')
        try:
            resp = json.loads(resp)
        except:
            self.flag = True
            return
        if not resp:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, '代理无效')
        if 'url' in resp:
            # 被封禁了
            self.retry_list.append((req['req']['url'], req['req']['flight']))
            return
        cabin = self.task.ticket_info.get('v_seat_type', 'E')
        first_flight = req['req']['flight']
        for f in resp['data']['flightItems']:
            flight_copy = deepcopy(first_flight)
            parser.process_mflight(flight_copy, f, cabin, '')
            all_flights.append(flight_copy.convert_to_mioji_flight().to_tuple())
        self.flag = False
        return all_flights


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new
    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    flight_no_list = [
        'PS288_PS127&SU2111_SU204',
        'MU5509_MU767&AA128_AA1022']

    result_count = 0
    for i in [1]:
        task = Task()
        task.content = 'BJS&PAR&20180301|ATH&BJS&20180322'
        task.ticket_info = {'v_seat_type': 'B', 'flight_no': 'PS288_PS127'}
        spider = FliggyMultiFlightSpider()

        spider.task = task
        result_code = spider.crawl()
        print result_code
        print json.dumps(spider.result, ensure_ascii=False)
        print spider.result
        print len(spider.result['Flight'])
    print '总共成功次数：', result_count
