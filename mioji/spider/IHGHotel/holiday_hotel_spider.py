#coding:utf-8
import re
import traceback
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ, PROXY_NEVER
from mioji.common.utils import simple_get_http_proxy
from mioji.common.class_common import Room
import datetime
import json
import requests
import re


class IhgHotelSpider(Spider):
    source_type = 'holidayHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'}
    }
    old_spider_tag = {
        'holidayListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(IhgHotelSpider, self).__init__(task)
        self.query_data = {}
        self.city_info = {}
        self.redis_key = 'Null'
        self.hotels = {}

    def response_error(self,req, resp, error):
        # 在这里处理29信息，暂时还没找到
        pass

    def targets_request(self):
        self.fetch_ticket_info()

        if hasattr(self.task, 'redis_key'):
            self.redis_key = self.task.redis_key

        @request(retry_count=3, proxy_type=PROXY_NEVER)
        def get_hotel_detail():
            return {
                'req': {
                    'url': 'https://apis.ihg.com/hotels/v1/profiles/{}/details'.format(self.query_data['hotel_id']),
                    'method': 'get',
                    'headers': {
                        'accept': 'application/json, text/plain, */*',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                        'ihg-language': 'zh-CN',
                    }
                },
                'user_handler': [self.parse_hotel_name],
                'data': {'content_type': 'json'}
            }

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def get_room_data():
            post_data = {"hotelCode":"PEGDZ","adults":2,"children":0,"rateCode":"6CBARC","showPointsRate":False,"rooms":2,"version":"1.2","corporateId":"","travelAgencyId":"99602392","dateRange":{"start":"2018-01-21","end":"2018-01-23"},"memberID":None}
            post_data['adults'], post_data['rooms'] = self.query_data['adults'], self.query_data['room']
            post_data['hotelCode'] = self.query_data['hotel_id']
            post_data['dateRange']['start'], post_data['dateRange']['end'] = self.query_data['check_in'], self.query_data['check_out']
            return {
                'req': {
                    'url': 'https://apis.ihg.com/guest-api/v1/ihg/cn/zh/rates',
                    'method': 'post',
                    'headers': {
                        'ihg-language':'zh-CN',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'accept':'application/json, text/plain, */*',
                        'Content-Type':'application/json; charset=UTF-8',
                        'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'x-ihg-api-key':'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                        'x-ihg-mws-api-token':'58ce5a89-485a-40c8-abf4-cb70dba4229b',
                    },
                    'data': json.dumps(post_data)
                },
                'data': {'content_type': 'json'}
            }
        yield get_hotel_detail
        yield get_room_data

    def fetch_ticket_info(self):
            """
            得到查询的data
            """
            city_id, hotel_id, nights, check_in = self.task.content.split('&')
            check_in_date = datetime.datetime.strptime(check_in, '%Y%m%d')
            days = datetime.timedelta(days=int(nights))
            room = self.task.ticket_info.get('room_count', 2)
            adult = self.task.ticket_info.get('occ', 2)
            check_out_date = check_in_date + days
            check_in, check_out = str(check_in_date).split(' ')[0], str(check_out_date).split(' ')[0]
            self.query_data = dict(check_in=check_in, check_out=check_out, hotel_id=hotel_id, adults=adult, room=room)

    def parse_hotel_name(self, req, data):
        self.hotels['hotel_name'] = data['hotelInfo']['profile']['name']
        self.hotels['city'] = data['hotelInfo']['address']['city']

    def parse_room(self, req, data):
        rooms = []
        hotel_code = data['hotelCode']
        room_index = 0
        for i in data['rooms']:
            rate_code = i['rateCode']
            rate = data['rates'][rate_code]
            room = Room()
            room.hotel_name = self.hotels.get('hotel_name', '')
            room.city = self.hotels.get('city', '')
            room.source = 'holiday'
            room.source_hotelid = hotel_code
            room.source_roomid = i.get('roomCode', '')
            room.room_type = i.get('description', '')
            room.real_source = 'holiday'
            room.occupancy = i.get('maxPeople', self.query_data['adults'])
            room.bed_type = 'NULL'
            room.floor = -1
            room.check_in = self.query_data['check_in']
            room.check_out = self.query_data['check_out']
            room.rest = i.get('numRoomsAvailable')
            # 每晚不含税的价格
            room.price = i['charges'].get('priceTotal') or i['charges'].get('total')
            room.tax = room.price - i['charges'].get('price', 0)
            room.currency = i.get('currencyCode', '')
            room.is_extrabed = 'NULL'
            room.is_extrabed_free = 'NULL'
            room_desc = ''
            if i['charges'].get('serviceCharges'):
                room.room_desc += '包含服务费：{} |'.format(i['charges'].get('serviceCharges'))
            for j in rate['rateInfos']:
                if '不可退' in j['description']:
                    room.is_cancel_free = 'No'
                if '含早餐' in j['description']:
                    room.is_breakfast_free = 'Yes'
                    room.has_breakfast = 'Yes'
                if '不含早餐' in j['description']:
                    room.is_breakfast_free = 'No'
                    room.has_breakfast = 'No'
                else:
                    room_desc += j['description'] + '|'

            room.room_desc = room_desc + i['longDescription']
            com = re.search('面积为(\d+)', room.room_desc)
            room.size = int(com.group(1)) if com else -1
            room.return_rule = rate['cancellationPolicy']
            if '需要定金' in room.room_desc and rate['aliPayAvailable']:
                room.pay_method = '在线支付'
            else:
                if not rate['aliPayAvailable']:
                    room.pay_method = '到店支付'
                else: room.pay_method = '支付方式'
            room.extrabed_rule = 'NULL'
            room.change_rule = 'NULL'
            room.others_info = {}
            if room.has_breakfast == 'Yes':
                breakfast = '含早餐'
            elif room.has_breakfast == 'No':
                breakfast = '不含早餐'
            else:
                breakfast = ''
            room.others_info['payInfo'] = i.get('charges', {})
            room.others_info['extra'] = {
                'breakfast': breakfast,
                'payment': room.pay_method,
                'return_rule':room.return_rule,
                'occ_des': '可支持最多' + str(room.occupancy) + '人入住'
            }
            room_index += 1
            pay_key = {
                'redis_key': self.redis_key,
                'id': room_index,
                'room_num': self.task.ticket_info['room_count']
            }
            room.others_info['pay_key'] = pay_key
            room.guest_info = 'NULL'
            room.hotel_url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/{}/hoteldetail'.format(room.source_hotelid)
            room.others_info = json.dumps(room.others_info)
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid,
                          room.source_roomid, room.real_source, room.room_type, room.occupancy,
                          room.bed_type, room.size, room.floor, room.check_in, room.check_out,
                          room.rest, room.price, room.tax, room.currency, room.pay_method,
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free,
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc,
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
        return rooms

    def parse_city(self, req, resp):
        self.city_info = json.loads(resp)[0]


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    # task.content = 'TYOHC&20180018&20180019'

    task.content = '13384&QNLVH&2&20171225'
    task.ticket_info = {
        'occ': '2',
        'room_count': 2
    }
    task.source = 'ihg'
    spider = IhgHotelSpider()
    spider.task = task
    print spider.crawl()
    print spider.result
