#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Created on    : 18/1/22 下午2:49
# @Author  : zpy
# @Software: PyCharm

from mioji.common.spider import Spider, request, PROXY_NEVER
from mioji.common import parser_except
from mioji.common.task_info import Task
from mioji.common.logger import logger
from mioji.common.class_common import Room
import xmltodict
from mioji.common.check_book.check_book_ratio import use_record_qid

from datetime import datetime, timedelta
import json
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class VeturisApiHotel(Spider):
    """
    这个api的整个流程

    搜索酒店获取酒店的基本信息（支持按照城市id 和 酒店id搜索） 获取到一个ocj 和 datos
    获取预订的详细信息 用obj datos
    预订确认 用 obj datos -> 订单id 和 SecurityCode
    取消预订 或者 查看订单 使用 订单id 和 SecurityCode

    """
    source_type = 'veturisApiHotel'

    targets = {'room': {'version': 'InsertHotel_room4'}}

    old_spider_tag = {
        'veturisApiHotel': {'required': ['room']}
    }
    def __init__(self, task=None):
        super(VeturisApiHotel, self).__init__(task)

    def convert_date(self, date):
        """ 20180101 --> 2018-01-01 """
        return '-'.join([date[:4], date[4:6], date[6:]])

    def str_datetime(self, s):
        """wtf ..   2018-02-15 --> datetime obj"""
        return datetime.strptime(s, "%Y-%m-%d")

    def add_day(self, date, night):
        """ 增加日期。"""
        night = int(night)
        _checkin = self.convert_date(date)
        _checkout = str(self.str_datetime(_checkin) + timedelta(night))[:10]
        return _checkin, _checkout

    def search_parse(self, hid, checkin, checkout, occlist):
        """
        传入一个hid ，occ列表，日期

        occ 可以添加多个。 格式是[[1,2,0],[3,3,1]] 分别代表房间数， 成人数，儿童数

        通过下面这个字段发送的请求能够拿到 sessionid obj datos
        （obj datos） 获取额外信息
         （sessionid hid） 获取酒店详情
        :param hid:
        :return:
        """
        # 拼occ字段
        occ = ''.join(['<Occupancy><Rooms>{}</Rooms><Adults>{}</Adults><Children>{}</Children></Occupancy>'.
                      format(i,j,k) for i,j,k in occlist])

        search_base = '''<?xml version="1.0" encoding="UTF-8"?>\n
            <SearchAvailabilityRQ version="2.0" language="ENG">
                <Request>
                    <DestinationID>H_{hid}</DestinationID>
                    <Check_in_date>{checkin}</Check_in_date>
                    <Check_out_date>{checkout}</Check_out_date>
                    {occ}
                </Request>
            </SearchAvailabilityRQ>
        '''
        search_req = search_base.format(hid=hid,checkin=checkin,checkout=checkout,occ=occ)
        return search_req

    def additonal_parse(self, obj, datos):
        """构造获取额外信息的请求, 在预订的时候会用到这个字段"""
        additional_base = '''<?xml version="1.0" encoding="UTF-8"?>\n
        <AdditionalInformationRQ version="2.0" language="ENG">
        <Request>
        <obj>{obj}</obj>
        <DATOS>{datos}</DATOS>
        </Request>
        </AdditionalInformationRQ>
        '''
        return additional_base.format(obj=obj, datos=datos)

    def detail_parse(self, sid, hid):
        detail_base  = '''<?xml version="1.0" encoding="UTF-8"?>\n
        <HotelDetailsAvailabilityRQ version="2.0" language="ENG">
         <Request>
         <HotelID>{hid}</HotelID>
         <Session_id>{sid}</Session_id>
         </Request>
        </HotelDetailsAvailabilityRQ>
        '''
        return detail_base.format(hid=hid, sid=sid)

    def occlist_parse(self, occ):
        """ rooms adults children"""
        occlist = []
        for o in occ:
            occlist.append((o['room_count'], o['occ'], 0))
        return occlist

    def parse_task(self, content, ticket_info):
        self._redis_key = getattr(self.task, 'redis_key', None)
        try:
            self._cid, self._hid, self._night, self._date = content.split('&')
            self._checkin, self._checkout = self.add_day(self._date, self._night)
            self._occlist = self.occlist_parse(ticket_info['room_info'])
            self._room_num = self._occlist[0][0] # 后面验证房间数量的时候用
            self._auth = json.loads(ticket_info['auth'])
        except:
            raise parser_except.ParserException(12, "检查任务是否正确")

        return

    def req_tmp(self, xmlrq):
        try:
            req = {
                'user': self._auth['User'],
                'password': self._auth['Password'],
                'agencyUser': self._auth['agencyUser'],
                'agencyPasword': self._auth['agencyPassword'],
            }
        except:
            raise parser_except.ParserException(121, "请检查auth信息是否给正确了。")
        req['xmlRQ'] = xmlrq
        return req

    def targets_request(self):
        use_record_qid(unionKey='veturisApi', api_name="veturisApi", task=self.task, record_tuple=[1, 0, 0])
        self.parse_task(self.task.content, self.task.ticket_info)
        url = json.loads(self.task.ticket_info['auth'])['URL']
        @request(retry_count=0, proxy_type=PROXY_NEVER, binding=['room'])
        def search_req():
            xmlrq = self.search_parse(self._hid, self._checkin, self._checkout, self._occlist)

            return {
                'req':{
                    'method': 'POST',
                    'url': url, # 测试url
                    'data': self.req_tmp(xmlrq)},
                # 'user_handler':[self.parse_search],
                'data':{'content_type':self.xml_to_dict}
            }

        @request(retry_count=0, proxy_type=PROXY_NEVER)
        def detail_req():
            xmlrq = self.detail_parse(self._sid, self._hid)
            return {
                'req': {
                    'method': 'POST',
                    'url': url,  # 测试url
                    'data': self.req_tmp(xmlrq)},
                'user_handler': [self.parse_room],
                'data': {'content_type': self.xml_to_dict}
            }


        yield search_req
        # yield detail_req

    def xml_to_dict(self,req, data):
        return xmltodict.parse(data)

    def fxxk_list(self, data):
        if not isinstance(data, list):
            return [data]
        return data

    def parse_room(self, req, data):
        """ 解析出sid， 和其他的基本信息
        occ如果有多个的话需要分开请求。。。
        """
        res = []
        room = Room()
        breakfast_list = ['2', '3', '4', '5', '11', '12']  # 检查是否有早餐

        # 在测试的时候未发现 用户名 密码会影响搜索结果。
        try:
            self._sid = data['resultadosRS']['Response']['SessionID']
        except:
            raise parser_except.ParserException(29, "无房") # 如果取不到，就是没有该类型的房间
        resp = data['resultadosRS']['Response']
        self._obj = resp['obj']

        _hotels = resp['Hotels']['Hotel']
        _hotels = self.fxxk_list(_hotels)

        room.hotel_name = _hotels[0]['HotelDetails']['Name']
        room.source = 'veturisApi'
        room.real_source = 'veturisApi'
        room.source_hotelid = self._hid
        room.check_in = self._checkin
        room.check_out = self._checkout

        for hotel in _hotels:
            _rooms = hotel['Accommodations']['Room']
            _rooms = self.fxxk_list(_rooms)

            for r in _rooms:
                room.room_type = r['RoomType']['Name']

                _board = r['Board']
                _board = self.fxxk_list(_board)

                room.currency = _board[0]['Currency']
                room.source_roomid = r['RoomType']['ID']
                room.occupancy = self._occlist[0][1]

                for _id, h in enumerate(_board):
                    if h['Board_type']['ID'] in breakfast_list:
                        room.has_breakfast = 'Yes'
                        room.is_breakfast_free = 'Yes'
                    else:
                        room.has_breakfast = 'No'
                        room.is_breakfast_free = 'No'
                    room.price = float(h['Price']['#text']) / float(r['RoomType']['NumberRooms'])

                    # if h['Refundable'] == 'Y':
                    #     room.is_cancel_free = 'Yes'
                    # elif h['Refundable'] == 'N':
                    #     room.is_cancel_free = 'No'
                    # else:
                    #     pass

                    room.others_info = json.dumps({
                        'paykey': {'redis_key': self._redis_key, 'id': _id},
                        'payKey': {'redis_key': self._redis_key, 'id': _id},
                        'rate_key': {
                            'obj': self._obj,  # 这里的obj 和 datos 用来唯一确定一个房间，在获取预订详情 和预订的时候要用。
                            'datos': h['DATOS'],
                            'room_num': self._room_num, # 后面用来对房间进行对比
                        }
                    })
                    roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                                 room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                                 room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                                 room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                                 room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                                 room.change_rule, room.room_desc, room.others_info, room.guest_info)
                    res.append(roomtuple)

        return res

    def parse_detail(self, req, data):
        """ 获取酒店的详细信息，暂时用不到 """
        res = []
        resp = data['HotelDetailsAvailabilityRS']['Response']
        room = Room()
        room.hotel_name = resp['Hotel']['HotelDetails']['Name']
        room.source_hotelid = self._hid





if __name__ == '__main__':
    task = Task()
    task.content = '51011&10634&1&20180413'
    for content in ['51011&10634&1&20180413', '10019&10016&1&20180413',
                    '10028&10463&1&20180413', '10019&10017&1&20180413',
                    '10019&10002&1&20180413', '10022&10243&2&20180228']:
        task.content = content
        task.other_info = {}
        task.ticket_info = {
            'room_info': [
                {
                    "occ": 2,
                    "num": 1,
                    "room_count": 1,
                },
            ],
            'auth': json.dumps({
                'User': 'testmioji',
                'Password': 'testmioji',
                'agencyUser': 'test',
                'agencyPassword': 'test',
                'URL': 'http://testxml.veturis.com/xmlWebServices.php',
            })
        }

        v = VeturisApiHotel()
        v.task = task
        print v.crawl()
        print v.result









