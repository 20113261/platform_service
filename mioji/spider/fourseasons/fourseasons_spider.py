#!/usr/bin/env python
# -*- coding: utf-8-*-

import re
import json
from copy import deepcopy
import datetime
from lxml import etree
import gevent.pool

from mioji.common import parser_except
from mioji.common.class_common import Hotel
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room
from mioji.common import parser_except


class HyattSpider(Spider):
    source_type = 'hyattHotel'

    targets = {
        'room': {},
        # 'get_price': {},
    }

    old_spider_tag = {
        'hyattHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(HyattSpider, self).__init__(task)
        self.other = {}
        self.room_id = []
        self.roomss = []
        self.query_data = {}
        self.need_flip_limit = False

    def fetch_ticket_info(self):
        hotel_id, nights, check_in = self.task.content.split('&')
        check_in_date = datetime.datetime.strptime(check_in, '%Y%m%d')
        days = datetime.timedelta(days=int(nights))
        room_info = self.task.ticket_info['room_info']
        room = room_info[0].get('room_count', [])
        if room != 1:
            room = 2
        adult = room_info[0].get('occ', [])

        check_out_date = check_in_date + days
        check_in, check_out = str(check_in_date).split(' ')[0], str(check_out_date).split(' ')[0]
        self.query_data = dict(check_in=check_in, check_out=check_out, hotel_id=hotel_id, adults=adult, room=room)

    def targets_request(self):
        self.fetch_ticket_info()

        url = "https://reservations.f.com/ibe/common/processSearchForm.do"
        # timein = '2018-04-22'
        # timeout = '2018-04-25'
        # id = 'DOH562'
        payload = '{"form":{"SearchPanelForm":{"SearchType":"H","method":"post","name":"plan_trip","action":"/common/processSearchForm.do","PageInfo":{"Language":"EN","Locale":"en_US","FromServicing":"false","ConversationID":"OJ1522225766257","SessionID":"16F36BB2A95422135AD03C43C98FA76B.ojibea1.live","ReadOnly":"false","skin":"legacy","SessionSource":"Browse-IBE","POS":{"CompanyCode":"ibe"}},"Restrictions":{"MaxChildren":"5","PostBookingDeeplink":"false","HomePage":"true","MaxNumLegs":"6"},"SearchTypeInput":{"type":"fixed","name":"Search/searchType","value":"H"},"XSellModeInput":{"type":"fixed","name":"xSellMode","value":"false"},"DropOffLocationRequiredInput":{"type":"fixed","name":"dropOffLocationRequired","value":"false"},"NumNightsInput":{"type":"fixed","name":"Search/DateInformation/numNights","value":"7"},"HotelSearch":{"SearchTypeValidatorInput":{"type":"fixed","name":"searchTypeValidator","value":"H"},"Location":{"DestinationTypeInput":{"type":"list","name":"destinationLocationSearchBoxType","value":"L","option":[{"value":"L","selected":"selected"},{"value":"G"}]},"DestinationLongitudeInput":{"type":"geocode","name":"Search/OriginDestinationInformation/Destination/location-longitude","value":""},"DestinationLatitudeInput":{"type":"geocode","name":"Search/OriginDestinationInformation/Destination/location-latitude","value":""},"DestinationNameInput":{"type":"fixed","name":"Search/OriginDestinationInformation/Destination/location_input_geocode","value":"","readonly":"false","disabled":"false"},"DestinationInput":{"type":"location","name":"Search/OriginDestinationInformation/Destination/location","value":"","display":"","parameters":"&searchableOnly=true&includeHotelNames=true","readonly":"false","disabled":"false"}},"Calendar":{"DepartDateInput":{"type":"calendar","name":"Search/DateInformation/departDate","value":"%s"},"ReturnDateInput":{"type":"calendar","name":"Search/DateInformation/returnDate","value":"%s"}},"NumRoomsInput":{"type":"number","name":"Search/HotelInformation/numRooms","value":1},"RoomTypeInput":{"type":"list","name":"Search/HotelInformation/roomType","value":""},"Rooms":{"Room":[{"AdultsInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$1$/adults","value":"2"},"ChildrenInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$1$/children","value":"0"},"ChildAges":{"ChildAgeInput":[{"type":"number","name":"Search/HotelInformation/RoomInformation$1$/ChildAges/childAge$1$","value":""},{"type":"number","name":"Search/HotelInformation/RoomInformation$1$/ChildAges/childAge$5$","value":""}]}},{"AdultsInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$2$/adults","value":"0"},"ChildrenInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$2$/children","value":"0"},"ChildAges":{"ChildAgeInput":[{"type":"number","name":"Search/HotelInformation/RoomInformation$2$/ChildAges/childAge$1$","value":""},{"type":"number","name":"Search/HotelInformation/RoomInformation$2$/ChildAges/childAge$5$","value":""}]}},{"AdultsInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$3$/adults","value":"0"},"ChildrenInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$3$/children","value":"0"},"ChildAges":{"ChildAgeInput":[{"type":"number","name":"Search/HotelInformation/RoomInformation$3$/ChildAges/childAge$1$","value":""},{"type":"number","name":"Search/HotelInformation/RoomInformation$3$/ChildAges/childAge$5$","value":""}]}},{"AdultsInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$4$/adults","value":"0"},"ChildrenInput":{"type":"number","name":"Search/HotelInformation/RoomInformation$4$/children","value":"0"},"ChildAges":{"ChildAgeInput":[{"type":"number","name":"Search/HotelInformation/RoomInformation$4$/ChildAges/childAge$1$","value":""},{"type":"number","name":"Search/HotelInformation/RoomInformation$4$/ChildAges/childAge$5$","value":""}]}}]},"MoreOptionsInput":{"type":"fixed","name":"Search/moreOptions","value":"true"},"AdditionalOptions":{"RoomRatingInput":{"type":"list","name":"Search/HotelInformation/roomRating","value":""},"PropertyTypeInput":{"type":"list","name":"Search/HotelInformation/propertyType","value":""},"LocationTypeInput":{"type":"list","name":"Search/HotelInformation/locationType","value":""},"HotelNameInput":{"type":"string","name":"Search/HotelInformation/hotelName","value":""},"HotelChainInput":{"type":"list","name":"Search/HotelInformation/hotelChain","value":"FS"},"HotelCodeInput":{"type":"list","name":"Search/HotelInformation/hotelCode","value":"%s"},"HotelPromoTypeInput":{"type":"string","name":"Search/HotelInformation/hotelPromoType","value":""},"HotelPromoCodeInput":{"type":"string","name":"Search/HotelInformation/hotelPromoCode","value":""},"RateCodeInput":{"type":"list","name":"Search/HotelInformation/rateCode","value":""}}}}},"content":[{"type":"accommodations","params":{"experimentId":""}},{"key":"propertyMetaData","type":"metadata"},{"type":"upsells","params":{"property":"%s"}},{"type":"offers","params":{"property":"%s"}},{"key":"propertyBookingMessagesAvailability","type":"propertyBookingMessages","params":{"property":"%s","bookingStep":"availability","checkinDate":"%s","checkoutDate":"%s"}},{"key":"propertyBookingMessagesSoldOut","type":"propertyBookingMessages","params":{"property":"%s","bookingStep":"soldout","checkinDate":"%s","checkoutDate":"%s"}}],"locale":"en"}' % (
        self.query_data['check_in'], self.query_data['check_out'], self.query_data['hotel_id'], self.query_data['hotel_id'], self.query_data['hotel_id'], self.query_data['hotel_id'], self.query_data['check_in'], self.query_data['check_out'], self.query_data['hotel_id'], self.query_data['check_in'], self.query_data['check_out'])
        #timein, timeout, id, id, id, id, timein, timeout, id, timein, timeout)
        headers = {
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36",
            'content-type': "application/json;charset=UTF-8",
        }
        url_f = 'https://reservations.f.com/ibe/common/clearHome.do'
        pay = '{"form":{"ClearSession":{"method":"POST","action":"/common/clearHome.do"}},"locale":"en"}'
        # 打第一个接口 拿cookie
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            return {
                'req': {
                    'method': 'POST',
                    'url': url_f,
                    'data': pay,
                    'headers': headers,
                },
            }

        yield first_page

        # 主要数据
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def index_page():
            return {
                'req': {
                    'method': 'POST',
                    'url': url,
                    'data': payload,
                    'headers': headers,
                },
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_room_other],
            }
        yield index_page

        # 取消政策
        change_rules=[]
        self.room_id
        room_id = self.room_id
        for i in room_id:
            URL = 'https://reservations.f.com/content/properties/{hotel_id}/termsandconditions?checkinDate={checkinDate}&checkoutDate={checkoutDate}&locale=en&offerCode={room_id_1}&roomCode={room_id_2}'.format(hotel_id=self.query_data['hotel_id'], checkinDate=self.query_data['check_in'], checkoutDate=self.query_data['check_out'], room_id_1=i[0], room_id_2=i[1])
            change_rules.append(({'req': {'url': URL, 'method': 'get', 'headers': headers,},'data': {'content_type': 'json'},}))
        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_room)
        def room_change_rule():
            return  change_rules
        yield room_change_rule



    def parse_room(self, req, resp):
        key_1 = req['req']['url'].split('&')[-2].split('=')[-1]
        key_2 = req['req']['url'].split('&')[-1].split('=')[-1]
        key = (key_1, key_2)
        value = resp['cancellationPolicy']
        try:
            v = self.other.get(key)
            v[24] = value
            return [tuple(v)]
        except:
            print '****'

        # if self.other[key] == key:
        #         room[24] = value
        #         print tuple(room)
        #         return [tuple(room)]
    def parse_room_other(self, req ,resp):
        # print resp
        room = Room()
        room.source_hotelid = resp['HotelSearchResults']['Hotels']['Hotel'][0]['Code']
        room.city = resp['HotelSearchResults']['Hotels']['Hotel'][0]['Address']['CityName'][0]['_text']
        room.source = 'f'
        room.real_source = 'f'
        room.hotel_name = resp['HotelSearchResults']['Hotels']['Hotel'][0]['Name']
        rooms = resp['HotelSearchResults']['Hotels']['Hotel'][0]['Rooms']['Room']
        for one_room in rooms:
            # print '****'
            # print one_room
            room.source_roomid = one_room['Code']

            # 获取退改信息url的id_1 和id_2
            room_id = one_room['RatePlanCode']
            offers = resp['offers']['bookableOffers']
            for one in offers:
                if one['owsCode'] == room_id:
                    a = one['orsCode']
                    b = room.source_roomid
                    self.room_id.append([a,b])

            room.id = one_room['RatePlanCode']
            room.room_type = one_room['Name']
            room_code = room.room_type.replace(' ','_').lower()
            others = resp['accommodations']['bookableAccommodations']
            for one in others:
                if one['uniqueName'] == room_code:
                    other_infos = one['sleepingArrangements']
                    for i in other_infos:
                        try:
                            if room.source_roomid == i['owsCode']:
                                room.bed_type = i['bedTypeDescription']
                                room.room_desc = i['unitLongDescription']
                                room.other = i['occupancyString']
                                room.occupancy = room.other.strip(' ')[0]
                                room.extrabed_rule = i['extraBed']
                                room.floor = i['location']
                                room.size = i['size'].strip(' ')[0]
                                room.room_desc_2 = i['bathroomDescription']
                                if 'rollaway' in room.extrabed_rule or 'crib' in room.extrabed_rule:
                                    room.is_extrabed = 'YES'
                                    room.extrabed_rule = i['extraBed']
                                else:
                                    room.is_extrabed = ''
                                    room.extrabed_rule = ''
                                room.check_in = self.query_data['check_in']
                                room.check_out = self.query_data['check_out']
                                room.rest = -1
                                room.price = one_room['Price']['Total']['Amount']
                                room.tax = -1
                                room.currency = one_room['Price']['Total']['Currency']
                                room.is_extrabed_free = ''
                                room.has_breakfast = ''
                                room.is_breakfast_free = ''
                                room.is_cancel_free = ''
                                # room.return_rule = self.other[one_room['RatePlanCode']]
                                room.return_rule = ''
                                room.pay_method = ''
                                room.change_rule = ''
                                room.guest_info = ''
                                room.hotel_url = ''
                                room.others_info = json.dumps({'extra':
                                    {
                                        'breakfast': '',
                                        'payment': '在线支付'.encode('utf-8'),
                                        'return_rule': '',
                                        'occ_des': room.other
                                    }
                                })
                                room_list = [room.hotel_name, room.city, room.source, room.source_hotelid,
                                              room.source_roomid, room.real_source, room.room_type, room.occupancy,
                                              room.bed_type, room.size, room.floor, room.check_in, room.check_out,
                                              room.rest, room.price, room.tax, room.currency, room.pay_method,
                                              room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free,
                                              room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc,
                                              room.others_info, room.guest_info]
                                # self.roomss.append(room_list)
                                self.other[(a,b)] = room_list
                        except:
                            print '-----'
        print len(self.other)





if __name__ == "__main__":
    from threading import Thread
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new, simple_get_socks_proxy
    from mioji.common import spider

    #
    spider.slave_get_proxy = simple_get_socks_proxy
    task = Task()
    task.content = 'DOH562&1&20180416'
    task.content = 'MIA953&1&20180330'
    task.content = 'DAM234&1&20180330'
    task.ticket_info = {
        'room_info': [{
            # 成年人数
            'occ': '2',
            # 房间数
            'room_count': 3,
            'num' : 1,
        }]
    }
    # task.source = 'hyatt'
    spider = HyattSpider(task)
    spider.crawl()

    # spider.crawl(required=['hotel'])
    print spider.code
    print spider.result