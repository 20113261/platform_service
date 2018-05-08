#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import json
import time
import requests
from mioji.common.class_common import MFlight as Flight
from mioji.common.class_common import RoundFlightLeg as Leg
from mioji.common.class_common import MFlightSegment as Segment

HOST = 'https://httpbin.org'
HOST = 'http://14.23.156.154:9114'

# partnerid: miojisit
# key: bacca05f-d94a-4ca0-9898-d9b70cf7d7b3

cabin2code = {
    'Economy': '经济舱',
    'PremiumEconomy': '超级经济舱',
    'Business': '商务舱',
    'First': '头等舱'
}


class Handler:
    def __init__(self, host=HOST, partnerId='miojisit', appid='miojisit',
                 appsecurity='bacca05f-d94a-4ca0-9898-d9b70cf7d7b3',*args,**kwargs):
        self.partnerId = partnerId
        self.appid = appid
        self.appsecurity = appsecurity
        self.create_session_url = host + '/flight/create-session'
        self.poll_url = host + '/flight/polling'
        self.currentSessionId = None
        self.poll_limit = 6
        self.session_life = 60
        self.page_index = 0
        self.page_size = 100
        self.is_oneway = False
        self.flight_list = []
        self.start_time = None

    def poll_setting(self, poll_limit, session_life):
        self.poll_limit = poll_limit
        self.session_life = session_life

    def get_token(self, req_data):
        """
        生成md5,先做大写后MD5
        :param req_dict: 存放的参数的dict
        :return: MD5码
        """
        str_md5 = json.dumps(req_data, sort_keys=True).replace(' ', '')
        m = hashlib.md5()
        str_md5 = str_md5 + self.appsecurity
        m.update(str_md5)
        return_str = m.hexdigest().lower()
        return return_str

    def get_headers(self, req_data):
        headers = {
            'appid': self.appid,
            'token': self.get_token(req_data)
        }
        return headers

    def get_proxy(self):
        return {
            'http': '10.10.95.29:8080',
            'https': '10.10.95.29:8080'
        }

    def get_cabin(self, req_type):
        cabin_map = {
            'E': 'Economy',
            'B': 'Business',
            'F': 'First',
            'P': 'PremiumEconomy'
        }
        return cabin_map[req_type]

    def build_search_scheme(self, content, ticket_info):
        tmp_content = content.split("|")
        len_tmp = len(tmp_content)
        igola_sg_list = []
        for content_item in tmp_content:
            segment_args_list = content_item.split("&")
            if len(segment_args_list) == 3:
                if len_tmp == 1:
                    self.is_oneway = 'one_flight'
                else:
                    self.is_oneway = 'multi_flight'
                # single flight and mutli flight
                tmp_sg = {"departPlace": segment_args_list[0],
                          "destination": segment_args_list[1],
                          "departDate": segment_args_list[2]
                          }
                igola_sg_list.append(tmp_sg)
            elif len(segment_args_list) == 4:
                self.is_oneway = 'round_flight'
                # return flight
                tmp_sg_a = {"departPlace": segment_args_list[0],
                            "destination": segment_args_list[1],
                            "departDate": segment_args_list[2]
                            }
                # a b segment
                tmp_sg_b = {"departPlace": segment_args_list[1],
                            "destination": segment_args_list[0],
                            "departDate": segment_args_list[3]
                            }
                igola_sg_list.append(tmp_sg_a)
                igola_sg_list.append(tmp_sg_b)
            else:
                raise Exception('Invalid search scheme')
        cabin = self.get_cabin(ticket_info.get('v_seat_type', 'E'))
        post_data = {
            "lang": "ZH",  # 表2
            "currency": "CNY",  # ISO
            "partnerId": self.partnerId,  #
            "cabinClass": cabin,  # Economy*, PremiumEconomy, Business, First
            "flightsItems": igola_sg_list  # v1.5 doc search flight items params
        }
        return post_data

    def create_session(self, content, ticket_info, redis_key):
        post_data = self.build_search_scheme(content, ticket_info)
        headers = self.get_headers(post_data)
        proxies = self.get_proxy()
        resp = requests.post(self.create_session_url, json=post_data,
                             headers=headers, proxies=proxies)
        resp_val = json.loads(resp.text)
        self.create_session_call_back(resp_val, redis_key=redis_key)

    def get_create_parameter(self, content, ticket_info):
        post_data = self.build_search_scheme(content, ticket_info)
        headers = self.get_headers(post_data)
        return self.create_session_url, headers, post_data

        # self.create_session_call_back(resp_val, redis_key=redis_key)

    def create_session_call_back(self, resp, *args, **kwargs):
        if resp['resultCode'] != 200:
            raise
        self.currentSessionId = resp['sessionId']
        self.start_time = time.time()
        self.start_poll(*args, **kwargs)

    def build_poll_scheme(self):
        scheme_base = {
            "sessionId": self.currentSessionId,
            "partnerId": self.partnerId,
            # "sortType": "duration",
            "sortOrder": "asc",
            "pageIndex": self.page_index,
            "pageSize": self.page_size,
            "filters": self.get_poll_filter()
        }
        return scheme_base

    def get_poll_filter(self):
        search_filter = {
            # "airports": [{
            #     "org": "CAN",
            #     "voyage": 0
            # }],
            # "unions": "skyteam;oneworld",
            # "airlines": "CZ",
            "stops": "1;2"
        }
        return search_filter

    def get_poll_parameter(self):
        post_data = self.build_poll_scheme()
        headers = self.get_headers(post_data)
        return self.poll_url, post_data, headers

    def poll_data(self, **kwargs):
        _, post_data, headers = self.get_poll_parameter()
        proxies = self.get_proxy()
        resp = requests.post(self.poll_url, json=post_data,
                             headers=headers, proxies=proxies)
        resp = json.loads(resp.text)
        val = self.parse(resp, **kwargs)
        return val

    def start_poll(self, **kwargs):
        self.start_time = time.time()
        failure_count = 0
        while True:
            if self.is_end() or failure_count > 2:
                break
            tmp_list = self.poll_data(**kwargs)
            self.flight_list.extend(tmp_list)
            time.sleep(self.poll_limit)
            failure_count += 1

    def get_result(self):
        return self.flight_list

    def parse(self, raw_data, redis_key='None'):
        if not raw_data or 'result' not in raw_data or not raw_data['result']:
            return []

        self.page_index += 1
        flight_count = 0
        flight_list = []
        for raw_flight in raw_data['result']:
            flight = Flight()
            flight.price = raw_flight['sellPrice']
            flight.currency = 'CNY'
            flight.supplier = raw_flight['supplier']
            flight.unique_id = raw_flight['flightId']
            cabin = raw_flight['cabinClass']

            for raw_leg in raw_flight['flightDetails']:
                is_direct = raw_leg['directFlight']
                leg = Leg()
                len_seg = len(raw_leg['segments'])
                leg.return_rule = "退改政策以最终线下沟通结果为准。"
                leg.change_rule = "退改政策以最终线下沟通结果为准。"
                for raw_segment in raw_leg['segments']:
                    segment = Segment()
                    segment.flight_no = raw_segment['flightNo']
                    segment.plane_type = raw_segment['planeStyle']
                    segment.flight_corp = raw_segment['airline']
                    segment.dept_id = raw_segment['org']['code']
                    segment.dest_id = raw_segment['dst']['code']
                    segment.seat_type = cabin2code[cabin]
                    segment.real_class = cabin
                    segment.set_dept_date(
                        raw_segment['org']['time'], '%Y-%m-%d %H:%M')
                    segment.set_dest_date(
                        raw_segment['dst']['time'], '%Y-%m-%d %H:%M')
                    leg.append_seg(segment)
                flight.append_leg(leg)
                # 变成 之前的flight
                others_info = {
                    'paykey': {
                        'redis_key': redis_key,
                        'id': flight_count,
                        'flightId': raw_flight['flightId']
                    },
                }

            if self.is_oneway == 'one_flight':
                print '进入单程解析'
                flight = flight.to_flight()
                others_info['paykey']['type'] = 'flight_one_way'
                flight.return_rule = "退改政策以最终线下沟通结果为准。" 
                flight.change_rule = flight.return_rule
                flight.others_info = json.dumps(others_info)

            elif self.is_oneway == 'multi_flight':
                print '进入联程解析'
                flight = flight.to_multi_flight()
                others_info['paykey']['type'] = 'flight_multi'
                flight.others_info = json.dumps(others_info) + "&NULL"
            elif self.is_oneway == 'round_flight':
                print '进入往返解析'
                flight = flight.to_round_flight()
                others_info['paykey']['type'] = 'flight_return'
                flight.others_info = json.dumps(others_info)
                flight.return_rule = "退改政策以最终线下沟通结果为准。"
                flight.change_rule = "退改政策以最终线下沟通结果为准。"
            else:
                raise Exception(27, '未进入正确的解析')
            flight.source = 'igola::igola'
            flight_count += 1
            flight_list.append(flight)
        return flight_list

    def is_end(self, bol, now):
        if bol == 1:
            return (time.time() - self.start_time > self.session_life) or (now - self.start_time > 60)
        else:
            return time.time() - self.start_time > self.session_life


