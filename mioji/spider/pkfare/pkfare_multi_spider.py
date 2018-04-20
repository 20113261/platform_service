#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mioji.common import parser_except

from pkfare_oneway_spider import PKfareFlightSpider
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from mioji.common.check_book.check_book_ratio import use_record_qid



class PKfareMultiSpider(PKfareFlightSpider):
    source_type = 'PKfare'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'pkfareMultiFlight': {'required': ['MultiFlight']}
    }

    def __init__(self, task=None):
        PKfareFlightSpider.__init__(self, task=task)
        # 任务信息
        self.mode = 'OJ'

    def process_task(self):
        section = []
        task = self.task
        use_record_qid(unionKey='PKfare API', api_name="Shopping", task=task, record_tuple=[1, 0, 0])
        legs = task.content.split('|')
        for leg in legs:
            dept_code, arr_code, dept_date = leg.split('&')
            section.append((dept_code, self.format_data_str(dept_date), arr_code))
        print section
        req = self.api.get_request_parameters(section, self.task.ticket_info)
        return req

    def targets_request(self):
        req = self.process_task()

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['MultiFlight'])
        def do_request():
            return {
                'req': req,
            }
        return [do_request]

    def parse_MultiFlight(self, req, resp):
        return self.parse_Flight(req, resp)


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_http_proxy
    httpset_debug()
    task = Task()
    # task.content = 'CKG&HAM&20170702&20170714'

    task.content = 'SEA&SFO&20171201|SFO&LAX&20171207'
    task.ticket_info = {
        'v_count': 1,
        "v_seat_type": "E",
        'v_age': '20_18_3_-1',
        "auth": json.dumps({"partner_id":"2+JvfTPfkn9+C4TYJplABQJfUJI=","partner_key":"OWI0M2I5OWNkZmZjZDg5MGZkYWU2OWE0ZWNkYmQ1MzQ=","url":"http://api.pkfare.com"})
    }
    task.other_info = {}
    task.redis_key = '123'

    s = PKfareMultiSpider(task)
    s.task = task
    s.crawl()
    print s.crawl()
    print s.result