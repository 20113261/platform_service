#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flight_base_class import BaseFlightSpider
from flight_lib import *


class EbookersFlightSpider(BaseFlightSpider):
    source_type = 'ebookersFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'},
        # 'VerifyFlight': {'version': 'InsertNewFlight'},
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ebookersFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        BaseFlightSpider.__init__(self, task)

        self.source = 'ebookers'
        self.host = 'https://www.ebookers.com'

    def format_time(self, dept_day, c):
        y = dept_day[:4]
        m = dept_day[4:6]
        d = dept_day[-2:]
        return d + c + m + c + y


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.ticket_info = {
        'v_count': '2',
        'v_age': '-1_1',
        'flight_no': 'AA186'
    }
    task.content = 'PEK&ORD&20170520'
    spider = EbookersFlightSpider()
    spider.task = task
    print spider.crawl()
