#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年03月31日

@author: hourong
"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
import cleartrip_round_lib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class ClearTripCityNameSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cleartripCity'

    targets = {
        'City': {},
    }

    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_City)
        def home_page():
            return {
                'req': {
                    'url': 'http://www.cleartrip.sa/places/airports/search?string=' + self.task.content,
                },
                'data': {
                    'content_type': 'json'
                }
            }

        return [home_page]

    def parse_City(self, req, data):
        return data


if __name__ == '__main__':
    from mioji.common.task_info import Task

    content = 'TXL'
    task = Task('cleartrip::cleartrip', content)

    spider = ClearTripCityNameSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})[0]['City'][0].get('v', '')
