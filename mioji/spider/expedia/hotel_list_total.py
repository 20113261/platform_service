#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import datetime
import sys

sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8

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

DATE_F = '%Y/%m/%d'
URL0 = 'https://www.expedia.com.hk/Hotel-Search?&langid=2052'
URL1 = 'https://www.expedia.com.hk/Hotel-Search-Data?responsive=true'

def crate_params(ci, start_date, end_date, city_id, person_num, hashParam, ins):
    params = {
        'destination': ci,
        'startDate': start_date,
        'endDate': end_date,
        'regionId': city_id,
        'adults': str(person_num),
        'hashParam': '',
        'sort': 'recommended',
        'page': str(ins),
        'hsrIdentifier': 'HSR'
    }

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
                    self.user_datas['city_id'] = 'NULL'
                else:
                    if re.match(r'.+regionId=(\d+)', url):
                        self.user_datas['city_id'] = re.search(r'regionId=(\d+)', url).group(1)
                    elif re.match(r'.+regionId%3D', url):
                        self.user_datas['city_id'] = re.search(r'regionId%3D(\d+)', url).group(1)
                    else:
                        self.user_datas['city_id'] = 'NULL'
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
                self_p = get_suggest_city('expedia', mjcity_id)  # 初始这个城市的酒店和房间的详细信息
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            # print "self_p:",self_p
            city_id = self_p['gaiaId']  # 问题：从数据库获取了和mjcity_id有关的信息，我的问题就是mjcity_id和city_id都代表了什么
            self.user_datas['city_id'] = city_id
            self.user_datas['adult'] = task_p.adult  # 房间能居住成人数量
            self.user_datas['check_in'] = task_p.check_in  # 入住时间
            self.user_datas['check_out'] = task_p.check_out  # 退房时间
            self.user_datas['night'] = task_p.night  # 入住的天数
            start_date = task_p.format_check_in(DATE_F)
            end_date = task_p.format_check_out(DATE_F)






if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, simple_get_http_proxy

    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy

    task = Task()
    task.ticket_info = {
        'is_new_type': True,
        'suggest_type': 1,
        'suggest': 'https://www.expedia.com.hk/Hotel-Search?destination=%E8%89%BE%E5%BE%B7%E5%A4%AB%EF%BC%8C+%E5%9F%83%E5%8F%8A&latLong=24.971925%2C32.873620&regionId=6233562&startDate=&endDate=&rooms=1&_xpid=11905%7C1&adults=2',
        'check_in': '20170930',
        'stay_nights': '2',
        'occ': '2'
    }

    spider = ExpediaListSpider(task)
    spider.crawl(required=['hotel'])
    print spider.code, spider.result
