#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from mioji.common import parser_except

from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from pkfare_oneway_spider import PKfareFlightSpider
from mioji.common.check_book.check_book_ratio import use_record_qid

class PKfareRoundSpider(PKfareFlightSpider):
    source_type = 'PKfare'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'RoundFlight': {'version': 'InsertRoundFlight2'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'pkfareRoundFlight': {'required': ['RoundFlight']}
    }

    def __init__(self, task=None):
        PKfareFlightSpider.__init__(self, task=task)
        # 任务信息
        self.mode = 'RT'

    def process_task(self):
        task = self.task
        use_record_qid(unionKey='PKfare API', api_name="Shopping", task=task, record_tuple=[1, 0, 0])
        dept_code, arr_code, dept_date, return_date = task.content.split('&')
        section = [(dept_code, self.format_data_str(dept_date), arr_code),
                   (arr_code, self.format_data_str(return_date), dept_code)]
        req = self.api.get_request_parameters(section, self.task.ticket_info)
        return req

    def targets_request(self):
        req = self.process_task()

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['RoundFlight'])
        def do_request():
            return {
                'req': req,
            }
        return [do_request]

    def parse_RoundFlight(self, req, resp):
        return self.parse_Flight(req, resp)


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_http_proxy
    httpset_debug()
    task = Task()
    task.redis_key = '123'
    # task.content = 'CKG&HAM&20170702&20170714'

    task.content = 'SEA&SFO&20171202&20171214'
    task.ticket_info = {
        'v_count': 1,
        "v_seat_type": "经济舱|经济舱",
        'v_age': '20_18_3_-1',
        "auth": json.dumps({"partner_id":"2+JvfTPfkn9+C4TYJplABQJfUJI=","partner_key":"OWI0M2I5OWNkZmZjZDg5MGZkYWU2OWE0ZWNkYmQ1MzQ=","url":"http://api.pkfare.com"})
    }
    task.other_info = {}

    s = PKfareRoundSpider(task)
    s.task = task
    s.crawl()
    print s.crawl()
    print s.result