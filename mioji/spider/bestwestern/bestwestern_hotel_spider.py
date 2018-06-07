#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.spider import Spider, PROXY_REQ, PROXY_FLLOW, request
from mioji.common.task_info import Task
from mioji.common.class_common import Hotel
from lxml import etree
import re
import json


class HotelSpider(Spider):
    source_type = 'bestwesternHotel'
    targets = {
        'Hotel': {'version': 'InsertNewHotel'}
    }
    old_spider_tag = {
        'bestwesternHotel': {'required': 'Hotel'}
    }

    def __init__(self, task):
        Spider.__init__(self, task=None)
        self.task = task

    def targets_request(self):

        # 请求酒店详情页
        @request(retry_count=2, proxy_type=PROXY_REQ, binding=self.parse_Hotel)
        def first_request():
            return {
                'req': {
                    'url': self.task.content,
                    'method': 'get',
                    # 'headers':{
                    #     'Cookie':"search_checkInDate=2018-04-01;search_checkOutDate=2018-04-03"
                    #     }
                }
            }

        return [first_request]

    # 处理请求酒店详情页的响应
    def parse_Hotel(self, req, resp):
        # 响应的cookie
        cookies = req['resp'].cookies

        html = etree.HTML(resp)
        hotel = Hotel()

        # 酒店名
        hotel.hotel_name = html.xpath('//div[contains(@class,"hotelImagebloc")]//h1[@id="hotel-name"]/a/text()')[0]
        # 酒店源
        hotel.source = 'bestwestern'
        # 酒店id
        hotel.source_id = self.task.content.split('-')[-1]
        # 酒店品牌名
        hotel.brand_name = self.__get_brand_name(html)
        # 酒店经纬度
        hotel.map_info = self.__get_map_info(cookies)
        # 酒店地址
        hotel.address = "".join(html.xpath(
            '//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span/text()'))
        # 酒店所在城市
        hotel.city = html.xpath(
            '//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span[@id="address-1-city-state-zip"]/text()')[
            0]
        # 酒店所在国家
        hotel.country = \
            html.xpath('//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span')[
                -1].text
        # 酒店邮编
        hotel.postal_code = html.xpath(
            '//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]//span[@class="postalCode"]/text()')[
            0]
        # 酒店星级
        hotel.star = 5
        # 酒店评分
        hotel.grade = html.xpath('//div[@class="tripAdvisorOwl"]/img/@src')[0].split("/")[-1].split('-')[0]
        # 酒店评价
        hotel.review_num = re.search(r'\d+', html.xpath(
            '//div[@class="tripAdvisorOwl"]//div[@class="reviewRatingCount"]/text()')[0]).group()
        # 是否有wifi,wifi是否免费
        hotel.has_wifi, hotel.is_wifi_free = self.__wifi(resp)
        # 是否有停车场
        hotel.has_parking = 'NULL'
        # 停车场是否免费
        hotel.is_parking_free = 'NULL'
        # 酒店服务
        hotel.service = self.__get_hotel_service(html)
        # 酒店照片
        hotel.img_items = ",".join(html.xpath("//div[contains(@class, 'hotelImageSlider')]//li/img/@src"))
        # 酒店描述
        hotel.description = html.xpath('//div[@class="hotelOverviewDetailSection"]/div[@class="overviewText"]/text()')[
            0].strip()
        # 是否接受信用卡
        hotel.accepted_cards = 'NULL'
        # 入住时间
        hotel.check_in_time = \
            html.xpath('//div[@class="uk-width-3-10 checkInPositionContainer addressCheckInTableCell"]/p[2]/text()')[0]
        # 退房时间
        hotel.check_out_time = \
            html.xpath('//div[@class="phoneNumbers"]/div[contains(@class,"phonesRow")][1]/div[2]/p[2]/text()')[0]
        # 酒店url
        hotel.hotel_url = self.task.content

        # 酒店信息
        hotel_info = tuple([
            hotel.hotel_name,
            hotel.hotel_name,
            hotel.source,
            hotel.source_id,
            hotel.brand_name,
            hotel.map_info,
            hotel.address,
            hotel.city,
            hotel.country,
            "NULL",
            hotel.postal_code,
            hotel.star,
            hotel.grade,
            hotel.review_num,
            hotel.has_wifi,
            hotel.is_wifi_free,
            hotel.has_parking,
            hotel.is_parking_free,
            hotel.service,
            hotel.img_items,
            hotel.description,
            hotel.accepted_cards,
            hotel.check_in_time,
            hotel.check_out_time,
            hotel.hotel_url,
            "NULL"
        ])

        print hotel_info
        return hotel_info

    # 获取酒店品牌名
    def __get_brand_name(self, html):
        src = html.xpath('//div[contains(@class,"hotelImagebloc")]//div[@class="uk-width-1-1"]/img/@src')[0]
        brand_name = src.split("/")[-1].split('_')[0]
        return brand_name

    # 获取酒店经纬度
    def __get_map_info(self, cookies):
        map_info = {c.name: c.value for c in cookies if c.name in ["search_locationLat", "search_locationLng"]}
        map = ",".join(map_info.values())
        return map

    # 获取酒店服务
    def __get_hotel_service(self, html):
        hotel_service = ";".join(html.xpath(
            '//div[@class="hotelAmenities"]//div[contains(@class,"hotelAmenities")]//div[contains(@class,"hotelAmenities")]/ul//li/text()'))
        room_service = ";".join(html.xpath(
            '//div[@class="hotelAmenities"]//div[contains(@class,"roomAmenities")]//ul[@id="roomamenities"]/li/text()'))
        service = hotel_service + ";" + room_service
        return service

    # 判断是否有Wi-Fi,及费用
    # has_wifi = 1 表示有Wi-Fi
    # is_wifi_free = 1 表示Wi-Fi免费
    def __wifi(self, html):
        # 判断Wi-Fi
        if re.findall(r'免费无线', html):
            result = "有免费无线"
        elif re.findall(r'无线网络', html):
            result = "有无线"
        else:
            result = "没有无线"
        # 返回结果
        if result == "有免费无线":
            has_wifi = 'YES'
            is_wifi_free = 'YES'
        elif result == "有无线":
            has_wifi = 'YES'
            is_wifi_free = 'NULL'
        else:
            has_wifi = 'NULL'
            is_wifi_free = 'NULL'

        return has_wifi, is_wifi_free


if __name__ == '__main__':
    task = Task()
    # task.content = 'https://www.bestwestern.net.cn/booking-path/hotel-details/best-western-plus-amedia-berlin-kurfuerstendamm-berlin-95473'
    task.content = 'https://www.bestwestern.net.cn/booking-path/hotel-details/best-western-corona-london-83799'
    # task.content = 'https://www.bestwestern.net.cn/booking-path/hotel-details/best-western-plus-gran-hotel-centro-historico-guadalajara-70271'
    spider = HotelSpider(task)
    spider.crawl()
