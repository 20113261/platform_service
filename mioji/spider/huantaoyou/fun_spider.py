#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
import json
import copy
setdefaultencoding_utf8()
from util import SkipException
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from huantaoyouAPI import HuantaoyouApi


class huantaoyouSpider(Spider):
    source_type = 'huantaoyou'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Fun': {}
    }

    old_spider_tag = {
        "huantaoyouFun": {"required": ["Fun"]}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.task = task
        self.header = {}
        self.api_object = None
        self.req_id = -1

    def targets_request(self):
        if self.task is None:
            raise parser_except.ParserException(parser_except.TASK_ERROR, '没传task进来')
        self.req_id = self.task.ticket_info['wanle']

        self.api_object = HuantaoyouApi(self.task)
        url = self.api_object.prepare_request(self.req_id)

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=self.parse_Fun)
        def make_request():
            return {
                'req': {
                    'method': 'GET',
                    'url': url,
                    'headers': self.header,
                },
                'data': {'content_type': 'json'},
            }

        return [make_request]

    def parse_Fun(self, req, resp):
        data = []
        try:
            type_ret = self.api_object.type_classification(self.req_id, resp)
        except SkipException as e:
            raise parser_except.ParserException(parser_except.TASK_ERROR, '任务信息有问题')
        except Exception as e:
            raise parser_except.ParserException(parser_except.PARSE_ERROR, str(e))
        for key, val in type_ret.items():
            if val:
                try:
                    ticket_ret = self.api_object.tickets_fun_analysis(self.req_id, val, resp)
                    for ticket in ticket_ret:
                        tickets = {'view_ticket':{"info":{}},'tour_ticket':{"info":{}},'play_ticket':{"info":{}},'activity_ticket':{"info":{}}}
                        val['tickets'] = ticket
                        del tickets[key]
                        tickets[key] = copy.deepcopy(val)
                        data.append(tickets)
                except Exception, e:
                    print e
        return data