#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/7 下午8:54
# @Author  : Hou Rong
# @Site    : 
# @File    : hotelbeds_spider.py
# @Software: PyCharm
import hashlib
import time
import datetime
import json
import dateutil.parser
import types
import sys
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common import parser_except
from common.class_common import Room
from itertools import groupby
from copy import deepcopy
from urlparse import urljoin
from mioji.common.check_book.check_book_ratio import  use_record_qid


def include_breakfast(board_code):
    """
    given a board code, return True of False, indicate whether including breakfast
    :param board_code:
    :return: True or False
    """
    primary_code = board_code.split("-")[0]
    # RO = Room only, SC = SELF CATERING, only these 2 code means no breakfast at current moment
    if primary_code in ['RO', 'SC']:
        return False
    return True


class HotelBedsSpider(Spider):
    source_type = 'hotelbedsApiHotel'

    targets = {
        'room': {}
    }

    old_spider_tag = {
        'hotelbedsApiHotel': {
            'required': ['room']
        }
    }

    def __init__(self, task=None):
        super(HotelBedsSpider, self).__init__(task)

    def targets_request(self):
        # 下移 task 相关内容
        auth = self.task.ticket_info.get('auth', {})
        if isinstance(auth, types.StringTypes):
            auth = json.loads(auth)
        elif isinstance(auth, types.DictType):
            auth = auth
        else:
            auth = {}

        # 增加对121错误的支持
        base_url = auth.get('api_key', None)
        requestor = auth.get('secret', None)
        secreta = auth.get('url', None)

        if not base_url or not requestor or not secreta:
            raise parser_except.ParserException(121, '无认证信息')

        task = self.task
        use_record_qid(unionKey='hotelbedsApi', api_name="SEARCH BY HOTEL CODE", task=task, record_tuple=[1, 0, 0])
        self.api_key = auth['api_key']
        self.shared_secret = auth['secret']
        self.sig_str = "%s%s%d" % (self.api_key, self.shared_secret, int(time.time()))
        self.signature = hashlib.sha256(self.sig_str).hexdigest()
        self.host = auth['url']

        # task parse
        content = self.task.content
        info = content.split('&')
        city_id, hotel_id, cnt_nights, check_in = info[:4]
        rooms = self.task.ticket_info.get("room_info", [{"room_count": 1, "occ": 2}])
        if rooms[0]['occ'] == 0:
            rooms[0]['occ'] = 2
        cnt_nights = int(cnt_nights)
        year, month, day = check_in[0:4], check_in[4:6], check_in[6:]
        check_in = year + '-' + month + '-' + day
        check_out = str(datetime.datetime(int(year), int(month), int(day)) + datetime.timedelta(days=int(cnt_nights)))[
                    :10]

        self.check_in = check_in
        self.check_out = check_out
        self.rooms = rooms
        self.hotel_id = hotel_id
        self.city_id = city_id

        self.redis_key = 'NULL'
        if hasattr(self.task, 'redis_key'):
            self.redis_key = self.task.redis_key

        @request(retry_count=3, proxy_type=PROXY_NONE)
        def auth_request():
            return {
                'req': {
                    'url': urljoin(self.host, 'status'),
                    'headers': {
                        "X-Signature": self.signature,
                        "Api-Key": self.api_key,
                        "Accept": "application/json"
                    }
                },
                'data': {
                    'content_type': 'json'
                },
                'users_handler': [
                    self.parse_api_key,
                ]
            }

        @request(retry_count=3, proxy_type=PROXY_NONE, binding=self.parse_room)
        def get_hotel():
            return {
                'req': {
                    'method': 'post',
                    'url': urljoin(self.host, 'hotels'),
                    'headers': {
                        'Api-Key': self.api_key,
                        'Accept-Encoding': 'Gzip',
                        'X-Signature': self.signature,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    'json': {
                        "stay": {
                            "checkIn": self.check_in,
                            "checkOut": self.check_out
                        },
                        "occupancies": map(
                            lambda x: {"rooms": x.get("room_count", x.get("num", 1)), "adults": x["occ"], "children": 0,
                                       "paxes": [{"type": "AD"}] * x["occ"]}, self.rooms),
                        "paymentData": "AT_WEB",
                        "hotels": {
                            "hotel": [
                                int(self.hotel_id)
                            ]
                        },
                    }
                },
                'data': {
                    'content_type': 'json'
                }
            }

        yield auth_request
        yield get_hotel

    @staticmethod
    def include_breakfast(board_code):
        """
        given a board code, return True of False, indicate whether including breakfast
        :param board_code:
        :return: True or False
        """
        primary_code = board_code.split("-")[0]
        # RO = Room only, SC = SELF CATERING, only these 2 code means no breakfast at current moment
        if primary_code in ['RO', 'SC']:
            return False
        return True

    def response_error(self,req, resp, error):
        # 目前测试403为认证信息错误所返回code
        if resp.status_code == 403:
            raise parser_except.ParserException(122, '认证信息错误')

    def room_parser(self, data_pair, template, room_index):
        """

        :param data_pair: a list contains 2 elements, both are dictionary which contains rate info
        :param template: a Room instance which contains only hotel info but no room info
        :return: a complete Room instance
        """
        # secondary, primary = data_pair
        secondary = data_pair

        # parse data in primary first
        def attr(key):
            return secondary.get(key)

        room = deepcopy(template)
        room.source_roomid = attr('source_roomid')
        room.room_type = attr("room_type")

        room.occupancy = attr('adults') + attr('children')

        # room.pay_method = attr('paymentType') or room.pay_method
        room.pay_method = 'mioji'

        try:
            room.rest = attr('allotment')
        except Exception, e:
            room.rest = -1

        comments = {}

        # if "breakfast" in attr('boardName').lower():
        board_cd = attr('boardCode')

        room.is_breakfast_free = 'Yes' if self.include_breakfast(board_cd) else 'No'

        gross_price = attr('sellingRate')
        # sometimes sellingRate is not given, use net price + taxes instead
        if gross_price is None:
            room.price = float(attr('net'))
            taxes = attr('taxes')
            if taxes:
                room.tax = sum(float(x["amount"]) for x in taxes["taxes"] if x["included"] == False)
        else:
            room.price = float(gross_price)
            room.tax = 0

        room.price /= attr("rooms")
        room.tax /= attr("rooms")

        room.room_type = attr("room_type")

        cancellation = attr('cancellationPolicies')
        if cancellation:
            room.return_rule = ''.join(['%s后取消收取%s%s;' % (x["from"], x["amount"], room.currency) for x in cancellation])
            charge_from = min([dateutil.parser.parse(x["from"]) for x in cancellation])
            room.is_cancel_free = 'Yes' if charge_from > datetime.datetime.now(charge_from.tzinfo) else 'No'

        # important message regarding price from hotel master as per document
        comments["remarks"] = attr('rateComments') or ''

        # record packaging for further business as product manager requested
        comments["packaging"] = attr('packaging')
        comments["rate_key"] = attr("rateKey")
        pay_key = {
            'redis_key': self.redis_key,
            'id': room_index,
            'room_num': self.task.ticket_info['room_count']
        }
        comments["paykey"] = pay_key
        comments["payKey"] = pay_key

        comments['rateType'] = attr("rateType")

        comments['extra'] = [
            {'breakfast': '包含早餐' if room.is_breakfast_free == 'Yes' else '不包含早餐'},
            {'payment': '在线支付'},
            {'return_rule': room.return_rule},
            {'occ_des': '可支持' + str(room.occupancy) + '名成人入住'}
        ]

        room.others_info = json.dumps(comments)

        try:
            room.guest_info = "adults: " + str(attr('adults')) + '_' + "children: " + str(attr('children')) + '_' \
                              + attr('childrenAges')
        except:
            room.guest_info = "adults: " + str(attr('adults'))

        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                      room.real_source, room.room_type, room.occupancy, room.bed_type, room.size,
                      room.floor, room.check_in, room.check_out, room.rest, room.price,
                      room.tax, room.currency, room.pay_method, room.is_extrabed, room.is_extrabed_free,
                      room.has_breakfast, room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule,
                      room.return_rule,
                      room.change_rule, room.room_desc, room.others_info, room.guest_info)

        return room_tuple

    def parse_api_key(self, req, data):
        if data['status'] != 'OK':
            raise parser_except.ParserException(parser_except.API_NOT_ALLOWED, "API token 认证未通过")

    def parse_room(self, req, data):
        rooms = []
        hotels = data.get('hotels', {}).get('hotels', [])
        if hotels:
            hotels = hotels[-1]
            hotel_public_info = {
                "hotel_name": hotels['name'],
                "check_in": self.check_in,
                "check_out": self.check_out,
                "city": self.city_id,
                "source_hotelid": self.hotel_id,
                "source": "hotelbedsApi",
                "real_source": "hotelbedsApi",
                "currency": hotels['currency'],
            }

            room_template = Room()
            room_template.__dict__.update(hotel_public_info)

            room_index = 0
            for room in hotels['rooms']:
                # 去除验价中按类型筛选的工作

                raw_rates = room["rates"]

                types = groupby(raw_rates, lambda x: include_breakfast(x["boardCode"]))
                rates = [min(group, key=lambda x: float(x["net"])) for _, group in types]

                for rate in rates:
                    if "rateType" in rate:
                        if rate["paymentType"] == "AT_WEB":
                            rate["room_type"] = room["name"]
                            rate["source_roomid"] = room["code"]
                            result = self.room_parser(rate, room_template, room_index)
                            rooms.append(result)
                            room_index += 1
            return rooms
        else:
            raise parser_except.ParserException(parser_except.EMPTY_TICKET, "请求返回无房间")


if __name__ == '__main__':
    from common.task import Task

    task = Task()
    task.content = "50557&87579&2&20171221"
    task.source = 'hotelbeds'

    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "", "secret": "xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "123", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "123xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'

    # test
    task.ticket_info = {"room_info": [{"room_count": 1, "occ": 2}], "env_name": "offline",
                        "auth": auth
                        }

    # online
    # task.ticket_info = {
    #     "room_info": [{"num": 3, "occ": 2}], "env_name": "offline",
    #     "auth": '{"api_key": "4esbwxh5rdhm7ejuj8z3xa7q", "secret": "5uv9w3tCzJ", "url": "https://api.hotelbeds.com/hotel-api/1.0/"}'
    # }
    task.other_info= {}

    hotel_beds_spider = HotelBedsSpider()
    hotel_beds_spider.task = task
    code = hotel_beds_spider.crawl(cache_config={'enable': False})
    print 'Code', code
    result = hotel_beds_spider.result
    for each in result['room']:
        print json.dumps(each)
