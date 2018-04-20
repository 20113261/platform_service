#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_REQ, PROXY_FLLOW, PROXY_NEVER
from igola_api import Handler
from mioji.common.logger import logger
from mioji.common.check_book.check_book_ratio import use_record_qid

class igolaFlightSpider(Spider):
    source_type = 'igola'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'igolaFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.api = None
        self.failure_count = 0
        self.redis_key = None
        self.res_num = 0    #验证票信息判断
        self.bol = 0        #获取数据判断
        self.now = 0

    def pre_process(self):
        task = self.task
        use_record_qid(unionKey='Igola API', api_name="CreateSession", task=task, record_tuple=[1, 0, 0])
        ticket_info = task.ticket_info
        self.redis_key = task.redis_key
        content = task.content
        auth = json.loads(task.ticket_info.get('auth', '{}'))
        if not auth.get('appid', None) or not auth.get('partnerId', None) or not auth.get("appsecurity", None):
            raise Exception(121, "认证信息错误")
        self.api = Handler(**auth)
        self.api.poll_setting(10, 60)
        return content, ticket_info

    def targets_request(self):
        content, ticket_info = self.pre_process()
        create_session_url, headers, post_data = self.api.get_create_parameter(content, ticket_info)

        @request(retry_count=1, proxy_type=PROXY_NEVER)
        def create_session():
            requests_info = {
                'req': {
                    'url': create_session_url,
                    'method': 'post',
                    'headers': headers,
                    # 'data': json.dumps(post_data)，
                    'json': post_data,
                },
                'user_handler': [self.assert_resp, self.after_create_session],
                'data': {'content_type': 'json'},
                }
            logger.info("建立连接的完整请求为：{0}".format(requests_info))
            return requests_info

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['Flight'])
        def poll():
            self.api.start_time = time.time()
            while True:
                poll_url, post_data, headers = self.api.get_poll_parameter()
                req = {
                    'req': {
                        'url': poll_url,
                        'method': 'post',
                        'headers': headers,
                        # 'data': json.dumps(post_data)
                        'json': post_data,
                    },
                    'user_handler': [self.assert_resp, self.after_poll],
                    'data': {'content_type': 'json'},
                }
                yield req
                if self.api.is_end(self.bol, self.now) or self.failure_count ==2 or self.res_num == 1 :
                    break
                time.sleep(self.api.poll_limit)
        return [create_session, poll]


    def assert_resp(self, req, resp):
        if resp['resultCode'] == 6000:
            raise parser_except.ParserException(99, '源不支持此content')
        elif resp['resultCode'] == 3001:
            raise parser_except.ParserException(122, '认证信息错误')
        elif resp['resultCode'] != 200:
            raise parser_except.ParserException(parser_except.API_ERROR, '检查下发送的内容')


    def after_create_session(self, req, resp):
        self.api.currentSessionId = resp['sessionId']

    def after_poll(self, req, resp):
        if len(resp['result']) > 0:
            self.now = time.time()
            self.bol = 1
        if not resp['result'] and self.bol == 1:
            self.failure_count += 1

    def parse_Flight(self, req, resp):
        ret = [x.to_tuple() for x in self.api.parse(resp, self.redis_key)]
        if 'flight_no' in self.task.ticket_info.keys(): 
            for li in ret:
                if li[1] == self.task.ticket_info['flight_no']:
                    self.res_num = 1
        return ret


def l_get_proxy(_):
    print 'ada'
    return '10.10.95.29:8080'


if __name__ == '__main__':
    import mioji.common.spider
    from mioji.common.task_info import Task
    from mioji.common.utils import httpset_debug

    httpset_debug()
    # 如果没有出口ip，可以把下面这行加上，并且把爬虫服务请求代理的关键字变成req
    mioji.common.spider.get_proxy = l_get_proxy

    task = Task()
    auth = {
        'partnerId': 'miojisit',
        'appid': 'miojisit',
        'appsecurity': 'bacca05f-d94a-4ca0-9898-d9b70cf7d7b3'
    }
    task.ticket_info = {
        'v_seat_type': 'E',
        'auth': json.dumps(auth)
    }
    # task.content = 'PEK&ORD&20170919'
    task.content = 'CAN&NYC&20170830'
    task.redis_key = 'default_redis_key'
    spider = igolaFlightSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    print spider.result
