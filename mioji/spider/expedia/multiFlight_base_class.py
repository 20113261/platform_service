#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import re
import json
import urllib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import MultiFlight
from mioji.common.airline_common import Airline
from mioji.common.logger import logger
from flight_lib import process_ages, process_passenger_info

id_pat = re.compile(r'<div id=\"originalContinuationId\">.+<\/div>')
classdict = {"3": "E", "2": "B", "1": "F", "5": "P"}
cabindict = {"E": "经济舱", "B": "商务舱", "F": "头等舱", "P": "超级经济舱"}
cabin_dict_n2c = {"3": "经济舱", "2": "商务舱", "1": "头等舱", "5": "超级经济舱"}
cabin_dict_en = {'E': 'economy', 'B': 'business', 'P': 'premium', 'F': 'first'}
passenger_type_dict = {  # 详情票类型的字典
    "Senior": "老年人",
    "Adult": "成年人",
    "Child": "儿童",
    "Infant in seat": "婴儿(占位)",
    "Infant in lap": "婴儿(不占位)"
}


def format_time(dept_day, c):
    y = dept_day[:4]
    m = dept_day[4:6]
    d = dept_day[-2:]
    return m + c + d + c + y


def get_dur(duration):
    h = duration['hours']
    m = duration['minutes']
    d = duration['numOfDays']
    return h * 60 * 60 + m * 60 + d * 24 * 60 * 60


