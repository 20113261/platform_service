#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

import re
import datetime
import sys

sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8
import requests

setdefaultencoding_utf8()
import json
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, mioji_data, PROXY_FLLOW, PROXY_REQ
from mioji.models.city_models import get_suggest_city
from mioji.common import parser_except
from mioji.common import logger
import hotellist_parse
import datetime
from datetime import timedelta
from urllib import urlencode
from urlparse import urljoin

DATE_F = '%Y/%m/%d'
URL0 = 'https://www.expedia.com.hk/Hotel-Search?&langid=2052'
URL1 = 'https://www.expedia.com.hk/Hotel-Search-Data?responsive=true'
json_url = 'https://www.expedia.com.hk/gc/model.json'
referer = 'https://www.expedia.com.hk/Hotel-Search?'
hd = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'Origin': 'https://www.expedia.com.hk',
    # 'Content-Length': 0,
}

model_json = {
    "site": {
        "id": 18,
        "tpid": 18,
        "eapid": 0,
        "brandName": "EXPEDIA",
        "companyCode": 10124,
        "defaultDomain": "www.expedia.com.hk",
        "langId": 2052,
        "locale": "zh_CN",
        "resolvedCurrency": "HKD"
    },
    "user": {
        "guid": "cf20f4e6-25d7-4183-99d0-954735abcb77",
        "tuid": -1,
        "expUserId": -1,
        "userStatus": "ANONYMOUS",
        "hasGroups": False,
        "arranged": False,
        "agent": False,
        "sua": False
    },
    "abTests": [],
    "coBrandedData": {
        "htmlDom": "<div><h1>Dummy HTML template</h1></div>"
    }
}


def crate_params(ci, start_date, end_date, city_id, person_num, hashParam, ins):
    params = {
        'destination': ci,
        'startDate': start_date,
        'endDate': end_date,
        'regionId': city_id,
        'langid': 2052,
        'adults': str(person_num),
        'hashParam': '',
        'sort': 'recommended',
        'page': str(ins),
        'hsrIdentifier': 'HSR',
    }

    return params


