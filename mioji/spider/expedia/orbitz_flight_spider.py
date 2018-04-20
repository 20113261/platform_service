#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flight_base_class import BaseFlightSpider


class orbitzFlightSpider(BaseFlightSpider):
    source_type = 'orbitzFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    def __init__(self, task=None):
        BaseFlightSpider.__init__(self, task)

        self.source = 'orbitz'
        self.host = 'https://www.orbitz.com'

    old_spider_tag = {
        'orbitzFlight': {'required': ['Flight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.ticket_info = {}
    task.content = 'LIS&PEK&20170717'
    spider = orbitzFlightSpider()
    spider.task = task
    print spider.crawl()
    print len(spider.tickets)
    for item in spider.tickets:
        print item
