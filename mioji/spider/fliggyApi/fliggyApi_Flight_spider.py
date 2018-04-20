#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import json
import hashlib
import urllib
import urlparse
import logging
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
FOR_FLIGHT_DATE = '%Y-%m-%dT%H:%M:%S'
cabins = {"E": 0, "P": 0, "B": 1, "F": 1}
cabin = {"Y": "经济舱", "S": "超值经济舱", "C": "公务舱", "F": "头等舱"}


class FliggyApiSpider(Spider):
    source_type = 'fliggyApiFlight'
    targets = {'Flight': {'version': 'InsertNewFlight'}}
    old_spider_tag = {'fliggyApiFlight': {'required': ['Flight']}}

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
        content = self.task.content.split("&")
        dept_code = content[0]
        dest_code = content[1]
        dept_time = "{}-{}-{}".format(content[2][:4], content[2][4:6], content[2][6:8])
        return dept_code, dest_code, dept_time

    def filter_attr(self, switch, all_ticket):
        tickets = []
        if switch:
            for i in range(len(all_ticket)):
                if str(bin(json.loads(all_ticket[i][32])['product_attr']))[-1] == "1":
                    tickets.append(all_ticket[i])
            return tickets
        else:
            return all_ticket

    def targets_request(self):
        if int(self.task.ticket_info['v_count']) > 10:
            raise parser_except.ParserException(12, "总人数不可超过10！")
        dept_code, dest_code, dept_time = self.parse_content()
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
                "trip_type": 1,
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

        od_info = {
            "dep_city_code": str(dept_code),
            "arr_city_code": str(dest_code),
            "dep_date": dept_time
        }
        public_params['od_info'] = od_info
        body = {'search_rq': public_params}
        _tmp_params = params.copy()
        _tmp_params.update(body)
        logging.info("BODY => {}".format(body))
        params['sign'] = self.sign(__secret, _tmp_params)
        path = '/router/rest?' + urllib.urlencode(params)

        @request(retry_count=0, proxy_type=PROXY_NONE, binding=['Flight'])
        def get_response():
            return {
                'req': {
                    'method': 'POST',
                    'url': urlparse.urljoin(url, path),
                    'headers': headers,
                    'data': urllib.urlencode(body),
                },
                'data': {'content_type': 'json'},
            }

        yield get_response

    def parse_flight(self, resp):
        offer_count = 0
        if hasattr(self.task, 'redis_key'):
            redis_key = self.task.redis_key
        all_ticket = list()
        others_info = dict()
        others_info['paykey'] = dict()
        others_info['product_attr'] = dict()
        for data in resp:
            mf = MFlight(MFlight.OD_ONE_WAY)
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
            ml = MFlightLeg()
            ml.others_info = json.dumps(others_info)
            for seg in data['journeys']['journey'][0]['flight_segments']['flight_segment']:
                ms = MFlightSegment()
                ms.flight_no = seg['marketing_flight_no']
                print ms.flight_no
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
                ml.append_seg(ms)
            mf.append_leg(ml)
            all_ticket.append(mf.convert_to_mioji_flight().to_tuple())
            all_ticket = self.filter_attr(True, all_ticket)
        return all_ticket

    def parse_Flight(self, req, resp):
        logging.info("RESPONSE: {}".format(json.dumps(resp)[:200]))
        try:
            if resp['alitrip_ie_ticket_service_search_response']['result']['success']:
                content = resp['alitrip_ie_ticket_service_search_response']['result']['products']['product']
                return self.parse_flight(content)
        except KeyError:
            raise parser_except.ParserException(122, "可能是session_key过期")


if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.redis_key = 'flight|10001|20001|20180129|20180130|CA934'
    task.content = u"PVG&NRT&20180424"
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
    spider = FliggyApiSpider(task)
    spider.task = task
    result_code = spider.crawl()
    print result_code
    print spider.result
