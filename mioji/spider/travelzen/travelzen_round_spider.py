#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
from TravelzenFlightParser import Handler
from mioji.common.spider import Spider, request, PROXY_NONE
from travelzen_oneway_spider import TravelzenFlightSpider
from mioji.common import parser_except
from mioji.common.check_book.check_book_ratio import use_record_qid


class TravelzenRoundSpider(TravelzenFlightSpider):
    source_type = 'travelzen'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'travelzenRoundFlight': {'required': ['RoundFlight']}
    }

    def __init__(self, task=None):
        TravelzenFlightSpider.__init__(self, task=task)
        # 任务信息
        self.mode = 'RT'

    def process_task(self):
        task = self.task
        use_record_qid(unionKey='travelzen', api_name="FlightSearchRequest", task=self.task, record_tuple=[1, 0, 0])
        # Auth
        auth = json.loads(self.task.ticket_info['auth'])
        self.check_auth(auth)
        self.api = Handler(task, **auth)
        #
        dept_code, arr_code, dept_date, return_date = task.content.split('&')
        section = [(dept_code, self.format_data_str(dept_date), arr_code),
                   (arr_code, self.format_data_str(return_date), dept_code)]
        return section

    def targets_request(self):
        section = self.process_task()

        req = self.api.get_post_parameters(self.mode, section, self.task.ticket_info)
        api_handler = self.api

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['RoundFlight'])
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

        @request(retry_count=1, proxy_type=PROXY_NONE, binding=['RoundFlight'])
        def req_rule():
            for ticket in self.verify_ticket:
                ticket[-2] = json.loads(ticket[-2])
                freight_rule_query_id = ticket[-2]['payInfo']['LimitQueryID']
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

    def parse_RoundFlight(self, req, resp):
        if req['extra']['method'] == 'req_rule':
            t = req['extra']['ticket']
            others_info = t[-2]
            others_info['dev_change_rule'] = resp
            t[-2] = json.dumps(others_info)
            return [t]

        section = req['extra']['section']
        ticket_info = req['extra']['ticket_info']
        flight_list = self.api.parse_resp(resp, self.mode, section, ticket_info)

        verify_flight_no = self.task.ticket_info.get('flight_no', None)
        verify_ret_flight_no = self.task.ticket_info.get('ret_flight_no', None)

        self.verify_ticket = []
        if verify_flight_no:
            ret = []
            for f in flight_list:
                tf = f.to_tuple()
                if tf[11] == verify_flight_no and tf[23] == verify_ret_flight_no:
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
    task.content = 'PEK&CDG&20180220&20180226'
    auth =  {
            'api': 'http://apis.travelzen.com/service/flight/international',
            'account': '594a45163db1ee2040b8b51e',
            'passwd': '0j9dfzt3'
    }
    # task.content = "SU201_SU3006&SU2581_SU204"
    task.ticket_info = {
        "v_seat_type": "经济舱|经济舱",
        'flight_no': 'KL898_KL1243',
        'ret_flight_no': 'KL1230_CZ768',
        'auth': json.dumps(auth)
    }
    task.redis_key = 'default_redis_key'
    task.other_info = {}
    s = TravelzenRoundSpider()
    s.task = task
    
    print s.crawl()
    print json.dumps(s.result, ensure_ascii=False)
