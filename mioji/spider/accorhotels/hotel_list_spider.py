#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import datetime
import urllib
from mioji.common.task_info import Task
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
setdefaultencoding_utf8()


class AccorListSpider(Spider):

    source_type = 'accorListHotel'
    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'accorListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(AccorListSpider, self).__init__(task=task)
        self.page = 1
        self.hotel_list = []
        self.total = 0

    @property
    def content_parser(self):
        city_id = str(json.loads(self.task.ticket_info['suggest'])['Code'])
        night = int(self.task.ticket_info['stay_nights'])
        checkin = datetime.datetime.strptime(self.task.ticket_info['check_in'], "%Y%m%d")
        checkout = checkin + datetime.timedelta(days=night)
        check_in = checkin.strftime("%Y-%m-%d")
        check_out = checkout.strftime("%Y-%m-%d")
        return city_id, check_in, check_out

    def targets_request(self):
        city_id, check_in, check_out = self.content_parser
        init_url = 'https://m.accorhotels.cn/api/search/'
        url = 'https://m.accorhotels.cn/api/search/{}'
        data = {"clientCode": "",
                "clientTimeZoneDifference": -480,
                "contractNumber": "",
                "endDate": "{}T00:00:00.000Z".format(check_out),
                "international": "",
                "loyaltyCardNumber": "",
                "prefferentialCode": "",
                "searchGeoCode": '{}'.format(city_id),
                "searchHotelNameText": "",
                "searchRidCode": "",
                "searchText": "",
                "startDate": "{}T00:00:00.000Z".format(check_in),
                "retrieved": 0,
                "fromLocation": False}

        @request(retry_count=5, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def get_init_url():
            return {'req': {
                'method': 'POST',
                'url': init_url,
                'data': data
            }}
        yield get_init_url

        while len(self.hotel_list) < self.total:
            @request(retry_count=5, proxy_type=PROXY_FLLOW, async=True, binding=self.parse_hotel)
            def get_url():
                pages = []
                num = int(self.total)/8 + 1
                for i in range(num):
                    self.page += 1
                    pages.append({'req': {
                    'method': 'GET',
                    'url': url.format(self.page)
                    }})
                return pages
            yield get_url

    def parse_hotel(self, req, res):
        data = json.loads(res)
        self.total = data['search']['total']
        hotel_list = data['hotelList']
        for hotel in hotel_list:
            hotel_code = hotel['code']
            hotel_name = hotel['name']
            hotel_url = 'https://www.accorhotels.com/zh/hotel-{}-{}/index.shtml'.format(
                hotel_code, urllib.quote(hotel_name.replace(' ', '-').encode('utf-8')))
            self.hotel_list.append((hotel_code, hotel_url))
        return self.hotel_list


if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy_new
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = AccorListSpider(task)
    task.ticket_info = {
        'is_new_type': True,
        'suggest_type': 2,
        'suggest': '''{"PinyinName": null, "GeoType": "VI", "Code": "V126676", "Name": "Paris, \u6cd5\u56fd", "AlternativeName": "Paris, France"}''',
        'dest_city': '巴黎',
        'check_in': '20180518',
        'stay_nights': '2',
        'occ': '1',
        'tid': 'demo',
        'used_times': 0
    }
    result = spider.crawl()
    print result
    print spider.result
