#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import datetime
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.task_info import Task
from mioji.common.parser_except import ParserException
from mioji.common.class_common import Room
setdefaultencoding_utf8()


class AccorHotelSpider(Spider):
    source_type = 'accorHotel'
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room4'}
    }
    old_spider_tag = {
        'accorHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(AccorHotelSpider, self).__init__(task=task)
        self.page = 1
        self.start_time = ""
        self.hotel_list = []
        self.total = 0
        self.price = ""
        self._room_id = {}
        self.room_new_list = dict()

    @property
    def content_parser(self):
        content_list = self.task.content.split('&')
        '1785&伦敦滑铁卢诺富特酒店&2&20180315'
        hotel_id = content_list[0]
        hotel_name = content_list[1]
        night = int(content_list[2])
        checkin = datetime.datetime.strptime(content_list[3], "%Y%m%d")
        checkout = checkin + datetime.timedelta(days=night)
        self.check_in = checkin.strftime("%Y-%m-%d")
        self.check_out = checkout.strftime("%Y-%m-%d")
        occ = self.task.ticket_info['room_info'][0].get('occ', 2)
        room_count = self.task.ticket_info['room_info'][0].get('room_count', 1)
        return hotel_id, hotel_name, self.check_in, self.check_out, occ, room_count

    def targets_request(self):
        hotel_id, hotel_name, check_in, check_out, occ, room_count = self.content_parser
        init_url = 'https://m.accorhotels.cn/api/search/'  # 初始请求
        url = 'https://m.accorhotels.cn/api/rooms?arrivalDate={}&hotelCode={}'.format(check_in, hotel_id)  # 房间信息
        room_url = 'https://m.accorhotels.cn/api/rooms?&UseDestinationCurrency=false&adults={}&children=0&currency=RMB&rooms={}'.format(str(occ), str(room_count))  # 房间数量入住人数

        data = {"clientCode": "",
                "clientTimeZoneDifference": -480,
                "contractNumber": "",
                "endDate": "{}T00:00:00.000Z".format(check_out),
                "international": "",
                "loyaltyCardNumber": "",
                "prefferentialCode": "",
                "searchGeoCode": "",
                "searchHotelNameText": "{}".format(hotel_name),
                "searchRidCode": "",
                "searchText": "",
                "startDate": "{}T00:00:00.000Z".format(check_in),
                "retrieved": 0,
                "fromLocation": False}

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def get_init_url():
            return {'req': {
                'method': 'POST',
                'url': init_url,
                'data': data,
            }}
        yield get_init_url

        @request(retry_count=5, proxy_type=PROXY_FLLOW)
        def get_url():
            return {'req': {'method': 'GET', 'url': url},
                    'user_handler': [self.parse_hotel]}
        yield get_url

        @request(retry_count=5, proxy_type=PROXY_FLLOW, binding=self.parse_room)
        def get_room_url():
            return {'req': {
                'method': 'GET',
                'url': room_url
            }}
        yield get_room_url

    def parse_hotel(self, req, res):
        data = json.loads(res)['hotel']
        room = Room()
        room.source_roomid = ""
        room.hotel_name = data['name']
        room.city = "NULL" # data['address'].split(',')[1]
        room.source = "accor"
        room.source_hotelid = data['code']
        room.real_source = "accor"
        for content in data['room']:
            room_id = content['code']
            self.room_new_list[room_id] = dict()
            room.occupancy = content['maxAdultOccupancy']
            maxoccupancy = content['maxOccupancy']
            room.bed_type = content['title']
            room.source_roomid = content['code']
            room_title = content['title']
            room.room_type = room_title
            room.size = -1.0
            room.floor = -1
            room.rest = -1
            room.room_desc = content['details']
            for cont in content['rates']:
                _rateplancode = cont['ratePlanCode']
                room.check_in = self.check_in
                room.check_out = self.check_out
                room.price = 0
                room.tax = 0
                room.currency = "CNY"
                room.is_extrabed = "NULL"
                room.is_extrabed_free = "NULL"
                breakfastlabel = cont['breakfastLabel']
                if cont['breakfastLabel'] == "含早餐":
                    room.has_breakfast = 'Yes'
                    room.is_breakfast_free = "Yes"
                else:
                    room.has_breakfast = 'No'
                    room.is_breakfast_free = "No"
                if cont['flexibility'] == 'Flexible' or cont["flexibilityLabel"] == "无条件更改和取消": # todo 注意编码
                    room.is_cancel_free = "Yes"
                elif cont['flexibility'] == 'Restricted':
                    room.is_cancel_free = "No"
                else:
                    room.is_cancel_free = "NULL"
                room.return_rule = cont['flexibilityDescription'].replace("\r\n", "")
                if cont['securePaymentLabel'] == "预付":
                    room.pay_method = "在线支付"
                else:
                    room.pay_method = "到店支付"
                room.extrabed_rule = "NULL"
                room.change_rule = "NULL"
                room.others_info = 'NULL'
                room.guest_info = 'NULL'
                other_info = dict()
                other_info['extra'] = dict()
                other_info['extra']['breakfast'] = breakfastlabel
                other_info['extra']['payment'] = room.pay_method
                other_info['extra']['return_rule'] = room.return_rule
                other_info['extra']['occ_des'] = '每间客房最多入住人数: {}人'.format(maxoccupancy)
                room.others_info = json.dumps(other_info)
                self.room_new_list[room_id][_rateplancode] = [room.hotel_name, room.city, room.source, room.source_hotelid,
                              room.source_roomid, room.real_source, room.room_type, room.occupancy,
                              room.bed_type, room.size, room.floor, room.check_in, room.check_out,
                              room.rest, room.price, room.tax, room.currency, room.pay_method,
                              room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                              room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule,
                              room.return_rule, room.change_rule, room.room_desc,
                              room.others_info, room.guest_info]
        return self.room_new_list

    def parse_room(self, req, res):
        room = Room()
        rooms = []
        data = json.loads(res)['hotel']
        room_dict = dict()
        if req['req']['url'].startswith('https://m.accorhotels.cn/api/rooms?&UseDestinationCurrency'):
            room_num = data['rooms']
            adults = data['adults']
            children = data['children']
            for content in data['room']:
                room_code = content['code']
                room_dict[room_code] = dict()
                for cont in content['rates']:
                    rateplancode = cont['ratePlanCode']
                    room_dict[room_code][rateplancode] = cont['total']
                    room.price = room_dict[room_code][rateplancode]
                    _room = self.room_new_list[room_code][rateplancode]
                    _room[14] = room.price
                    rooms.append(tuple(_room))
        return rooms


if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy_new
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = AccorHotelSpider(task)
    """ 酒店ID&酒店中文名&2&20180315 """
    task.content = '0351&拉斯拜尔蒙帕纳斯美居酒店&1&20180126'
    task.ticket_info = {
        "room_info": [{"occ": 2, "num": 1, "room_count": 1}],
    }
    result = spider.crawl()
    print result
    print spider.result
