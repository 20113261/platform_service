#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import json
import hashlib
import urllib
import urlparse
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment

FOR_FLIGHT_DATE = '%Y-%m-%dT%H:%M:%S'
cabins = {"E": 0, "P": 0, "B": 1, "F": 1}
cabin = {"Y": "经济舱", "S": "超值经济舱", "C": "公务舱", "F": "头等舱"}


class FliggyApiMultiFlightSpider(Spider):
    source_type = 'fliggyApiMultiFlight'
    targets = {'Flight': {'version': 'InsertRoundFlight2'}}
    old_spider_tag = {'fliggyApiMultiFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.trace_id = ''

    @staticmethod
    def sign(secret, parameters):
        if hasattr(parameters, 'items'):
            keys = parameters.keys()
            keys.sort()
            parameters = '%s%s%s' % (secret, str().join('%s%s' % (key, parameters[key]) for key in keys), secret)
        sign = hashlib.md5(parameters).hexdigest().upper()
        return sign

    def parse_content(self):
        content = self.task.content.split("|")
        con_a = content[0].split("&")
        con_b = content[1].split("&")
        city_code_a = con_a[0]
        city_code_b = con_a[1]
        city_code_c = con_b[0]
        city_code_d = con_b[1]
        date_a_b = "{}-{}-{}".format(con_a[2][:4], con_a[2][4:6], con_a[2][6:8])
        date_c_d = "{}-{}-{}".format(con_b[2][:4], con_b[2][4:6], con_b[2][6:8])
        return city_code_a, city_code_b, city_code_c, city_code_d, date_a_b, date_c_d

    def filter_attr(self, switch, all_ticket):
        tickets = []
        if switch:
            for i in range(len(all_ticket)):
                if str(bin(json.loads(all_ticket[i][32])['product_attr']))[-1] == "1":
                    tickets.append(all_ticket[i])
            return tickets
        else:
            return all_ticket

    @staticmethod
    def split_seg(_seg):
        return [_seg[i:i + (len(_seg) / 2)] for i in range(0, len(_seg), (len(_seg) / 2))]

    def filter_paykey(self, li):
        for l in li:
            l.others_info = re.findall('(.*?)\}&{', str(l.others_info))[0] + '}'
        return li

    def new_to_tuple(self, ticket):
        _n = list()
        for tic in ticket:
            n = tic.to_tuple()
            _n.append(n)
        return _n

    def seg(self, data):
        _seg = list()
        for i in range(0, 2):
            for seg in data['journeys']['journey'][i]['flight_segments']['flight_segment']:
                ms = MFlightSegment()
                ms.flight_no = seg['marketing_flight_no']
                ms.plane_type = seg.get('equip_type', 'NULL')
                ms.flight_corp = seg['marketing_airline']
                ms.seat_type = cabin[seg['cabin_class']]
                ms.real_class = seg['cabin_class']
                ms.dept_id = seg['dep_airport']
                ms.dest_id = seg['arr_airport']
                dept_date = seg['dep_time'].replace(' ', 'T')
                dest_date = seg['arr_time'].replace(' ', 'T')
                ms.set_dept_date(dept_date, FOR_FLIGHT_DATE)
                ms.set_dest_date(dest_date, FOR_FLIGHT_DATE)
                _seg.append(ms)
        return self.split_seg(_seg)

    def parse_flight(self, resp):
        offer_count = 0
        if hasattr(self.task, 'redis_key'):
            redis_key = self.task.redis_key
        others_info = dict()
        others_info['product_attr'] = dict()
        others_info['paykey'] = dict()
        all_ticket = list()
        content = resp['alitrip_ie_ticket_service_search_response']['result']['products']['product']
        for data in content:
            mf = MFlight(MFlight.OD_MULTI)
            mf.price = float((data['adult_price'] + data['adult_tax'])*0.01)
            mf.currency = 'CNY'
            mf.source = 'fliggyApi'
            mf.stopby = self.task.ticket_info['v_seat_type']
            others_info['paykey']['rate_key'] = list()
            others_info['paykey']['rate_key'].append(data['search_key'])
            others_info['paykey']['rate_key'].append(self.trace_id)
            others_info['paykey']['redis_key'] = redis_key
            others_info['paykey']['id'] = offer_count
            others_info['product_attr'] = data['product_attr']
            offer_count += 1
            mlg = MFlightLeg()
            mlg.others_info = json.dumps(others_info)
            mlb = MFlightLeg()
            mlb.others_info = json.dumps(others_info)
            _seg_list = self.seg(data)
            for g in _seg_list[0]:
                mlg.append_seg(g)
            for b in _seg_list[1]:
                mlb.append_seg(b)
            mf.legs.extend([mlg, mlb])
            all_ticket.append(mf.convert_to_mioji_flight())
        all_ticket = self.new_to_tuple(self.filter_paykey(all_ticket))
        all_ticket = self.filter_attr(True, all_ticket)
        return all_ticket

    def targets_request(self):
        if int(self.task.ticket_info['v_count']) > 10:
            raise parser_except.ParserException(12, "总人数不可超过10！")
        city_code_a, city_code_b, city_code_c, city_code_d, date_a_b, date_c_d = self.parse_content()
        try:
            redis_key = getattr(self.task, 'redis_key', '')
            f_type = redis_key.split('|', 1)[0]
            auth = json.loads(self.task.ticket_info['auth'])
            __secret = auth['app_secret']
            url = auth['url']
            self.trace_id = hashlib.md5(str(time.time())).hexdigest().upper()
            params = {
                'format': 'json',
                'timestamp': str(long(time.time() * 1000)),
                'app_key': auth['app_key'],
                'session': auth['session_key'],
                'sign_method': 'md5',
                'v': '2.0',
                'method': 'alitrip.ie.ticket.service.search'
            }
            public_params = {
                'passenger_num': int(self.task.ticket_info['v_count']),
                'trace_id': self.trace_id,
                'search_type': 1,
                "cabin_type": cabins[self.task.ticket_info['v_seat_type']],
                "trip_type": 3,
                "product_select_codes": 1
            }
        except Exception as e:
            logger.error(e)
            raise parser_except.ParserException(121, "检查一下auth信息")

        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            "Cache-Control": "no-cache",
            "Connection": "Keep-Alive"
        }
        od_info = [
            {
                "dep_city_code": str(city_code_a),
                "arr_city_code": str(city_code_b),
                "dep_date": date_a_b
            },
            {
                "dep_city_code": str(city_code_c),
                "arr_city_code": str(city_code_d),
                "dep_date": date_c_d
            }
        ]

        public_params['od_info'] = od_info
        body = {'search_rq': public_params}
        _tmp_params = params.copy()
        _tmp_params.update(body)
        logger.debug("BODY => {}".format(body))
        params['sign'] = self.sign(__secret, _tmp_params)
        path = '/router/rest?' + urllib.urlencode(params)

        @request(retry_count=0, proxy_type=PROXY_NONE, binding=['Flight'])
        def get_response():
            return {
                'req': {
                    'method': 'POST',
                    'url': urlparse.urljoin(url, path),
                    'headers': headers,
                    'data': urllib.urlencode(body)
                },
                'data': {'content_type': 'json'},
            }

        yield get_response

    def parse_Flight(self, req, resp):
        try:
            logger.debug("RESPONSE: {}".format(json.dumps(resp)[:200]))
            if resp['alitrip_ie_ticket_service_search_response']['result']['success']:
                return self.parse_flight(resp)
        except TypeError as e:
            raise parser_except.ParserException(29, e.message)
        except KeyError:
            raise parser_except.ParserException(122, "可能是session_key过期")


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.redis_key = "flightround|PVG&HKG&20180421&20180423|fliggyApi|E|10.10.95.29:8090|1519728836913|2daf4afcdadeeef9a844d07791e2687d|0"
    task.content = "BJS&PAR&20180401|ATH&BJS&20180422"
    task.other_info = {}
    task.ticket_info = {"v_count": 2,
                        'v_seat_type': 'E',
                        "auth": json.dumps({
                            "url": "http://gw.api.taobao.com/",
                            "port": 80,
                            "app_key": "24770167",
                            "app_secret": "d0e82af2fb815bcc299390c63b9b937b",
                            "session_key": "610240379c11e4312728b8af9a2909080baa8abb3a1ba5c3709925017"
                        })}
    spider = FliggyApiMultiFlightSpider(task)
    spider.task = task
    result_code = spider.crawl()
    print result_code, spider.result
