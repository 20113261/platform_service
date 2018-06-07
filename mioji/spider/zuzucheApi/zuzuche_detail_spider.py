#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import base64
import datetime
import re
import urlparse

from mioji.common.utils import setdefaultencoding_utf8
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NEVER
from mioji.common.check_book.check_book_ratio import use_record_qid

setdefaultencoding_utf8()


# 用来处理返回的json格式不规范的问题
def consult_resp(resp):
    pre_time = datetime.datetime.now()
    complete, pos = False, 0
    while not complete:
        try:
            if (datetime.datetime.now() - pre_time).seconds > 10:
                raise parser_except.ParserException(27, '返回数据的json解析超时')
            resp = json.loads(resp)
            complete = True
        except ValueError as e:
            wrong_pos = int(re.search('char (\d+)', e.message).group(1))
            pre, aft = resp[:wrong_pos - 1 - pos], resp[wrong_pos - 1 - pos:]
            resp = pre + '\\' + aft
            pos += 2
    return resp


class zuzucheDetailSpider(Spider):
    source_type = 'zuzuche'
    targets = {
        'car_detail': {}
    }
    old_spider_tag = {
        "zuzucheCar": {"required": ["Car"]}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.header = {}
        self.url = ''
        self.auth_str = ''
        self.params = {}

    def targets_request(self):
        if self.task is None:
            raise parser_except.ParserException(parser_except.TASK_ERROR, '没传task进来')
        self.get_requests_data()
        use_record_qid(unionKey='zuzucheApi', api_name="quoteAppendix.php", task=self.task, record_tuple=[1, 0, 0])

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=self.parse_car_detail)
        def make_request():
            return {
                'req': {
                    'method': 'GET',
                    'url': self.url,
                    'headers': self.header,
                    'params': self.params
                }
            }
        return [make_request]

    def get_requests_data(self):
        auth_info = json.loads(self.task.ticket_info.get('auth', '{}'))
        base_url = auth_info.get('url')
        username = auth_info.get('username')
        password = auth_info.get('password')
        # if not base_url or not username or not password:
        #     raise parser_except.ParserException(121, '无认证信息')
        # if not base_url.endswith('quoteAppendix.php'):
        #     base_url = base_url + '/' if not base_url.endswith('/') else base_url
        #     self.url = urlparse.urljoin(base_url, 'queryQuote.php')
        # else:
        #     self.url = base_url
        self.url = base_url
        self.auth_str = base64.b64encode(username + ':' + password)
        rent_info = self.task.ticket_info['zuche']
        self.params = {'id': rent_info['order_id']}
        self.header = {'Authorization': self.auth_str}

    def response_error(self, req, resp, error):
        # 目前测试403为认证信息错误所返回code
        if error.response.status_code == 401 and "AUTH_FALSE" in error.response.content:
            raise parser_except.ParserException(122, '认证信息错误')

    def parse_car_detail(self, req, resp):
        data = consult_resp(resp)
        if not data['success']:
            if '报价详细不存在' in data['text']:
                raise parser_except.ParserException(29, '报价详细不存在')
            else:
                raise parser_except.ParserException(27, data['text'])
        zuche = data['data']
        # id = self.task.ticket_info['zuche']['order_id']
        # policy = [{'title': name, 'desc': val} for name, val in data['data']['onSale'].items()]
        # insure = [{'name': i.get(u'name', u''),
        #            'code': i.get(u'mark', u''),
        #            'excess': float(re.search('(\d+\.\d+|\d+\.|\d+)', i.get(u'excess', u'')).group(1)) if i.get(u'excess', u'') else '',
        #            'desc': i.get(u'description', u'') + i.get(u'desc', u'')
        #            } for i in data['data']['insuranceExplain']]
        # zuche['id'] = id
        # zuche['policy'] = policy
        # zuche['insure'] = insure
        # zuche['cancel'] = {'title': '', 'desc': ''}
        # zuche['order'] = []
        # for i in data['data']['orderConditions'].values():
        #     if u'取消' in i['title'] or u'取消' in i['content']:
        #         zuche['cancel']['title'] += '; {}'.format(i['title']) if zuche['cancel']['title'] else i['title']
        #         zuche['cancel']['desc'] += '; {}'.format(re.sub('<.*?>', '', i['content'])) if zuche['cancel']['desc'] else re.sub('<.*?>', '',i['content'])
        #     else:
        #         zuche['order'].append({'title': i['title'], 'desc': re.sub('<.*?>', '', i['content'])})
        return [zuche]


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy, httpset_debug

    httpset_debug()

    query = {'order_id' : "58157121-660203820-5a3220e408f0f052ff4c6b96"}
    task = Task()
    auth_str = json.dumps({'username': 'L01130847-TEST', 'password':'TESTfhALO)', 'url': 'http://test.api.zuzuche.com/2.0/standard/rentalTerms.php'})
    task.ticket_info = {'zuche': query,'auth': auth_str, }
    task.other_info = {}
    # task.redis_key = 'asdfasdfasdf'
    spider = zuzucheDetailSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    # print spider.browser.resp.text
    print spider.result
    # print tes
    # for a, b in tes:
    #     print a, b
    # import json, io
    # with io.open('output', 'w', encoding='utf=8') as fp:
    #     tmp = json.dumps(spider.result, indent=2, ensure_ascii=False)
    #     fp.write(tmp)
