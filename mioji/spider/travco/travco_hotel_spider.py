#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日
@author: fuhongyu
'''

import json
import datetime
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mioji.common import parser_except
from mioji.common.class_common import Room
from mioji.common.spider import Spider, request, PROXY_NEVER


class Travco_hotel_spider(Spider):
    source_type = 'travcoApiHotel'
    targets = {'room': {'version': 'InsertHotel_room4'}}
    old_spider_tag = {'travcoApiHotel': {'required': ['room']}}

    def __init__(self, task=None):
        super(Travco_hotel_spider, self).__init__(task)
        self.hotel_id = ''

    def get_auth(self):
        auth = self.task.ticket_info.get('auth', None)
        if auth is None:
            raise parser_except.ParserException(121, "缺少认证信息")
        auth = json.loads(auth)
        try:
            host = auth['Host']
            agentcode = auth['AgentCode']
            password = auth['Password']
            self.redis_key = 'NULL'
            if hasattr(self.task, 'redis_key'):
                self.redis_key = self.task.redis_key
        except Exception as e:
            raise parser_except.ParserException(121, "auth获取失败")
        return host, agentcode, password

    def get_date(self):
        try:
            content = self.task.content
            checkin = content.split('&')[-1]
            self.durday = content.split('&')[-2]
            hotel_id = content.split('&')[-3]
            dates = datetime.datetime.strptime(checkin, "%Y%m%d")
            check_in = dates.strftime('%Y-%m-%d')
            check_out = (dates + datetime.timedelta(days=int(self.durday))).strftime('%Y-%m-%d')
        except Exception as e:
            raise parser_except.ParserException(12, "任务格式问题")
        return check_in, check_out, hotel_id

    def targets_request(self):
        bath_path = '/trlinkjws/services/HotelAvailabilityV7Service.HotelAvailabilityV7HttpSoap11Endpoint/'
        host, agentcode, password = self.get_auth()
        room_info = self.task.ticket_info.get('room_info', [{"occ": 2, "num": 1, "room_count": 1}])[0]
        occ = str(room_info['occ'])
        occ_dict = {'1': 'SingleRoom', '2': 'DoubleRoom', '3': 'TripleRoom', '4': 'QuadRoom'}
        self.room_occ = occ_dict.get(occ, '2')
        self.room_num = str(room_info.get('room_count', 1))
        self.check_in, self.check_out, self.hotel_id = self.get_date()
        data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" ' \
               'xmlns:req="http://www.travco.co.uk/trlink/xsd/hotelavailabilityv7/request">' \
               '<soapenv:Header/><soapenv:Body><req:checkAvailabilityByHotelCode>' \
               '<req:RequestBase AgentCode="{0}" AgentPassword="{1}" Lang="en-GB"/>' \
               '<req:HotelCode>{2}</req:HotelCode>' \
               '<req:CheckInDate>{3}</req:CheckInDate>' \
               '<req:CheckOutDate>{4}</req:CheckOutDate>' \
               '<req:RoomData {5}="{6}"/>' \
               '<req:AdditionalData NeedTotalNoOfHotels="no" NeedAvailableHotelsOnly="yes" NeedReductionAmount="no" ' \
               'NeedHotelMessages="no" NeedFreeNightDetail="no" NeedHotelAddress="no" NeedTelephoneNo="no" ' \
               'NeedFaxNo="no" NeedBedPicture="no" NeedMapPicture="no" NeedEmail="no" NeedPicture="no" ' \
               'NeedAmenity="no" NeedHotelDescription="no" NeedHotelCity="no" NeedArrivalPointMain="no" ' \
               'NeedArrivalPointOther="no" NeedGeoCodes="no" NeedHotelProperties="no" NeedLocation="no" ' \
               'NeedCityArea="no" NeedEnglishText="no" NeedCancellationDetails="no"/>' \
               '</req:checkAvailabilityByHotelCode></soapenv:Body></soapenv:Envelope>'

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def pages_request():    
            base_url = host + bath_path
            if 'http://' not in base_url:
                base_url = 'http://' + base_url
            post_data = data.format(agentcode, password, self.hotel_id, self.check_in, self.check_out, self.room_occ, self.room_num)
            return {'req': {'url': base_url, 'headers': {'Accept-Encoding': 'gzip'}, 'method': 'post',
                            'data': post_data
                            }}

        return [pages_request]

    def parse_room(self, req, data):
        rooms = []
        allrooms = []
        root = ET.fromstring(str(data))
        avail = root[0][0][0][0][0][0][0].attrib.get('Status', None)
        title = '{http://www.travco.co.uk/trlink/xsd/hotelavailabilityv7/response}'
        rate = {}
        city_code = ''
        hotel_name = ''
        room_index = 0
        if avail != 'Available':
            return []
        for i in root.iter():
            if i.tag == title + 'HotelData':
                city_code = i.attrib.get('CityCode')
            elif i.tag == title + 'SubHotelData':
                rooms.append(i)
            elif i.tag == title + 'RatePlanDetails':
                rate['code'] = i.attrib.get('RatePlanCode')
            elif i.tag == 'RatePlanDescription':
                rate['desc'] = i.text
            elif i.tag == 'HotelName':
                if hotel_name:
                    pass
                else:
                    hotel_name = i.text
            else:
                pass
        for hotel_room in rooms:
            if hotel_room.attrib['Status'] == 'Available':
                CurrencyCode = hotel_room.attrib['CurrencyCode']
                hotel_code = hotel_room.attrib['HotelCode']
                for room in hotel_room:
                    if room.tag == 'RoomDatas':
                        for ls in room:
                            room_info = ls.attrib
                            bed_type = ls[0].text.split('-')
                            room = Room()
                            room.hotel_name = hotel_name
                            room.city = city_code
                            room.source = 'travcoApi'
                            room.source_hotelid = hotel_code
                            room.source_roomid = room_info.get('RoomCode')
                            room.room_type = room_info.get('RoomCode')
                            room.occupancy = int(room_info.get('RoomPax'))
                            room.bed_type = bed_type[0]
                            room.check_in = self.check_in
                            room.check_out = self.check_out
                            room.price = float(room_info.get('TotalAdultPrice'))
                            room.tax = 0
                            room.size = 0
                            room.real_source = 'travcoApi'
                            room.currency = CurrencyCode
                            room.pay_method = 'mioji'
                            if 'With Breakfast' == bed_type[-1].replace(' ',''):
                                has_breakfast = 'Yes'
                            else:
                                has_breakfast = 'No'
                            room.has_breakfast = has_breakfast
                            room.is_breakfast_free = has_breakfast
                            room.is_cancel_free = 'NULL'
                            room.extrabed_rule = 'NULL'
                            room.return_rule = 'NULL'
                            room.change_rule = 'NULL'
                            comments = {}
                            comments['PayInfo'] = {'PriceCode': room_info.get('PriceCode'),
                                                   'Cancelcode': room_info.get('CancellationChargeCode'),
                                                   'rate': rate, 'occ': self.room_occ, 'dur': self.durday}
                            pay_key = {
                                'redis_key': self.redis_key,
                                'id': room_index,
                                'room_num': self.task.ticket_info['room_info'][0]['room_count']
                            }
                            extra = {'breakfast': '',
                                     'payment': '',
                                     'return_rule': room.return_rule,
                                     'occ_des': ''}
                            comments["paykey"] = pay_key
                            comments["payKey"] = pay_key
                            comments["extra"] = extra
                            room.others_info = json.dumps(comments)
                            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                                          room.real_source, room.room_type, room.occupancy, room.bed_type, room.size,
                                          room.floor, room.check_in, room.check_out, room.rest, room.price, room.tax,
                                          room.currency, room.pay_method, room.is_extrabed, room.is_extrabed_free,
                                          room.has_breakfast,
                                          room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                                          room.change_rule,
                                          room.room_desc, room.others_info, room.guest_info)
                            allrooms.append(room_tuple)
                            room_index += 1
        return allrooms


if __name__ == '__main__':
    """
    AgentCode	273LGD
    Password:  R7V21DJ18 
    Request IP	185.44.27.183
    Host	v8apitest1.travco.co.uk
    """
    from mioji.common.task_info import Task
    task = Task()
    task.source = 'travco'
    task.other_info = {}
    auth = {
        "Host": "http://v8apitest1.travco.co.uk:8080",
        "AgentCode": "273LGD",
        "Password": "R7V21DJ18",
    }
    task.ticket_info = {
        "room_info": [{"num": 3, "occ": 2, "room_count": 3}],
        "auth": json.dumps(auth)
    }
    task.content = 'NULL&YYB&2&20180521'
    spider = Travco_hotel_spider(task)

    code = spider.crawl()
    print spider.result
