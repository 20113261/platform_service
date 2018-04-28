#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
import json
import urllib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight, RoundFlight
from mioji.common.logger import logger
from flight_lib import process_ages, process_passenger_info
from mioji.common.func_log import current_log_tag
cabin = {'E': 'economy', 'P': 'premium', 'F': 'first', 'B': 'business'}
cabin_dict = {'5': '超级经济舱', '1': '头等舱', '2': '商务舱', '3': '经济舱'}
passenger_type_dict = {  # 详情票类型的字典
    "Senior": "老年人",
    "Adult": "成年人",
    "Child": "儿童",
    "Infant in seat": "婴儿(占位)",
    "Infant in lap": "婴儿(不占位)"
}
url_template = '%s/Flights-Search?trip=roundtrip&leg1=from:%s,to:%s,departure:%sTANYT' \
               '&leg2=from:%s,to:%s,departure:%sTANYT' \
               '&%s&' \
               'options=cabinclass:%s&mode=search'

pat_time = re.compile('\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d')
pat_day = re.compile('\d\d\d\d-\d\d-\d\d')



def gen_para_dict(org, arg):
    l = org.split('\n')
    s = []
    for e in l:
        e = e.strip()
        k, v = tuple(e.split(':'))
        s.append('\"' + k + '\":' + '\"' + v + '\",')
    res = '\n'.join(s)
    res = '{\n' + res[:-1] + '\n}'
    res_dict = json.loads(res)
    for k, v in arg.items():
        res_dict[k] = v
    return res_dict


def get_dur(duration):
    h = duration['hours']
    m = duration['minutes']
    d = duration['numOfDays']
    return h * 60 * 60 + m * 60 + d * 24 * 60 * 60


