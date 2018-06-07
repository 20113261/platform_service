#!/usr/bin/env python
# -*- coding:utf-8 -*-


import re
import datetime
import urlparse
from lxml.html import tostring
from mioji.common.task_info import Task
from mioji.common.class_common import Room
from mioji.models.city_models import get_suggest_city
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


def get_postData():
    pass

base_url = "http://hotels.ctrip.com/international/{0}"
class TestSpider(Spider):

    source_type = "ctripListHotel"
    targets = {"hotel": {'version': 'InsertHotel_room4'}}
    old_spider_tag = {'ctripListHotel': {'required': ['hotel']}}
    total_page = 0

    def get_post_data(self):

        data = {
            'cityPY':self.cityPy,
            'cityId':self.cityId,
            'checkIn':self.checkIn,
            'checkOut': self.checkOut,
        }
        return data
    def targets_request(self):
        if self.task.ticket_info.get('is_new_type'):
            self.rooms = self.task.ticket_info.get('occ')
            night = self.task.ticket_info.get('stay_nights')
            check_in = self.task.ticket_info.get('check_in')
            hotel_url = self.task.ticket_info.get('suggest')
            self.checkIn = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10]
            self.checkOut = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + datetime.timedelta(
                    int(night)))[:10]
            if self.task.ticket_info.get('suggest_type') == 1:
                cityId_Py = re.search(r'international/([a-zA-Z]+)([0-9]+)', hotel_url)
                self.cityId = cityId_Py.group(2)
                self.cityPy = cityId_Py.group(1)
                city_id = ''.join([self.cityPy,self.cityId])
            else:
                suggest_json = self.task.ticket_info.get('suggest').split('|')
                self.cityId,self.cityPy = suggest_json[5],suggest_json[6]
                self.mioji_city_id = 'NULL'
                city_id = ''.join([self.cityPy,self.cityId])
        else:
            taskcontent = self.task.content
            taskcontent = taskcontent.encode('utf-8')
            task_infos = taskcontent.split('&')
            self.mioji_city_id, self.rooms, stay_nights, check_in = task_infos[0], task_infos[1], task_infos[2], \
                                                                    task_infos[3]
            suggest_city = get_suggest_city('ctrip', str(self.mioji_city_id))
            is_new_type = suggest_city.get('is_new_type')
            self_p = suggest_city.get('suggest')
            if is_new_type == 0:
                self_p = self_p.split('|')

                self.cityId, self.cityPy = self_p[5], self_p[6]
            else:
                hotel_url = self_p.get('url')
                cityId_Py = re.search(r'international/([a-zA-Z]+)([0-9]+)', hotel_url)
                self.cityId = cityId_Py.group(2)
                self.cityPy = cityId_Py.group(1)
            self.checkOut = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]),
                                                  int(check_in[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
            self.checkIn = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
            city_id = ''.join([self.cityPy,self.cityId])

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def first_page():
            data = self.get_post_data()
            return {
                'req': {'url': base_url.format(city_id),'method':'post','data':data},
                'data': {'content_type': 'html'},
            }

        yield first_page

    def parse_hotel(self,req,data):
        tree = data
        hotel_count = tree.xpath('//span[contains(@class,"total_htl")]/span/text()')[0].strip()
        print "hotel_count:",hotel_count
        return [hotel_count,]

if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    spider.get_proxy = simple_get_socks_proxy
    task = Task()
    contents = [
        '51505&1&1&20171228'
    ]
    task.ticket_info = {
        'is_new_type': False,
        'suggest_type': 2,
        'suggest': "Paris|\u5df4\u9ece\uff0c\u6cd5\u5170\u897f\u5c9b\u5927\u533a\uff0c\u6cd5\u56fd|city|192|paris|192|paris|%E5%B7%B4%E9%BB%8E|3105|0||3600",
        'check_in': '20171130',
        'stay_nights': '2',
        'occ': '2'
    }
    task.content = contents[0]
    spider = TestSpider(task)
    ret = spider.crawl(required=['hotel'], cache_config={'enable': False})
    print spider.result
    print spider.result['hotel']