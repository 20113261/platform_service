#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

import sys
sys.path.insert(0, '/Users/miojilx/Desktop/git/Spider/src/')
import re
import hashlib
import json
import time
import datetime
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE
from mioji.common.task_info import Task
from mioji.common import parser_except
from mioji.common.class_common import Room
from lxml import html
from mioji.common.logger import logger
import traceback
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mioji.common import parser_except
# from mioji.common.check_book.check_book_ratio import use_record_qid



class DOTW_Spider(Spider):
    source_type = 'DOTW'
    targets = {
        'room': {'version': 'InsertHotel_room4'},
    }
    old_spider_tag = {
        'dotwApiHotel': {'required': ['room']}
    }
    header = {
        'Content-Type': 'text/xml',
        'Connection': 'close',
        'Compression': 'Gzip',
    }

    def check_auth(self, auth):
        """checkauth  """
        _a = ('URL', 'username', 'password', 'company_code')
        for i in _a:
            if i not in auth or not auth[i]:
                raise parser_except.ParserException(121, "缺少认证信息")

    def make_data(self, task):
        # use_record_qid(unionKey='dotwApi', api_name="Search Hotels", task=task, record_tuple=[1, 0, 0])
        auth = json.loads(task.ticket_info['auth'])
        self.check_auth(auth)
        URL = auth['URL']
        username = auth['username']
        password = hashlib.md5(auth['password']).hexdigest()
        # print password
        company_code = auth['company_code']
        ticket_info = task.ticket_info
        content = task.content
        self.hotel_code, self.check_in, self.check_out, self.cityID = self.content_parser(
            content)
        # print self.hotel_code, self.check_in, self.check_out
        currency = 520
        # userInfo，
        user_info = '''<username>{username}</username><password>{password}</password><id>{company_code}</id><source>1</source><product>hotel</product>''' \
            .format(**{'username': username, 'password': password, 'company_code': company_code})
        # 入住、离店时间，和货币类型
        time_Currency = '''<fromDate>{check_in}</fromDate><toDate>{check_out}</toDate><currency>{currency}</currency>''' \
            .format(**{'check_in': self.check_in, 'check_out': self.check_out, 'currency': currency})
        rooms_info = ''
        len_rooms = ticket_info['room_info'][0]["num"]
        logger.info("同时预定{0}间房".format(len_rooms))
        # roomInfox需提供国籍信息,默认中国168
        for i in range(len_rooms):
            # print i
            roomNum = i
            # print roomNum
            self.occ = ticket_info['room_info'][0]["occ"]
            if self.occ == 0:
                self.occ = 2
            room_info = '''<room runno="{roomNum}"><adultsCode>{occ}</adultsCode><children no="{childrenNum}"></children><rateBasis>-1</rateBasis><passengerNationality>168</passengerNationality><passengerCountryOfResidence>168</passengerCountryOfResidence></room>''' \
                .format(**{'roomNum': roomNum, 'occ': self.occ, 'childrenNum': 0})
            rooms_info = rooms_info + room_info
        rooms = '''<rooms no="{len_rooms}">{roomInfos}</rooms>''' \
            .format(**{'len_rooms': len_rooms, 'roomInfos': rooms_info})
        # 酒店编码
        product_id = '''<productId>{hotel_code}</productId>''' \
            .format(**{'hotel_code': self.hotel_code})
        room_request_info = '''<request command="getrooms"><bookingDetails>{time_Currency}{rooms}{product_id}</bookingDetails></request>''' \
            .format(**{'time_Currency': time_Currency, 'rooms': rooms, 'product_id': product_id})
        data = '''<customer>{user_info}{room_request_info}</customer>''' \
            .format(**{'user_info': user_info, 'room_request_info': room_request_info})
        print '=='*20
        print data
        return data, URL

    def content_parser(self, content):
        content = content
        content_list = content.split('&')
        hotel_code = content_list[1]
        cityID = content_list[0]
        night = int(content_list[2])
        checkin = datetime.datetime.strptime(content_list[3], "%Y%m%d")
        checkout = checkin + datetime.timedelta(days=night)
        check_in = checkin.strftime("%Y-%m-%d")
        check_out = checkout.strftime("%Y-%m-%d")
        # check_in = time.mktime(time.strptime(content_list[2], '%Y%m%d'))
        # content_list[2]为入住天数，每天有24*60*60=86400秒，住几天乘几，并相加。
        # check_out = check_in + int(content_list[1])*86400
        # print hotel_code, check_in, check_out, cityID
        # print '-'*20
        return hotel_code, check_in, check_out, cityID

    def targets_request(self):
        task = self.task
        data, URL = self.make_data(task)

        @request(retry_count=3, proxy_type=PROXY_NONE, binding=self.parse_room)
        def pages_request():
            return {'req': {
                'method': 'POST',
                'url': URL,
                'headers': self.header,
                'data': data
            }, }

        return [pages_request, ]

    def get_property_info(self, root, name):
        for i in root.iter(name):
            pruduct = i
            return pruduct

    def parse_room(self, req, data):
        # 认证失败
        if "Wrong customer username or password or no access rights" in data:
            raise parser_except.ParserException(122, "认证失败")

        print '进入解析'
        # w = open('response_01.xml', 'w')
        # w.write(data)
        # w.close()
        # print data
        logger.info("返回内容：{0}".format(str(data)))
        task = self.task
        offer_count = 0
        redis_key = 'Null'
        if hasattr(task, 'redis_key'):
            redis_key = task.redis_key
        # print '-' * 20
        rooms = []
        mioji_hotel = Room()
        try:
            root = html.etree.fromstring(data.encode('utf-8'))
        except:
            print traceback.format_exc()
        try:
            allowBook = root.xpath("//allowBook")[0].text
            # print "allowBook:", allowBook
        except:
            print traceback.format_exc()
            raise parser_except.ParserException(29, "无此房型")
        if allowBook != 'yes':
            print traceback.format_exc()
            raise parser_except.ParserException(29, '有房间返回，但此房间不可预定')
        mioji_hotel.city = self.cityID
        mioji_hotel.check_in = self.check_in
        mioji_hotel.check_out = self.check_out
        mioji_hotel.source_hotelid = self.hotel_code
        mioji_hotel.source = 'dotwApi'
        mioji_hotel.real_source = 'dotwApi'
        # mioji_hotel.currency = root[0].text
        # try:
        mioji_hotel.currency = root.xpath('//currencyShort/text()')[0]
        mioji_hotel.hotel_name = root.find('hotel').attrib['name']
        # room = self.get_property_info(root, 'room')
        room_1 = root.xpath("/result/hotel/rooms/room")
        allkeys = re.findall(
            '<roomType runno="\d+" roomtypecode="(\d+)">.*?<allowsBeddingPreference>.*?</allowsBeddingPreference>.*?<allocationDetails>(.*?)</allocationDetails>',
            data, re.S)
        # print "---+---"*10
        # print allkeys
        allocations = {}
        for (m, n) in allkeys:
            allocations.setdefault(m, []).append(n)
        # print allocations
        # print allocations.keys()
        print "---+---" * 10
        rooms_id_list = []
        rooms_len = len(room_1)
        room = []
        roomtypecodes = []
        if rooms_len != 1:
            print "同时订了多间房"
            for i in room_1[1:]:
                room_ids = []
                room_123 = i.xpath("./roomType")
                for room_info in room_123:
                    room_ids.append(room_info.attrib['roomtypecode'])
                rooms_id_list.append(room_ids)
            
            room_id_list_1 = room_1[0].xpath("./roomType")
            for i1 in room_id_list_1:
                bowen = 1
                o = i1.attrib['roomtypecode']
                for i2 in rooms_id_list:
                    for h_id in i2:
                        if o == h_id:
                            bowen += 1
                if bowen == rooms_len:
                    room.append(i1)
                    roomtypecodes.append(o)
            print roomtypecodes
        else:
            room = root.xpath("/result/hotel/rooms/room/roomType")
            for i in room:
                roomtypecodes.append(i.attrib['roomtypecode'])
        print roomtypecodes
        print len(room)
        print "____"
        
        # print room
        # for i in room:
        #     print i.tag,i.attrib,i.text
        for room_info in room:
            # 给others_info 中
            rateBasis = room_info.xpath(
                './rateBases/rateBasis[1]')[0].attrib['id']
            mioji_hotel.source_roomid = room_info.attrib['roomtypecode']
            mioji_hotel.room_type = room_info.findtext('name')
            roomInfo = room_info.xpath('./roomInfo')
            try:
                mioji_hotel.occupancy = int(room_info.xpath(
                    './roomInfo/maxOccupancy/text()')[0])
                # print '最大入住人数为%d' % (mioji_hotel.occupancy)
            except:
                print traceback.format_exc()
                mioji_hotel.occupancy = self.occ
            mioji_hotel.price = float(room_info.xpath('.//total')[0].text)
            try:
                is_extrabed = root.xpath('//extraMeals')[0].attrib['count']
            except:
                is_extrabed = "No"
            if is_extrabed != 0:
                mioji_hotel.is_extrabed = 'Yes'
            else:
                mioji_hotel.is_extrabed = 'No'
            mioji_hotel.is_cancel_free = 'NULL'
            try:
                cancellationRules = room_info.xpath('.//cancellationRules')
                str_change_1, str_change_2, str_change_3, str_change_4 = '', '', '', ''
                str_return_1, str_return_2, str_return_3, str_return_4 = '', '', '', ''
                for i in cancellationRules:
                    miki_Date = i[0].tag
                    if miki_Date == 'toDate':
                        str_change_1 = '如果您在%s之前修改您的预定，我们将扣除您%s元的房款。' % (
                            i[0].text, i[2].text)
                        str_return_1 = '如果您在%s之前退订您的房间，我们将扣除您%s元的房款。' % (
                            i[0].text, i[3].text)
                        if i[3].text == '0':
                            mioji_hotel.is_cancel_free = 'Yes'
                        else:
                            mioji_hotel.is_cancel_free = 'No'
                    if miki_Date == 'fromDate':
                        if i[2].text == 'true':
                            str_change_2 = '在%s之后，您的预定将不可修改。' % (i[0].text)
                        if i[3].text == 'true':
                            str_return_2 = '在%s之后，您的预定将不可取消。' % (i[0].text)
                        if i[2].tag == 'toDate':
                            str_change_3 = '如果您在%s至%s之间修改您的预定，我们将扣除您%s元的房款。' % (
                                i[0].text, i[2].text, i[4][0].text)
                            str_return_3 = '如果您在%s至%s之间退订您的房间，我们将扣除您%s元的房款。' % (
                                i[0].text, i[2].text, i[5][0].text)
                        if i[2].tag == 'amendCharge':
                            str_change_4 = '如果您在%s之后修改您的预定，我们将扣除您%s元的房款。' % (
                                i[0].text, i[2].text)
                            str_return_4 = '如果您在%s之后退订您的房间，我们将扣除您%s元的房款。' % (
                                i[0].text, i[3].text)
                mioji_hotel.change_rule = str_change_1 + \
                    str_change_3 + str_change_4 + str_change_2
                mioji_hotel.return_rule = str_return_1 + \
                    str_return_3 + str_return_4 + str_return_2
            except:
                mioji_hotel.change_rule = 'NULL'
                mioji_hotel.return_rule = 'NULL'
            try:
                mealType = root.xpath('//mealType')[0].text
                # print "mealType:", mealType
                if mealType == 'Breakfast' or 'Half Board' or 'Full Board' or 'All Inclusive':
                    mioji_hotel.has_breakfast = 'Yes'
                    mioji_hotel.is_breakfast_free = 'Yes'
                else:
                    mioji_hotel.has_breakfast = 'No'
                    mioji_hotel.is_breakfast_free = 'No'
            except:
                mioji_hotel.has_breakfast = 'NULL'
                mioji_hotel.is_breakfast_free = 'NULL'
            pay_info = room_info.xpath('.//allocationDetails')[0].text
            # print "pay_info:", pay_info
            # pay_info = '123456abc'
            # others_info = {
            #     'rate_key':pay_info,
            #     'paykey':{'redis_key': redis_key,
            #             'id': offer_count},
            #     'payKey':{'redis_key': redis_key,
            #                 'id': offer_count},
            #     'roomtypecode':mioji_hotel.source_roomid,
            #     'selectedRateBasis':rateBasis,
            #     'productId':self.hotel_code,
            # }
            others_info = {}
            logger.info("roomtypecodes:{0}".format(roomtypecodes))
            logger.info("allocations:{0}".format(allocations))
            for roomtypecode in roomtypecodes:
                if roomtypecode in allocations.keys():
                    pay_infos = allocations[roomtypecode]
            others_info['rate_key'] = pay_infos
            others_info['paykey'] = {'redis_key': redis_key,
                                        'id': offer_count}
            others_info['payKey'] = {'redis_key': redis_key,
                                        'id': offer_count}
            others_info['roomtypecode'] = mioji_hotel.source_roomid
            others_info['selectedRateBasis'] = rateBasis
            others_info['productId'] = self.hotel_code
            offer_count += 1
            mioji_hotel.others_info = json.dumps(others_info)
            mioji_hotel.bed_type = 'NULL'
            mioji_hotel.size = -1
            mioji_hotel.floor = -1
            mioji_hotel.rest = -1
            mioji_hotel.tax = -1
            mioji_hotel.pay_method = 'NULL'
            mioji_hotel.is_extrabed_free = 'No'
            mioji_hotel.extrabed_rule = 'NULL'
            mioji_hotel.room_desc = 'NULL'
            mioji_hotel.guest_info = 'NULL'
            room = mioji_hotel
            roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                            room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                            room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                            room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                            room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                            room.change_rule, room.room_desc, room.others_info, room.guest_info)
            rooms.append(roomtuple)
        print rooms
        return rooms
        # except Exception as e:
        #     print traceback.format_exc()


