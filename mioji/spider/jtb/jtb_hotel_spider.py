#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
jtbhotel
"""
import json
import datetime
import hashlib
import hmac
import xmltodict

from bs4 import BeautifulSoup
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

room_type = {
    1: ["PSG", "SGL", "SIT", "JPN", "JWS", "DSR", "MSN"],
    2: ["SDB", "TWN", "DBL", "SIT", "JPN", "JWS", "DSR", "MSN"],
    3: ["TPL", "SIT", "JPN", "JWS", "DSR", "MSN"],
    4: ["QUD", "SIT", "JPN", "JWS", "DSR", "MSN"]
    # "suite": "SIT",
    # "japanese style": "JPN",
    # "Japanese and western": "JWS",
    # "Stateroom": "DSR",
    # "Maisonette": "MSN"
}


class JtbHotelSpider(Spider):
    source_type = 'jtbApiHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'},
    }
    old_spider_tag = {
        'jtbApiHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.hotel = {}
        super(JtbHotelSpider, self).__init__(task=task)

    def pretreatment(self):
        self.auth = json.loads(self.task.ticket_info.get('auth', 'NULL'))
        self.headers = dict()
        self.headers['Accept-Encoding'] = 'application/gzip'
        self.headers['Content-Type'] = 'application/xml'
        self.base_url = self.auth['url']
        self.occ = int(self.task.ticket_info['room_info'][0].get('occ', 2))
        self.room_num = int(self.task.ticket_info['room_info'][0]['room_count'])
        TypeCode = room_type[self.occ]
        self.room_stay = ''
        if type(TypeCode) == list:
            for i in range(len(TypeCode)):
                self.room_stay += '<RoomStayCandidate RoomTypeCode="%s" Quantity="%d"/>' % (TypeCode[i], self.room_num)
        else:
            self.room_stay += '<RoomStayCandidate RoomTypeCode="%s" Quantity="%d"/>' % (TypeCode, self.room_num)
        self.city_id, self.hotelid, self.night, self.check_in = self.task.content.split('&')
        self.checkin = self.check_in[:4] + '-' + self.check_in[4:6] + '-' + self.check_in[6:]
        self.checkout = datetime.datetime.strftime(datetime.datetime.strptime(self.checkin, '%Y-%m-%d') + datetime.timedelta(int(self.night)), '%Y-%m-%d')

    def targets_request(self):
        self.pretreatment()
        use_record_qid(unionKey='jtbApi', api_name="availability", task=self.task, record_tuple=[1, 0, 0])

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def get_room_data():
            url = self.base_url + '/GA_HotelAvail_v2013?wsdl'
            headers = self.headers
            req_param = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns="http://service.api.genesis2.jtbgmt.com/">
                       <soapenv:Header/>
                       <soapenv:Body>
                          <GA_HotelAvailRQ>
                             <POS>
                                <Source>
                                   <RequestorID ID="{ID}" MessagePassword="{PW}">
                                      <CompanyName Code="{Code}"/>
                                      <BasicInfo Version="2013" Language="ZH-CN"/>
                                   </RequestorID>
                                </Source>
                             </POS>
                             <AvailRequestSegments>
                                <AvailRequestSegment>
                                   <HotelSearchCriteria>
                                      <Criterion  SortType="PRICE" AvailStatus="ALL">
                                         <HotelCode Code="{hotelid}"/>
                                         <RoomStayCandidates SearchCondition="OR">
                                            {room_stay}
                                         </RoomStayCandidates>
                                         <StayDateRange Start="{checkin}" End="{checkout}"/>
                                      </Criterion>
                                   </HotelSearchCriteria>
                                </AvailRequestSegment>
                             </AvailRequestSegments>
                          </GA_HotelAvailRQ>
                       </soapenv:Body>
                    </soapenv:Envelope>
                    '''.format(ID=self.auth['ID'], PW=self.auth['MessagePassword'], Code=self.auth['Code'],
                               hotelid=self.hotelid, room_stay=self.room_stay, checkin=self.checkin, checkout=self.checkout)
            return {
                'req': {
                    'method': 'POST',
                    'url': url,
                    'headers': headers,
                    'data': req_param
                },
            }

        return [get_room_data, ]

    def parse_room(self, req, resp):
        '''
        :param req:
        :param resp:
        :return:
        '''
        print '开始解析'
        soup = BeautifulSoup(resp, 'lxml')
        # print 'debug4->', soup.prettify()
        task = self.task
        redis_key = 'Null'
        if hasattr(task, 'redis_key'):
            redis_key = task.redis_key
        rooms = []
        unuse = []
        room_index = 0
        if soup.errors:
            raise parser_except.ParserException(21, soup.errorinfo.get('shorttext'))
        numberofrateplans = int(soup.ga_hotelavailrs.get('numberofrateplans'))
        if numberofrateplans == 0:
            raise parser_except.ParserException(29, 'no rooms')
        self.hotel['address'] = soup.basicpropertyinfo.get('hoteladdress')
        for plan in soup.rateplans:
            rateplanid = plan.get('rateplanid')
            rateplanname = plan.get('rateplanname').split(' ')
            room = Room()
            if len(rateplanname) == 4:
                room.room_type = rateplanname[1]
            elif len(rateplanname) == 3:
                room.room_type = rateplanname[0]
            room.price = 0.00
            room.room_desc = plan.get('rateplanname')
            if plan.mealsincluded.get('mealplancodes') == 'RMO':
                room.has_breakfast = 'No'
                room.is_breakfast_free = 'No'
            else:
                room.has_breakfast = 'Yes'
                room.is_breakfast_free = 'Yes'
            c = 0
            cancel_content = ''
            for roomstay in soup.roomstays:
                # print roomstay
                # 若预定时间内有房间状态不可用，当前的房间不可预定
                status = roomstay.get('statuscomment')

                if status:
                    unuse.append(roomstay.rateplans.rateplan.get('rateplanid'))
                    unuse = set(unuse)
                    unuse = list(unuse)

                if rateplanid in unuse:
                    self.room_type_code = roomstay.roomtypes.roomtype.get('roomtypecode')
                    continue
                occ = int(roomstay.roomtypes.occupancy.get('maxoccupancy'))
                if rateplanid == roomstay.rateplans.rateplan.get('rateplanid') and self.occ == occ:
                    c += 1
                    self.room_type_code = roomstay.roomtypes.roomtype.get('roomtypecode')
                    fee = float(roomstay.roomrates.roomrate.total.get('amountaftertax'))
                    if roomstay.cancelpenalties.cancelpenalty.amountpercent.get('percent'):
                        durations = roomstay.cancelpenalties
                        times = []
                        for duration in durations:
                            details = {}
                            details['end'] = duration.get('end')
                            details['start'] = duration.get('start')
                            details['percent'] = duration.amountpercent.get('percent')
                            times.append(details)
                        new_detail = sorted(times, key=lambda x: x.get('end', ''), reverse=False)
                        cancel_content += '第%s晚退改政策：<br />申请退款时间：%s至%s<br />扣款比例：%d％<br />申请退款时间：%s至%s<br />' \
                                          '扣款比例：%d％<br />申请退款时间：%s至%s<br />扣款比例：%d％<br />申请退款时间：%s至%s<br />' \
                                          '扣款比例：免费取消<br /><br />'%(
                                             c, new_detail[3].get('start'), new_detail[3].get('end'), int(new_detail[3].get('percent')[:-3]),
                                             new_detail[2].get('start'), new_detail[2].get('end'), int(new_detail[2].get('percent')[:-3]),
                                             new_detail[1].get('start'), new_detail[1].get('end'), int(new_detail[1].get('percent')[:-3]),
                                             new_detail[0].get('start'), new_detail[0].get('end'))
                    else:
                        durations = roomstay.cancelpenalties
                        times = []
                        for duration in durations:
                            details = {}
                            details['end'] = duration.get('end')
                            details['start'] = duration.get('start')
                            details['amount'] = duration.amountpercent.get('amount')
                            times.append(details)
                        new_detail = sorted(times, key=lambda x: x.get('end', ''), reverse=False)
                        # print new_detail
                        cancel_fee1 = float(new_detail[1].get('amount'))
                        cancel_fee2 = float(new_detail[2].get('amount'))
                        cancel_content += '第%s晚退改政策：<br />申请退款时间：%s至%s<br />取消费用：%s日元<br />申请退款时间：%s至%s<br />' \
                                          '取消费用：%s日元<br />申请退款时间：%s至%s<br />取消费用：%s日元<br />申请退款时间：%s至%s<br />' \
                                          '取消费用：%s日元<br /><br />' % (
                                            c, new_detail[3].get('start'), new_detail[3].get('end'), fee,
                                            new_detail[2].get('start'), new_detail[2].get('end'), cancel_fee2,
                                            new_detail[1].get('start'), new_detail[1].get('end'), cancel_fee1,
                                            new_detail[0].get('start'), new_detail[0].get('end'), 0)
                    room.source_roomid = roomstay.rateplans.rateplan.get('rateplanid')
                    room.occupancy = int(roomstay.roomtypes.occupancy.get('maxoccupancy'))
                    room.bed_type = roomstay.roomtypes.roomtype.get('roomtype')
                    room.rest = int(roomstay.get('numberofunitsfortheday'))
                    room.price += float(roomstay.roomrates.roomrate.total.get('amountaftertax'))
                    room.hotel_name = soup.basicpropertyinfo.get('hotelname')

            room.city = 'Null'
            room.source = 'jtbApi'
            room.source_hotelid = soup.basicpropertyinfo.get('hotelcode')
            room.real_source = 'jtbApi'
            room.size = -1
            room.floor = -1
            room.check_in = self.checkin
            room.check_out = self.checkout
            room.tax = -1
            room.currency = 'JPY'
            room.pay_method = 'mioji'
            room.is_extrabed = 'Null'
            room.is_extrabed_free = 'Null'
            room.extrabed_rule = 'Null'
            room.guest_info = 'Null'
            room.return_rule = ''
            room.is_cancel_free = 'Null'
            room.change_rule = ''
            # print cancel_content
            room.return_rule = cancel_content

            room.others_info = json.dumps({
                'paykey': {
                    'redis_key': redis_key,
                    'id': room_index,
                    'room_num': self.room_num,
                    'room_type_code': self.room_type_code
                },
                'payKey': {
                    'redis_key': redis_key,
                    'id': room_index,
                    'room_num': self.room_num,
                    'room_type_code': self.room_type_code
                },
                'extra': {
                    'breakfast': '',
                    'payment': '',
                    'return_rule': room.return_rule,
                    'occ_des': room.occupancy
                }
            }, ensure_ascii=False)
            room_index += 1

            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                          room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                          room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                          room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                          room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                          room.change_rule, room.room_desc, room.others_info, room.guest_info)

            # 排除不可用状态的房间
            if room_tuple[0] is not 'NULL':
                rooms.append(room_tuple)
        return rooms


if __name__ == '__main__':
    spider.slave_get_proxy = utils.simple_get_socks_proxy
    task = Task(source='jtbApi')
    # content: 城市ID，hotelID，入住天数，入住日期 4016001 1101002 1111002 4017003
    task.content = '20045&4016003&3&20180609'
    task.ticket_info = {
        "room_info": [
            {
                "occ": 2,
                "num": 2,
                "room_count": 2,
            },
        ],
        "auth": json.dumps(
            {"Code": "X1873", "ID": "X1873GAUSER", "MessagePassword": "js6X8z3i",
             "url": "https://trial-www.jtbgenesis.com/genesis2-demo/services"})
    }
    spider = JtbHotelSpider(task)
    print spider.crawl()
    print json.dumps(spider.result['room'], ensure_ascii=False)