class ExpediaListSpider(Spider):
    source_type = 'expediaListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room4'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'expediaListHotel': {'required': ['room']}
    }

    def targets_request(self):
        if self.task.ticket_info.get('is_new_type'):
            url = self.task.ticket_info.get('suggest')
            self.user_datas['night'] = self.task.ticket_info.get('stay_nights')
            check_in = self.task.ticket_info.get("check_in")
            self.user_datas['check_in'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10].replace('-', '/')
            self.user_datas['check_out'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + timedelta(
                    int(self.user_datas['night'])))[:10].replace('-', '/')
            self.user_datas['adult'] = self.task.ticket_info.get('occ')
            if self.task.ticket_info.get('suggest_type') == 1:
                if 'regionId' not in url:
                    destination = re.search(r'destination=(.*?)(?=&)', url).group(1)
                    self.user_datas['mjcity_id'] = destination
                    self.user_datas['city_id'] = ''
                    try:
                        json_str = requests.get(json_url).content
                        json_params = json.loads(json_str).get('site')
                    except Exception:
                        json_params = model_json['site']

                else:
                    if re.match(r'.+regionId=(\d+)', url):
                        self.user_datas['city_id'] = re.search(r'regionId=(\d+)', url).group(1)
                    elif re.match(r'.+regionId%3D', url):
                        self.user_datas['city_id'] = re.search(r'regionId%3D(\d+)', url).group(1)
                    else:
                        self.user_datas['city_id'] = ''
            else:
                suggest_json = json.loads(self.task.ticket_info.get('suggest'))
                self.user_datas['city_id'] = suggest_json['gaiaId']
            start_date = self.user_datas['check_in']
            end_date = self.user_datas['check_out']
            city_id = self.user_datas['city_id']
            self.user_datas['mjcity_id'] = 'NULL'
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]  # 获取城市ID
                task_p = creat_hotelParams(self.task.content)  # 酒店的初始信息
                self.user_datas['mjcity_id'] = mjcity_id
                suggest_city = get_suggest_city('expedia', mjcity_id)
                is_new_type = suggest_city.get('is_new_type')
                self_p = suggest_city.get('suggest')  # 初始这个城市的酒店和房间的详细信息
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            # print "self_p:",self_p
            if is_new_type == 0:
                city_id = self_p['gaiaId']  # 问题：从数据库获取了和mjcity_id有关的信息，我的问题就是mjcity_id和city_id都代表了什么
                self.user_datas['city_id'] = city_id
            else:
                url = self_p.get('url')
                if 'regionId' not in url:
                    destination = re.search(r'destination=(.*?)(?=&)', url).group(1)
                    self.user_datas['mjcity_id'] = destination
                    self.user_datas['city_id'] = ''
                    try:
                        json_str = requests.get(json_url).content
                        json_params = json.loads(json_str).get('site')
                    except Exception:
                        json_params = model_json['site']
                else:
                    if re.match(r'.+regionId=(\d+)', url):
                        self.user_datas['city_id'] = re.search(r'regionId=(\d+)', url).group(1)
                    elif re.match(r'.+regionId%3D', url):
                        self.user_datas['city_id'] = re.search(r'regionId%3D(\d+)', url).group(1)
                    else:
                        self.user_datas['city_id'] = ''
                city_id = self.user_datas['city_id']
            self.user_datas['adult'] = task_p.adult  # 房间能居住成人数量
            self.user_datas['check_in'] = task_p.check_in  # 入住时间
            self.user_datas['check_out'] = task_p.check_out  # 退房时间
            self.user_datas['night'] = task_p.night  # 入住的天数
            start_date = task_p.format_check_in(DATE_F)
            end_date = task_p.format_check_out(DATE_F)
        self.user_datas['page_size'] = 40  # 获取40页的数据

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def get_hash_param():
            return {'req': {'url': URL0},
                    'data': {'content_type': 'string'},
                    'user_handler': [self.parse_hash_param]}

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=["hotel", 'room'])
        def first_page():

            params = crate_params(self.user_datas['mjcity_id'], start_date, end_date, city_id, self.user_datas['adult'],
                                  '', 1)
            if not params.get('regionId'):
                test_params = {
                    'siteid': model_json['site']['id'],
                    'langid': model_json['site']['langId'],
                    'view': 'results',
                    'timezoneOffset': 28800000,
                }
                test_params.update(params)
                params = test_params
                del params['regionId']
                del params['destination']
                params_str = urlencode(params)
                params_str = ''.join([params_str, '&', 'destination', '=', destination])
                req_url = ''.join([URL1, '&', params_str])
                return {'req': {'url': req_url, 'data': '', "method": "POST", 'headers': hd, },
                        'data': {'content_type': 'json'},
                        'user_handler': [self.parse_first_page]}

            return {'req': {'url': URL1, 'data': params, "method": "POST", 'headers': hd, },
                    'data': {'content_type': 'json'},
                    'user_handler': [self.parse_first_page]}

        # one by one
        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=["hotel", 'room'])
        def all_pages():

            page_size = self.user_datas.get('page_size', 0)
            pages = []
            print
            page_size
            for i in xrange(2, page_size):
                param = crate_params(self.user_datas['mjcity_id'], start_date, end_date, city_id,
                                     self.user_datas['adult'],
                                     '', i, )
                if not param.get('regionId'):
                    test_param = {
                        'siteid': model_json['site']['id'],
                        'langid': model_json['site']['langId'],
                        'view': 'results',
                        'timezoneOffset': 28800000,

                    }
                    test_param.update(param)
                    param = test_param
                    del param['regionId']
                    del param['destination']
                    params_str = urlencode(param)
                    params_str = ''.join([params_str, '&', 'destination', '=', destination])
                    req_url = ''.join([URL1, '&', params_str])
                    pages.append(
                        {
                            'req':
                                {'method': 'POST',
                                 'url': req_url,
                                 'data': '',
                                 'headers': hd,
                                 },
                            'data': {'content_type': 'json'}
                        }
                    )
                else:
                    pages.append(
                        {
                            'req':
                                {'method': 'POST',
                                 'url': URL1,
                                 'data': param,
                                 'headers': hd,
                                 },
                            'data': {'content_type': 'json'}
                        }
                    )
            return pages

        # yield get_hash_param
        yield first_page
        yield all_pages

    def parse_first_page(self, req, data):
        try:
            # print req
            hotels_dic = data
            print
            "hotels_dic", hotels_dic
            pagination = hotels_dic['pagination']
            page_num = int(pagination['pageCount'])
            self.user_datas['page_size'] = page_num
            print
            "page_num:", page_num
        except Exception, e:
            logger.logger.error("expediaList:: load json occur some error :%s " % str(e))

    def parse_hash_param(self, req, data):

        try:
            print
            "获取的数据:", data
            print
            "发出的所有JS请求:", re.findall(r'<script (\S*)></script>', data.encode('UTF-8'), re.IGNORECASE)
            print
            "JS函数的内容：", re.findall(r'<script><(\S*)</script>', data.encode('UTF-8'))
            data = data.encode('UTF-8')
            pat_page = re.compile(r'"hashParam":(.*?),')
            hashParam = pat_page.findall(data)[0].strip()[1:-1]
            print
            "hashParam:", hashParam
            self.user_datas['hashParam'] = hashParam

        except Exception, e:
            try:
                pat_page = re.compile(r'hashParam=".*?"(.*?);')
                hashParam = pat_page.findall(data)[0].strip()[:-1]
                self.user_datas['hashParam'] = hashParam
                print
                hashParam, '-' * 100
            except Exception, e:
                raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                    'can’t find parse hashparam city:{0}. error{1}'.format(
                                                        self.user_datas['mjcity_id'], str(e)))

    def parse_hotel(self, req, data):
        print
        type(data)
        if 'searchResults' in data:
            if 'retailHotelModels' in data['searchResults']:
                return hotellist_parse.parse_hotels_hotel(data)

        raise parser_except.ParserException(parser_error_code=parser_except.EMPTY_TICKET)

    def parse_room(self, req, data):
        return hotellist_parse.parse_hotels_room(data, self.user_datas['mjcity_id'], self.user_datas['check_in'],
                                                 self.user_datas['night'], \
                                                 self.user_datas['check_out'], self.user_datas['adult'])


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, simple_get_http_proxy

    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    contents = [
        # '50104&3&1&20170914',
        # '11469&3&1&20170926',
        # '11469&3&1&20170728',
        # '11469&3&1&20170807',
        # '11469&3&1&20170804',
        # '10021&3&1&20170828',
        # '11317&3&1&20170715',
        # '11469&3&1&20170808',
        # '20148&1&1&20170715',
        # '20148&1&1&20170729',
        # '20148&1&1&20170805',
        # '20148&1&1&20170811',
        # '20148&1&1&20170812',
        # '20148&1&1&20170728',
        # '20152&3&1&20170825',
        # '20152&3&1&20170828',
        # '20152&3&1&20170906',
        # '20152&3&1&20170829',
        # '20152&3&1&20170905',
        # '20152&3&1&20170912',
        # '20152&3&1&20170908',
        # '20152&3&1&20170916',
        # '20152&3&1&20170904',
        # '20152&3&1&20170911',
        # '20152&3&1&20170915',
        # '20152&3&1&20170827',
        # '20152&3&1&20170914',
        # '20152&3&1&20170918',
        # '20152&3&1&20170907',
        # '20152&3&1&20170922',
        # '20152&3&1&20170917',
        # '20152&3&1&20170921',
        # '60141&3&1&20170914',
        # '60141&3&1&20170907',
        # '60141&3&1&20170911',
        # '60141&3&1&20170908',
        # '20238&2&1&20170812',
        # '60141&3&1&20170906',
        # '60141&3&1&20170920',
        # '60141&3&1&20170903',
        # '20238&2&1&20170810',
        # '60141&3&1&20170910'

        # '50104&2&1&20170915',
        # '50104&3&1&20170915',
        # '50106&3&1&20170819',
        # '50106&3&1&20170818',
        # '50106&3&1&20170815',
        # '50106&3&1&20170816',
        # '50104&1&1&20170914',
        # '50104&2&1&20170914',
        # '50104&3&1&20170913',
        # '50104&3&1&20170914',
        # '50063&1&1&20170915',
        # '50046&3&1&20170812',
        # '50044&3&1&20170818',
        # '50044&1&1&20170818',
        # '50044&3&1&20170819',
        # '50044&2&1&20170819',
        # '50044&1&1&20170819',
        # '50044&2&1&20170818',
        # '50044&1&1&20170715',
        # '40081&1&1&20170731',
        # '40081&3&1&20170730',
        # '40081&2&1&20170801',
        # '40081&3&1&20170729',

        # '40081&2&1&20170730',
        # '40081&3&1&20170801',
        # '40081&3&1&20170731',
        # '40081&1&1&20170801',
        # '40081&2&1&20170729',
        # '40081&1&1&20170729',
        # '60141&3&1&20170930',
        # '40080&1&1&20170813',
        # '40080&1&1&20170814',
        # '40080&2&1&20170814',
        # '20238&2&1&20170811',
        # '40080&3&1&20170813',
        # '40080&3&1&20170811',
        # '40080&2&1&20170811',
        # '40080&1&1&20170812',
        # '40080&1&1&20170811',
        # '40080&3&1&20170810',
        # '60141&3&1&20170921',
        # '60141&3&1&20170919',
        # '60141&3&1&20170923',
        # '60141&3&1&20171001',
        # '60141&3&1&20170905',
        # '60141&3&1&20170922',
        # '60141&3&1&20170924',
        # '60141&3&1&20170912',
        # '60141&3&1&20170917',
        # '20238&2&1&20170818',
        # '60141&3&1&20170918',
        # '60141&3&1&20170913',
        '60141&3&1&20170916',
        '60141&3&1&20170915',
        '60141&3&1&20170925'

    ]
    # data_j = json.loads(
    #     """{"hierarchyInfo": {"country": {"name": "法国", "isoCode2": "FR", "isoCode3": "FRA"}, "airport": {"airportCode": "PAR", "multicity": "179898", "metrocode": "PAR"}}, "index": "0", "packageable": "false", "regionNames": {"fullName": "巴黎（及周边地区）", "lastSearchName": "巴黎（及周边地区）", "displayName": "<B>巴黎</B>（及周边地区）", "shortName": "巴黎（及周边地区）"}, "popularity": "1066.0", "coordinates": {"lat": "48.862720", "long": "2.343750"}, "hotelCountPerRegion": "3065", "score": "1.0", "regionGrades": {"globalGrade": "0"}, "essId": {"sourceName": "GAI", "sourceId": "179898"}, "gaiaId": "179898", "type": "MULTICITY", "@type": "gaiaRegionResult", "regionMetadata": {"hotelCount": "3065"}}""")


    # task.ticket_info = {
    #     'is_new_type': True,
    #     'suggest_type': 2,
    #     'suggest': json.dumps(data_j),
    #     'check_in': '20170930',
    #     'stay_nights': '2',
    #     'occ': '2'
    # }

    # task.ticket_info = {
    #     'is_new_type': True,
    #     'suggest_type': 1,
    #     'suggest': 'https://www.expedia.com.hk/Hotel-Search?destination=%E7%93%A6%E6%A0%BC%E7%93%A6%E6%A0%BC,+%E6%96%B0%E5%8D%97%E5%A8%81%E5%B0%94%E5%A3%AB,+%E6%BE%B3%E5%A4%A7%E5%88%A9%E4%BA%9A&startDate=2017/11/17&endDate=2017/11/18&adults=2&regionId=181592&sort=recommended',
    #     'check_in': '20170930',
    #     'stay_nights': '2',
    #     'occ': '2'
    # }

    # task.ticket_info = {
    #     'is_new_type': True,
    #     'suggest_type': 1,
    #     'suggest': 'https://www.expedia.com.hk/Hotel-Search?destination=%E8%89%BE%E5%BE%B7%E5%A4%AB%EF%BC%8C+%E5%9F%83%E5%8F%8A&startDate=2017/09/18&endDate=2017/09/19&adults=2&regionId=6233562',
    #     'check_in': '20170930',
    #     'stay_nights': '2',
    #     'occ': '2'
    # }
    #     task.content = '13384&2&1&20180121'
    #     task.content = '21275&2&1&20180121'
    #     task.content = '51417&2&1&20180121'
    #     task.content = '51376&2&1&20180304'
    #     task.content = '51431&2&1&20180304'
    #     task.content = '21269&2&1&20180304'
    #     task.content = '13127&2&1&20180304'
    #     suggest = json.dumps({'@type': 'gaiaRegionResult',
    #  'coordinates': {'lat': '48.862720', 'long': '2.343750'},
    #  'essId': {'sourceId': '179898', 'sourceName': 'GAI'},
    #  'gaiaId': '179898',
    #  'hierarchyInfo': {'airport': {'airportCode': 'PAR',
    #    'metrocode': 'PAR',
    #    'multicity': '179898'},
    #   'country': {'isoCode2': 'FR',
    #    'isoCode3': 'FRA',
    #    'name': '\xe6\xb3\x95\xe5\x9b\xbd'}},
    #  'hotelCountPerRegion': '3065',
    #  'index': '0',
    #  'packageable': 'false',
    #  'popularity': '1066.0',
    #  'regionGrades': {'globalGrade': '0'},
    #  'regionMetadata': {'hotelCount': '3065'},
    #  'regionNames': {'displayName': '<B>\xe5\xb7\xb4\xe9\xbb\x8e</B>\xef\xbc\x88\xe5\x8f\x8a\xe5\x91\xa8\xe8\xbe\xb9\xe5\x9c\xb0\xe5\x8c\xba\xef\xbc\x89',
    #   'fullName': '\xe5\xb7\xb4\xe9\xbb\x8e\xef\xbc\x88\xe5\x8f\x8a\xe5\x91\xa8\xe8\xbe\xb9\xe5\x9c\xb0\xe5\x8c\xba\xef\xbc\x89',
    #   'lastSearchName': '\xe5\xb7\xb4\xe9\xbb\x8e\xef\xbc\x88\xe5\x8f\x8a\xe5\x91\xa8\xe8\xbe\xb9\xe5\x9c\xb0\xe5\x8c\xba\xef\xbc\x89',
    #   'shortName': '\xe5\xb7\xb4\xe9\xbb\x8e\xef\xbc\x88\xe5\x8f\x8a\xe5\x91\xa8\xe8\xbe\xb9\xe5\x9c\xb0\xe5\x8c\xba\xef\xbc\x89'},
    #  'score': '1.0',
    #  'type': 'MULTICITY'}
    # )
    task.content = "60184&2&1&20180402"
    # task.ticket_info = {
    #     'is_new_type': True,
    #     'suggest_type': 1,
    #     # 'suggest': "https://www.expedia.com.hk/Hotel-Search?destination=%E5%87%AF%E5%A1%94%E4%BA%9A,+%E6%96%B0%E8%A5%BF%E5%85%B0&startDate=2018/02/27&endDate=2018/02/28&adults=2&regionId=1758&sort=recommended",
    #     # 'suggest': 'https://www.expedia.com.hk/Hotel-Search?destination=%E5%87%AF%E5%A1%94%E4%BA%9A,+%E6%96%B0%E8%A5%BF%E5%85%B0&startDate=2018/02/01&endDate=2018/02/02&adults=2&searchPriorityOverride=213',
    #     # 'suggest': 'https://www.hotels.cn/search.do?resolved-location=CITY%3A707601%3AUNKNOWN%3AUNKNOWN&destination-id=707601&q-destination=%E8%92%99%E7%89%B9%E5%86%85%E7%BD%97,%20%E6%84%8F%E5%A4%A7%E5%88%A9&q-check-in=2018-02-01&q-check-out=2018-02-02&q-rooms=1&q-room-0-adults=2&q-room-0-children=0',
    #     'suggest':'https://www.expedia.com.hk/Hotel-Search?destination=%E8%92%99%E7%89%B9%E5%86%85%E7%BD%97%2C+%E6%84%8F%E5%A4%A7%E5%88%A9&latLong=44.507706%2C10.869584&regionId=6023643&startDate=&endDate=&rooms=1&_xpid=11905%7C1&adults=2',
    #     'check_in': '20180427',
    #     'stay_nights': '2',
    #     'occ': '2'
    # }

    spider = ExpediaListSpider(task)
    spider.crawl(required=['hotel'], cache_config={'enable': False})
    print(spider.code, spider.result)
    for i in spider.result['hotel']:
        print(i)

        # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{}] }
        # for i, content in enumerate(contents):
        #     print
        #     "case:", i, "*" * 200
        #     task.content = content
        #     spider = ExpediaListSpider(task)
        #     spider.crawl()
        #     for i, hotel in enumerate(spider.result['hotel']):
        #         print
        #         "数量", i, hotel
        #     for i, room in enumerate(spider.result['room']):
        #         print
        #         "数量：", i, room
        # [{
        #      "url": "https://www.expedia.com.hk/Hotel-Search?destination=%E9%98%BF%E6%8B%89%E7%B1%B3%E8%BE%BE%E5%85%AC%E5%9B%AD,+%E5%8A%A0%E5%88%A9%E7%A6%8F%E5%B0%BC%E4%BA%9A,+%E7%BE%8E%E5%88%A9%E5%9D%9A%E5%90%88%E4%BC%97%E5%9B%BD&startDate=2018/01/21&endDate=2018/01/22&adults=2&view=results"}]
        # [{
        #      "url": "https://www.expedia.com.hk/Hotel-Search?destination=%E8%8B%B1%E6%A0%BC%E5%B0%94%E4%BC%8D%E5%BE%B7,+%E5%8A%A0%E5%88%A9%E7%A6%8F%E5%B0%BC%E4%BA%9A%E5%B7%9E,+%E7%BE%8E%E5%9B%BD&startDate=2018/01/21&endDate=2018/01/22&adults=2"}]
        # [{
        #      "url": "https://www.expedia.com.hk/Hotel-Search?destination=%E4%B9%8C%E9%87%8C%E9%9B%85%E8%8B%8F%E5%90%88,+%E8%92%99%E5%8F%A4&startDate=2018/01/21&endDate=2018/01/22&adults=2"}]
        # [{
        #      "url": "https://www.expedia.com.hk/Hotel-Search?destination=%E5%93%88%E7%B1%B3%E7%BA%B3,+%E8%8A%AC%E5%85%B0&startDate=2018/01/21&endDate=2018/01/22&adults=2"}]
