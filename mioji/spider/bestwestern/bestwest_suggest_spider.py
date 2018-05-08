#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.logger import logger
import datetime
from datetime import timedelta
import re
from mioji.common import spider
spider.NEED_FLIP_LIMIT = False
# spider.pool.set_size(256)


class mikiSuggSpider(Spider):
    source_type = 'bestwestSuggest'
    targets = {
        'suggest': {}
    }

    old_spider_tag = {
        'bestwestSuggest': {'required': ['suggest']}
    }
    url = 'https://maps.googleapis.com/maps/api/place/autocomplete/json?input={}&language=zh_CN&key={}'

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

    def targets_request(self):

        @request(retry_count=3,proxy_type=PROXY_REQ,binding=['suggest'])
        def first_page():
            return {
                'req': {'url':self.url.format(self.task.content, self.task.ticket_info['key'])},
                'method':'get',
                'data': {'content_type': 'json'}
                }
        yield first_page


    def parse_suggest(self, req, data):
        data_list = data["predictions"]
        result = []
        for data in data_list:
            if len(data["terms"])<3:
                result.append((data['id'],data["terms"][0]['value'],data))
            else:
                result.append((data['id'],data["terms"][-3]['value'],data["terms"][-2]['value'],data["terms"][-1]['value'],data ))
        if len(result)==0:
            result.append(data["status"])
        return result


if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    spider.NEED_FLIP_LIMIT = False
    spider.pool.set_size(256)

    from mioji.common.task_info import Task

    task = Task()
    task.content = 'xiyi'
    task.ticket_info['key']='123'
    spider = mikiSuggSpider()
    spider.task = task
    spider.crawl()
    print spider.result
