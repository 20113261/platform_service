#!/usr/bin/env python
# -*- coding: utf-8 -*-
from roundFlight_base_class import BaseRoundFlightSpider


class expediaRoundFlightSpider(BaseRoundFlightSpider):
    source_type = 'expediaRoundFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }

    def __init__(self, task=None):
        BaseRoundFlightSpider.__init__(self, task)

        self.source = 'expedia'
        self.host = 'https://www.expedia.com'

    old_spider_tag = {
        'expediaRoundFlight': {'required': ['RoundFlight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.ticket_info = {
        'v_count': '2',
        # 'v_age': '-1_1',
        'flight_no': 'AA186',
        'ret_flight_no': 'AA187'
    }
    task.content = 'PEK&ORD&20170620&20170627'
    spider = expediaRoundFlightSpider()
    spider.task = task
    print spider.crawl()
    import json
    print json.dumps(spider.result['RoundFlight'], ensure_ascii=False)
