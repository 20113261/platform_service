#!/usr/bin/env python
# -*- coding:utf-8 -*-



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
import re
import json

DATE_F = '%Y-%m-%d'

hd = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip,deflate,br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

base_url = 'http://ihotel.elong.com/region_{0}'

class ElongListSpider(Spider):
    source_type = 'elongListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
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
            city_id = self.user_datas['city_id']
            self.user_datas['mjcity_id'] = 'NULL'
        else:
            try:
                mjcity_id = self.task.content.split('&')[0]
                task_p = creat_hotelParams(self.task.content)
                self.user_datas['mjcity_id'] = mjcity_id
                self_p = get_suggest_city('elong', mjcity_id)
                if not self_p:
                    raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                        'can’t find suggest config city:[{0}]'.format(mjcity_id))
            except Exception, e:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'parse task occur some error:[{0}]'.format(e))
            city_id = self_p['regionId']


        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel'])
        def first_page():
            return {'req': {'url':base_url.format(city_id), 'headers': hd},
                    'data': {'content_type': 'html'},
                    }
        yield first_page

    def parse_hotel(self,req,data):
        tree = data
        str_content = tree.xpath(('//script[contains(text(),"hotelNum")]'))[0]
        hotel_total = re.search(r"hotelNum:'([0-9]+)'",str_content.text_content()).group(1)

        return [hotel_total,]

if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy
    import json

    task = Task()
    content = json.dumps({"hotelCnt": "2810", "composedName": "巴黎及周边-法国", "stateNameCn": "法国", "regionId": "179898", "regionNameEn": "Paris and vicinity", "countryNameCn": "法国", "regionNameCn": "巴黎及周边"})
    task.ticket_info = {
        'is_new_type': True,
        'suggest_type': 2,
        'suggest': content,
        'check_in': '20170930',
        'stay_nights': '2',
        'occ': '2'
    }
    task.content = '10003&2&1&20171104'
    # task.extra['hotel'] = {'check_in':'20170504', 'nights':1, 'rooms':[{}] }
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2}]}
    # task.extra['hotel'] = {'check_in':'20170403', 'nights':1, 'rooms':[{'adult':1, 'child':2, 'child_age':[0, 6]}] * 2}
    # print json.dumps(task.extra['hotel'])
    spider = ElongListSpider(task)
    ss = spider.crawl()
    print spider.result
    # print spider.first_url()