if __name__ == '__main__':
    task = Task()
    task.source = 'DOTW'
    task.other_info= {}
    auth = {
        'URL': 'https://xmldev.DOTWconnect.com/gatewayV3.dotw',
        'username': 'MiojiXML',
        'password': 'Mioji2017',
        'company_code': 1439065,
    }
    auth = {"URL":"https://xmldev.DOTWconnect.com/gatewayV3.dotw","username":"MiojiXML","password":"Mioji2017","company_code":1439065}

    task.ticket_info = {
        "room_info": [{"num":1,"occ":2,"room_count":1}],
        # "room_info": [{"occ": 2, "num": 1}],
        'auth': json.dumps(auth)
    }
    # content:我方城市id、对方酒店id、居住天数、入住时间
    content_list = [
        # 33084,
        # 33094,
        33104,
        # 33114,
        # 33124,
        # 33134,
        # 33144,
        # 33154,
        # 33164,
        # 33174,
        # 33184,
        # 33194,
        # 1598908,

    ]
    result = []
    for i in content_list:
        task.content = '''20142&{num}&1&20171220'''.format(**{'num': i})
        task.content = "10009&33104&4&20171222"
        spider = DOTW_Spider(task)
        if spider.crawl() == 0:
            result.append(i)

    print result
        # result.append(spider.result)
        # print spider.result

        # print len(spider.result)
        # print i
