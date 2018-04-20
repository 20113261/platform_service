#!/usr/bin/env python
# encoding:utf-8

"""
Created on 2017年04月13日

@author: dongkai
"""

import time
import json
from copy import deepcopy

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
from cheapair_oneway_lib import build_search_args, search_json_parse
from cheapair_oneway_lib import convert_task
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class CheapairOneWayFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cheapairFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
        'Flight': {'version': 'InsertNewFlight'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        "cheapairFlight": {"required": ["Flight"]}
    }

    req_header = {"Accept": "*/*",
                  "Referer": "https://www.cheapair.com/",
                  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
                  "X-Requested-With": "XMLHttpRequest"}

    def targets_request(self):
        self.task_dict = convert_task(self.task.content, self.task.ticket_info)

        self.req_header = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': "http://www.cheapair.com/",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def home_page():
            return {
                'req': {
                    'url': 'https://www.cheapair.com/',
                    'headers': self.req_header,
                    'method': 'get'
                }
            }

        @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_Flight)
        def post_search():
            search_url = "https://www.cheapair.com/ws/airshop/GetBrandedFareOptions"
            req_data = build_search_args(self.task_dict)
            post_header = deepcopy(self.req_header)

            ret = {"req": {"url": search_url,
                           "params": req_data,
                           "headers": post_header,},
                   "data": {'content_type': 'json'}
                  }
            return ret

        return [home_page, post_search]

    def cache_check(self, req, data):
        return False

    def parse_Flight(self, req, data):
        """
        parse data result
        """
        try:
            return search_json_parse(data)
        except Exception:
            parser_except.ParserException(
                parser_except.PARSE_ERROR, 'cheapairOneWayFlight::爬虫解析异常')


if __name__ == '__main__':
    from mioji.common.task_info import Task

    import httplib
    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    content = 'PEK&PAR&20170615'
    task = Task('cheapair::cheapair', content)
    task.ticket_info["flight_no"] = "LH723_LH2456&LH1167_LH720"

    spider = CheapairOneWayFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    print spider.result
