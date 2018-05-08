#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
aichotel
"""
import json
import datetime
import hashlib
import hmac

from mioji.common.spider import Spider, request, PROXY_NEVER
from mioji.common.logger import logger
from mioji.common import parser_except
from mioji.common.class_common import Room
from collections import defaultdict
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.task_info import Task
from mioji.common.check_book.check_book_ratio import use_record_qid
from mioji.common import spider, utils
setdefaultencoding_utf8()


def gettoken(method, mid_url):
    date = datetime.datetime.utcnow().strftime('%a,%d %b %Y %H:%M:%-S ')
    Date = date + 'UTC'
    method = method.upper()
    url = mid_url
    req_param = method + ' ' + url + '\n' + Date
    sercret_key = '68d1d24#bcaA1K!d638c21d97RQe1'
    APIClientToken = hmac.new(sercret_key, req_param, hashlib.sha1).digest().encode('base64').rstrip()
    token = dict()
    token['Date'] = Date
    token['APIClientToken'] = APIClientToken
    token['APIClientKey'] = 'mioji'
    return token


class AicHotelSpider(Spider):
    source_type = 'aicApiHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'},
    }
    old_spider_tag = {
        'aicApiHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.hotel = {}
        super(AicHotelSpider, self).__init__(task=task)

    def pretreatment(self):
        try:
            auth = json.loads(self.task.ticket_info.get('auth', 'NULL'))
            self.ctx = dict()
            self.ctx['Accept-Encoding'] = 'gzip,deflate'
            self.base_url = auth['url']
            self.occ = int(self.task.ticket_info['room_info'][0].get('occ', 2))
            self.room_num = int(self.task.ticket_info['room_info'][0]['room_count'])
            #self.adult_num = int(self.task.ticket_info['room_info'][0].get('adult_num'))
            self.kids_num = int(self.task.ticket_info['room_info'][0].get('kids_num', 0))
        except Exception as e:
            raise parser_except.ParserException(121, msg='')
        #"20045&59149&1&20180216"
        self.city_id, self.hotelid, night, self.check_in = self.task.content.split('&')
        self.check_in = self.check_in[:4] + '-' + self.check_in[4:6] + '-' + self.check_in[6:]
        self.check_out = datetime.datetime.strftime(datetime.datetime.strptime(self.check_in, '%Y-%m-%d') + datetime.timedelta(int(night)), '%Y-%m-%d')

    def targets_request(self):
        self.pretreatment()

        @request(retry_count=0, proxy_type=PROXY_NEVER)
        def get_info():
            mid_url = '/rate/public/search/hotels'
            headers = gettoken('post', mid_url)
            headers.update(self.ctx)
            req_param = {
                "hotel_ids": [self.hotelid],
                "latitude": "NULL",
                "longitude": "NULL",
                "radius": 0,
                "check_in": self.check_in,
                "check_out": self.check_out,
                "room_number": self.room_num,
                "adult_number": self.occ,
                "kids_number": 0,
                "light": 0
            }
            return {
                'req': {
                    'method': 'post',
                    'url': self.base_url + mid_url + '?locale=zh_CN',
                    'headers': headers,
                    'json': req_param
                },
                'user_handler': [self.parse_info],
                'data': {'content_type': 'json'}
            }

        use_record_qid(unionKey='aicApi', api_name="availability", task=self.task, record_tuple=[1, 0, 0])

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def get_room_data():
            mid_url = '/rate/public/search/room_availability'
            headers = gettoken('post', mid_url)
            headers.update(self.ctx)
            req_param = {
                "hotel_id": self.hotelid,
                "check_in": self.check_in,
                "check_out": self.check_out,
                "room_number": self.room_num,
                "adult_number": self.occ,
                "kids_number": 0
            }
            url = self.base_url + mid_url + '?locale=zh_CN'
            return {
                'req': {
                    'method': 'post',
                    'url': url,
                    'headers': headers,
                    'json': req_param
                },
                'data': {'content_type': 'json'}
            }
        return [get_info, get_room_data]

    def parse_info(self, req, resp):
        print '开始解析'

        if resp['result']['return_status']['success'] == 'false':
            # 抛出错误
            raise parser_except.ParserException(21, msg=resp['result']['return_status']['exception'])
        # 对hotel ids 做兼容
        if resp.get('key_word').get('hotel_ids')[0]:
            self.hotel['source_hotelid'] = resp.get('key_word').get('hotel_ids')[0]
        elif not resp.get('key_word').get('hotel_ids')[0]:
            self.hotel['source_hotelid'] = resp.get('hotel_list')[0].get('hotel_id')
        else:
            raise parser_except.ParserException(29, msg='')
        self.hotel['hotel_name'] = resp.get('hotel_list')[0].get('hotel_name')
        self.hotel['occupancy'] = resp.get('key_word').get('adult_number')

    def parse_room(self, req, resp):
        '''
        订单不可修改，只退整单
        :param req:
        :param resp:
        :return: rooms (type list)
        '''
        # print 'debug->', json.dumps(resp, ensure_ascii=False)
        task = self.task
        redis_key = 'Null'
        if hasattr(task, 'redis_key'):
            redis_key = task.redis_key
        rooms = []
        room_index = 0
        if resp.get('result')['return_status']['success'] == 'false':
            raise parser_except.ParserException(21, resp.get('result').get('return_status').get('exception'))
        for data in resp.get('room_list', []):
            cancel_Policies = data.get('rates_and_cancellation_policies', [])
            if not cancel_Policies:
                continue

            roomPrices = defaultdict(list)
            for _ in cancel_Policies:
                roomPrices[_['room_key']].append(_)

            for rate in [_[0] for _ in roomPrices.values()]:

                room = Room()
                room.hotel_name = self.hotel['hotel_name']
                room.city = 'NULL'
                room.source = 'aicApi'
                room.source_hotelid = self.hotel['source_hotelid']
                room.source_roomid = rate.get('room_key')
                room.real_source = 'aicApi'
                room.room_type = data.get('room_name')
                room.occupancy = self.hotel['occupancy']
                room.bed_type = 'NULL'
                room.size = -1
                room.floor = -1
                room.check_in = self.check_in
                room.check_out = self.check_out
                room.rest = -1
                room_num = self.room_num
                price = '%.2f' % (float(rate.get('total_amount_after_tax')) / room_num)
                room.price = float(price)
                room.tax = -1
                room.currency = rate.get('currency')
                room.pay_method = 'mioji'
                room.is_extrabed = 'NULL'
                room.is_extrabed_free = 'NULL'
                if rate.get('breakfast').get('include') == 1:
                    room.has_breakfast = 'Yes'
                elif rate.get('breakfast').get('include') == 0:
                    room.has_breakfast = 'No'
                else:
                    room.has_breakfast = 'NULL'
                room.is_breakfast_free = room.has_breakfast
                room.extrabed_rule = 'NULL'
                room.room_desc = data.get('room_desc')
                room.guest_info = 'Null'
                # 判断取消规则
                timezone = rate.get('cancellation_information').get('timezone')
                ccy = rate.get('currency')
                details = rate.get('cancellation_information').get('details')
                new_detail = sorted(details, key=lambda x: x.get('datetime', ''), reverse=True)
                if rate.get('cancellation_information').get('support_cancel') == 'yes':
                    if rate.get('cancellation_information').get('non_refundable') == 'no':
                        if len(new_detail) > 2:
                            room.return_rule = '免费取消截止时间：%s（时区：%s）<br/>从%s（时区：%s）开始，扣取费用%s%s<br/>'\
                                                '从%s（时区：%s）开始，扣取费用%s%s<br/>若到达入住时间客人未出现，则扣取费用%s%s' % \
                                                (new_detail[0].get('datetime', ''), timezone,
                                                 new_detail[0].get('datetime', ''), timezone,
                                                 new_detail[0].get('amount_penalty'), ccy,
                                                 new_detail[1].get('datetime', ''), timezone,
                                                 new_detail[1].get('amount_penalty'), ccy,
                                                 new_detail[-1].get('amount_penalty'), ccy)
                        else:
                            room.return_rule = '免费取消截止时间：%s（时区：%s）<br/>从%s（时区：%s）开始，扣取费用%s%s' \
                                               '<br/>若到达入住时间客人未出现，则扣取费用%s%s' % \
                                               (new_detail[0].get('datetime', ''), timezone,
                                                new_detail[0].get('datetime', ''), timezone,
                                                new_detail[0].get('amount_penalty'), ccy,
                                                new_detail[-1].get('amount_penalty'), ccy)
                    elif rate.get('cancellation_information').get('non_refundable') == 'yes':
                        room.return_rule = '从%s（时区：%s）开始，订单取消不退款' % (new_detail[0].get('datetime', ''), timezone)
                    else:
                        room.return_rule = '从%s（时区：%s）开始，扣取费用%s%s' % (new_detail[0].get('datetime',''), timezone, new_detail[0].get('amount_penalty'), ccy)
                        room.return_rule += '<br/>若到达入住时间客人未出现，则扣取费用%s%s' % (new_detail[1].get('amount_penalty'), ccy)
                else:
                    room.return_rule = '从%s（时区：%s）开始，此订单不可取消' % (new_detail[0].get('datetime', ''), timezone)
                room.is_cancel_free = 'Null'
                room.change_rule = ''
                room.others_info = json.dumps({
                    'paykey': {
                        'redis_key': redis_key,
                        'id': room_index,
                        'room_num': self.room_num
                    },
                    'payKey': {
                        'redis_key': redis_key,
                        'id': room_index,
                        'room_num': self.room_num
                    },
                    'extra': {
                        'breakfast': '',
                        'payment': 'NULL',
                        'return_rule': room.return_rule,
                        'occ_des': 'NULL'
                    }
                }, ensure_ascii=False)
                room_index += 1
                room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                              room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                              room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                              room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                              room.  is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                              room.change_rule, room.room_desc, room.others_info, room.guest_info)
                rooms.append(room_tuple)
        return rooms


if __name__ == '__main__':
    spider.slave_get_proxy = utils.simple_get_socks_proxy
    task = Task(source='aicApi')
    # content: 城市ID，hotelID，入住天数，入住日期
    task.content = "20045&116633&1&20180509"
    task.ticket_info = {
        "room_info": [
            {
                "occ": 2,
                "num": 2,
                "room_count": 2,
            },
        ],
        "auth": json.dumps(
            {"APIClientKey": "mioji", "sercret_key": "68d1d24#bcaA1K!d638c21d97RQe1", "url": "https://testopenapi.aichotels-service.com"})
    }
    spider = AicHotelSpider(task)
    print spider.crawl()
    print json.dumps(spider.result['room'], ensure_ascii=False)