#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import re
import urllib
import json
import random
import socket
from datetime import datetime
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from ctrip_flight_lib import get_postdata, get_promotion, get_city_no
from common_lib import process_ages, seat_type_to_queryparam
from ctrip_moblie_flight_parse import Flight_moblie_parse
from mioji.common.phone_user_agent_list import moblie_user_agent

cabintask = {'E': 0, 'P': 4, 'B': 2, 'F': 3}
user_agent_list = moblie_user_agent
user_agent = user_agent_list[random.randint(0, 200)]
class CtripFlightSpider(Spider):
    # source_type = 'ctripFlight'
    # # 基础数据城市酒店列表 & 例行城市酒店
    # targets = {
    #     'Flight': {'version': 'InsertNewFlight'}
    # }

    # # 关联原爬虫
    # #   对应多个原爬虫
    # old_spider_tag = {
    #     'ctripFlight': {'required': ['Flight']}
    # }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.task_info = {}
        self.tickets = []
        self.task_info = None


    def targets_request(self):
        # 处理这些信息
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')
        @request(retry_count=1, proxy_type=PROXY_REQ, async=False, binding=self.parse_Flight)
        def get_flight_data():
            dc = self.task.content[:3]
            ac = self.task.content[4:7]
            dt = self.task.content[8:12] + '-' + self.task.content[12:14] + '-' + self.task.content[14:]
            seat_type = self.task.ticket_info.get('v_seat_type', 'E')
            saty = cabintask[seat_type]
            adult = self.task.ticket_info.get('adultNumber', 1)
            child = self.task.ticket_info.get('childNumber', 0)
            search_url = 'https://sec-m.ctrip.com/restapi/soa2/13212/flightListSearch'
            data_change = '{"preprdid":"","trptpe":1,"flag":8,"searchitem":[{"dccode":"%s","accode":"%s","dtime":"%s"}],"version":[{"Key":"170710_fld_dsmid","Value":"E"}],"psgList":[{"type":1,"count":1}],"token":"1","seat":%d,' % (
            dc, ac, dt, saty)
            data_not = '"segno":1,"head":{"cid":"","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":null,"extension":[{"name":"protocal","value":"http"}]},"contentType":"json"}'
            data = data_change + data_not
            self.url1 = 'http://m.ctrip.com/html5/flight/swift/international/%s/%s/%s/%d-%d-0' % (dc, ac, dt, adult, child)
            if saty == 0:
                self.url1 = 'http://m.ctrip.com/html5/flight/swift/international/%s/%s/%s/%d-%d-0' % (
                    dc, ac, dt, adult, child)
            else:
                self.url1 = 'http://m.ctrip.com/html5/flight/swift/international/%s/%s/%s/%d-%d-0' % (
                    dc, ac, dt, adult, child) + '?seat=%d' % saty
            pages = []
            pages.append({
                'req': {'url': search_url, 'headers': {'Referer': self.url1,
                                                       'User-Agent': user_agent,
                                                       'Content-Type': 'application/json',
                                                       'Connection': 'keep-alive'},
                        'method': 'post', 'data': data},
            })
            data = data.replace('"token":"1"', '"token":"2"')
            pages.append({
                'req': {'url': search_url, 'headers': {'Referer': self.url1,
                                                       'User-Agent': user_agent,
                                                       'Content-Type': 'application/json',
                                                       'Connection': 'keep-alive'},
                        'method': 'post', 'data': data},
            })
            return pages
        return [get_flight_data]

    def respon_callback(self, req, resp):
        print req, resp

    def parse_Flight(self, req, resp):
        cabin = self.task.ticket_info['v_seat_type']
        try:
            resp = json.loads(resp)
            if resp['ResponseStatus']['Ack'] != 'Success':
                raise parser_except.ParserException(23, '代理封禁')
            parser_moblie = Flight_moblie_parse()
            return parser_moblie.parse_mo_flight(resp, cabin)
        except Exception as e:
            print e


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug
    import time

    # httpset_debug()

    ctrip_list = ['BJS&PAR&20170930',
                  'MRY&SFO&20171002',
                  'ZRH&NCE&20171010',
                  'PAR&NCE&20171003',
                  'OSA&SHA&20171002',
                  ]
    for i in range(1):
        mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
        task = Task()
        task.content = ctrip_list[4]
        task.ticket_info = {'v_seat_type': 'E'}
        spider = CtripFlightSpider()
        spider.task = task
        print spider.crawl()
        print spider.result
        time.sleep(20)
