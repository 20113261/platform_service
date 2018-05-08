# -*- coding: utf-8 -*-

from lxml import etree
import urllib
import re
from mioji.common import logger
from mioji.common import parser_except
import json
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Hotel


class GhaSpider(Spider):
    source_type = 'ghaDetailHotel'
    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'ghaDetailHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(GhaSpider, self).__init__(task)
        self.hotels = {}
        self.task = task
        self.reviewsurl = ""
        self.hotel = Hotel()

    def targets_request(self):

        url = self.task.content

        @request(retry_count=3,proxy_type=PROXY_REQ)
        def get_hotel():
            return {
                "req": {
                    "url": url,
                    "method": "get"
                },
                'user_handler': [self.parse_info],
            }
        yield get_hotel

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def get_reviews():
            return {
            "req": {
                "url": self.reviewsurl,
                "method": "get",
                "headers":{"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"}
            },
        }
        yield get_reviews

    def parse_info(self, req, resp):
        select = etree.HTML(resp)
        info = re.compile("pins\.gha_hotel\.push\((.*?)\)", re.S)
        address = re.compile("<script type=\"application/ld\+json\">(.*?)</script>", re.S)
        address = json.loads(address.findall(resp)[0])
        info =json.loads(info.findall(resp)[0])
        self.hotel.hotel_name = info["title"]
        self.hotel.hotel_name_en = address["name"]
        self.hotel.source = "gha"
        self.hotel.source_id = info["id"]
        self.hotel.brand_name = info["brand_name"]
        self.hotel.map_info = str(info["lon"])+","+str(info["lat"])
        self.hotel.address = ''.join(select.xpath("//adress/text()")).strip()
        self.hotel.city = address["address"]["addressLocality"]
        self.hotel.country = address["address"]["addressCountry"]
        self.hotel.postal_code = address["address"]["postalCode"]
        self.hotel.star = '5'
        reviewsurl = re.compile('<script src="//(.*?)"')
        self.reviewsurl = "http://"+reviewsurl.findall(resp)[0]
        service = select.xpath('//ul[@class="prop-Amenities"]/li/span/text()')
        self.hotel.service = '|'.join(service)
        if u"无线上网" in service:
            self.hotel.has_wifi = 'Yes'
        else:
            self.hotel.has_wifi = 'No'
        self.hotel.has_parking = 'NULL'
        self.hotel.is_parking_free = 'NULL'
        img_list = select.xpath('//div[@class="RotateBanner-itemImg"]/span/@style')
        imgurl = re.compile("url\('(.*?)'\)")
        imgurl_list = []
        for img in img_list:
            imgurl_list.append(imgurl.findall(img)[0])

        self.hotel.img_items = '|'.join(imgurl_list)
        description = select.xpath("//div[@id='content-about-hotel']/p/text()")
        self.hotel.description = ''.join(description)
        self.hotel.check_in_time = '14:00'
        self.hotel.check_out_time = '12:00'

    def parse_hotel(self, req, resp):
        grade = re.compile('<div class=\\\\"rating-value\\\\">\\\\n(.*?)%',re.S)
        self.hotel.grade = str(float(grade.findall(resp)[0].strip())/10)

        review = re.compile('<div class=\\\\"review-count\\\\">\\\\n(.*?)reviews',re.S)
        self.hotel.review_num = review.findall(resp)[0].strip()

        room_tuple = dict(
            hotel_name=self.hotel.hotel_name,
            hotel_name_en=self.hotel.hotel_name_en,
            source=self.hotel.source,
            source_id=self.hotel.source_id,
            brand_name=self.hotel.brand_name,
            map_info=self.hotel.map_info,
            address=self.hotel.address,
            city=self.hotel.city,
            country=self.hotel.country,
            postal_code=self.hotel.postal_code,
            star=self.hotel.star,
            grade=self.hotel.grade,
            review_num=self.hotel.review_num,
            has_wifi=self.hotel.has_wifi,
            is_wifi_free=self.hotel.is_wifi_free,
            has_parking=self.hotel.has_parking,
            is_parking_free=self.hotel.is_parking_free,
            service=self.hotel.service,
            img_items=self.hotel.img_items,
            description=self.hotel.description,
            accepted_cards=self.hotel.accepted_cards,
            check_in_time=self.hotel.check_in_time,
            check_out_time=self.hotel.check_out_time,
            hotel_url=self.hotel.hotel_url
        )
        # print room_tuple
        return [room_tuple]


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_http_proxy
    from mioji.common import spider
    # spider.slave_get_proxy = simple_get_http_proxy
    task = Task()
    spider = GhaSpider(task)

    task.content = 'https://zh.gha.com/Kempinski/Yanqi-Hotel-managed-by-Kempinski'
    spider.crawl()
    print spider.code
    print spider.result