if __name__ == '__main__':
    from mioji.common.utils import httpset_debug

    httpset_debug()

    ow_task = ['CHI&SHA&20170820',
               'CHI&PAR&20170820',
               'CHI&LON&20170820',
               'CHI&YTO&20170820',
               'SHA&CHI&20170820',
               'SHA&PAR&20170820',
               'SHA&LON&20170820',
               'SHA&YTO&20170820',
               'PAR&CHI&20170820',
               'PAR&SHA&20170820',
               'PAR&LON&20170820',
               'PAR&YTO&20170820',
               'LON&CHI&20170820',
               'LON&SHA&20170820',
               'LON&PAR&20170820',
               'LON&YTO&20170820',
               'YTO&CHI&20170820',
               'YTO&SHA&20170820',
               'YTO&PAR&20170820',
               'YTO&LON&20170820']
    rd_task = [
        'CHI&SHA&20171220&20171224',
        # 'CHI&PAR&20170820&20170910',
        # 'CHI&LON&20170820&20170910',
        # 'CHI&YTO&20170820&20170910',
        # 'SHA&CHI&20170820&20170910',
        # 'SHA&PAR&20170820&20170910',
        # 'SHA&LON&20170820&20170910',
        # 'SHA&YTO&20170820&20170910',
        # 'PAR&CHI&20170820&20170910',
        # 'PAR&SHA&20170820&20170910',
        # 'PAR&LON&20170820&20170910',
        # 'PAR&YTO&20170820&20170910',
        # 'LON&CHI&20170820&20170910',
        # 'LON&SHA&20170820&20170910',
        # 'LON&PAR&20170820&20170910',
        # 'LON&YTO&20170820&20170910',
        # 'YTO&CHI&20170820&20170910',
        # 'YTO&SHA&20170820&20170910',
        # 'YTO&PAR&20170820&20170910',
        # 'YTO&LON&20170820&20170910']
    # 'CAN&NYC&20170830&20170920'
    ]
    result_list = []
    for task in rd_task:
        h = Handler()
        h.create_session(task, {'v_seat_type': 'E'}, redis_key='default_key')
        s = h.get_result()
        result_list.append(len(s))
    print result_list
