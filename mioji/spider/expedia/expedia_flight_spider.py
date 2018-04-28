#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flight_base_class import BaseFlightSpider


class ExpediaFlightSpider(BaseFlightSpider):
    source_type = 'expediaFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'},
    # 'VerifyFlight': {'version': 'InsertNewFlight'},
    }
    
    # 关联原爬虫
    old_spider_tag = {
        'expediaFlight': {'required': ['Flight']}
    }
    
    def __init__(self, task=None):
        BaseFlightSpider.__init__(self, task)
        self.source = 'expedia'
        self.host = 'https://www.expedia.com'

if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.ticket_info = {
    # 'v_count': '2',
    # 'v_age': '-1_1',
    # 'flight_no': "MU8666"
    }
    task.content = 'PAR&BJS&20171101'
    #时间
    spider = ExpediaFlightSpider(task)
    
    # spider.task = task
#    print "爬虫返回的错误码："
    print spider.crawl()
#    print "爬虫返回结果如下："
    print spider.result
#    print "验证结果出来保存的票："
    print spider.verify_tickets
