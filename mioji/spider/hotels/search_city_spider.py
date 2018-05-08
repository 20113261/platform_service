#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''
from langconv import *
import urllib
from random import randint
from mioji.common.utils import setdefaultencoding_utf8
import re
import json

setdefaultencoding_utf8()
import traceback

from mioji.common.task_info import Task
from mioji.common.utils import remove_html_tags
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR

F_URL = 'https://lookup.hotels.com/1/suggest/v1.7/json?' + \
        'locale=zh_HK&boostConfig=config-boost-champion&excludeLpa=false&callback=srs&query={key}'
USE_EQ_KEY = 'key'

class CitySpider(Spider):

    source_type = 'hotelsSearchCity'

    targets = {
        'citySearch_city': {},
    }

    def targets_request(self):
        key = self.task.extra.get(USE_EQ_KEY, None)
        if not key:
            raise ParserException(TASK_ERROR, 'task.extra must has "key"')

        if key.find('(')>-1:
            key = key.split('(')[0]
        url = F_URL.format(key=urllib.unquote(key))

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_citySearch_city, new_session=False)
        def search():
            return {'req': {'url': url},
                    'data': {'content_type': self.parse_json},}

        return [search]

    def parse_json(self, request_template, data):
        return json.loads(data[4:-2])

    def parse_citySearch_city(self, req, data):
        key = self.task.extra.get(USE_EQ_KEY, None)
        if key.find('(') > -1:
            key = key.split('(')[0]

        index = -1
        cities = []
        CityId = randint(1, 1000) + randint(1, 200)
        CityId = CityId * 1000
        max = 0
        try:
            for sug in data.get('suggestions', []):
                if 'CITY_GROUP' == sug.get('group', None):
                    cities = sug.get('entities', [])
                    for i, city in enumerate(cities):

                        # print Converter('zh-hans').convert(city['caption'])
                        city['caption'] = remove_html_tags(city['caption'])

                        before_city = Converter('zh-hans').convert(city['caption']).replace(' ','')
                        special = re.findall(r'\(.*\)', before_city)
                        if len(special)>0:
                            special = special[0]
                        # city_name, states, country = before_city.split(',')
                        args = before_city.split(',')

                        flags = []
                        for src, dest in zip([args[-3], args[-2], args[-1]], key.replace(' ', '').split(',')):
                            if src.find(dest) > -1 or special.find(dest)>-1:
                                flags.append(True)
                        if len(flags)>max:
                            index = i+1
                            CityId = int(city['destinationId'])
                            max = len(flags)
                            flags = []
                            if len(flags)==3:
                                break
                    break
        except Exception as e:
            print traceback.format_exc(e)

        return [cities, index, CityId]


def search(key):
    task = Task()
    task.extra['key'] = key
    spider = CitySpider(task)
    try:
        code = spider.crawl()
        assert code==0, 'has a error result'
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

    print json.dumps(search('里士满, 弗吉尼亚, 美国 (Richmond)')[1])
    # print Converter('zh-hans').convert(u'阿瓦崙, 加州, 美國 (阿渥伦)')

