#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import time
import sys
sys.path.insert(0, '/Users/miojilx/Desktop/git/Spider/src')
import pdb
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE
from mioji.common.task_info import Task
from mioji.common import parser_except
from mioji.common.class_common import Room
import traceback
import xmltodict
from lxml import html


class Miki_Spider(Spider):
    source_type = 'mikiHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'},
    }
    old_spider_tag = {
        'mikiApiHotel': {'required': ['room']}
    }
    redis_key = 'Null'

    def init_ctx(self, task):
        task = task
        auth = json.loads(task.ticket_info['auth'])
        ctx = dict()
        ctx['url'] = auth.get(
            'URL', 'https://test.mikinet.co.uk/interfaceWL/ws/7.0')
        ctx['method'] = 'post'
        ctx['header'] = {
            'Accept-Encoding': 'gzip,deflate',
            'Content-Type': 'application/soap+xml;charset=UTF-8;action="hotelSearch"',
        }
        taskContent = task.content
        taskcontent = taskContent.encode('utf-8')
        requestDateTime = time.strftime(
            '%Y-%m-%dT%H:%M:%S', time.localtime(time.time()))
        #'20142&CAJ282100&2&20170910'
        task_infos = taskContent.split('&')
        # cityNumber=城市编码 20142  productiCode = 酒店编码CAJ282100 numberOfNights = 住几晚1 check_in = 20170909,
        self.cityNumber, productCode, numberOfNights, check_in = task_infos[
            0], task_infos[1], task_infos[2], task_infos[3]
        agentCode = auth.get('agentCode', 'YJI001')
        # print agentCode
        requestPassword = auth.get('requestPassword', 'PASSWORDPASSWORD1234')
        # print requestPassword
        # 2017-09-10
        checkIn = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
        # 总共请求的房间数
        miojiRoomNo = task.ticket_info['room_info'][0]['num']
        # print miojiRoomNo
        
        # print occ
        # 账号信息认证模块
        requestAuditInfo = '''<requestAuditInfo><agentCode>{agentCode}</agentCode><requestPassword>{requestPassword}</requestPassword><requestID>0</requestID><requestDateTime>{requestDateTime}</requestDateTime></requestAuditInfo>'''\
            .format(**{'agentCode': agentCode, 'requestPassword': requestPassword, 'requestDateTime': requestDateTime})
        # cityNumber = '<cityNumbers><cityNumber>{cityNumber}</cityNumber></cityNumbers>'
        # 以下为请求中房间信息
        destination = '''<destination><hotelRefs><productCodes><productCode>{productCode}</productCode></productCodes></hotelRefs></destination>'''\
            .format(**{'productCode': productCode, 'cityNumber': self.cityNumber, })
        stayPeriod = '''<stayPeriod><checkinDate>{checkIn}</checkinDate><numberOfNights>{numberOfNights}</numberOfNights></stayPeriod>'''\
            .format(**{'checkIn': checkIn, 'numberOfNights': numberOfNights, })
        resultDetails = '''<returnHotelInfo>1</returnHotelInfo>'''
        # 一般一次只预定一间房，留接口做判断，如果非一间那么通过for凑齐格式
        roomlist = []
        for i in range(miojiRoomNo):
            # 人数
            self.occ = int(task.ticket_info['room_info'][0]['occ'])
            roomNo = '''<roomNo>{miojiRoomNo_i}</roomNo>'''.format(
                **{'miojiRoomNo_i': i+1})
            guest = '''<guest><type>ADT</type></guest>''' * self.occ
            guests = '''<guests>{guest}</guests>'''.format(**{'guest': guest})
            room = '''<room>{roomNo}{guests}</room>'''.format(
                **{'roomNo': roomNo, 'guests': guests})
            roomlist.append(room)
            # rooms = '''<rooms>{room}</rooms>'''.format(**{'room':room})
        room_str = ''.join(roomlist)
        # 所有房间信息拼凑完成
        rooms = '''<rooms>{0}</rooms>'''.format(room_str)
        # 是否只返回最便宜的房0or1
        # priceCriteria = '''<priceCriteria><returnBestPriceIndicator>0</returnBestPriceIndicator></priceCriteria>'''
        # 关于房间信息的整合
        hotelSearchCriteria = '<hotelSearchCriteria currencyCode="USD" paxNationality="CN" languageCode="zh">{destination}{stayPeriod}{rooms}<resultDetails><returnHotelInfo>1</returnHotelInfo></resultDetails></hotelSearchCriteria>'''\
            .format(**{'destination': destination, 'stayPeriod': stayPeriod, 'rooms': rooms, })
        # 所有信息在此拼接完成
        data = '''<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Header/><soap:Body><hotelSearchRequest versionNumber="7.0">{requestAuditInfo}{hotelSearchCriteria}</hotelSearchRequest></soap:Body></soap:Envelope>'''\
            .format(**{'requestAuditInfo': requestAuditInfo, 'hotelSearchCriteria': hotelSearchCriteria})
        ctx['data'] = data
        print '_'
        print data 
        return ctx

    def targets_request(self):
        task = self.task
        ctx = self.init_ctx(task)
        url = ctx['url']
        data = ctx['data']
        header = ctx['header']

        @request(retry_count=3, proxy_type=PROXY_NONE, binding=self.parse_room)
        def token_request():
            a = {'req': {
                    'method': 'POST',
                    'url': url,
                    'headers': header,
                    'data': data}
                    }
            print a
            print '='*100
            return a
        return [token_request]

    def get_property_info(self, root, name):
        for i in root.iter(name):
            pruduct = i
            return pruduct

    def parse_room(self, req, data):
        try:
            print '进入解析'
            print data
            # w = open('Miki_responseCAI636700.xml', 'w')
            # w.write(data)
            # print '保存完成'
            # w.close()
            task = self.task
            redis_key = 'Null'
            if hasattr(task, 'redis_key'):
                redis_key = task.redis_key
            rooms = []
            mioji_hotel = Room()
            root = html.etree.fromstring(data)
            mioji_hotel.source = 'mikiApi'
            # print mioji_hotel
            mioji_hotel.real_source = 'mikiApi'
            mioji_hotel.city = self.cityNumber
            try:
                availabilitySummary = root.xpath('//availabilitySummary')[0]
                totalAvailable, totalOnRequest = [
                    child.text for child in availabilitySummary.iterchildren()]
                print "totalAvailable", 'totalOnRequest', totalAvailable, totalOnRequest
                hotelInfo = root.xpath('//hotelInfo')[0]
                mioji_hotel.hotel_name = hotelInfo.find('hotelName').text
                print "hotel_name:", mioji_hotel.hotel_name
            except:
                print traceback.format_exc()
                raise parser_except.ParserException(29, "无此房型")
            room_desc = ''
            try:
                alerts = root.xpath('//alerts/alert')
                for alert in alerts:
                    title = alert.findtext('title')
                    fromDate = alert.findtext('fromDate')
                    toDate = alert.findtext('toDate')
                    description = alert.findtext('description')
                    room_desc = room_desc + \
                        '%s：在%s至%s之间，%s;|' % (
                            title, fromDate, toDate, description)
                print "room_desc:", room_desc
                mioji_hotel.room_desc = room_desc
            except:
                mioji_hotel.room_desc = 'NULL'
            category = hotelInfo.findtext('category')
            starRating = hotelInfo.findtext('starRating')
            cityname = hotelInfo.findtext('cityname')
            print "category", 'starRating', 'cityname', category, starRating, cityname
            hotel = root.xpath('//hotel')[0]
            mioji_hotel.source_hotelid = hotel.findtext('productCode')
            mioji_hotel.currency = hotel.findtext('currencyCode')
            # mioji_hotel.currency = hotel[1].text #currencyCode:EUR
            stayPeriod = self.get_property_info(root, 'stayPeriod')
            # <checkinDate>2017-09-10</checkinDate>
            mioji_hotel.check_in = stayPeriod[0].text
            # <checkoutDate>2017-09-12</checkoutDate>
            mioji_hotel.check_out = stayPeriod[1].text
            mioji_hotel.others_info = {}
            offer_count = 0
            try:
                roomOptions = root.xpath('//roomOptions/roomOption')
            except:
                raise parser_except.ParserException(29, "无此房型")
            for roomOption in roomOptions:
                availabilityStatus = roomOption.findtext('availabilityStatus')
                rateIdentifier = roomOption.findtext('rateIdentifier')
                if int(availabilityStatus) == 2:
                    continue
                room_desc_1 = roomOption.findtext("roomDescription")
                mioji_hotel.source_roomid = roomOption.attrib.get(
                    'roomTypeCode', None)
                mioji_hotel.room_type = roomOption.findtext("roomDescription")
                mioji_hotel.price = float(roomOption.xpath(
                    './roomTotalPrice/price')[0].text)
                # print mioji_hotel.price
                cancellationPolicies = root.xpath(
                    '//cancellationPolicies/cancellationPolicy')
                Mioji_others_info = dict()
                Mioji_others_info = {
                    'paykey': {'redis_key': redis_key,
                               'id': offer_count},
                    'roomTypeCode': mioji_hotel.source_roomid,
                    'rate_key': rateIdentifier,
                    'payKey': {'redis_key': redis_key,
                               'id': offer_count},
                }
                mioji_hotel.others_info = json.dumps(Mioji_others_info)
                offer_count += 1
                refunds_info = []
                for cancellationPolicy in cancellationPolicies:
                    refunds_list = dict()
                    refunds_list['appliesFrom'] = cancellationPolicy.findtext(
                        'appliesFrom')
                    refunds_list['fullStay'] = cancellationPolicy.findtext(
                        'fullStay')
                    refunds_list['Percentage'] = cancellationPolicy.xpath(
                        './cancellationCharge/percentage')[0].text
                    refunds_info.append(refunds_list)
                occ_dict = {
                    '00001': 2,
                    '00002': 1,
                    '00003': 3,
                    '00004': 1,
                    '01001': 2,
                    '01002': 1,
                    '01127': 5,
                    '01147': 6,
                    '01158': 7,
                    '01191': 8,
                    '01204': 9,
                    '01238': 1,
                    '01239': 1,
                    '01240': 1,
                    '01242': 1,
                    '02095': 4,
                    '93039': self.occ}
                try:
                    mioji_cancel_strs = ''
                    cancellationPolicies = root.xpath(
                        '//cancellationPolicies')[0]
                    # cancellationPolicies = self.get_property_info(root, 'cancellationPolicies')
                    refundable = cancellationPolicies.attrib['refundable']
                    if refundable == '0' or refundable == '1':
                        mioji_hotel.is_cancel_free = 'No'
                    else:
                        mioji_hotel.is_cancel_free = 'Yes'
                    for cancellationPolicy in cancellationPolicies.getchildren():
                        if cancellationPolicy[1].text == 'false':
                            cancel_str = '第一晚房款的'
                        elif cancellationPolicy[1].text == 'true':
                            cancel_str = '所有房款的'
                        cancel_time = cancellationPolicy[0].text
                        cancellationCharge = cancellationPolicy[2][0].text
                        print cancellationCharge
                        mioji_cancel_str = '从您预订时间开始，到%s,如果您取消您的预定，我们将扣除您%s,百分之%s;|' % (
                            cancel_time, cancel_str, cancellationCharge)
                        mioji_cancel_strs += mioji_cancel_str
                except:
                    mioji_hotel.is_cancel_free = 'NULL'
                    mioji_cancel_strs = 'NULL'
                mioji_hotel.return_rule = mioji_cancel_strs
                mioji_hotel.occupancy = occ_dict[mioji_hotel.source_roomid]
                mioji_hotel.bed_type = 'NULL'
                mioji_hotel.size = -1.0
                mioji_hotel.floor = -1
                mioji_hotel.rest = -1
                mioji_hotel.tax = -1.0
                mioji_hotel.is_extrabed = 'NULL'
                mioji_hotel.is_extrabed_free = 'NULL'
                mioji_hotel.has_breakfast = 'NULL'
                mioji_hotel.is_breakfast_free = 'NULL'
                mioji_hotel.pay_method = 'mioji'
                mioji_hotel.extrabed_rule = 'NULL'
                mioji_hotel.change_rule = 'NULL'
                mioji_hotel.guest_info = 'NULL'
                mioji_hotel.hotel_url = 'NULL'
                room = mioji_hotel
                roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                             room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                             room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                             room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                             room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                             room.change_rule, room.room_desc, room.others_info, room.guest_info)
                rooms.append(roomtuple)
            return rooms
        except Exception as e:
            print traceback.format_exc()


if __name__ == '__main__':
    task = Task()
    task.source = 'Miki'
    auth = {
        # 主要信息
        'agentCode': 'YJI001',
        'requestPassword': 'PASSWORDPASSWORD1234',
        'URL': 'https://test.mikinet.co.uk/interfaceWL/ws/7.0',
        # 次要信息
        'Clientcode': 'MMM001',
        'UserID': 'sdkaccess',
        'Password': 'password',
    }
    task.ticket_info = {
        # "room_info": [{"occ": 3, "num": 1}, {"occ": 2, "num": 2}],
        "room_info": [{"occ": 2, "num": 24},],
        # "room_info": [{"occ": 2, "num": 1},{"occ": 2, "num": 1},{"occ": 2, "num": 1},{"occ": 2, "num": 1},{"occ": 2, "num": 1},{"occ": 2, "num": 1},{"occ": 2, "num": 1},],
        "auth": json.dumps(auth)
    }
    # source_id(对方:city_code, item_code), 住几晚, 入住时间
    task.content = '20142&CAF562300&1&20171226'
    # task.content = "10002&CAN432700&433320170831"
    print task
    spider = Miki_Spider(task)
    spider.crawl()
    print '==' * 30
    print spider.result
