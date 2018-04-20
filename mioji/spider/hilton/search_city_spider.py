#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from datetime import datetime
import urllib
import re
import hashlib
import traceback
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from random import randint

from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.parser_except import ParserException, TASK_ERROR

F_URL = 'https://www.agoda.com/Search/Search/GetUnifiedSuggestResult/3/8/1/0/zh-cn?guid=9c6be1f0-e830-41e6-989c-0161a7b486c3&searchText={key}&origin=CN&cid=-1&pageTypeId=1&logtime={local_time}&logTypeId=1&qs=%7Cexplist%3D%26expuser%3D%7C&isHotelLandSearch=true'
USE_EQ_KEY = 'key'

class CitySpider(Spider):
    source_type = 'hiltonSearchCity'

    targets = {
        'citySearch_city': {},
    }

    def targets_request(self):
        url = 'http://www.hilton.com.cn/Handler/AutoComplete.ashx?type=get&nation=1&chinese=0&q=zh&limit=500&timestamp=1523182064982'

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_citySearch_city, new_session=True)
        def search():
            return {'req':{'url':url},
                    }
        
        return [search]
        
    def parse_citySearch_city(self, req, data):
        print data
        result = []
        suggest_list = re.findall(r'{.*?}', data)
        for suggest in suggest_list:
            cn_list = re.findall(r'to: ".*?"', suggest)
            sid = re.search(r'domain:"(.*?)"', suggest)
            if sid:
                sid = sid.group(1)
                sid_md5 = hashlib.md5(random_content.encode()).hexdigest()
            for cn in cn_list:
                result.append({'s_city': cn.split(',')[0], 's_country': cn.split(',')[1], 'suggest': suggest, 'sid': sid,
                               'source': 'hilton', 'sid_md5': sid_md5, 'suggest_type': 2})

        return result
# [{ name: "美国 芝加哥 America Chicago usa,us,meiguo,the united states chi,zhijiage", to: "芝加哥, 美国",to_en: "America|Chicago",domain:"Chicago",cdomain:"TheUnitedStates,America"  },{ name: "新西兰 皇后镇 New Zealand Queenstown nz,xinxilan huanghouzhen", to: "皇后镇, 新西兰",to_en: "New Zealand|Queenstown",domain:"Queenstown",cdomain:"NewZealand"  }]
# def search(key):
#     task = Task()
#     task.extra['key'] = key
#     spider = CitySpider(task)
#     try:
#         code = spider.crawl()
#         assert code==0, 'has a error result'
#         # import pprint
#         # pprint.pprint(spider.result['citySearch_city'][0])
#         return key, {'error': {'code': 0}, 'data': spider.result.get('citySearch_city')}
#     except Exception, e:
#         print traceback.format_exc(e)
#         return key, {'error': {'code': -1, 'msg': str(e)}, 'data': []}


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy
    import json
    task = Task()
    spider = CitySpider(task)
    try:
        code = spider.crawl()
        # assert code == 0, 'has a error result'
    except Exception, e:
        print traceback.format_exc(e)



