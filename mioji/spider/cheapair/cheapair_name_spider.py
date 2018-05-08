#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年04月13日

@author: dongkai
"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class CheapairCityNameSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cheapairCity'

    targets = {
        'City': {},
    }

    req_header = {"Accept": "*/*",
                  "Referer": "https://www.cheapair.com/",
                  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
                  "X-Requested-With": "XMLHttpRequest"}

    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_City)
        def search_city():
            search_args = {"searchString": self.task.content,
                         "mode": "Flights"}
            req_data = {"queryparams": json.dumps(search_args)}

            return {
                "req": {
                    "url": "https://www.cheapair.com/ws/search/FindLocations",
                    "params": req_data,
                    "header": self.req_header
                },
                'data': {
                    'content_type': 'json'
                }
            }

        return [search_city]

    def parse_City(self, req, data):
        self.city_info = data
        return data


if __name__ == '__main__':
    from mioji.common.task_info import Task

    content = 'TXL'
    task = Task('cheapair::cheapair', content)

    spider = CheapairCityNameSpider()
    spider.task = task
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    # import pdb;pdb.set_trace()
    print spider.user_datas["location"]
    # req_header = spider.req_header
    # url = "https://www.cheapair.com/ws/search/FindLocations"
    # req_data = {"queryparams":
    #                         {"searchString": content,
    #                         "mode": "Flights"}}
    # import requests
    # r = requests.get(url, params=req_data, headers=req_header)
    # print r.url
    # print r.content
