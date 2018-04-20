#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __auth__ = "fan bowen"

import datetime
import json
import types
import base64
from mioji.common import parser_except
from common.class_common import Room
from copy import deepcopy
from mioji.common.spider import Spider, request, PROXY_NEVER
# from mioji.common.check_book.check_book_ratio import use_record_qid

meal_type = {"UL": "超级", "AI": "全包式", "FB": "全食宿", "HB": "半食宿", "BE": "英式早餐", "BC": "欧陆式早餐",
             "RO": "不含早餐"}


class HotelsProSpider(Spider):
    source_type = 'hotelsproApiHotel'
    targets = {'room': {'version': 'InsertHotel_room4'}}
    old_spider_tag = {'hotelsproApiHotel': {'required': ['room']}}

    def __init__(self, task=None):
        super(HotelsProSpider, self).__init__(task)

    def targets_request(self):
        # 下移 task 相关内容
        _auth = self.task.ticket_info.get('auth', {})
        if isinstance(_auth, types.StringTypes):
            _auth = json.loads(_auth)
        elif isinstance(_auth, types.DictType):
            _auth = _auth
        else:
            _auth = {}

        # 增加对121错误的支持
        username = _auth.get('Username', None)
        password = _auth.get('Password', None)
        url = _auth.get('url', None)

        if not username or not password or not url:
            raise parser_except.ParserException(121, '无认证信息')
        # use_record_qid(unionKey='hotelbedsApi', api_name="SEARCH BY HOTEL CODE", task=task, record_tuple=[1, 0, 0])

        self.user_datas['username'] = username
        self.user_datas['password'] = password
        if str(url[-1]) == '/':
            url = url[:-1]
        self.user_datas['url'] = url

        # 解析task
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
        self.user_datas['night'] = cnt_nights
        self.user_datas['check_in'] = check_in
        self.user_datas['check_out'] = check_out
        self.user_datas['rooms'] = rooms
        self.user_datas['hotel_id'] = hotel_id
        self.user_datas['city_id'] = city_id
        self.user_datas['occ'] = rooms[0]['occ']
        self.user_datas['room_num'] = rooms[0]['room_count']
        self.user_datas['code'] = ''
        self.redis_key = 'NULL'
        if hasattr(self.task, 'redis_key'):
            self.redis_key = self.task.redis_key

        @request(retry_count=3, proxy_type=PROXY_NEVER)
        def get_code():
            url = '{0}/search/?checkin={1}&checkout={2}&client_nationality=cn&currency=USD&{3}&hotel_code={4}'.format(
                self.user_datas['url'], self.user_datas['check_in'], self.user_datas['check_out'],
                '&'.join(['pax={0}'.format(self.user_datas['occ']) for _ in range(int(self.user_datas['room_num']))]),
                self.user_datas['hotel_id']
            )
            return {
                'req': {
                    'url': url,
                    'headers': {
                        "Authorization": 'Basic {0}'.format(base64.b64encode('{0}:{1}'.format(self.user_datas['username'],
                                                                                              self.user_datas['password']))),
                        "Accept": "application/json"
                    },
                },
                'user_handler': [self.parse_code],
                'data': {
                    'content_type': 'json'
                }
            }

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def get_hotel():
            get_room_url = '{0}/hotel-availability/?hotel_code={1}&search_code={2}'.format(
                self.user_datas['url'], self.user_datas['hotel_id'], self.user_datas['code']
            )
            return {
                'req': {
                    'url': get_room_url,
                    'headers': {
                        "Authorization": 'Basic {0}'.format(
                            base64.b64encode('{0}:{1}'.format(self.user_datas['username'],
                                                              self.user_datas['password']))),
                        "Accept": "application/json"
                    },
                },
                'data': {
                    'content_type': 'json'
                }
            }

        yield get_code
        if self.user_datas['code'] != '':
            yield get_hotel

    def response_error(self, req, resp, error):
        # 目前测试403为认证信息错误所返回code
        if resp.status_code == 403:
            raise parser_except.ParserException(122, '认证信息错误')

    def room_parser(self, _room, template, room_index):
        room = deepcopy(template)
        room.source_roomid = _room['code']
        room.room_type = _room['rooms'][0]['room_type']
        room.occupancy = self.user_datas['occ']
        room.pay_method = 'mioji'
        room.rest = -1
        if _room['meal_type'] == 'RO':
            room.has_breakfast = 'No'
            room.is_breakfast_free = "No"
            breakfast_title = ''
        else:
            room.has_breakfast = 'Yes'
            room.is_breakfast_free = 'Yes'
            breakfast_title = meal_type[_room['meal_type']]
        room.price = float(float(_room['price']) / int(self.task.ticket_info['room_count']))
        room.tax = 0
        policy = []
        for i in _room['policies']:
            ratio = i['ratio']
            days_remaining = i['days_remaining']
            policy.append('距离入住日期时间:{0}天<br />退订费用: 订单价*{1}'.format(days_remaining, ratio))
        room.return_rule = '<br /><br />'.join(policy)
        room.is_cancel_free = 'NULL'
        comments = {}
        comments['code'] = _room['code']
        pay_key = {
            'redis_key': self.redis_key,
            'id': room_index,
            'room_num': self.task.ticket_info['room_count']
        }
        extra = {'breakfast': breakfast_title,
                 'payment': '',
                 'return_rule': room.return_rule,
                 'occ_des': ''}
        comments["paykey"] = pay_key
        comments["payKey"] = pay_key
        comments["extra"] = extra
        room.others_info = json.dumps(comments)
        room.guest_info = ""

        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                      room.real_source, room.room_type, room.occupancy, room.bed_type, room.size,
                      room.floor, room.check_in, room.check_out, room.rest, room.price,
                      room.tax, room.currency, room.pay_method, room.is_extrabed, room.is_extrabed_free,
                      room.has_breakfast, room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule,
                      room.return_rule,
                      room.change_rule, room.room_desc, room.others_info, room.guest_info)

        return room_tuple

    def parse_code(self, req, data):
        a_code = data['code']
        self.user_datas['code'] = a_code

    def parse_room(self, req, data):
        rooms = []
        print json.dumps(data, ensure_ascii=False)
        hotels = data.get('results', [])
        if hotels == []:
            return []
        elif hotels:
            hotel_public_info = {
                "hotel_name": '',
                "check_in": self.user_datas['check_in'],
                "check_out": self.user_datas['check_out'],
                "city": self.user_datas['city_id'],
                "source_hotelid": self.user_datas['hotel_id'],
                "source": "hotelsproApi",
                "real_source": "hotelsproApi",
                "currency": "USD",
            }

            room_template = Room()
            room_template.__dict__.update(hotel_public_info)

            room_index = 0
            for room in hotels:
                if len(set([i['room_description'] for i in room['rooms']])) != 1:
                    break
                _result = self.room_parser(room, room_template, room_index)
                rooms.append(_result)
                room_index += 1
            return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.content = "50557&1362c9&2&20180121"
    task.source = 'hotelbeds'
    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "", "secret": "xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "123", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    # auth = '{"api_key": "gjy3nx7tyufwtggfnjw4z769", "secret": "123xrryq2hpMa", "url": "https://api.test.hotelbeds.com/hotel-api/1.0/"}'
    auth = '{"Username": "Miaoji", "Password": "Ext5wbaudEx65YN7", "url": "https://api-test.hotelspro.com/api/v2/"}'

    # test
    task.ticket_info = {"room_info": [{"room_count": 2, "occ": 4}], "env_name": "offline",
                        "auth": auth, 'room_count': 2
                        }

    # online
    # task.ticket_info = {
    #     "room_info": [{"num": 3, "occ": 2}], "env_name": "offline",
    #     "auth": '{"api_key": "4esbwxh5rdhm7ejuj8z3xa7q", "secret": "5uv9w3tCzJ", "url": "https://api.hotelbeds.com/hotel-api/1.0/"}'
    # }
    task.other_info= {}

    hotel_beds_spider = HotelsProSpider()
    hotel_beds_spider.task = task
    code = hotel_beds_spider.crawl(cache_config={'enable': False})
    print 'Code', code
    result = hotel_beds_spider.result
    for each in result['room']:
        print json.dumps(each)
