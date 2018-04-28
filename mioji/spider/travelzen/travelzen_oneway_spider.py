#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import json
from TravelzenFlightParser import Handler
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common import parser_except
from mioji.common.check_book.check_book_ratio import use_record_qid


class TravelzenFlightSpider(Spider):
    source_type = 'travelzen'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'travelzenFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.api = None
        self.mode = 'OW'
        # 验证的票
        self.verify_ticket = None

    def format_data_str(self, date):
        return date[:4] + '-' + date[4:6] + '-' + date[6:]

    def check_auth(self, auth):
        """ 检查认证信息是否为空 """
        check_auth = ('api', 'account', 'passwd')
        for i in check_auth:
            if i not in auth or auth[i] == '':
                raise parser_except.ParserException(121, u"却少认证信息")

    def process_task(self):
        # Auth
        task = self.task
        auth = json.loads(self.task.ticket_info['auth'])
        self.check_auth(auth)
        self.api = Handler(task, **auth)
        #
        dept_code, arr_code, date = task.content.split('&')
        section = [(dept_code, self.format_data_str(date), arr_code)]
        return section

    def targets_request(self):
        section = self.process_task()

        req = self.api.get_post_parameters(self.mode, section, self.task.ticket_info)
        api_handler = self.api

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['Flight'])
        def do_request():
            return {
                'req': req,
                'user_handler': [self.assert_resp],
                'data': {'content_type': 'json'},
                'extra': {
                    'method': 'search',
                    'section': section,
                    'ticket_info': self.task.ticket_info
                }
            }

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['Flight'])
        def req_rule():
            for ticket in self.verify_ticket:
                ticket[-1] = json.loads(ticket[-1])
                freight_rule_query_id = ticket[-1]['payInfo']['LimitQueryID']
                yield {
                    'req': api_handler.get_change_rule_params(freight_rule_query_id),
                    'data': {'content_type': 'json'},
                    'extra': {
                        'method': 'req_rule',
                        'ticket': ticket,
                    }
                }

        yield do_request
        if self.verify_ticket:
            yield req_rule

    def assert_resp(self, req, resp):
        if 'responseMetaInfo' not in resp or 'resultCode' not in resp['responseMetaInfo']:
            raise parser_except.ParserException(parser_except.API_NOT_ALLOWED, '返回格式错误:responseMetaInfo')
        elif resp['responseMetaInfo']['resultCode'] == "9008": # 对方返回 9008 是认证错误，转为122
            raise parser_except.ParserException(122, resp['responseMetaInfo']['reason'])
        elif resp['responseMetaInfo']['resultCode'] != "0":
            if '查询结果为空' in resp['responseMetaInfo']['reason']:
                raise parser_except.ParserException(parser_except.EMPTY_TICKET, 'API 提示无票')
            raise parser_except.ParserException(parser_except.API_NOT_ALLOWED,
                                                '返回出错:%s' % resp['responseMetaInfo']['reason'])

    def parse_Flight(self, req, resp):
        if req['extra']['method'] == 'req_rule':
            t = req['extra']['ticket']
            others_info = t[-1]
            others_info['dev_change_rule'] = resp
            t[-1] = json.dumps(others_info)
            return [t]
        use_record_qid(unionKey='travelzen', api_name="FlightSearchRequest", task=self.task, record_tuple=[1, 0, 0])
        section = req['extra']['section']
        ticket_info = req['extra']['ticket_info']
        flight_list = self.api.parse_resp(resp, self.mode, section, ticket_info)

        verify_flight_no = self.task.ticket_info.get('flight_no', None)
        self.verify_ticket = []
        if verify_flight_no:
            ret = []
            for f in flight_list:
                tf = f.to_tuple()
                if tf[0] == verify_flight_no:
                    self.verify_ticket.append(list(tf))
                else:
                    ret.append(tf)

        else:
            ret = [x.to_tuple() for x in flight_list]

        return ret


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import httpset_debug

    # httpset_debug()

    task = Task()
    auth =  {
        'api': 'http://apis.travelzen.com/service/flight/international',
        'account': '594a45163db1ee2040b8b51e',
        'passwd': '0j9dfzt3'
    }
    auth = {"api":"http://api.test.travelzen.com/tops-openapi-for-customers/service/flight/international",
            "account":"5941e779f47ba45ac43f84a2",
            "passwd":"g0e9ax1h1"}
    task.ticket_info = {
        'v_seat_type': 'E',
        'flight_no': 'MU9158_MU595',
        'auth': json.dumps(auth)
    }
    task.other_info = {}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'BJS&BER&20171216'
    task.redis_key = 'default_redis_key'
    spider = TravelzenFlightSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    import time
    time.sleep(2)
    print json.dumps(spider.result, ensure_ascii=False)
