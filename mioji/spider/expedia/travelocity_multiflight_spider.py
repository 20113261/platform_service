#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiFlight_base_class import BaseMultiFlightSpider


class travelocityMultiFlightSpider(BaseMultiFlightSpider):
    source_type = 'travelocityMultiFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    def __init__(self, task=None):
        BaseMultiFlightSpider.__init__(self, task)

        self.source = 'travelocity'
        self.host = 'https://www.travelocity.com'

    old_spider_tag = {
        'travelocityMultiFlight': {'required': ['MultiFlight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider

    content = 'BJS&TYO&20170621|SEL&BJS&20170629'
    task = Task('expediamultiFlight', content)
    task.ticket_info["flight_no"] = "HU7919&OZ335"

    spider = travelocityMultiFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    import json

    print json.dumps(spider.result['MultiFlight'], ensure_ascii=False)