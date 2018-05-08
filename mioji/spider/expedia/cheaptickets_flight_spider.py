#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flight_base_class import BaseFlightSpider


class CheapticketsFlightSpider(BaseFlightSpider):
    source_type = 'cheapticketsFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    def __init__(self, task=None):
        BaseFlightSpider.__init__(self, task)

        self.source = 'cheaptickets'
        self.host = 'https://www.cheaptickets.com'

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'cheapticketsFlight': {'required': ['Flight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task

    print CheapticketsFlightSpider.__base__
    print CheapticketsFlightSpider.__bases__

    task = Task()
    task.ticket_info = {}
    task.content = 'PEK&ORD&20170419'
    spider = CheapticketsFlightSpider()
    spider.task = task
    print spider.crawl()
    print len(spider.tickets)
    for item in spider.tickets:
        print item
