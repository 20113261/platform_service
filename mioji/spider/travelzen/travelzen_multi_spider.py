#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

from travelzen_oneway_spider import TravelzenFlightSpider
from mioji.common.spider import Spider, request, PROXY_NONE
from TravelzenFlightParser import Handler
import json
from mioji.common import parser_except
from mioji.common.check_book.check_book_ratio import use_record_qid


class TravelzenMultiSpider(TravelzenFlightSpider):
    source_type = 'travelzen'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'travelzenMultiFlight': {'required': ['MultiFlight']}
    }

    def __init__(self, task=None):
        TravelzenFlightSpider.__init__(self, task=task)
        # 任务信息
        self.mode = 'OJ'
        self.verify_ticket = None

    def process_task(self):
        section = []
        task = self.task
        # Auth
        auth = json.loads(self.task.ticket_info['auth'])
        self.check_auth(auth)
        self.api = Handler(task, **auth)
        #
        legs = task.content.split('|')
        for leg in legs:
            dept_code, arr_code, dept_date = leg.split('&')
            section.append((dept_code, self.format_data_str(dept_date), arr_code))
        return section

    def targets_request(self):
        section = self.process_task()
        import json
        print json.dumps(section)

        req = self.api.get_post_parameters(self.mode, section, self.task.ticket_info)
        api_handler = self.api

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['MultiFlight'])
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

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['MultiFlight'])
        def req_rule():
            for ticket in self.verify_ticket:
                ticket[-1] = json.loads(ticket[-1][0:-5])
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


    def parse_MultiFlight(self, req, resp):
        if req['extra']['method'] == 'req_rule':
            t = req['extra']['ticket']
            others_info = t[-1]
            others_info['dev_change_rule'] = resp
            t[-1] = json.dumps(others_info) + '&NULL'
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
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_http_proxy
    httpset_debug()
    task = Task()
    # task.content = 'CKG&HAM&20170702&20170714'

    auth = {
            'api': 'http://apis.travelzen.com/service/flight/international',
            'account': '594a45163db1ee2040b8b51e',
            'passwd': '0j9dfzt3'
    }

    task.content = 'PEK&CDG&20171220|LON&PEK&20171226'
    task.ticket_info = {
        "v_seat_type": "E",
        'flight_no': 'KL4302_AF1641&KL1010_KL897',
        'auth': json.dumps(auth)
    }
    task.redis_key = 'default_redis_key'
    task.other_info = {}
    s = TravelzenMultiSpider()
    s.task = task
    s.crawl()
    print s.crawl()
    print json.dumps(s.result, ensure_ascii=False)
    
    # for item in s.result['MultiFlight']:
    #     print '=='*30
    #     print item

