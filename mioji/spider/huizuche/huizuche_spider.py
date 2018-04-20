#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

import urlparse
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from huizucheAPI import HuizucheApi
from common.class_common import Car
from mioji.common.check_book.check_book_ratio import use_record_qid
import json

API_PATH = 'drv-open-api/v1/vehicles/find'


class huizucheSpider(Spider):
    source_type = 'huizuche'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Car': {}
    }

    old_spider_tag = {
        "huizucheCar": {"required": ["Car"]}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.task = task
        self.header = {}
        self.zuche_info = {}
        self.url = None

    def targets_request(self):
        if self.task is None:
            raise parser_except.ParserException(parser_except.TASK_ERROR, '没传task进来')
        self.get_requests_data()
        task = self.task
        use_record_qid(unionKey='惠租车 API', api_name="Vehicle List", task=task, record_tuple=[1, 0, 0])
        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=self.parse_Car)
        def make_request():
            """
            data 如需要保存结果，指定data.key
            这个请求访问 /m/fly/search 获取token
            """
            return {
                'req': {
                    'method': 'POST',
                    'url': self.url,
                    'headers': self.header,
                    'data': json.dumps(self.zuche_info, encoding='utf-8')
                },
                'data': {'content_type': 'json'},
            }

        return [make_request]

    def get_requests_data(self):
        # {"url": "http://zj.mock.api.huizuche.com", "requestor": "mioji_api", "secret": "jimiao"}
        auth_info = json.loads(self.task.ticket_info.get('auth', '{}'))
        base_url = auth_info.get('url', None)
        requestor = auth_info.get('requestor', None)
        secret = auth_info.get('secret', None)

        # 添加对121错误的追踪
        if not base_url or not requestor or not secret:
            raise parser_except.ParserException(121, '无认证信息')

        self.url = urlparse.urljoin(base_url, API_PATH)

        self.pay_key = 'Null'
        if hasattr(self.task, 'redis_key'):
            self.pay_key = self.task.redis_key

        self.api_object = HuizucheApi(
            redis_key=self.pay_key,base_url=base_url, requestor=requestor, secret=secret)

        self.zuche_info = self.task.ticket_info['zuche']
        self.header = self.api_object.req_post_header(self.zuche_info)

    def parse_Car(self, req, resp):
        if resp['errors'] == []:
            resp = self.api_object.analysis_json(resp)
            return resp
        else:
            if int(resp['errors'][0]['code']) == 100002 or int(resp['errors'][0]['code']) == 100004:
                raise parser_except.ParserException(122, '认证信息错误')
            else:
                raise parser_except.ParserException(90, '返回信息报错')
        


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy, httpset_debug

    httpset_debug()

    post = {
        "pickupLocationCode": "LAX",
        "returnLocationCode": "LAX",

        "pickupDateTime": "2017-12-09T18:00:00",
        "returnDateTime": "2017-12-11T08:00:00"
    }
    task = Task()
    # auth_str = json.dumps({"url": "http://zj.mock.api.huizuche.com", "requestor": "mioji_api"})
    # auth_str = json.dumps({"url": "", "requestor": "mioji_api", "secret": "jimiao"})
    # auth_str = json.dumps({"url": "http://zj.mock.api.huizuche.com", "secret": "jimiao"})
    auth_str = json.dumps({})
    # auth_str = json.dumps({"url": "http://zj.mock.api.huizuche.com", "requestor": "mioji_api123", "secret": "jimiao"})
    # auth_str = json.dumps({"url": "http://zj.mock.api.huizuche.com", "requestor": "mioji_api", "secret": "jimiao"})
    task.ticket_info = {'zuche': post ,'auth': auth_str}
    task.other_info = {}
    # task.redis_key = 'asdfasdfasdf'
    spider = huizucheSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    print spider.result
    # import json, io
    # with io.open('output', 'w', encoding='utf=8') as fp:
    #     tmp = json.dumps(spider.result, indent=2, ensure_ascii=False)
    #     fp.write(tmp)