class BaseMultiFlightSpider(Spider):

    def __init__(self, task=None):
        Spider.__init__(self)
        # 任务信息
        self.num_passenger = 1
        self.dept_id = None
        self.dest_id = None
        self.dept_day = None
        self.return_day = None
        self.seat_code = None  # seat_code  E B F P
        self.seat_type = None  # seat_type  英文全称
        self.flight_no = None
        self.passenger_count = 0
        self.target_carrier = None
        self.trips = None
        # 链接
        self.host = ''
        self.source = ''
        # self.request_url_template = url_template
        self.request_url = None
        self.request_url_airline = None
        self.paging_url_template = '%s/Flight-Search-Paging?c=%s&is=1&sp=asc&cz=200&cn=0'
        self.paging_url = None
        self.paging_url_verify = None

        self.ages_info = None
        self.adults = None
        self.child = []
        self.child_count = None
        self.has_infant = False
        self.verify_urls = []
        self.verify_flights = []
        self.verify_tickets = []
        # 处理这些信息
        if task:
            self.task = task

        # 爬取的某些参数
        self.ids = None
        # 最后返回的数据
        self.tickets = []

    def targets_request(self):
        if self.dept_day is None:
            self.process_task_info()

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, new_session=True)
        def first_page():
            ret = []
            ret1 = {
                'req': {'url': self.request_url, 'headers': {"Connection": "close"}},
                'user_handler': [self.process_paging_url],
            }
            ret.append(ret1)
            if self.request_url_airline:
                ret2 = {
                    'req': {'url': self.request_url_airline, 'headers': {"Connection": "close"}},
                    'user_handler': [self.process_paging_url_verify],
                }
                ret.append(ret2)
            return ret

        yield first_page

        @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_MultiFlight, async=True)
        def get_tickets_page():
            ret = []
            ret1 = {
                'req': {'url': self.paging_url},
                'data': {'content_type': 'json'},
                'user_handler': [self.assert_ticket],
                'v': 0,
            }
            ret.append(ret1)
            if self.paging_url_verify:
                ret2 = {
                    'req': {'url': self.paging_url_verify},
                    'data': {'content_type': 'json'},
                    'user_handler': [self.assert_ticket],
                    'v': 1,
                }
                ret.append(ret2)
            return ret

        yield get_tickets_page

        # if self.verify_urls:
        #     @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_MultiFlight, async=True)
        #     def get_verify_page():
        #         reqs = [{
        #             'req': {'url': url},
        #             'user_handler': [self.parse_VerifyFlight],
        #         } for url in self.verify_urls]
        #         return reqs
        #     yield get_verify_page
        # return ret

    def respon_callback(self, req, resp):
        pass

    def parse_MultiFlight(self, req, json_data):
        url = req['req']['url']
        url_regex = 'Flight-Search-Details'

        if url_regex in url:
            return self.verify_tickets
        else:
            ticket = self.process_resp_json(req, json_data)
            self.tickets.extend(ticket)
            return ticket

    def process_resp_json(self, req, json_data):  # 解析返回的json数据（机票信息）
        ticket = []
        legs = json_data['content']['legs']

        offers = json_data['content']['offers']  # offer里面 找leg
        for k, val in offers.items():
            multiflight = MultiFlight()
            totalPrice = val['price']['totalPriceAsDecimal']
            leg_list = []
            for legid in val['legIds']:
                leg_list.append(legs[legid])
            multiflight.price = float(totalPrice) / self.adults
            multiflight.tax = 0
            multiflight.currency = val['price']['currencyCode']

            flights_nos = []
            plane_types = []
            flight_corps = []
            dept_ids = []
            dest_ids = []
            dept_days = []
            dept_times = []
            dest_times = []
            durations = []
            seat_types = []
            stop_ids = []
            stop_times = []
            stops = []
            daydiff = []
            for leg in leg_list:
                dept_times.append(leg['departureTime']['isoStr'][:19])
                dest_times.append(leg['arrivalTime']['isoStr'][:19])
                itinerary = get_flight_numbers(leg['timeline'])
                flights_nos.append(itinerary['flights_nos'])
                duration = leg['duration']['hours'] * 3600 + leg['duration']['minutes'] * 60
                durations.append(str(duration))
                # stops.append(str(len(leg['timeline'])-1))
                stops.append(str(len(itinerary['flights_nos'].strip().split('_')) - 1))
                plane_types.append(itinerary['plane_types'])
                flight_corps.append(itinerary['flight_corps'])
                dept_ids.append(itinerary['dept_id'])
                dest_ids.append(itinerary['dest_id'])
                dept_days.append(itinerary['dept_day'])
                seat_types.append(itinerary['seat_types'])
                stop_ids.append(itinerary['stop_ids'])
                stop_times.append(itinerary['stop_times'])
                count = len(itinerary['flights_nos'].strip().split('_'))
                daydiff.append("_".join(['0'] * count))
            multiflight.flight_no = "&".join(flights_nos)
            multiflight.plane_type = "&".join(plane_types)
            multiflight.flight_corp = "&".join(flight_corps)
            # multiflight.dept_id = "&".join(dept_ids)
            # multiflight.dest_id = "&".join(dest_ids)
            dept_id_0 = stop_ids[0].split('_')[0]
            dest_id_0 = stop_ids[0].split('_')[-1]
            dept_id_1 = stop_ids[-1].split('_')[0]
            dest_id_1 = stop_ids[-1].split('_')[-1]
            multiflight.dept_id = dept_id_0 + '&' + dept_id_1
            multiflight.dest_id = dest_id_0 + '&' + dest_id_1
            multiflight.dept_day = "&".join(dept_days)
            multiflight.dept_time = "&".join(dept_times)
            multiflight.dest_time = "&".join(dest_times)
            multiflight.dur = "&".join(durations)
            multiflight.seat_type = "&".join(seat_types)
            multiflight.real_class = multiflight.seat_type
            multiflight.stop_id = "&".join(stop_ids)
            multiflight.stop_time = "&".join(stop_times)
            multiflight.stop = "&".join(stops)
            multiflight.source = '%s::%s' % (self.source, self.source)
            multiflight.promotion = "&".join(['NULL'] * 2)
            multiflight.package = "&".join(['NULL'] * 2)
            multiflight.daydiff = "&".join(daydiff)
            multiflight.return_rule = "&".join(['NULL'] * 2)
            multiflight.change_rule = "&".join(['NULL'] * 2)
            multiflight.share_flight = "&".join(['NULL'] * 2)
            multiflight.stopby = "&".join(['NULL'] * 2)
            multiflight.baggage = "&".join(['NULL'] * 2)
            multiflight.transit_visa = "&".join(['NULL'] * 2)
            multiflight.reimbursement = "&".join(['NULL'] * 2)
            multiflight.flight_meals = "&".join(['NULL'] * 2)
            multiflight.ticket_type = "&".join(['NULL'] * 2)
            multiflight.others_info = "&".join(['NULL'] * 2)
            if multiflight.flight_no == self.flight_no:
                multiflight.offer_ids = k
                id = self.ids_verify if req['v'] else self.ids
                url = self.host + '/Flight-Search-Details?c=' + id + \
                      '&tripId1=%20&offerId=' + urllib.quote(multiflight.offer_ids) + '&xsellchoice=normal&isSplitTicket=false'
                self.verify_urls.append(url)
                self.verify_flights.append(multiflight)

            ticket.append(multiflight.to_tuple())
        return ticket

    def process_task_info(self):
        ticket_info = self.task.ticket_info
        content = self.task.content

        self.target_carrier = get_carrier(ticket_info)
        self.trips = extract_trips(content)
        self.flight_no = self.task.ticket_info.get('flight_no', None)
        self.seat_code = ticket_info.get('v_seat_type', 'E')
        self.passenger_count = int(ticket_info.get('v_count', '2'))
        self.num_passenger = int(ticket_info.get('v_count', '2'))
        self.ages_info = ticket_info.get('v_age', None)
        self.adults, self.child, self.child_count, self.has_infant = process_ages(int(self.num_passenger),
                                                                                  self.ages_info)
        self.option_passenger = process_passenger_info(self.adults, self.child, self.child_count, self.has_infant)
        self.get_search_url()

    def get_search_url(self, children=0):
        if self.adults > 6:
            raise parser_except.ParserException(12, '任务出错')
        base = '%s/Flights-Search?trip=multi' % self.host
        self.adults, self.child, self.child_count, self.has_infant = process_ages(int(self.num_passenger),
                                                                                  self.ages_info)
        passenger_part = '&' + self.option_passenger
        cabin = cabin_dict_en[self.seat_code]
        option = '&mode=search&options=cabinclass:' + cabin
        index = 1
        legs = ''
        for trip in self.trips:
            val = '&leg%s=from:%s,to:%s,departure:%sTANYT' % (index, trip['dept'],
                                                              trip['dest'], trip['dept_time'])
            legs += val
            index += 1
        base = base + legs
        base += passenger_part
        base += option

        self.request_url = base
        if self.target_carrier:
            base += ',carrier:' + self.target_carrier  # 逗号 option 冒号 航空公司
            self.request_url_airline = base
            assert self.request_url != self.request_url_airline

    def process_paging_url(self, req, resp):
        pat = re.compile('id="originalContinuationId">(.*?)<')
        try:
            self.ids = pat.findall(resp)[0]
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "找不到ContinuationId")
        self.paging_url = self.paging_url_template % (self.host, self.ids)  # 这里要不要yield

    def process_paging_url_verify(self, req, resp):
        pat = re.compile('id="originalContinuationId">(.*?)<')
        try:
            self.ids_verify = pat.findall(resp)[0]
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "找不到ContinuationId")
        self.paging_url_verify = self.paging_url_template % (self.host, self.ids_verify)  # 这里要不要yield
        self.paging_url_verify += '&fa=%s' % self.target_carrier


    def assert_ticket(self, req, resp):
        if not resp['content']['legs']:
            if not self.tickets:
                raise parser_except.ParserException(parser_except.PROXY_INVALID, "获得空的json")

    def parse_VerifyFlight(self, req, resp):
        pat = re.compile('priceBreakDown = (.*);')
        try:
            data = pat.findall(resp)[0]
            data = json.loads(data)
            type_list = data['productPriceModels'][0]['model']['flightTravelerModelList']
            val = []
            for tickets_type in type_list:
                tmp = "%s:%s" % (passenger_type_dict[tickets_type['passengerType']], tickets_type['totalPrice'])
                val.append(tmp)
            flight = self.verify_flights.pop()
            flight.others_info = ';'.join(val)
            flight.others_info = "%s&%s" % (flight.others_info, flight.others_info)
            self.verify_tickets.append(flight.to_tuple())
        except:
            pass



