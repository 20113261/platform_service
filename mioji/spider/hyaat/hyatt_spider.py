#!/usr/bin/env python
# -*- coding: utf-8-*-

import re
import json
import datetime
from lxml import etree
import gevent.pool

from mioji.common import parser_except
from mioji.common.class_common import Hotel
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room
from mioji.common import parser_except


class HyattSpider(Spider):
    source_type = 'hyattHotel'
    targets = {'room': {}}
    old_spider_tag = {'hyattHotel': {'required': ['room']}}

    def __init__(self, task=None):
        super(HyattSpider, self).__init__(task)
        self.query_data = {}
        self.room_doc = {}
        self.all_rooms = {}
        self.price_tax = []
        self.over_rooms = []
        self.need_flip_limit = False

    def fetch_ticket_info(self):
        # 解析任务
        hotel_id, nights, check_in = self.task.content.split('&')
        check_in_date = datetime.datetime.strptime(check_in, '%Y%m%d')
        days = datetime.timedelta(days=int(nights))
        room_info = self.task.ticket_info['room_info']
        # room = room_info[0].get('room_count', [])
        # if room != 1 :
        #     room =
        # adult = room_info[0].get('occ', [])

        check_out_date = check_in_date + days
        check_in, check_out = str(check_in_date).split(' ')[0], str(check_out_date).split(' ')[0]
        room = len(room_info)
        adult = 0
        child = 0
        ages = []
        for people in room_info:
            adult += len(people.get('adult_info', []))
            child += len(people.get("child_info", []))
            for age in people.get("child_info", []):
                ages.append(age)
        if room > 2:
            raise parser_except.ParserException(12, u'房间数不能超过两个')
        if adult > 5:
            raise parser_except.ParserException(12, u'成人数不能超过五个')
        if child > 4:
            raise parser_except.ParserException(12, u'成人数不能超过四个')
        self.query_data = dict(check_in=check_in, check_out=check_out, hotel_id=hotel_id, adults=adult, room=room,
                               kids=child, childAge1=-1, childAge2=-1, childAge3=-1, childAge4=-1)
        for index, age in enumerate(ages):
            self.query_data['childAge' + str(index + 1)] = age

        # print self.query_data

    def targets_request(self):
        self.fetch_ticket_info()
        url = "https://www.hyatt.com/en-US/shop/" + self.query_data['hotel_id']
        querystring = {"rooms": self.query_data['room'], "adults": self.query_data['adults'], "location": "hotelsname",
                       "checkinDate": self.query_data['check_in'],
                       "checkoutDate": self.query_data['check_out'], "accessibilityCheck": "false", "rate": "Standard",
                       "src":"agn_pfx_prop_sem_multi_other_zh_baidu_pc_20170704_brand-city-pc_phrase_brand-city-beijing_00002",
                       "kids": self.query_data['kids'], "currency": "CNY"}
        print querystring
        headers = {
            # 'accept-encoding': "gzip, deflate, br",
            # 'accept-language': "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            # 'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36",
            # 'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'authority': "www.hyatt.com",
        }

        # 打第一个接口
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            return {
                'req': {
                    'url': url,
                    'params': querystring,
                    'headers': headers
                },
                'user_handler': [self.parse_rooms_data],
            }

        yield first_page

        room_list = []
        self.price_tax = self.price_tax
        for i in self.price_tax:
            url = 'https://www.hyatt.com' + i[0]
            room_list.append({'req': {'url': url, 'method': 'get'}})

        # 打价格接口
        @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True, binding=self.parse_room)
        def get_price():
            return room_list

        yield get_price

    # 价格接口解析
    def parse_room(self, req, resp):
        # print resp
        room = Room()
        data = etree.HTML(resp)

        price2 = data.xpath('//dl[@class="subtotal bg-background definition-table pt1 ph2 mb0"]/dd/text()')[0]
        # price2 = 'CN¥4,450.71 CNY'
        price2 = price2.replace(',', '')

        price = re.findall(r'(\d+.\d+)', price2)[0]
        # try:
        #     price1 = re.findall(r'(\d*,*\d+\.\d+)', price2)[0]
        #     price = ''.join(price1.split(','))
        # except:
        #     price1 = re.findall(r'(\d+\.\d+)', price2)[0]
        #     price = ''.join(price1.split(','))

        tax2 = data.xpath(
            '//dl[@class="total-taxes-and-fees definition-table bg-background pt1 ph2 mb0 b-text_weight-bold"]/dd/text()')[
            0]
        # tax2 = 'CN¥1,417.10 CNY'
        tax2 = tax2.replace(',', '')
        # CN¥742.59 CNY
        # try:
        #     tax1 = re.findall(r'(\d+\.\d+)', tax2)[0]
        #     tax = ''.join(tax1.split(','))
        # except:
        #     tax1 = re.findall(r'(\d*,*\d+\.\d+)', tax2)[0]
        #     tax = ''.join(tax1.split(','))
        tax = re.findall(r'(\d+.\d+)', tax2)[0]

        # 房间id
        rate_plan_id = re.findall(r'"rate_plan":"(.*?)"', resp, re.S)[0]
        room_type_id = re.findall(r'"room_type":"(.*?)"', resp, re.S)[0]
        id = room_type_id + rate_plan_id
        self.room_doc[id] = [price, tax]
        self.all_rooms[id]['price'] = price
        self.all_rooms[id]['tax'] = tax
        room.hotel_name = self.all_rooms[id]['hotel_name']
        room.city = self.all_rooms[id]['city']
        room.source = self.all_rooms[id]['source']
        room.source_hotelid = self.all_rooms[id]['source_hotelid']
        room.source_roomid = str(self.all_rooms[id]['source_roomid'])
        room.real_source = self.all_rooms[id]['real_source']
        room.room_type = str(self.all_rooms[id]['room_type_T'])

        room.occupancy = self.query_data['adults']
        room.bed_type = self.all_rooms[id]['bed_type']
        room.size = self.all_rooms[id]['size']
        room.floor = -1
        room.check_in = self.all_rooms[id]['check_in']
        room.check_out = self.all_rooms[id]['check_out']
        room.rest = -1
        room.price = float(self.all_rooms[id]['price'])
        room.tax = float(self.all_rooms[id]['tax'])
        room.currency = 'CNY'.encode('utf-8')
        room.pay_method = '在线支付'.encode('utf-8')
        room.is_extrabed = 'No'
        room.is_extrabed_free = 'No'
        room.has_breakfast = self.all_rooms[id]['has_breakfast']
        # room.is_breakfast_free = ''
        room.is_cancel_free = ''
        room.is_cancel_free = self.all_rooms[id]['is_cancel_free']
        # room.extrabed_rule = ''
        room.return_rule = self.all_rooms[id]['return_rule']
        room.change_rule = ''
        room.room_desc = str(self.all_rooms[id]['room_desc'])
        room.others_info = [self.all_rooms[id]['others_info']][0]
        room.guest_info = ''

        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid,
                      room.source_roomid, room.real_source, room.room_type, room.occupancy,
                      room.bed_type, room.size, room.floor, room.check_in, room.check_out,
                      room.rest, room.price, room.tax, room.currency, room.pay_method,
                      room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free,
                      room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc,
                      room.others_info, room.guest_info)
        # print room_tuple
        return [room_tuple]

    # 除价格外所有的解析
    def parse_rooms_data(self, req, resp):
        data = etree.HTML(resp)
        try:
            # self.hotel_name = re.findall(r'"hotel_name":"(.*?)"', resp, re.S)[0].encode('utf8')
            hotel_name = data.xpath('//div[@class="hotel-name-text b-text_display-1 b-text_weight-bold"]//text()')
            self.hotel_name = hotel_name[0].replace('\n', '').strip()
        except:
            self.hotel_name = ''
        try:
            # self.hotel_city = re.findall(r'"hotel_city":"(.*?)"', resp, re.S)[0].encode('utf8')
            city = data.xpath('//p[@class="pv0"][2]/text()')
            self.hotel_city = city[0].split(',')[0]
        except:
            self.hotel_city = ''

        pages = data.xpath("//div[@class='content']")
        self.query_data['pages'] = pages

        rooms = {}
        for page in pages:
            # 一个页面
            # 解析房价规定：
            rule = page.xpath(
                ".//div[@class='col xs12 rate-rules-container b-text_copy-1 pb1 display-none']/div/text()")
            if 'breakfast' in rule[1] or 'Breakfast' in rule[1]:
                self.has_breakfast = 'Yes'
                zao = rule[1]
            else:
                self.has_breakfast = 'No'
                zao = ''
            try:
                self.return_rule = rule[-1]
            except:
                self.return_rule = ''

            self.source_roomid = page.xpath("./@data-id")[0]
            source_roomid_2 = \
                page.xpath('.//span[@class="b-text_copy-2 b-text_weight-bold display-xs-none display-sm-none"]/text()')[
                    0]

            # rooms_name_1 = page.xpath(".//span[@class='b-text_copy-2 b-text_weight-bold display-xs-none display-sm-none']/text()")[0]

            # 每间房
            roomss = page.xpath(".//div[@class='p-rate-card']")
            for room in roomss:
                room_test = {}
                # 每间房的ID
                room_type = room.xpath("./@data-room-type-code")[0]
                room_test['room_type'] = room_type

                # room_test['room_type_T'] = room_type + '--' + source_roomid_2
                try:
                    rooms_name = room.xpath(
                        ".//div[@class='b-text_copy-3 b-text_weight-bold display-xs-none display-sm-none']/text()")[0]
                except:
                    rooms_name = ''
                room_test['bed_type'] = rooms_name
                room_test['room_type_T'] = rooms_name + '--' + source_roomid_2
                # try:
                #     room_test['size'] = re.search(r'spacious (\d+)', resp, re.S)[0].encode('utf8')
                # except:
                #     room_test['size'] = -1
                try:
                    room_desc = room.xpath(".//div[@class='b-text_copy-2 text-preformatted room-desc mt1 mr3']/text()")[
                        0]
                except:
                    room_desc = ''
                try:
                    size_info = re.compile(u'\d+\.*\d*\s*[-]*\s*\.*\d*\s*Sqm|\d+-square-meter|\d+\ssquare\smetre|\d+-square-metre', re.I).findall(room_desc)[0]
                except:
                    size_info = ''
                temp_size = None
                if size_info:
                    temp_size = re.compile(u'(\d+)[-\s]*sq', re.I).findall(size_info)[0]
                if temp_size:
                    size = round(float(temp_size), 2)
                    room_test['size'] = size
                else:
                    room_test['size'] = -1
                if not size_info:
                    try:
                        size_info = re.compile(u'\d+\.*\d*\s*[-]*\s*\.*\d*\s*Sq|\d+-square-foot', re.I).findall(room_desc)[0]
                    except:
                        size_info = ''
                if size_info and not temp_size:
                    temp_size = re.compile(u'(\d+)[-\s]*sq', re.I).findall(size_info)[0]
                    if temp_size:
                        size = round(float(temp_size) / 10.7639104, 2)
                        room_test['size'] = size
                    else:
                        room_test['size'] = -1

                # size1 = re.findall(r"(\d\s*[-]*\s*\d*)", room_desc)
                # size2 = re.findall(r"(\d+) ()", room_desc)

                test_size = ''
                # if size1:
                #     test_size = ''.join(size1[0])
                #     room_test['size'] = int(size1[0][0].split(' ')[-1])
                # if size2:
                #     test_size = ''.join(size2[0])
                #     room_test['size'] = int(size2[0][0])
                room_test['room_desc'] = room_desc + ' | ' + rule[1].encode('raw-unicode-escape')
                room_test['city'] = self.hotel_city
                room_test['source'] = 'hyatt'.encode('utf-8')
                room_test['source_hotelid'] = self.query_data['hotel_id']
                room_test['real_source'] = 'hyatt'
                room_test['check_in'] = self.query_data['check_in']
                room_test['check_out'] = self.query_data['check_out']
                room_test['check_out'] = self.query_data['check_out']
                room_test['hotel_name'] = self.hotel_name
                room_test['source_roomid'] = self.source_roomid
                room_test['has_breakfast'] = self.has_breakfast
                room_test['return_rule'] = self.return_rule
                tig = 'No'

                if '48hours' in self.return_rule:
                    tig = 'NULL'
                elif 'Non-Refundable Full' in self.return_rule:
                    tig = 'No'
                room_test['is_cancel_free'] = tig
                room_test['others_info'] = json.dumps({'extra':
                    {
                        'breakfast': zao,
                        'payment': '在线支付'.encode('utf-8'),
                        'return_rule': self.return_rule,
                        'occ_des': '',
                        'occ_num': json.dumps(
                            {'adult_num': self.query_data['adults'], 'child_num': self.query_data['kids']}),
                        'size_info': size_info
                    }
                })

                url = room.xpath(".//a[@class='button-shop ph0']/@href")
                self.price_tax.append(url)
                # print room_test['room_type']
                # print self.source_roomid
                id = room_test['room_type'] + self.source_roomid
                # print id
                room_test['id'] = id
                self.all_rooms[id] = room_test


