#!/usr/bin/env python
# -*- coding: utf-8 -*-
from roundFlight_base_class import BaseRoundFlightSpider


class orbitzRoundFlightSpider(BaseRoundFlightSpider):
    source_type = 'orbitzRoundFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }

    def __init__(self, task=None):
        BaseRoundFlightSpider.__init__(self, task)

        self.source = 'orbitz'
        self.host = 'https://www.orbitz.com'

    old_spider_tag = {
        'orbitzRoundFlight': {'required': ['RoundFlight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider

    content = 'PEK&LAX&20170621&20170629'
    task = Task('orbitzRoundFlight', content)
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_http_proxy
    spider = orbitzRoundFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    import json

    print '共有', len(spider.result['RoundFlight']), '张票'
    print json.dumps(spider.result['RoundFlight'], ensure_ascii=False)
