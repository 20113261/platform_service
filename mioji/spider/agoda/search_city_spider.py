#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from datetime import datetime
import pytz
import urllib
import traceback
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from random import randint

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR

F_URL = 'https://www.agoda.com/Search/Search/GetUnifiedSuggestResult/3/8/1/0/zh-cn?' \
        'guid=9c6be1f0-e830-41e6-989c-0161a7b486c3&searchText={key}&origin=CN&cid=-1&pageTypeId=1&' \
        'logtime={local_time}&logTypeId=1&qs=%7Cexplist%3D%26expuser%3D%7C&isHotelLandSearch=true'
USE_EQ_KEY = 'key'

class CitySpider(Spider):
    source_type = 'aogdaSearchCity'

    targets = {
        'citySearch_city': {},
    }

    def targets_request(self):
        key = self.task.extra.get(USE_EQ_KEY, None)
        if not key:
            raise ParserException(TASK_ERROR, 'task.extra must has "key"')

        key_split_flag = '(' if key.find('(') < key.find(',') else ','
        url = F_URL.format(key=urllib.unquote(key.split(key_split_flag)[0]), local_time=urllib.unquote(datetime.now(pytz.timezone(pytz.country_timezones('cn')[0])).strftime('%a %b %d %Y %H:%M:%S GMT+0800 (%Z)')))

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_citySearch_city, new_session=True)
        def search():
            return {'req':{'url':url},
                    'data':{'content_type':'json'}, }
        
        return [search]
        
    def parse_citySearch_city(self, req, data):
        key = self.task.extra.get(USE_EQ_KEY, None)

        key_split_flag = '(' if key.find('(') < key.find(',') else ','
        index = -1
        CityId = randint(1, 1000)+randint(1, 200)
        CityId = CityId*1000

        flag = True
        Objects = [city for city in data['ViewModelList'] if city['PageTypeId'] == 5]
        for i, city in enumerate(Objects):
            if city['PageTypeId'] == 5 and city['ResultText'].replace(' ','').find(key.replace(' ','')) > -1:
                index = i+1
                CityId = int(city['CityId']) or int(city['ObjectId'])
                flag = False


        if flag:
            for i, city in enumerate(Objects):
                if city['PageTypeId'] == 5 and city['ResultText'].replace(' ', '').find(key.split(key_split_flag)[0].replace(' ', '')) > -1:
                    index = i + 1
                    CityId = int(city['CityId']) or int(city['ObjectId'])

        if len(Objects)==0:
            flag = True
            Objects = data['SuggestionList']
            for i, city in enumerate(Objects):
                if city['Name'].replace(' ','').replace("'", "’").find(key.replace(' ','')) > -1:
                    index = i + 1
                    CityId = int(city['ObjectID'])
                    flag = False

            if flag:
                for i, city in enumerate(Objects):
                    if city['Name'].replace(' ', '').replace("'", "’").find(key.split(key_split_flag)[0].replace(' ', '')) > -1:
                        index = i + 1
                        CityId = int(city['ObjectID'])

        return [Objects, index, CityId]

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
    import json

    print json.dumps(search(u'Nancy’s Attic,太平洋丛林市(CA)')[1])
    # from datetime import datetime
    # import pytz
    #
    # tz = pytz.timezone(pytz.country_timezones('cn')[0])
    # print tz
    # print 'Thu Aug 24 2017 10:12:14 GMT+0800 (CST)'
    # print datetime.now(tz)
    # print datetime.now(tz).strftime('%a %b %d %Y %H:%M:%S GMT+0800 (%Z)')