if __name__ == "__main__":
    from threading import Thread
    from mioji.common.task_info import Task
    # from mioji.common.utils import simple_get_socks_proxy_new, simple_get_socks_proxy
    from mioji.common import spider

    #
    # spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    lists = ['hangz']
    # 酒店id 夜晚 入住时间
    # task.content = 'cmezc&1&20180516'
    # task.content = 'cmezc&1&20180614'
    # task.content = 'hangz&1&20180530'
    # task.content = 'hangz&1&20180530'
    # task.content = 'cmezc&1&20180616'
    # task.content = 'cmezc&1&20180614'
    # task.content = 'hangz&1&20180530'
    # task.content = 'hangz&1&20180630'
    # task.content = 'detzl&1&20180830'
    task.content = 'beigh&1&20180506'

    task.ticket_info['room_info'] = [
        {"adult_info": [33, ], "child_info": [7, ]},
        # {"adult_info": [33], "child_info": [1]}
    ]
    task.source = 'hyatt'
    spider = HyattSpider(task)
    spider.crawl()

    # spider.crawl(required=['hotel'])
    print spider.code
    # print spider.result
    print json.dumps(spider.result, ensure_ascii=False, indent=4)

    # with open('hyatt.json', 'a') as f:
    #     f.write(json.dumps(spider.result, ensure_ascii=False))
    #     f.write('\n')