class BaseRoundFlightSpider(Spider):
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
        self.dept_flight_no = None
        self.ret_flight_no = None
        # 链接

        self.ages_info = None
        self.adults = None
        self.child = []
        self.child_count = None
        self.has_infant = False

        self.host = ''
        self.source = ''
        self.request_url_template = url_template
        self.request_url = None
        self.paging_url_template = '%s/Flight-Search-Paging?c=%s&is=1&sp=asc&cz=200&cn=0&ul=0'
        self.paging_url = None

        self.verify_urls = []
        # 处理这些信息
        if task:
            self.task = task

        # 爬取的某些参数
        self.ids = None
        self.verify_flights = []

        self.tickets = []
        self.verify_tickets = []
        self.dept_flight_naturalkey = ''

    def targets_request(self):
        if self.dept_day is None:
            self.process_task_info()

        @request(retry_count=3, proxy_type=PROXY_REQ, new_session=True)
        def get_dept_list_page():
            return {
                'req': {'url': self.request_url, 'headers': {"Connection": "close"}},
                'user_handler': [self.process_paging_url]
            }
        yield get_dept_list_page

        @request(retry_count=5, proxy_type=PROXY_FLLOW, binding=self.parse_RoundFlight)
        def get_dept_list_data():
            #parse_fuc = self.parse_tickets_verify if self.dept_flight_no else self.parse_tickets
            return {
                'req': {'url': self.paging_url},
                'data': {'content_type': 'json'},
                'user_handler': [self.assert_ticket, self.parse_tickets,self.parse_tickets_verify],
            }
        yield get_dept_list_data

        # if self.dept_flight_no:
        #     # @request(retry_count=3, proxy_type=PROXY_REQ)
        #     # def get_ret_list_page():
        #     #     return {
        #     #         'req': {'url': self.request_url + '#leg/' + self.dept_flight_naturalkey},
        #     #         'user_handler': [self.process_paging_url]
        #     #     }
        #     # yield get_ret_list_page

        #     # 修改 paging_url
        #     self.process_paging_url_ret()
        #     @request(retry_count=5, proxy_type=PROXY_FLLOW, binding=self.parse_RoundFlight)
        #     def get_ret_list_data():
        #         return {
        #         'req': {'url': self.paging_url},
        #         'data': {'content_type': 'json'},
        #         'user_handler': [self.assert_ticket, self.parse_tickets],
        #         }
        #     yield get_ret_list_data

        #     @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_RoundFlight)
        #     def get_verify_page():
        #         reqs = [{
        #                     'req': {'url': url},
        #                     'user_handler': [self.parse_VerifyFlight],
        #                 } for url in self.verify_urls]
        #         return reqs
        #     yield get_verify_page

    def respon_callback(self, req, resp):
        pass
    """
    修改注解：以前的时候只要给出了出发的航班号，那么结果保存的就只有验证回来的机票，
    及时得到数据也没有保存下来,现在只有发出验证请求时才返回验证的机票信息
    """
    def parse_RoundFlight(self, req, json_data):
        if 'fl0' in req['req']['url']:
            if self.dept_flight_no:
                return self.verify_tickets
        else:
            return self.tickets

    def parse_tickets(self, req, json_data):
        legs = json_data['content']['legs']
        legs_detail_dict = {}
        for leg in legs.values():
            legs_detail_dict[leg['naturalKey']] = self.parse_leg(leg)

        offers = json_data['content']['offers']
        self.get_ticket(offers, legs_detail_dict)

    def parse_tickets_verify(self, req, json_data):
        legs = json_data['content']['legs']
        for leg in legs.values():
            flight_no = '_'.join(x['carrier']['airlineCode'] + x['carrier']['flightNumber']
                                 for x in leg['timeline'] if x['segment'])
            if flight_no == self.dept_flight_no:
                self.dept_flight_naturalkey = leg['naturalKey']
                break

    def get_ticket(self, offers, legs_detail_dict):
        for offerid, offer in offers.items():
            price = offer['price']['exactPrice']
            if not price:
                continue
            flight = RoundFlight()
            leg_id_A, leg_id_B = offer['legIds']
            flight_A, flight_B = legs_detail_dict[leg_id_A], legs_detail_dict[leg_id_B]
            for k, v in flight_A.__dict__.iteritems():
                if k.startswith('_'):
                    continue
                flight.__dict__[k + '_A'] = v
            for k, v in flight_B.__dict__.iteritems():
                if k.startswith('_'):
                    continue
                flight.__dict__[k + '_B'] = v
            flight.dept_id = flight_A.dept_id
            flight.dest_id = flight_A.dest_id
            flight.dept_day = flight_A.dept_day
            flight.tax = 0
            flight.dest_day = flight_B.dept_day
            flight.price = price
            flight.currency = offer['price']['currencyCode']
            flight.source = '%s::%s' % (self.source, self.source)
            flight.return_rule = 'Free CancellationOpens within 24 hours of booking!' if offer['price']['feesMessage'][
                'isShowFreeCancellation'] else 'No Free Cancellation.'

            if flight_A.flight_no == self.dept_flight_no and flight_B.flight_no == self.ret_flight_no:
                url = self.host + '/Flight-Search-Details?c=' + self.ids + '&tripId1=%20&offerId=' + urllib.quote(
                    offerid) + '&xsellchoice=normal&isSplitTicket=false'
                self.verify_urls.append(url)
                self.verify_flights.append(flight)
            self.tickets.append(flight.to_tuple())

    def parse_leg(self, leg):
        flight = Flight()
        flight.flight_no = '_'.join(x['carrier']['airlineCode'] + x['carrier']['flightNumber']
                                    for x in leg['timeline'] if x['segment'])
        flight.airline = flight.get_airline()
        plane_nos = []
        for x in leg['timeline']:
            if x['segment']:
                plane_nos.append(x['carrier']['planeCode'] if x['carrier']['planeCode'] else 'NULL')
        flight.tax = 0
        flight.plane_no = '_'.join(plane_nos)
        flight.dept_time = pat_time.search(leg['departureTime']['isoStr']).group()
        flight.dest_time = pat_time.search(leg['arrivalTime']['isoStr']).group()
        flight.dur = get_dur(leg['duration'])
        flight.seat_type = '_'.join(cabin_dict.get(x['carrier']['cabinClass'], self.seat_type)
                                    for x in leg['timeline'] if x['segment'])
        flight.real_class = flight.seat_type
        flight.stop_id = '|'.join('%s_%s' % (x['departureAirport']['code'], x['arrivalAirport']['code'])
                                  for x in leg['timeline'] if x['segment'])
        flight.stop_time = '|'.join('%s_%s' % (pat_time.search(x['departureTime']['isoStr']).group(),
                                               pat_time.search(x['arrivalTime']['isoStr']).group())
                                    for x in leg['timeline'] if x['segment'])
        flight.daydiff = '_'.join(str(x['duration']['numOfDays']) for x in leg['timeline'] if x['segment'])
        flight.stop = leg['stops']
        flight.dept_id = flight.stop_id.split('_', 1)[0]
        flight.dest_id = flight.stop_id.rsplit('_', 1)[-1]
        flight.dept_day = pat_day.search(flight.stop_time.split('_', 1)[0]).group()
        flight.dest_day = pat_day.search(flight.stop_time.split('_')[-1]).group()
        return flight

    def process_task_info(self):
        ticket_info = self.task.ticket_info
        content = self.task.content
        self.seat_code = ticket_info.get('v_seat_type', 'E')
        self.seat_type = cabin[self.seat_code]
        self.dept_flight_no = self.task.ticket_info.get('flight_no', None)
        self.ret_flight_no = self.task.ticket_info.get('ret_flight_no', None)
        self.dept_id, self.dest_id, dept_day, return_day = str(content).split('&')
        self.dept_day = self.format_time(dept_day, '/')
        self.return_day = self.format_time(return_day, '/')
        self.num_passenger = int(ticket_info.get('v_count', '2'))
        self.ages_info = ticket_info.get('v_age', None)
        self.adults, self.child, self.child_count, self.has_infant = process_ages(int(self.num_passenger),
                                                                                  self.ages_info)
        self.get_search_url()

    def format_time(self, dept_day, c):
        y = dept_day[:4]
        m = dept_day[4:6]
        d = dept_day[-2:]
        return m + c + d + c + y

    def get_search_url(self):
        if self.adults > 6:
            raise parser_except.ParserException(12, '任务出错')
        option_passenger = process_passenger_info(self.adults, self.child, self.child_count, self.has_infant)
        self.request_url = self.request_url_template % (self.host, self.dept_id, self.dest_id, self.dept_day,
                                                        self.dest_id, self.dept_id, self.return_day,
                                                        option_passenger,self.seat_type)

    def process_paging_url(self, req, resp):
        pat = re.compile('id="originalContinuationId">(.*?)<')
        try:
            self.ids = pat.findall(resp)[0]
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "找不到ContinuationId")
        self.paging_url = self.paging_url_template % (self.host, self.ids)  # 这里要不要yield

    def process_paging_url_ret(self):
        self.paging_url = list(self.paging_url)
        self.paging_url[-1] = '1'   # ul=1
        self.paging_url[-25] = '0'  # is=0
        self.paging_url = ''.join(self.paging_url)
        self.paging_url += '&fl0=%s' % self.dept_flight_naturalkey

    def assert_ticket(self, req, resp):
        if not resp['content']['legs']:
            raise parser_except.ParserException(parser_except.EMPTY_TICKET, "获得空的json")

    def parse_VerifyFlight(self, req, resp):

        with open('content1.txt','w+') as content:
            content.write(resp)
        try:
            pat = re.compile('priceBreakDown = (.*);')
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
        except Exception as e:
            try:
                pat = re.compile('userInteraction: (.*)')
                data = pat.findall(resp)[0]
                data = json.loads(data)
                avg_adult_price = data['entity']['tripDetails']['flightOffer']['avgPriceOfAdultAndSenior']['amount']
                adult_total_price = avg_adult_price * self.adults
                adult_tmp = "%s:%s" % (passenger_type_dict['Adult'],adult_total_price)
                avg_child_price = data['entity']['tripDetails']['flightOffer']['avgPriceOfChildrenAndInfants']['amount']
                child_total_price = avg_child_price * self.child_count
                child_tmp = "%s:%s" % (passenger_type_dict['Child'],child_total_price)
                val = []
                val.extend([adult_tmp,child_tmp])
                flight = self.verify_flights.pop()
                flight.others_info = ';'.join(val)
                flight.others_info = '%s&%s' % (flight.others_info,flight.others_info)
                self.verify_tickets.append(flight.to_tuple())
            except Exception as e:
                logger.debug(current_log_tag()+'【验证机票解析错误】%s',e)
