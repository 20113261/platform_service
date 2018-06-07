#!/usr/bin/env python
# -*- coding: utf-8 -*-

from roundFlight_base_class import BaseRoundFlightSpider
from flight_lib import *


class EbookersRoundFlightSpider(BaseRoundFlightSpider):
    source_type = 'ebookersRoundFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'},
        # 'VerifyFlight': {'version': 'InsertNewFlight'},
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ebookersRoundFlight': {'required': ['RoundFlight']}
    }

    def __init__(self, task=None):
        BaseRoundFlightSpider.__init__(self, task)

        self.source = 'ebookers'
        self.host = 'https://www.ebookers.com'

    def format_time(self, dept_day, c):
        y = dept_day[:4]
        m = dept_day[4:6]
        d = dept_day[-2:]
        return d + c + m + c + y

if __name__ == '__main__':
    from mioji.common.task_info import Task
    test_task = Task()
    test_task.content = 'PEK&JHB&20170628&20171208'
    test_task.source = 'ebookersroundFlight'
    # s = '{"flight_no": "KL1366_KL1193", "dest_id": "BGO", "v_count": 1, "source": "cheaptickets", "v_seat_type": "E", "env_name": "online", "dept_id": "WAW", "dept_time": "20170401", "is_block": "true"}'
    # task.ticket_info = dict(v_seat_type='F')
    test_task.ticket_info = dict(v_seat_type='B', v_count='3', v_age='22_10_22', v_hold_seat='1_1_1')
    # task.ticket_info = dict(v_count='3', v_age='20_10_0.5', v_hold_seat='1_1_0')
    # task.ticket_info = dict(v_seat_type='P', v_count=3)
    # task.ticket_info = json.loads(s)
    spider = EbookersRoundFlightSpider()
    spider.task = test_task
    """
    import json
    s = '{"flight_no": "KL1366_KL1193", "dest_id": "BGO", "v_count": 1, "source": "cheaptickets", "v_seat_type": "E", "env_name": "online", "dept_id": "WAW", "dept_time": "20170401", "is_block": "true"}'
    task.ticket_info = json.loads(s)
    """

    print spider.crawl()
    print spider.result
