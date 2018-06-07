#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年4月12日

@author: chenjinhui
'''
from mioji.common.task_info import Task
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common import parser_except
from mioji.common.class_common import Train
from common.city_common import City
import re
import json

class_dict = {'1': '标准车厢', '2': '商务车厢'}

headers = {
    'Accept': '*/*',
    'Accept-Encoding': "gzip, deflate",
    'Host': 'rails.ctrip.com',
    'Origin': 'http://rails.ctrip.com',
    'Referer': 'http://rails.ctrip.com/train/',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
}
url = "http://rails.ctrip.com/international/Ajax/PTPProductListHandler.ashx?Action=GetTrainProductList"

class testTrain(Train):

    def __str__(self):
        for k, v in self.__dict__.items():
            print k, '=>', v
        return 'testEND'

class CtripTWRailSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripTW_rail_spider.py'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'trains': {'version': 'InsertNewTrain'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctripTWRail': {'required': ['trains']}
    }

    def __init__(self, task=None):
        super(CtripTWRailSpider, self).__init__(task)
        if task:
            content = task.content
            ticket_info = task.ticket_info
            if 'start_time' in ticket_info:
                start_time = ticket_info['start_time']
            else:
                start_time = '00:00'
            contentlist = content.split('&')
            dept_city = contentlist[0].strip()
            self.user_datas['dept_city'] = dept_city
            dept_city_code = contentlist[1].strip()
            dest_city = contentlist[2].strip()
            self.user_datas['dest_city'] = dest_city
            dest_city_code = contentlist[3].strip()
            dept_day_tmp = contentlist[4].strip()
            dept_day = dept_day_tmp[0:4] + '-' + dept_day_tmp[4:6] + '-' + dept_day_tmp[6:8]
            dept_city_zh = City[dept_city]['city_name_zh']
            dest_city_zh = City[dest_city]['city_name_zh']
            adults, children, seniors, youth = 1, 0, 0, 0
            self.user_datas['data'] = {
                "adults": str(adults),
                "children": str(children),
                "seniors": str(seniors),
                "youth": str(youth),
                "departureDate": dept_day,
                "departureTimeHigh": "12:00",
                "departureTimeLow": "06:00",
                "fromCityCode": dept_city_code,
                "toCityCode": dest_city_code,
                "arriveDate": "",
                "startCityName": dept_city_zh,
                "destCityName": dest_city_zh,
                "backTimeHigh": "12:00",
                "backTimeLow": "06:00",
                "passHolders": "0",
                "searchType": "0",
                "pageStatus": "",
                "data": "null"
            }

    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=[self.parse_trains])
        def pages_request():
            fromcode = self.user_datas['data']['fromCityCode']
            tocode = self.user_datas['data']['toCityCode']
            date = self.user_datas['data']['departureDate']
            headers['Referer'] += fromcode + '-' + tocode + '?departureDate=' + date
            return {'req': {'url': url, 'method': 'post', 'headers': headers,
                            'data': {'value': json.dumps(self.user_datas['data'])}
                            },
                    'data': {'content_type': 'json'}}

        return [pages_request]

    def respon_callback(self, req, resp):
        print req, resp

    def parse_trains(self, req, data):
        # 可以通过request binding=[]指定解析方法
        dept_id = self.user_datas['dept_city']
        dest_id = self.user_datas['dest_city']
        page = data
        trains = []
        res = page
        bookingData = json.loads(res['BookingData'].replace('\"', '"'))
        products_list = bookingData["trainProductView"]
        dept_day = bookingData["trainProductListView"]["departureDate"]
        for product in products_list:
            train = testTrain()
            train.dept_day = dept_day
            train.dept_city = dept_id  # City[dept_city]['city_name_zh']
            train.dest_city = dest_id  # City[dest_city]['city_name_zh']

            train.dept_id = product["startStationName"] + '站'
            train.dest_id = product["arrivedStationName"] + '站'

            train.stopid = train.dept_id + '_' + train.dest_id
            train.dept_time = dept_day + ' ' + product["startTime"] + ':00'
            train.dest_time = dept_day + ' ' + product["arrivedTime"] + ':00'
            train.stoptime = train.dept_time + '_' + train.dest_time
            train.train_no = product["trainNumber"]
            train.train_type = product["TrainType"]
            dur = product["drivingTime"]
            dur_list = re.findall('\d+', dur)
            # print dur_list
            train.dur = int(dur_list[0]) * 3600 + int(dur_list[1]) * 60
            train.currency = "CNY"
            train.source = "ctripTW"
            train.tax = 0
            if train.train_type == 'TWGT':
                train.train_corp = '台湾高铁'
            else:
                train.train_corp = '台湾铁路公司'
            train.stop = 0
            train.daydiff = 0
            prices = product["trainCarriageAndTicketPrice"]
            for each in prices:
                train.price = float(each["AdultPrice"])
                seat_type = each["CarriageType"]
                train.seat_type = class_dict[str(seat_type)]
                train.real_class = class_dict[str(seat_type)]
                train_tuple = (train.train_no, train.train_type,
                               train.train_corp, train.dept_city, train.dept_id,
                               train.dest_city, train.dest_id, train.dept_day,
                               train.dept_time, train.dest_time, train.dur,
                               train.price, train.tax, train.currency, train.seat_type,
                               train.real_class, train.promotion, train.source,
                               train.return_rule, train.change_rule, train.stopid,
                               train.stoptime, train.daydiff, train.stop,
                               train.train_facilities, train.ticket_type,
                               train.electric_ticket, train.others_info, train.rest)
                trains.append(train_tuple)
        return trains


if __name__ == '__main__':
    task = Task()
    task.content = 'TPE&TWTB&HUA&TWHUALIAN&20170421'
    task.content = 'TPE&TWTB&TNN&TWTN&20170421'
    task.content = 'CIY&TWJY&TPE&TWTB&20170423'
    task.source = 'ctripTWRail'
    spider = CtripTWRailSpider(task)
    spider.crawl()
    print spider.result