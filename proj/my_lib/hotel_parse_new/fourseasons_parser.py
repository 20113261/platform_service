#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import time
import datetime
import json
import re
from lxml import etree

from mioji.common import logger
from mioji.common import parser_except
from mioji.common.class_common import Hotel_New
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW


class FourseasonsListHotel(Spider):
    source_type = 'fourseasonsDetailHotel'

    targets = {
        'hotel': {},
    }

    old_spider_tag = {
        'fourseasonsDetailHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.hotel_test = {}
        self.other_url = ['houston', ]
        self.status = 0
        super(FourseasonsListHotel, self).__init__(task)

    def targets_request(self):
        self.url = self.task.content

        # 酒店首页1
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_hotel_data():
            return {
                'req': {
                    'url': self.url,
                    'method': 'get',
                    'headers': {
                        'ihg-language': 'zh-CN',
                        'accept': 'application/json, text/plain, */*',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                    },
                },
                'user_handler': [self.parse_first],
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def get_ohter():
            return {
                'req': {
                    'url': self.url + 'accommodations/?c=t&_s_icmp=mmenu',
                    'method': 'get',
                    'headers': {
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                    },
                }
            }

        yield get_hotel_data
        # 特别 url
        for i in self.other_url:
            if i in self.url:
                @request(retry_count=3, proxy_type=PROXY_REQ)
                def get_map_info():
                    return {
                        'req': {
                            'url': 'https://www.fourseasons.com/zh/' + i,
                            'method': 'get',
                            'headers': {
                                'ihg-language': 'zh-CN',
                                'accept': 'application/json, text/plain, */*',
                                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                            },
                        },
                        'user_handler': [self.parse_map_info],
                    }

                yield get_map_info

        # fix by fnegyufei
        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def feng_map_info():
            return {
                'req': {'url': self.task.content + 'getting-here', 'method': 'get'},
                'data': {'content_type': 'html'},
                'user_handler': [self.parse_feng_map]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def servers():
            return {
                'req': {'url': self.task.content + 'services_and_amenities/other_facilities_and_services/complimentary_services_and_amenities/', 'method': 'get'},
                'user_handler': [self.parse_server]
            }
        # if self.status:
        #     yield servers

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def servers_T():
            return {
                'req': {
                    'url': self.task.content + 'services-and-amenities/',
                    'method': 'get'},
                'user_handler': [self.parse_server]
            }
        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def feng_map():
            return {
                'req': {'url': self.task.content + 'destination/directions_and_maps/', 'method': 'get'},
                'data': {'content_type': 'html'},
                'user_handler': [self.parse_feng]
            }

        # if self.hotel_test['map_info'] == ',':
        #     yield feng_map
        if self.hotel_test['map_info'] == ',':
            yield feng_map_info
        if self.status:
            yield feng_map
            yield servers
        else:
            yield servers_T
        yield get_ohter

    def parse_server(self, req, resp):
        self.resp_server = resp


    def parse_feng(self, req, resp):
        data = resp
        print resp
        try:
            lat = data.xpath("//span[@id='location-data']/@data-latitude")[0]
            lng = data.xpath("//span[@id='location-data']/@data-longitude")[0]
            self.hotel_test['map_info'] = lng + ',' + lat
            self.hotel_test['traffic'] = ''.join(data.xpath("//div[@class='wett_text']/ul/li//text()"))
            # self.status = 1
        except:
            pass

    def parse_feng_map(self, req, resp):
        data = resp
        try:
            ma = data.xpath("//div[@class='EmbeddedMap-map']/@data-map")[0]

            ma = json.loads(ma)
            self.hotel_test['map_info'] = ma['lng'] + ',' + ma['lat']
            self.hotel_test['traffic'] = ''
        except:
            pass


    def parse_first(self, req, resp):
        img_urls = ''
        data = etree.HTML(resp)
        self.hotel_test['hotel_name_en'] = ''
        try:
            self.hotel_test['hotel_name_en'] = re.findall(r'"name" : "(.*?)"', resp, re.S)[0].encode('utf-8')
        except:
            pass
        try:
            self.hotel_test['hotel_name_en'] = re.findall(r'"name": "(.*?)"', resp, re.S)[0].encode('utf-8')
        except:
            pass
        if self.hotel_test['hotel_name_en'] == '':
            self.hotel_test['hotel_name_en'] = 'Four Seasons ' + self.task.content.split('/')[-2]

        # self.hotel_test['source_id'] = re.findall(r'"hotelcode":"(.*?)"', resp, re.S)[0].encode('utf-8')
        try:
            self.hotel_test['source_id'] = data.xpath("//input[@name='generalReservationForm.locationId']/@value")[0]
            self.status = 1
        except:
            self.hotel_test['source_id'] = re.findall(r'"properties":\["(.*?)"\]', resp, re.S)[0].encode('utf-8')
        try:
            lat = re.findall(r'"lat":"(.*?)"', resp, re.S)[0].encode('utf-8')
            lng = re.findall(r'"lng":"(.*?)"', resp, re.S)[0].encode('utf-8')
        except:
            lat = ''
            lng = ''
        self.hotel_test['map_info'] = lng + ',' + lat
        address = "".join(data.xpath('//div[@class="schema-hidden"]//text()'))
        address = address.replace(' ', '').replace('\r\n', ' ')
        if not address:
            address = data.xpath('//address[@class="LocationBar-address"]//text()')[0]
        # address = data.xpath('normalize-space(//div[@class="schema-hidden"]//text()[1])').extract()
        self.hotel_test['address'] = address
        try:
            self.hotel_test['hotel_city'] = data.xpath('//input[@name="generalReservationForm.locationName"]/@value')[0]
        except:
            self.hotel_test['hotel_city'] = re.findall('"addressLocality" : "(.*?)"', resp, re.S)[0].encode('utf-8')

        self.hotel_test['country'] = re.findall(r'"property_subregion":"(.*?)"', resp, re.S)[0].encode('utf-8')

        try:
            self.hotel_test['hotel_postal_code'] = data.xpath('//span[@itemprop="postalCode"]/text()')[0]
        except:
            self.hotel_test['hotel_postal_code'] = ''
        # if 'Complimentary standard Wi-Fi' in resp:
        #     self.hotel_test['is_wifi_free'] = 'YES'
        #     self.hotel_test['has_wifi'] = 'YES'
        # else:
        #     self.hotel_test['is_wifi_free'] = ''
        #     self.hotel_test['has_wifi'] = ''
        # imgs = data.xpath('//*[@id="carousel"]/li[7]//img/@src')
        try:
            self.hotel_test['phone']= data.xpath("//li[@class='phone tk tk1 no-mobile-phone ']/span[@class='ltr invoca_class']//text()")[0]
        except:
            self.hotel_test['phone'] = re.findall('"telephone" : "(.*?)"',resp,re.S)[0]
        imgs = re.findall(r'&quot;(.*?)&quot;', resp, re.S)
        if not imgs:
            imgs = data.xpath('//img[@class="Image-img"]/@src')
        self.hotel_test['Img_first'] = imgs[0]
        for i in imgs:
            img_urls += ('https://www.fourseasons.com' + i + '|')
        self.hotel_test['img_items'] = img_urls
        # description = data.xpath('//meta[@property="og:description"]/@content')[0]
        # self.hotel_test['description'] = description.repalce('\n', '')
        self.hotel_test['description'] = data.xpath('//meta[@property="og:description"]/@content')[0]

    def parse_map_info(self, req, resp):
        data = etree.HTML(resp)
        all = data.xpath("//span[@class='detail-temp']/@data-lat-and-lon")[0]
        lat = all.split('/')[0]
        lng = all.split('/')[1]
        self.hotel_test['map_info'] = lng + ',' + lat

    def parse_hotel(self, req, resp):
        data = etree.HTML(resp)
        check_time = data.xpath('//table[@summary="Check In/Out times for [Resort]"]//span/text()')
        if check_time:
            check_in_time = check_time[0]
            check_out_time = check_time[1]
        else:
            try:
                check_in_time = re.findall('Check-in Time: (.*?)C', resp, re.S)[0].encode('utf-8')
                check_out_time = re.findall('Check-out Time: (.*?)\<', resp, re.S)[0].encode('utf-8')
            except:
                check_in_time = ''
                check_out_time = ''
        # service_titles = data.xpath('//div[@class="col-wrap col-wrap-re cf"]//span')
        # service_uls = data.xpath('//ul[@class="amenities-list"]')
        # service = ''
        # for service_name, s in zip(service_titles, service_uls):
        #     try:
        #         name = service_name.xpath(".//text()")[0]
        #         info = s.xpath('./li/text()')[0]
        #     except:
        #         continue
        #     service += '{}::{}|'.format(name, ''.join(info))
        hotel = Hotel_New()
        if 'bar' in resp:
            hotel.facility["Bar"] = 'Refrigerated private bar'
        if 'Complimentary standard internet' in resp:
            hotel.facility["Room_wifi"] = 'Complimentary standard internet'
            hotel.facility["Public_wifi"] = 'Complimentary standard internet'
        if 'dry-cleaning and pressing' in resp:
            hotel.service["Laundry"] = 'dry-cleaning and pressing'
        if 'Spa' in self.resp_server:
            hotel.facility["Spa"] = 'Spa'
        if 'Pool' in self.resp_server:
            hotel.facility["Swimming_Pool"] = 'Pool'
        if 'Fitness' in self.resp_server:
            hotel.facility["gym"] = 'Fitness Facilities'
        if 'Business' in self.resp_server:
            hotel.facility['Business_Centre'] = 'Business Services'

        if 'Coffee' in self.resp_server:
            hotel.facility[""] = "Coffee service"
        if 'shoe shine' in self.resp_server:
            hotel.facility["polish_shoes"] = 'shoe shine'
        if 'Multilingual concierge' in self.resp_server:
            hotel.service["Chinese_front"] = 'Multilingual concierge'
        if 'Wi-Fi' in self.resp_server:
            hotel.facility["Room_wifi"] = 'Complimentary standard internet'
            hotel.facility["Public_wifi"] = 'Complimentary standard internet'
        if 'car service' in self.resp_server:
            hotel.facility["Rental_service"] = 'car service'
        if 'Weddings' in self.resp_server:
            hotel.facility['Wedding_hall'] = 'Weddings'
        if 'Valet parkin' in self.resp_server:
            hotel.facility["Valet_Parking"] = 'Valet Parking'
        if 'fitness' in self.resp_server:
            hotel.facility["gym"] = 'Fitness Facilities'
        try:
            try:
                accepted_cards = data.xpath('//div[@class="slider"][4]/p/text()')[0]
            except:
                accepted_cards = data.xpath('//p[@class="Accordion-item-description"]/text()')[4]
            accepted_cards = accepted_cards.replace(',', '|')
        except:
            accepted_cards = 'UnionPay'
        hotels = []
        hotel.hotel_name = 'NULL'
        hotel.hotel_name_en = self.hotel_test['hotel_name_en']
        hotel.source = 'fourseasons'
        hotel.source_id = self.hotel_test['source_id']
        hotel.brand_name = '四季'.encode('utf-8')
        hotel.map_info = self.hotel_test['map_info']
        hotel.address = self.hotel_test['address']
        hotel.Img_first = self.hotel_test['Img_first']
        hotel.city = self.hotel_test['hotel_city']
        hotel.country = self.hotel_test['country']
        hotel.postal_code = self.hotel_test['hotel_postal_code']
        try:
            hotel.traffic = self.hotel_test["traffic"]
        except:
            pass
        hotel.star = 5

        hotel.grade = 'NULL'
        hotel.review_num = 'NULL'
        # hotel.has_wifi = self.hotel_test['has_wifi']
        # hotel.is_wifi_free = self.hotel_test['is_wifi_free']
        # hotel.has_parking = 'NULL'
        # hotel.is_parking_free = 'NULL'
        hotel.img_items = self.hotel_test['img_items']
        hotel.description = self.hotel_test['description']
        hotel.accepted_cards = accepted_cards
        hotel.check_in_time = check_in_time
        hotel.check_out_time = check_out_time
        hotel.hotel_url = self.task.content
        print hotel.to_dict()
        return hotels


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new, simple_get_socks_proxy
    from mioji.common import spider

    #
    # spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()
    task.ticket_info = {}
    # task.content = 'https://highlandsinn.hyatt.com/en/hotel/home.html'
    # task.content = 'https://www.fourseasons.com/zh/beijing/'
    # task.content = 'https://seattledowntown.place.hyatt.com/en/hotel/home.html'
    task.content = 'https://www.fourseasons.com/en/baku/'

    # task.content = 'https://www.fourseasons.com/en/anguilla/'
    # task.content = 'https://www.fourseasons.com/en/atlanta/'
    task.content = 'https://www.fourseasons.com/en/austin/'
    # task.content = 'https://www.fourseasons.com/en/oceanclub/'
    # task.content = 'https://www.fourseasons.com/en/maui/'
    # task.content = 'https://www.fourseasons.com/en/oahu/'
    task.content = 'https://www.fourseasons.com/en/houston/'
    # task.content = 'https://www.fourseasons.com/en/jacksonhole/'
    # task.content = 'https://www.fourseasons.com/en/lasvegas/'
    # task.content = 'https://www.fourseasons.com/en/losangeles/'
    # task.content = 'https://www.fourseasons.com/en/beverlywilshire/'
    # task.content = 'https://www.fourseasons.com/en/westlakevillage/'
    # task.content = 'https://www.fourseasons.com/en/mexico/'
    # task.content = 'https://www.fourseasons.com/en/miami/'
    # task.content = 'https://www.fourseasons.com/en/maldivesfse/'

    spider = FourseasonsListHotel(task)
    spider.crawl(required=['hotel'])
    print spider.code
    # print json.dumps(spider.result, ensure_ascii=False)
    print spider.result
