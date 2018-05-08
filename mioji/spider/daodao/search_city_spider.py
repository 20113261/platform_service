#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年8月24日

@author: luwannign
'''

import traceback
import time
import traceback
from random import randint
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR

F_URL = 'https://www.tripadvisor.cn/TypeAheadJson'
USE_EQ_KEY = 'key'

class CitySpider(Spider):
    source_type = 'daodaoSearchCity'

    targets = {
        'citySearch_city': {},
    }

    def targets_request(self):
        key = self.task.extra.get(USE_EQ_KEY, None)
        if not key:
            raise ParserException(TASK_ERROR, 'task.extra must has "key"')

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_citySearch_city, new_session=True)
        def search():
            key = self.task.extra.get(USE_EQ_KEY, None)
            return {'req':{'url':F_URL, 'method': 'post', 'params': {
                'action': 'API',
                'startTime': int(round(time.time() * 1000)),
                'uiOrigin': 'PTPT-hotel',
                'types': 'geo,hotel',
                'hglt': True,
                'global': True,
                'query': key.split(',')[0],
                'legacy_format': True,
                '_ignoreMinCount': True
            }},
            'data':{'content_type':'json'}, }
        
        return [search]
        
    def parse_citySearch_city(self, req, data):
        key = self.task.extra.get(USE_EQ_KEY, None)

        CityId = randint(1, 1000) + randint(1, 200)
        CityId = CityId * 1000
        index = -1

        for i, city in enumerate(data):
            if city['name'].replace(' ','').find(key.replace(' ','')) > -1:
                index = i+1
                CityId = int(city['value'])

        return [data, index, CityId]

def search(key):
    task = Task()
    task.extra['key'] = key
    spider = CitySpider(task)
    try:
        code = spider.crawl()
        assert code==0, 'has a error result'
        # print spider.result['citySearch_city'][0]
        # import pprint
        # pprint.pprint(spider.result['citySearch_city'][0])
        return key, {'error': {'code': 0}, 'data': spider.result.get('citySearch_city')}
    except Exception, e:
        print traceback.format_exc(e)
        return key, {'error': {'code': -1, 'msg': str(e)}, 'data': []}


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy
    import json

    print json.dumps(search('阿瓦隆, 加利福尼亚, 美国')[1])

