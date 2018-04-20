#!/usr/bin/env python
# -*- coding: utf-8 -*-

from multiFlight_base_class import BaseMultiFlightSpider


class expediaMultiFlightSpider(BaseMultiFlightSpider):
    source_type = 'expediaMultiFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    def __init__(self, task=None):
        BaseMultiFlightSpider.__init__(self, task)

        self.source = 'expedia'
        self.host = 'https://www.expedia.com'

    old_spider_tag = {
        'expediaMultiFlight': {'required': ['MultiFlight']}
    }


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    # mioji.common.spider.get_proxy = simple_get_http_proxy
    content = 'PEK&YYZ&20180210|YVR&PEK&20180220'
    task = Task('expediamultiFlight', content)
    task.ticket_info = {
        'v_count': '1',
        'v_seat_type': 'E',
        # 'v_age': '-1_1',
        'flight_no':'MU521_AA182&AA186',
        # 'ret_flight_no': 'AA187'
    }

    spider = expediaMultiFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    import json

    print json.dumps(spider.result['MultiFlight'], ensure_ascii=False)
    print len(spider.result['MultiFlight'])
    print len(set(spider.result['MultiFlight']))