def get_flight_numbers(timeline):
    flight_no_list = []
    plane_type_list = []
    seat_type_list = []
    flight_corp_list = []
    stop_id_list = []
    stop_time_list = []
    dept_id = 'NULL'
    dest_id = 'NULL'
    for segment in timeline:
        if not segment['segment']:
            continue
        carrier = segment['carrier']
        flight_no = carrier['airlineCode'] + carrier['flightNumber']
        flight_no_list.append(flight_no)
        plane_type_list.append(carrier['plane'])
        cabin = cabin_dict_n2c[str(carrier['cabinClass'])]
        seat_type_list.append(cabin)
        flight_corp = Airline.get(carrier['airlineCode'], 'NULL')
        if flight_corp == 'NULL':
            logger.info("expediamulti:Cannot found airport code %s", carrier['airlineCode'])
        flight_corp_list.append(flight_corp)
        dept_airport = segment['departureAirport']['code']
        dest_airport = segment['arrivalAirport']['code']
        stop_id_list.append(dept_airport + '_' + dest_airport)
        dept_time = segment['departureTime']['isoStr'][:19]
        arr_time = segment['arrivalTime']['isoStr'][:19]
        stop_time_list.append(dept_time + '_' + arr_time)
        if dept_id == 'NULL':
            dept_id = dept_airport
        dest_id = dest_airport
    ret = {}
    ret['dept_id'] = dept_id
    ret['dest_id'] = dest_id
    ret['flights_nos'] = '_'.join(flight_no_list)
    ret['plane_types'] = '_'.join(plane_type_list)
    ret['flight_corps'] = '_'.join(flight_corp_list)
    ret['seat_types'] = '_'.join(seat_type_list)
    ret['stop_ids'] = '|'.join(stop_id_list)
    ret['stop_times'] = '|'.join(stop_time_list)
    ret['dept_day'] = ret['stop_times'][:10]
    return ret


def get_carrier(ticket_info):
    if 'flight_no' in ticket_info:
        return ticket_info['flight_no'][:2]
    return ''


def extract_trips(taskcontent):
    trips = []
    for content in taskcontent.split('|'):
        trip = {}
        trip['dept'], trip['dest'], trip['date'] = content.split('&')
        trip['dept_time'] = format_time(trip['date'], '/')
        # dt.strptime(trip['date'], '%Y%m%d').strftime('%m/%d/%Y')
        trips.append(trip)
    return trips
