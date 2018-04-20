#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from PKFareAPI import Handler
from mioji.common.check_book.check_book_ratio import use_record_qid

g_partner_id = 'TkgRsQ9kS+onyJy9VnSCl+Sj9PE='
g_partner_key = 'YmQzNTMxZDg1NzM1YTdhM2Y5ZWZlNzVkMmUzM2VhNWY='
# g_shopping_api= 'http://api.pkfare.com/shopping'
g_shopping_api = 'http://open.pkfare.com/apitest/shopping'
class PKfareFlightSpider(Spider):
    source_type = 'PKfare'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'pkfareFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.api = Handler(task)
        self.mode = 'OW'

    def format_data_str(self, date):
        return date[:4] + '-' + date[4:6] + '-' + date[6:]

    def process_task(self):
        task = self.task
        use_record_qid(unionKey='PKfare API', api_name="Shopping", task=task, record_tuple=[1, 0, 0])
        dept_code, arr_code, date = task.content.split('&')
        section = [(dept_code, self.format_data_str(date), arr_code)]
        req = self.api.get_request_parameters(section, self.task.ticket_info)

        return req

    def targets_request(self):
        req = self.process_task()

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['Flight'])
        def do_request():
            return {
                'req': req,
            }
        return [do_request]

    def parse_Flight(self, req, resp):
        json_str = self.api.decodeGzip(req['resp'].content)
        ret_dict = json.loads(json_str)

        if 'errorCode' not in ret_dict or ret_dict['errorCode'] != '0':
            if 'errorMsg' in ret_dict:
                if u'Partner is not exists.' == ret_dict['errorMsg'] or u'Illegal sign.' == ret_dict['errorMsg']:
                # raise parser_except.ParserException(parser_except.API_ERROR, u'返回错误:' + ret_dict['errorMsg'])
                    raise parser_except.ParserException(122, u'认证信息，认证失败')
                raise parser_except.ParserException(parser_except.API_ERROR, u'返回错误:' + ret_dict['errorMsg'])
            else:
                raise parser_except.ParserException(parser_except.API_ERROR, u'返回错误: 错误ID为' + ret_dict['errorCode'])

        if not ret_dict['data']:
            raise parser_except.ParserException(parser_except.API_ERROR, u'返回错误:' + ret_dict['errorMsg'])

        flight_list = self.api.parse_resp(self.mode, ret_dict, self.task.ticket_info)
        ret = [x.to_tuple() for x in flight_list]
        return ret



if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import httpset_debug
    import json

    httpset_debug()

    city_list = ['PAR', 'ROM', 'MIL', 'BCN', 'AMS', 'MUC', 'LON', 'FRA', 'ZRH', 'CPH', 'MOW', 'BJS', 'SHA', 'CAN', 'SZX', 'HKG', 'DXB', 'MNL', 'SEL', 'DOH', 'KUL', 'OSA', 'TYO', 'NGO', 'BKK', 'SIN', 'AUH', 'SYD', 'MEL', 'AKL', 'CAI', 'NBO', 'CAS', 'JNB', 'CPT', 'YTO', 'YVR', 'CHI', 'NYC', 'SFO', 'LAX', 'SEA', 'MEX', 'CUN', 'SAO', 'RIO', 'BUE']
    task = Task()
    task.redis_key = '123'
    # task.ticket_info = {'v_count':1, 'v_seat_type': 'E', 'v_age': '20_18_3_-1', "auth": json.dumps({"partner_id":"2+JvfTPfkn9+C4TYJplABQJfUJI=","partner_key":"OWI0M2I1231235OWNkZmZjZDg5MGZkYWU2OWE0ZWNkYmQ1MzQ=","url":"http://api.pkfare.com"})}
    # task.ticket_info = {'v_count':1, 'v_seat_type': 'E', 'v_age': '20_18_3_-1', "auth": json.dumps({"partner_id":"2+JvfTPfkn9+C4TYJplABQJfUJI=","partner_key":"OWI0M2I5OWNkZmZjZDg5MGZkYWU2OWE0ZWNkYmQ1MzQ=","url":"http://api.pkfare.com"})}
    task.ticket_info = {'v_count':1, 'v_seat_type': 'E', 'v_age': '20_18_3_-1', "auth": json.dumps({"partner_id":"2+JvfTPfkn9+C4TYJplABQJfUJI=","partner_key":"OWI0M2I5OWNkZmZjZDg5MGZkYWU2OWE0ZWNkYmQ1MzQ=","url":"http://api.pkfare.com"})}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'SEA&SFO&20171130'
    task.other_info = {}
    spider = PKfareFlightSpider(task)
    spider.task = task
    print spider.source_type
    print spider.crawl()
    print spider.result
