#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import time
import datetime
import json
import re
try:
    from lxml import etree
except:
    import lxml.etree as etree

from mioji.common import logger
from mioji.common import parser_except
# from mioji.common.class_common import Hotel as Hotel_New
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
# from mioji.common.class_common import Hotel_New
from proj.my_lib.models.HotelModel import HotelNewBase as Hotel_New
# from proj.my_lib.models.HotelModel import HotelNewBase

class HyattHotelSpider(Spider):
    source_type = 'hyattDetailHotel'

    targets = {
        'hotel': {},
    }

    old_spider_tag = {
        'hyattDetailHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.hotel_test = {}
        super(HyattHotelSpider, self).__init__(task)
        self.url_newUrl = {
            'https://abudhabi.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/united-arab-emirates/park-hyatt-abu-dhabi-hotel-and-villas/abuph',
            'https://beavercreek.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/colorado/park-hyatt-beaver-creek-resort-and-spa/beave',
            'https://bangkok.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/thailand/park-hyatt-bangkok/bkkph',
            'https://buenosaires.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/argentina/palacio-duhau-park-hyatt-buenos-aires/bueph',
            'https://canberra.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/australia/hyatt-hotel-canberra-a-park-hyatt-hotel/canbe',
            'https://chennai.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/india/park-hyatt-chennai/cheph',
            'https://chicago.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/illinois/park-hyatt-chicago/chiph',
            'https://playadelcarmen.grand.hyatt.com/en/hotel/home.html': 'https://playadelcarmen.grand.hyatt.com/en/hotel/home.html',
            'https://dubai.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/united-arab-emirates/park-hyatt-dubai/dxbph',
            # 'https://macae.place.hyatt.com/en/hotel/home.html': 'https://macae.place.hyatt.com/en/hotel/home.html',
            'https://goa.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/india/park-hyatt-goa-resort-and-spa/goarg',
            'https://hamburg.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/germany/park-hyatt-hamburg/hamph',
            'https://hyderabad.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/india/park-hyatt-hyderabad/hydph',
            'https://istanbul.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/turkey/park-hyatt-istanbul-macka-palas/istph',
            'https://jeddah.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/saudi-arabia/park-hyatt-jeddah-marina-club-and-spa/jedph',
            'https://mallorca.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/spain/park-hyatt-mallorca/malph',
            'https://mendoza.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/argentina/park-hyatt-mendoza-hotel-casino-and-spa/menph',
            'https://milan.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/italy/park-hyatt-milan/milph',
            'https://maldiveshadahaa.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/maldives/park-hyatt-maldives-hadahaa/mldph',
            'https://moscow.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/russia/ararat-park-hyatt-moscow/mosph',
            'https://newyork.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/new-york/park-hyatt-new-york/nycph',
            'https://parisvendome.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/france/park-hyatt-paris-vendome/parph',
            'https://siemreap.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/cambodia/park-hyatt-siem-reap/repph',
            'https://saigon.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/vietnam/park-hyatt-saigon/saiph',
            'https://shanghai.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/china/park-hyatt-shanghai/shaph',
            'https://stkitts.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/saint-kitts-and-nevis/park-hyatt-st-kitts/skbph',
            'https://sydney.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/australia/park-hyatt-sydney/sydph',
            'https://toronto.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/canada/park-hyatt-toronto/torph',
            'https://vienna.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/austria/park-hyatt-vienna/vieph',
            'https://washingtondc.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/washington-dc/park-hyatt-washington-dc/wasph',
            'https://zanzibar.park.hyatt.com/en/hotel/home.html': 'https://www.hyatt.com/en-US/hotel/tanzania/park-hyatt-zanzibar/znzph',
            'https://zurich.park.hyatt.com/en/hotel/home.html':'https://www.hyatt.com/en-US/hotel/switzerland/park-hyatt-zurich/zurph',

        }

    def targets_request(self):
        self.url_en = self.task.content
        self.url = self.url_en.split('/en')[0]
        self.url_cn = self.url_en.replace('/en/hotel/', '/zh-Hans/hotel/abridged/')
        self.url_cn_2 = self.url_en.replace('/en-US/', '/zh-CN/')

        self.url_en = self.url_newUrl.get(self.url_en, self.url_en)
        # 一种页面模式
        if 'www.hyatt.com' in self.url_en:
            # 酒店首页1
            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_hotel_data():
                return {
                    'req': {
                        'url': self.url_en,
                        'method': 'get',
                        'headers': {
                            # 'ihg-language': 'zh-CN',
                            'Connection': 'keep-alive',
                            'accept-language': 'zh-CN,zh;q=0.9',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_www_com1],
                }

            @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_hotel)
            def get_hotel_data_rooms():
                return {
                    'req': {
                        'url': self.url_en+'/rooms',
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_www_com_rooms],
                }

            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_hotel_grade_and_reviews():
                return {
                    'req': {
                        'url': self.url_en + '/photos-reviews',
                        'method': 'get',
                        'headers': {
                            'referer':self.url_en,
                            'connection':'keep-alive',
                            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_www_grade_and_reviews],
                }


            yield get_hotel_data
            yield get_hotel_grade_and_reviews
            yield get_hotel_data_rooms
        # 另一种页面模式
        else:
            #酒店首页1
            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_hotel_data():
                return {
                    'req': {
                        'url': self.url_en,
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_hotel_key],
                }
            # 获取儿童信息
            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_children():
                return {
                    'req': {
                        'url': self.url+'/hyatt/help.jsp?language=en#kids',
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_children],
                }
            # 获取英文酒店页面
            @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
            def get_English_data():
                return {
                    'req': {
                        'url': self.url_en,
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_English_hotel],
                }
            # 获取评论条数和评分
            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_grade():
                return {
                    'req': {
                        'url': self.url+'/bin/tripadvisorreviews?service=getAggregatedReviewRatingAndTotalReviews&locationKey='+self.locationKey,
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    # 'data': {'content_type': 'json'},
                    'user_handler': [self.parse_hotel_grade_review_num],
                }

            # 获取入住退房时间
            @request(retry_count=3, proxy_type=PROXY_REQ)
            def get_time():
                return {
                    'req': {
                        'url': self.url + '/en/hotel/our-hotel.html',
                        'method': 'get',
                        'headers': {
                            'ihg-language': 'zh-CN',
                            'accept': 'application/json, text/plain, */*',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        },
                    },
                    'user_handler': [self.parse_hotel_time],
                }

            # 获取服务页面

            yield get_hotel_data
            yield get_time
            yield get_grade
            yield get_children
            yield get_English_data

    def parse_hotel_key(self,req ,resp):
        try:
            self.locationKey = re.findall(r'locationKey="(.*?)"', resp, re.S)[0]
        except:
            self.locationKey = ''

    def parse_hotel_time(self, req, resp):
        data = etree.HTML(resp)
        try:
            self.hotel_test['check_in_time'] = data.xpath("//span[@class='checkinoutTime'][1]/text()")[0]
            self.hotel_test['check_out_time'] = data.xpath("//span[@class='checkinoutTime'][2]/text()")[0]
        except :
            self.hotel_test['check_in_time'] = 'NUll'
            self.hotel_test['check_out_time'] = 'NULL'

    def parse_hotel_grade_review_num(self,req, resp):
        try:
            resp = json.loads(resp)
            a = resp['totalReview']
            b = resp['aggregatedReviewRating']
            self.hotel_test['grade'] = b
            self.hotel_test['review_num'] = a
        except:
            self.hotel_test['grade'] = 'NULL'
            self.hotel_test['review_num'] = 'NULL'


    def parse_English_hotel(self, req, resp):
        data = etree.HTML(resp)
        try :
            self.hotel_test['hotel_name_en'] = data.xpath("//p[@class='homePropertyName']//text()")[0]
        except:
            raise parser_except.ParserException(22,'代理失效，重试')
        self.hotel_test['source'] = 'hyatt'
        self.hotel_test['brand_name'] = '凯悦'
        self.hotel_test['source_id'] = re.findall(r"var spiritCode='(.*?)'", resp, re.S)[0].encode('utf8')

        latitude = re.findall(r'"latitude" : "(.*?)"', resp, re.S)[0].encode('utf8')
        longitude = re.findall(r'"longitude" : "(.*?)"', resp, re.S)[0].encode('utf8')
        self.hotel_test['map_info'] = longitude + ',' + latitude
        # self.hotel_test['address'] = data.xpath("//p[@class='address']//text()")[0]
        self.hotel_test['address'] = ''.join(data.xpath("//p[@class='address']//text()"))
        self.hotel_test['hotel_city'] = re.findall(r'hotel_city:"(.*?)"', resp, re.S)[0].encode('utf-8')
        self.hotel_test['hotel_country'] = data.xpath("//p[@class='address']/span[1]/text()")[0]
        try :
            self.hotel_test['hotel_postal_code'] = data.xpath("//p[@class='address']/span[2]/text()")[0]
        except:
            self.hotel_test['hotel_postal_code'] = 'NULL'
        self.hotel_test['star'] = '5.0'
        self.hotel_test['grade'] = self.hotel_test['grade']
        self.hotel_test['review_num'] = self.hotel_test['review_num']

        wifi = data.xpath(
            "//img[@src='/content/dam/PropertyWebsites/andaz/nycaw/Media/All/xBHSG_RightRail_Four_101216.png.pagespeed.ic.1FAby01L8_.png']")
        if len(wifi):
            # self.hotel_test['has_wifi'] = 'YES'
            self.hotel_test['has_wifi'] = 'Free WiFi'
            self.hotel_test['is_wifi_free'] = 'YES'
        else:
            # self.hotel_test['has_wifi'] = 'NULL'
            self.hotel_test['has_wifi'] = ''
            self.hotel_test['is_wifi_free'] = 'NULL'

        self.hotel_test['has_parking'] = 'NULL'
        self.hotel_test['is_parking_free'] = 'NULL'
        # self.hotel_test['services'] = 'NULL'
        self.hotel_test['services'] = ''

        imgs = data.xpath("//div[@class='carousel fullWidth floatL']//a/img/@src")[0]
        url = self.url_en.split('/en')[0]
        self.hotel_test['img_items'] = url + imgs



        # self.hotel_test['description'] = data.xpath("//div[@class='readMoreContent']//text()")[0]
        self.hotel_test['description'] = data.xpath("/html/head/meta[1]/@content")[0]

        while '\n' in self.hotel_test['description']:
            self.hotel_test['description'].remove('\n')
        self.hotel_test['accepted_cards'] = 'NULL'
        self.hotel_test['check_in_time'] = self.hotel_test['check_in_time']
        self.hotel_test['check_out_time'] = self.hotel_test['check_out_time']
        self.hotel_test['hotel_url'] = self.url_en
        try:
            self.hotel_test['Img_first'] = self.url+data.xpath("//div[@class='carousel fullWidth floatL']//@src")[0]
        except:
            self.hotel_test['Img_first'] = ''

        phone= data.xpath("//p[@class='phnNo']/text()")[0].split('+')[1]
        self.hotel_test['hotel_phone'] = phone.replace(' ','')

    # 第二种页面
    def parse_www_com1(self, req, resp):
        data = etree.HTML(resp)
        self.hotel_test['hotel_name_en'] = re.findall(r'hotel_name: "(.*?)"', resp, re.S)[0].encode('utf8')
        try:
            latitude = re.findall(r'"latitude": "(.*?)"', resp, re.S)[0].encode('utf8')
            longitude = re.findall(r'"longitude": "(.*?)"', resp, re.S)[0].encode('utf8')
        except:
            latitude = re.findall(r'"latitude":"(.*?)"', resp, re.S)[0].encode('utf8')
            longitude = re.findall(r'"longitude":"(.*?)"', resp, re.S)[0].encode('utf8')
        self.hotel_test['map_info'] = str(longitude) + ',' + str(latitude)

        try:
            addressLine1 = re.findall(r'"addressLine1": "(.*?)"', resp, re.S)[0].encode('utf8')
            addressLine2 = re.findall(r'"addressLine2": "(.*?)"', resp, re.S)[0].encode('utf8')
            self.hotel_test['address'] = addressLine1 + addressLine2
        except:
            self.hotel_test['address'] = re.findall(r'"streetAddress":"(.*?)"',resp, re.S)[0].encode('utf-8')
        try:
            self.hotel_test['source_id'] = re.findall(r'name="spiritCode" value="(.*?)"', resp, re.S)[0].encode('utf8')
        except:
            self.hotel_test['source_id'] = re.findall(r'hotel_spirit_code: "(.*?)"', resp, re.S)[0].encode('utf8')
        self.hotel_test['hotel_city'] = re.findall(r'hotel_city: "(.*?)"', resp, re.S)[0].encode('utf8')
        # self.hotel_test['hotel_country'] = re.findall(r'hotel_country: "(.*?)"', resp, re.S)[0].encode('utf8')
        self.hotel_test['hotel_country'] = re.findall(r'"addressLine2": "(.*?)"', resp, re.S)[0].split(',')[-2].encode('utf8')

        self.hotel_test['hotel_postal_code'] = re.findall(r'hotel_postal_code: "(.*?)"', resp, re.S)[0].encode('utf8')

        try:
            self.hotel_test['has_wifi'] = re.findall('Wi-Fi', resp ,re.S)[0].encode('utf8')
            # if self.hotel_test['has_wifi']:
            #     self.hotel_test['has_wifi'] = 'YES'
        except:
            # self.hotel_test['has_wifi'] = 'NULL'
            self.hotel_test['has_wifi'] = ''

        try:
            is_wifi_free = re.findall('Complimentary Wi-Fi', resp,re.S)[0].encode('utf8')
            if is_wifi_free:
                self.hotel_test['is_wifi_free'] = 'YES'
        except:
            self.hotel_test['is_wifi_free'] = 'NULL'

        # a = data.xpath("//div[@class='cq-dd-fragment']/div/p/text()")[0]
        # self.hotel_test['description'] = a
        try:
            self.hotel_test['description'] = re.findall('"description":"(.*?)"', resp, re.S)[0].encode('utf-8')
            # print data.xpath('/html/head/meta[1]/@content')
            # self.hotel_test['description'] = data.xpath('/html/head/meta[1]/@content')[0]
        except:
            self.hotel_test['description'] = 'NULL'
        # self.hotel_test['services']= data.xpath("//div[@class='titled-list Business Services']//li/text()")
        self.hotel_test['services'] = data.xpath("//li//text()")
        # try:
        #     for one in services:
        #         ser = one+'|'
        #     self.hotel_test['services'] = 'Business Services::'+ser
        # except:
        #     # self.hotel_test['services'] = 'NULL'
        #     self.hotel_test['services'] = ''

        self.hotel_test['img_items'] = data.xpath("//div[@class='banner js-object-fit']//img/@src")[0]
        self.hotel_test['accepted_cards'] = 'NULL'
        try:
            self.hotel_test['Img_first'] = data.xpath("//picture//@src")[0]
        except:
            self.hotel_test['Img_first'] = ''
        phone = data.xpath('//dd[@class="phone"]//text()')[0].split('+')[1]
        self.hotel_test['hotel_phone'] = phone.replace(' ', '')
        self.hotel_test['chiled_bed_type'] = ''

    def parse_www_com_rooms(self,req, resp):
        data = etree.HTML(resp)
        try:
            self.hotel_test['check_in_time'] = data.xpath("//div[@class='check-in']//span[@class='time']/text()")[0]
            self.hotel_test['check_out_time'] = data.xpath("//div[@class='check-out']//span[@class='time']/text()")[0]
        except:
            self.hotel_test['check_in_time'] = 'NULL'
            self.hotel_test['check_out_time'] = 'NULL'

    def parse_www_grade_and_reviews(self, req, resp):
        # reviews = re.findall('reviewCount":"(.*?)"', resp)
        reviews = re.findall('based on (\d+) reviews', resp)
        self.hotel_test['review_num'] = reviews[0] if reviews else 'NULL'
        grades = re.findall('stars-(\d+).svg', resp)
        grade = grades[0] if grades else ''
        if grade:
            self.hotel_test['grade'] = grade[0:-1]+'.'+grade[-1:]


    def parse_children(self, req, resp):
        data = etree.HTML(resp)
        try:
            self.hotel_test['chiled_bed_type'] = data.xpath('//*[@id="corp-profiles-description"]/div[5]/div[2]/text()')[1].strip('\n')
        except:
            self.hotel_test['chiled_bed_type'] = ''
    # 返回数据
    def parse_hotel(self,req, resp):
        hotels = []
        # hotel = Hotel()
        hotel = Hotel_New()
        # hotel = BaseModel()
        hotel.hotel_name = 'NULL'
        hotel.hotel_name_en = self.hotel_test['hotel_name_en']
        hotel.source = 'hyatt'
        hotel.source_id = self.hotel_test['source_id']
        hotel.brand_name = '凯悦'
        hotel.map_info = self.hotel_test['map_info']
        hotel.address = self.hotel_test['address']
        hotel.city = self.hotel_test['hotel_city']
        hotel.country = self.hotel_test['hotel_country']
        hotel.postal_code = self.hotel_test['hotel_postal_code']
        hotel.star = 5
        hotel.grade = self.hotel_test.get('grade', hotel.grade)
        hotel.review_num = 'NULL'
        print self.hotel_test.get('review_num')
        hotel.review_num = self.hotel_test.get('review_num', 'NULL')
        # hotel.has_wifi = self.hotel_test['has_wifi']
        # hotel.is_wifi_free = self.hotel_test['is_wifi_free']
        # hotel.has_parking = 'NULL'
        # hotel.is_parking_free = 'NULL'
        # hotel.service = self.hotel_test['services']
        # hotel.img_items = self.hotel_test['img_items']
        hotel.description = self.hotel_test['description']
        hotel.Img_first = self.hotel_test['Img_first']
        hotel.hotel_phone = self.hotel_test['hotel_phone']
        hotel.hotel_zip_code = self.hotel_test['hotel_postal_code']
        hotel.traffic = ''
        hotel.chiled_bed_type = self.hotel_test['chiled_bed_type']
        hotel.pet_type = ''
        if self.hotel_test['has_wifi']:
            hotel.facility_content['Room_wifi'] = self.hotel_test['has_wifi']
        for one  in self.hotel_test['services']:
            one = one.lower()
            if 'faxing' in one:
                hotel.service_content['Fax_copy'] = one
            elif 'postal' in one:
                hotel.service_content['Postal_Service'] = one
            elif 'laundry' in one:
                hotel.service_content['Laundry'] = one
            elif 'room service' in one:
                hotel.service_content['Food_delivery'] = one
            elif 'concierge service' in one:
                hotel.service_content['Protocol'] = one
            elif 'babysitting' in one:
                hotel.service_content['child_care'] = one
            elif 'shoeshine' in one:
                hotel.service_content['polish_shoes'] = one


            elif 'valet parking' in one:
                hotel.facility_content['Valet_Parking'] = one
            elif 'parking' in one:
                hotel.facility_content['Parking'] = one
            elif 'wifi' in one or 'wi-fi' in one:
                hotel.facility_content['Room_wifi'] = one
            elif 'pool' in one:
                hotel.facility_content['Swimming_Pool'] = one
            elif 'gym' in one:
                hotel.facility_content['gym'] = one
            elif 'bar' in one:
                hotel.facility_content['Bar'] = one
            elif 'coffee' in one:
                hotel.facility_content['coffee'] = one
            elif 'parking' in one:
                hotel.facility_content['Parking'] = one
            elif 'spa' in one:
                hotel.facility_content['SPA'] = one
            elif 'golf' in one:
                hotel.facility_content['Golf_Course'] = one
            elif 'restaurant' in one:
                hotel.facility_content['Restaurant'] = one
            elif 'sauna' in one:
                hotel.facility_content['Sauna'] = one
            elif 'service to airport' in one or 'shuttle airport' in one:
                hotel.facility_content['Airport_bus'] = one
            elif 'wedding' in one:
                hotel.facility_content['Wedding_hall'] = one
            elif 'restaurant' in one:
                hotel.facility_content['Restaurant'] = one
            elif 'business centre' in one:
                hotel.facility_content['Business_Centre'] = one
            elif 'sereno Spa' in one:
                hotel.facility_content['Mandara_Spa'] = one
            elif 'tennis' in one:
                hotel.facility_content['Tennis_court'] = one
            elif 'spa' in one:
                hotel.facility_content['SPA'] = one

            elif "China_Friendly" in one:
                hotel.feature_content['China_Friendly'] = one
            elif "Romantic_lovers" in one:
                hotel.feature_content['Romantic_lovers'] = one
            elif "Parent_child" in one:
                hotel.feature_content['Parent_child'] = one
            elif "Beach_Scene" in one:
                hotel.feature_content['Beach_Scene'] = one
            elif "Hot_spring" in one:
                hotel.feature_content['Hot_spring'] = one
            elif "Japanese_Hotel" in one:
                hotel.feature_content['Japanese_Hotel'] = one
            elif "Vacation" in one:
                hotel.feature_content['Vacation'] = one

        hotel.accepted_cards = 'NULL'
        hotel.check_in_time = self.hotel_test['check_in_time']
        hotel.check_out_time = self.hotel_test['check_out_time']
        hotel.hotel_url = self.url_en


        # hotel_tuple = dict(
        #     hotel_name=hotel.hotel_name,
        #     hotel_name_en=hotel.hotel_name_en,
        #     source=hotel.source,
        #     source_id=hotel.source_id,
        #     brand_name=hotel.brand_name,
        #     map_info=hotel.map_info,
        #     address=hotel.address,
        #     city=hotel.city,
        #     country=hotel.country,
        #     postal_code=hotel.postal_code,
        #     star=hotel.star,
        #     grade=hotel.grade,
        #     review_num=hotel.review_num,
        #     has_wifi=hotel.has_wifi,
        #     is_wifi_free=hotel.is_wifi_free,
        #     has_parking=hotel.has_parking,
        #     is_parking_free=hotel.is_parking_free,
        #     service=hotel.service,
        #     img_items=hotel.img_items,
        #     description=hotel.description,
        #     accepted_cards=hotel.accepted_cards,
        #     check_in_time=hotel.check_in_time,
        #     check_out_time=hotel.check_out_time,
        #     hotel_url=hotel.hotel_url,
        # )
        # hotels.append(hotel_tuple)
        # return hotels
        res = hotel.to_dict()
        res = json.loads(res)

        # print json.dumps(res,ensure_ascii=False)
        return res


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new,simple_get_socks_proxy
    from mioji.common import spider
    #
    # spider.slave_get_proxy = simple_get_socks_proxy
    urls = [
        # 'https://parisvendome.park.hyatt.com/en/hotel/home.html',
        'https://saigon.park.hyatt.com/en/hotel/home.html',
        'https://toronto.park.hyatt.com/en/hotel/home.html',
        'https://toronto.park.hyatt.com/en/hotel/home.html',
        'https://seattledowntown.place.hyatt.com/en/hotel/home.html',
        'https://www.hyatt.com/en-US/hotel/italy/park-hyatt-milan/milph',
        'https://www.hyatt.com/en-US/hotel/china/park-hyatt-shanghai/shaph',
        'https://www.hyatt.com/en-US/hotel/france/park-hyatt-paris-vendome/parph',
        'https://www.hyatt.com/en-US/hotel/cambodia/park-hyatt-siem-reap/repph',
        'https://www.hyatt.com/en-US/hotel/vietnam/park-hyatt-saigon/saiph',
        'https://www.hyatt.com/en-US/hotel/china/park-hyatt-shanghai/shaph',
        'https://www.hyatt.com/en-US/hotel/saint-kitts-and-nevis/park-hyatt-st-kitts/skbph',
        'https://www.hyatt.com/en-US/hotel/australia/park-hyatt-sydney/sydph',
        'https://www.hyatt.com/en-US/hotel/canada/park-hyatt-toronto/torph',
        'https://www.hyatt.com/en-US/hotel/austria/park-hyatt-vienna/vieph',
        'https://www.hyatt.com/en-US/hotel/washington-dc/park-hyatt-washington-dc/wasph',
        'https://www.hyatt.com/en-US/hotel/tanzania/park-hyatt-zanzibar/znzph',
        'https://www.hyatt.com/en-US/hotel/switzerland/park-hyatt-zurich/zurph'
    ]
    results = []

    # for url in urls:
    task = Task()
    task.ticket_info = {}
    # task.content = 'https://highlandsinn.hyatt.com/en/hotel/home.html'
    # task.content = 'https://kochibolgatty.grand.hyatt.com/en/hotel/home.html'
    # task.content = 'https://albuquerqueairport.place.hyatt.com/en/hotel/home.html'
    # task.content = 'https://newyork.park.hyatt.com/en/hotel/home.html'
    # task.content = 'https://macae.place.hyatt.com/en/hotel/home.html'
    # task.content = 'https://parisvendome.park.hyatt.com/en/hotel/home.html'
    # task.content = 'https://saigon.park.hyatt.com/en/hotel/home.html'
    # task.content = 'https://toronto.park.hyatt.com/en/hotel/home.html'
    # task.content = 'https://toronto.park.hyatt.com/en/hotel/home.html'


    # task.content = 'https://seattledowntown.place.hyatt.com/en/hotel/home.html'



    # task.content = 'https://www.hyatt.com/en-US/hotel/italy/park-hyatt-milan/milph'

    # task.content = 'https://www.hyatt.com/en-US/hotel/china/park-hyatt-shanghai/shaph'  # here
    # task.content = 'https://www.hyatt.com/en-US/hotel/france/park-hyatt-paris-vendome/parph'
    # task.content = 'https://www.hyatt.com/en-US/hotel/cambodia/park-hyatt-siem-reap/repph'
    #{"service_content": {"20011": {"key": "洗衣服务", "value": "laundry"}, "21003": {"key": "送餐服务", "value": "room service"}}, "hotel_name_en": "Park Hyatt St. Kitts", "city_id": "NULL", "brand_name": "凯悦", "check_in_time": "4:00 PM", "postal_code": "KN7000", "pet_type": "", "continent": "NULL", "description": "Escape to the glamour and luxury of the Caribbean Islands and find five-star service, beachfront rooms, and refined resort dining at Park Hyatt St. Kitts. ", "city": "St. Kitts", "chiled_bed_type": "", "facility_content": {"13004": {"key": "餐厅", "value": "restaurant on-site"}, "12003": {"key": "SPA", "value": "more than 7,000 square feet of flexible event space and banquet facilities"}, "10001": {"key": "客房wifi", "value": "wi-fi"}, "12001": {"key": "游泳池", "value": "the penthouse suite offers a private swimming pool and terrace from the hotel’s top floor"}}, "map_info": "-62.638056,17.228889", "grade": "NULL", "others_info": "NULL", "img_items": "NULL", "hotel_url": "https://www.hyatt.com/en-US/hotel/saint-kitts-and-nevis/park-hyatt-st-kitts/skbph", "Img_first": "https://assets.hyatt.com/content/dam/hyatt/hyattdam/images/2017/11/27/1306/Park-Hyatt-St-Kitts-P098-Park-Executive-Suite-Pool.jpg/Park-Hyatt-St-Kitts-P098-Park-Executive-Suite-Pool.16x9.adapt.1280.720.jpg", "star": 5, "accepted_cards": "NULL", "traffic": "", "address": "Banana Bay, PO Box 1073, BasseterreSt. Kitts, Saint Kitts and Nevis, KN7000", "check_out_time": "12:00 PM", "hotel_name": "NULL", "hotel_phone": "18694681234", "hotel_zip_code": "KN7000", "country": " Saint Kitts and Nevis", "feature_content": {}, "source": "hyatt", "source_id": "skbph", "review_num": "NULL"}

    # task.content = 'https://www.hyatt.com/en-US/hotel/vietnam/park-hyatt-saigon/saiph'
    # task.content = 'https://www.hyatt.com/en-US/hotel/china/park-hyatt-shanghai/shaph'
    # task.content = 'https://www.hyatt.com/en-US/hotel/saint-kitts-and-nevis/park-hyatt-st-kitts/skbph'
    # task.content = 'https://www.hyatt.com/en-US/hotel/australia/park-hyatt-sydney/sydph'
    task.content = 'https://www.hyatt.com/en-US/hotel/canada/park-hyatt-toronto/torph' # !!!
    task.content = 'https://www.hyatt.com/en-US/hotel/austria/park-hyatt-vienna/vieph'
    task.content = 'https://www.hyatt.com/en-US/hotel/washington-dc/park-hyatt-washington-dc/wasph'
    task.content = 'https://www.hyatt.com/en-US/hotel/tanzania/park-hyatt-zanzibar/znzph'
    task.content = 'https://www.hyatt.com/en-US/hotel/switzerland/park-hyatt-zurich/zurph'

    spider = HyattHotelSpider(task)
    spider.crawl(required=['hotel'])
    print spider.code
    # print spider.result
    print json.dumps(spider.result['hotel'][0], ensure_ascii=False)
    # results.append(json.dumps(spider.result['hotel'][0], ensure_ascii=False))
    # print spider.result['hotel'][0]

    # print '*'*30
    # for result in results:
    #     print result
