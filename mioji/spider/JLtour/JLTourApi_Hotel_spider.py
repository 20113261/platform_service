#coding:utf-8
from mioji.common.spider import Spider, request, PROXY_NONE
from mioji.common import parser_except
from mioji.common.task_info import Task
from mioji.common.logger import logger
from mioji.common.class_common import Room

import json
import time
import datetime
from collections import defaultdict


breakfast = {
    '7': '无早',
    '8': '一份早餐',
    '9': '两份早餐',
    '10': '床位早餐',
    '11': '床位中餐',
    '12': '床位晚餐',
    '41': '儿童早',
    '15785': '三份早餐',
    '15786': '四份早餐',
    '15787': '五份早餐',
    '15788': '六份早餐',
    '15789': '七份早餐',
    '15790': '八份早餐',
    '15791': '九份早餐',
    '15792': '十份早餐',
    '21923': '2大1小早餐',
    '21924': '2大1小晚餐',
    '21925': '双早双晚'
}

class JLTourApi_Hotel_Spider(Spider):
    source_type = 'jielvApiHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'},
    }
    old_spider_tag = {
        'jielvApiHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

    def init(self):
        try:
            self.redis_key = getattr(self.task, 'redis_key', None)
            auth = json.loads(self.task.ticket_info['auth'])
            self.req_query = {
                'Usercd': auth['Username'],
                'Authno': auth['Password'],
            }
            self.url = auth['url']+'service.do'
            self.occ = int(self.task.ticket_info['room_info'][0]['occ'])
        except Exception as e:
            logger.error(e)
            raise parser_except.ParserException(12, "检查一下auth信息")
        self.headers = {'Accept-Encodin': 'gzip'}
        self.city_id, self.source_id, night, check_in_data = self.task.content.split('&')
        self.check_in_data = check_in_data[:4]+'-'+check_in_data[4:6]+'-'+check_in_data[6:]
        self.check_out_data = datetime.datetime.strftime(datetime.datetime.strptime(self.check_in_data, '%Y-%m-%d') + datetime.timedelta(int(night)), '%Y-%m-%d')

    def targets_request(self):
        self.init()

        @request(retry_count=0, proxy_type=PROXY_NONE, binding=['room'])
        def validation():
            req_tpl = {
                'QueryType': 'hotelpricecomfirm',
                'hotelIds': self.source_id,
                'roomtypeids': '',
                'checkInDate': self.check_in_data,
                'checkOutDate': self.check_out_data,
                'pricingtype': '12'
            }
            req_tpl.update(self.req_query)
            return {
                'req': {
                    'method': 'POST',
                    'url': self.url,
                    'headers': self.headers,
                    'json': req_tpl
                },
                'data': {'content_type': 'json'},
            }

        @request(retry_count=0, proxy_type=PROXY_NONE)
        def info():
            req_tpl = {
                'hotelIds': self.source_id,
                'QueryType': 'hotelinfo'
            }
            req_tpl.update(self.req_query)
            return {
                'req': {
                    'method': 'POST',
                    'url': self.url,
                    'headers': self.headers,
                    'json': req_tpl
                },
                'user_handler': [self.parse_info],
                'data': {'content_type': 'json'},
            }
        return [info, validation]

    def parse_room(self, req, resp):
        print json.dumps(resp, ensure_ascii=False)
        """
        has_breakfast  该字段类型变动对方会发送邮件通知到君哥邮箱
        7   无早
        8   一份早餐
        9   两份早餐
        10  床位早餐
        11  床位中餐
        12  床位晚餐
        41  儿童早
        15785   三份早餐
        15786   四份早餐
        15787   五份早餐
        15788   六份早餐
        15789   七份早餐
        15790   八份早餐
        15791   九份早餐
        15792   十份早餐
        21923   2大1小早餐
        21924   2大1小晚餐
        21925   双早双晚
        备注：具体更新以新早餐份数列表附件为准


        一、取消修改条款逻辑如下。
            1、先看voidabletype是否为13，即“即订即保”（一旦预定不可取消或修改）。
            2、如果不是就看Dayselect和Timeselect字段，表示入住前多久可以取消。
            Dayselect int类型  如 1，Timeselect string类型 如 18:00，表示入住前1天的18:00后就不能取消了
            3、Dayselect和Timeselect为空不限制，据行业行规是当天18：00后不能取消
            4、下多间、多晚的订单时，请查询每天/每间房的取消条款，整张订单以最严格条款条款为准
        :param req:
        :param resp:
        :return:
        """
        if int(resp['success'])==8:
            raise parser_except.ParserException(121, resp.get('msg'))

        rooms = []
        _i_ = 0
        for data in resp.get('data', []):

            roomPriceDetails = data.get('roomPriceDetail', [])
            if not roomPriceDetails: continue

            roomPrices = defaultdict(list)
            for _ in roomPriceDetails:
                roomPrices[_['includebreakfastqty2']].append(_)

            for roomPriceDetail in [_[0] for _ in roomPrices.values()]:
                _room = self._rooms.get(data.get('roomtypeId'))
                if _room is None:continue
                room = Room()
                room.hotel_name = data.get('hotelName')
                room.city = self.city_id
                room.source = 'jielvApi'
                room.real_source = 'jielvApi'
                room.source_hotelid = str(data.get('hotelId'))
                room.source_roomid = str(data.get('roomtypeId', 'NULL'))
                room.room_type = data.get('roomtypeName', 'NULL')
                room.occupancy = _room.get('maximize')
                if room.occupancy<self.occ:continue
                room.bed_type = _room.get('bedtype')
                room.size = _room.get('acreages') or -1
                room.floor = _room.get('floordistribution') or -1

                _roomPrices = roomPrices[roomPriceDetail['includebreakfastqty2']]
                self.user_datas["restype"] = roomPriceDetail.get("restype", "")
                if self.user_datas["restype"] == 11:
                    self.user_datas['restype'] = "入住前"
                room.check_in = self.check_in_data
                room.check_out = self.check_out_data
                room.rest = roomPriceDetail.get('qtyable', 'NULL')
                room.price = roomPriceDetail.get('preeprice', 'NULL')
                room.price = sum(roomPrice['preeprice'] for roomPrice in _roomPrices)
                room.tax = -1
                room.currency = 'CNY'
                room.pay_method = 'mioji'
                room.is_extrabed = 'Yes' if _room.get('allowaddbed')==1 else 'No'
                room.has_breakfast = 'Yes' if roomPriceDetail.get('includebreakfastqty2') not in (7, 11, 12, 41, 21924) else 'No'
                room.is_breakfast_free = room.has_breakfast #早餐是否免费

                #判断取消规则
                if roomPriceDetail.get('voidabletype')==13:
                    room.is_cancel_free = 'No'
                    room.return_rule = '订单不可取消'
                    room.change_rule = ''
                else:
                    roomDetails = [(roomDetail.get('dayselect'), roomDetail.get('timeselect'), roomDetail.get('cashscaletype')) for roomDetail in _roomPrices]
                    dayselect = None
                    timeselect = None
                    cashscale_type = None
                    for Dayselect, Timeselect, cashscaletype in roomDetails:
                        if not Dayselect and not Timeselect:
                            _ = '可以免费退改'
                            continue
                        flag = False
                        if type(Dayselect) is int:
                            if dayselect is None:
                                dayselect = Dayselect
                                cashscale_type = cashscaletype
                                flag = True
                            if Dayselect > dayselect:
                                dayselect = Dayselect
                                cashscale_type = cashscaletype
                                flag = True

                            if flag and Timeselect.strip() and time.strptime(Timeselect.strip(), '%H:%M'):
                                if timeselect is None:
                                    timeselect = time.strptime(Timeselect.strip(), '%H:%M')
                                if time.strptime(Timeselect.strip(), '%H:%M') > timeselect:
                                    timeselect = time.strptime(Timeselect.strip(), '%H:%M')

                    if dayselect is None and timeselect is None:
                        room.is_cancel_free = 'Yes'
                        room.return_rule = '可以免费取消'
                        room.change_rule = ''
                    else:
                        room.is_cancel_free = 'NULL'
                        print repr(dayselect), repr(timeselect)
                        if dayselect is None:
                            room.return_rule = '免费取消截止时间：入住当日%s 点之前<br/>逾期收取罚金:' % ( time.strftime('%H:%M', timeselect))
                            room.change_rule = ""
                        else:
                            room.return_rule = '免费取消截止时间：%s %s 天，%s 点之前<br/>逾期收取罚金:' % ( self.user_datas["restype"], dayselect, time.strftime('%H:%M', timeselect))
                            room.change_rule = ""
                    if cashscale_type==12:
                        room.return_rule += '扣除全额房费'
                        room.change_rule += ''
                    elif cashscale_type == 11:
                        room.return_rule += '扣除首晚房费'
                        room.change_rule += ''

                if room.is_extrabed=='Yes':
                    room.extrabed_rule = '允许加床数量 %s, 允许加床尺寸 %s' % (_room.get('allowaddbedqty'), _room.get('allowaddbedsize'))
                else:
                    room.extrabed_rule == 'NULL'
                room.room_desc = _room.get('remark2')

                room.others_info = json.dumps({
                    'paykey': {'redis_key': self.redis_key, 'id': _i_},
                    'payKey': {'redis_key': self.redis_key, 'id': _i_},
                    'rate_key': {
                        'includebreakfastqty2': roomPriceDetail['includebreakfastqty2'],
                        'preeprices': str([roomPrice['preeprice'] for roomPrice in _roomPrices]),
                        'ratetype': roomPriceDetail.get('ratetype'),
                        'supplierid': roomPriceDetail.get('supplierid'),
                        'hotelId': data.get('hotelId'),
                        'roomtypeId': data.get('roomtypeId')
                    },
                    'extra': {
                        'breakfast': breakfast.get(str(roomPriceDetail.get('includebreakfastqty2')), '无'),
                        'return_rule': ''.join([room.return_rule, room.change_rule]),
                        'occ_des': str(room.occupancy),
                    }
                })
                room.guest_info = 'NULL'
                _i_ += 1
                roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                             room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                             room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                             room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                             room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                             room.change_rule, room.room_desc, room.others_info, room.guest_info)
                rooms.append(roomtuple)

        print '*'*100
        print json.dumps(rooms, ensure_ascii=False)
        print '*' * 100
        return rooms

    def parse_info(self, req, resp):
        """
        房间最大入住人数需要从 基础信息接口中拿
        :param req:
        :param resp:
        :return:
        """
        print json.dumps(resp, ensure_ascii=False)
        if int(resp['success'])==8:
            raise parser_except.ParserException(121, resp.get('msg'))

        if resp.get('data', [{}])[0].get('active')==8:
            raise parser_except.ParserException(121, '该酒店禁用')
        self._rooms = {room['roomtypeid']: room for room in resp.get('data', [{}])[0].get('rooms', []) if room.get('active')==1}

if __name__ == '__main__':
    tasks = Task()
    tasks.redis_key = "hotel|ht11804435|jielvApi|20180216|1|1517371858994|10.10.80.208|8090|0"
    # tasks.content = 'NULL&34288&1&20180412'
    tasks.content = '20040&171813&1&20180216'
    tasks.ticket_info = {
        'room_info': [
            {
                "occ":2,
                "num":1,
                "room_count":1
            }
        ],
        'auth': json.dumps({"Password":"123456","Username":"SZ28276","url":"http://58.250.56.211:8081/common/"})}
    gta = JLTourApi_Hotel_Spider(tasks)
    gta.crawl()
    print gta.result
    print gta.result['room']