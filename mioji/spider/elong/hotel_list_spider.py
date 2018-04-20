#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

test gitflow bugfix

@author: dujun
'''

import re
import datetime

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, mioji_data, PROXY_FLLOW, PROXY_REQ
from mioji.common import parser_except
import hotellist_parse
from mioji.models.city_models import get_suggest_city
import datetime
from datetime import timedelta
from urllib import urlencode
import re
import json

DATE_F = '%Y-%m-%d'
URL = 'http://ihotel.elong.com/list/AjaxGetHotelList?'

base_url = 'http://ihotel.elong.com/region_{0}/'
hd = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Host': 'ihotel.elong.com',
}


class ElongListSpider(Spider):
    source_type = 'elongListHotel'
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
        'elongListHotel': {'required': ['room']}
    }

    def targets_request(self):
        if self.task.ticket_info.get('is_new_type'):
            self.user_datas['night'] = self.task.ticket_info.get('stay_nights')
            self.user_datas['adult'] = self.task.ticket_info.get('occ')
            check_in = self.task.ticket_info.get('check_in')
            self.user_datas['check_in'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10]
            self.user_datas['check_out'] = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + timedelta(
                    int(self.user_datas['night'])))[:10]
            if self.task.ticket_info.get("suggest_type") == 1:
                hotel_url = self.task.ticket_info.get('suggest')
                self.user_datas['city_id'] = re.search(r'region_([0-9]+)', hotel_url).group(1)
            else:
                suggest_json = json.loads(self.task.ticket_info.get('suggest'))
                self.user_datas['city_id'] = suggest_json.get('id') or suggest_json.get('regionId')
            check_in = self.user_datas['check_in']
            check_out = self.user_datas['check_out']    
            person_num = self.user_datas['adult']
            city_id = self.user_datas['city_id']
            self.user_datas['mjcity_id'] = 'NULL'
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]
                task_p = creat_hotelParams(self.task.content)
                self.user_datas['mjcity_id'] = mjcity_id
                suggest_city = get_suggest_city('elong',mjcity_id)
                self_p = suggest_city.get('suggest')
                is_new_type = suggest_city.get('is_new_type')
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            if is_new_type == 0:
                try:
                    city_id = self_p.get('regionId') or self_p['id']
                except:
                    city_id = self_p['regionResult']['regionId']
            else:
                hotel_url = self_p.get('url')
                city_id = re.search(r'region_([0-9]+)', hotel_url).group(1)

            self.user_datas['city_id'] = city_id

            self.user_datas['adult'] = task_p.adult
            self.user_datas['check_in'] = task_p.check_in
            self.user_datas['check_out'] = task_p.check_out
            self.user_datas['night'] = task_p.night

            check_in = task_p.format_check_in(DATE_F)
            check_out = task_p.format_check_out(DATE_F)
            person_num = str(task_p.adult)
        ages = person_num + '|' + person_num + '+0+'
        hd = {
            'Cookie': 'IHotelSearch=RoomPerson=' + ages + '&RegionId=' + str(city_id) + '&OutDate=' + check_out + '&InDate=' + check_in + '; IHotelSearchData={"InDate":' + check_in + ',"OutDate":' + check_out + ',"RegionId":' + str(city_id) + ',"RoomPerson":' + ages + '}; s_cc=true',
            "Host": 'ihotel.elong.com'
        }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel', 'room'])
        def first_page():
            param = {
                'regionID': self.user_datas['city_id'],
                'sort': '0',
                'pageNo': str(1)
            }
            hd.update({'Referer':base_url.format(self.user_datas['city_id'])})
            params_str = urlencode(param)
            return {'req': {'url': URL+params_str,'headers':hd},
                    'data': {'content_type': 'json'},
                    'user_handler': [self.parse_next_page]}

        # one by one
        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=['hotel', 'room'])
        def all_pages():
            page_num = self.user_datas.get('pageNum', 1)
            # by 产品，限制翻页 10
            page_num = min((10, page_num))
            pages = []
            for i in xrange(1, page_num):
                param = {
                    'regionID': self.user_datas['city_id'],
                    'sort': '0',
                    'pageNo': str(i)
                }
                params_str = urlencode(param)
                hd.update({'Referer':base_url.format(self.user_datas['city_id'])})
                pages.append(
                    {
                        'req':
                            {
                             'url': URL+params_str,
                             'headers': hd,
                             },
                        'data': {'content_type': 'json'}
                    }
                )
            return pages

        return [first_page, all_pages, ]

    def parse_next_page(self, req, data):
        # print self.browser.headers, 'dsadsadsadsadsadsadsadsad'
        # 防止编码错误
        try:
            # raw_input()
            # print data
            pageNum = int(data['page']['pageNum'])
            print pageNum, '=' * 100
            self.user_datas['pageNum'] = pageNum
        except Exception, e:
            print str(e), '=' * 100
            pass

    def parse_hotel(self, req, data):
        # print data

        return hotellist_parse.parse_hotels_hotel(data)  # mioji_id 没有办

    def parse_room(self, req, data):
        # return []
        return hotellist_parse.parse_hotels_room(self.user_datas['city_id'], data, self.user_datas['check_in'],
                                                 self.user_datas['check_out'], self.user_datas['night'],
                                                 self.user_datas['adult'], self.user_datas['mjcity_id'])


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy
    import json

    task = Task()
    # suggest = json.dumps({"success_times": 0, "is_assigned": 0, "error": -1, "proxy": "10.10.95.70", "workload_key": "20550_2_elongListHotel_1_20180116", "id": "7", "priority": 0, "update_times": 0, "content": "20550&2&1&20180116", "source": "elongListHotel", "score": "-100", "timeslot": 240})
    # suggest = json.dumps({"url": "http://ihotel.elong.com/region_6025647/"})
    # task.ticket_info = {
    #     'is_new_type': 1,
    #     'suggest_type': 1,
    #     'suggest': suggest,
    #     'check_in': '20180430',
    #     'stay_nights': '2',
    #     'occ': '2'
    # }
    # task.content = '10156&2&1&20180328'
    task.content = '60336&2&1&20180328'
    # task.extra['hotel'] = {'check_in':'20170504', 'nights':1, 'rooms':[{}] }
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2, 'child_age':[0, 6]}] * 2}
    # print json.dumps(task.extra['hotel'])
    spider = ElongListSpider(task)
    ss = spider.crawl()
    print spider.result
    print spider.result['room']
    # print spider.first_url()
