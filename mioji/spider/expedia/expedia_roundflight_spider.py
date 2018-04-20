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
    from mioji.common.task_info import Task
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    task.ticket_info = {
        'v_count': '1',
        'v_seat_type': 'E',
        # 'v_age': '-1_1',
        'flight_no':'MU521_AA182&AA186',
        # 'ret_flight_no': 'AA187'
    }

    # 'https://www.expedia.com/Flight-Search-Paging?c=92e84238-cf7e-4376-98f3-c29f7301523c&is=1&sp=asc&cz=200&cn=0&ul=0'
    task.content = 'XIY&QLA&20180219&20180219'
    spider = expediaRoundFlightSpider()
    spider.task = task
    print spider.crawl()
    import json
    print spider.result['RoundFlight']
    print len(spider.result['RoundFlight'])
