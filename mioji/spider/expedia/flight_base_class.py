#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
import unicodedata

setdefaultencoding_utf8()
import re
import json
import urllib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from flight_lib import process_ages, process_passenger_info

cabin = {'E': 'economy', 'P': 'premium', 'F': 'first', 'B': 'business'}
cabin_e2c = {'E': '经济舱', 'B': '商务舱', 'F': '头等舱', 'P': '超级经济舱'}
cabin_ex = {'1': 'First Class', '2': 'Business', '3': 'Economy / Coach', '5': 'Premium Economy'}
passenger_type_dict = {  # 详情票类型的字典
    "Senior": "老年人",
    "Adult": "成年人",
    "Child": "儿童",
    "Infant in seat": "婴儿(占位)",
    "Infant in lap": "婴儿(不占位)"
}
url_template = '%s/Flights-Search?trip=oneway&leg1=from:%s,to:%s,departure:%sTANYT&%s&options=cabinclass:%s&mode=search'


# self.host, self.dept_id, self.dest_id,self.date_formatted, option_passenger, self.seat_type


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


class BaseFlightSpider(Spider):
    def __init__(self, task=None):
        Spider.__init__(self)
        # 任务信息
        self.num_passenger = 1
        self.dept_id = None
        self.dest_id = None
        self.date_formatted = None
        self.seat_type = None
        self.flight_no = None
        # 验证时的信息
        self.ages_info = None
        self.adults = None
        self.child = []
        self.child_count = None
        self.has_infant = False
        # 链接
        self.host = ''
        self.source = ''
        self.request_url_template = url_template
        self.request_url = None
        self.paging_url_template = '%s/Flight-Search-Paging?c=%s&is=1&sp=asc&cz=200&cn=0'
        self.paging_url = None
        self.verify_urls = []
        # 处理这些信息
        if task:
            self.task = task

        # 爬取的某些参数
        self.ids = None
        self.verify_flights = []  # 这个是验证时保存的flight

        self.tickets = []
        self.verify_tickets = []  # 这个是验证结果出来保存的票

    def targets_request(self):
        if self.date_formatted is None:
            self.process_task_info()

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Flight, new_session=True)
        def first_page():
            return {
                'req': {'url': self.request_url, 'headers': {"Connection": "close"}},
                'data': {'content_type': self.parse_feng}
                # 'user_handler': [self.process_paging_url]
            }

        @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_Flight)
        def get_tickets_page():
            return {
                'req': {'url': self.paging_url},
                'data': {'content_type': self.parse_ticket},
                # 'user_handler': [self.assert_ticket],
            }

        # @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_Flight)
        # def get_verify_page():
        #     reqs = [{
        #         'req': {'url': url},
        #         'user_handler': [self.parse_VerifyFlight],
        #     } for url in self.verify_urls]
        #     return reqs
        yield first_page
        if self.paging_url is not None:
            yield get_tickets_page
        # if self.flight_no:
        #     yield get_verify_page

    def parse_ticket(self, req, data):
        try:
            return json.loads(data)
        except Exception:
            raise parser_except.ParserException(22, "retry !!!")

    def respon_callback(self, req, resp):
        pass

    def parse_Flight(self, req, json_data):
        if not json_data:
            return []
        url = req['req']['url']
        url_regex = 'Flight-Search-Details'
        if url_regex in url:
            return self.verify_tickets

        legs = json_data['content']['legs']
        if legs == 'null':
            return []
        offers = json_data['content']['offers']
        if offers is None:
            return []
        for offer_id, offer_value in offers.items():
            leg_id = offer_value['legIds'][0]
            info = legs[leg_id]
            ticket = self.get_ticket(info, offer_id)
            if ticket != -1:
                self.tickets.append(ticket)
        return self.tickets

    def get_ticket(self, info, offer_id):
        flight = Flight()
        segs = info['timeline']

        flight_no = []
        plane_type = []
        stopid = []
        stoptime = []
        duration = info['duration']
        dur = get_dur(duration)
        seat = []
        for seg in segs:
            if not seg['segment']:
                continue
            seat_type_number = str(seg['carrier']['cabinClass'])  # 此处使用从Expedia找到的舱位对应dict值
            if seat_type_number in cabin_ex.keys():  # 预留错误捕捉
                seat.append(cabin_ex[seat_type_number])
            else:
                seat.append(self.seat_type.title())
            carrier = seg['carrier']
            no = carrier['airlineCode'] + carrier['flightNumber']
            flight_no.append(no)
            if seg['carrier']['plane'].encode('utf8') == '':
                plane_tmp = 'NULL'
            else:
                plane_tmp = seg['carrier']['plane']
            plane_type.append(plane_tmp)

            dep = seg['departureAirport']
            dest = seg['arrivalAirport']
            stopid.append(dep['code'] + '_' + dest['code'])
            dept_time = seg['departureTime']['isoStr'].split('.')[0]
            dest_time = seg['arrivalTime']['isoStr'].split('.')[0]
            stoptime.append(dept_time + '_' + dest_time)

        flight.source = '%s::%s' % (self.source, self.source)
        flight.flight_no = '_'.join(flight_no)
        flight.plane_type = '_'.join(plane_type)
        flight.stop_id = '|'.join(stopid)
        flight.dept_id = stopid[0].split('_')[0]
        flight.dest_id = stopid[-1].split('_')[-1]

        flight.seat_type = '_'.join(seat)
        flight.real_class = flight.seat_type
        flight.stop_time = '|'.join(stoptime)
        flight.dept_time = stoptime[0].split('_')[0]
        flight.dest_time = stoptime[-1].split('_')[-1]
        flight.dur = dur
        try:
            pricestr = info['price']['formattedRoundedPrice'].replace(',', '')
        except Exception:
            return -1
        pat = re.compile(r'\d+')
        flight.price = str(pat.findall(pricestr)[0])
        if not flight.price:
            return -1

        flight.currency = info['price']['currencyCode']
        flight.stop = info['stops']
        flight.tax = 0
        flight.dept_day = flight.dept_time.split('T')[0]

        flight.daydiff = flight.get_day_diff()
        flight.airline = flight.get_airline()

        # 实时验证再做次请求去找价格
        if flight.flight_no == self.flight_no:
            flight.offer_ids = offer_id
            url = self.host + '/Flight-Search-Details?c=' + self.ids + '&tripId1=%20&offerId=' + urllib.quote(
                flight.offer_ids) + '&xsellchoice=normal&isSplitTicket=false'
            self.verify_urls.append(url)
            self.verify_flights.append(flight)
        result = flight.to_tuple()
        return result

    def process_task_info(self):
        ticket_info = self.task.ticket_info
        content = self.task.content
        seat_type = ticket_info.get('v_seat_type', 'E')
        self.seat_type = cabin[seat_type]
        self.num_passenger = int(ticket_info.get('v_count', '2'))
        self.flight_no = self.task.ticket_info.get('flight_no', None)
        self.dept_id, self.dest_id, dept_day = content.split('&')
        self.date_formatted = self.format_time(dept_day, '/')
        self.ages_info = ticket_info.get('v_age', None)
        self.adults, self.child, self.child_count, self.has_infant = process_ages(int(self.num_passenger),
                                                                                  self.ages_info)
        self.get_search_url()

    def get_search_url(self):
        if self.adults > 6:
            raise parser_except.ParserException(12, '任务出错')
        option_passenger = process_passenger_info(self.adults, self.child, self.child_count, self.has_infant)
        self.request_url = self.request_url_template % (self.host, self.dept_id, self.dest_id,
                                                        self.date_formatted, option_passenger, self.seat_type)

    def parse_VerifyFlight(self, req, resp):
        if self.source_type == "travelocityFlight":
            flight = self.verify_flights.pop()
        else:
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

    def process_paging_url(self, req, resp):
        pat = re.compile('id="originalContinuationId">(.*?)<')
        try:
            self.ids = pat.findall(resp)[0]
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "找不到ContinuationId")

        self.paging_url = self.paging_url_template % (self.host, self.ids)  # 这里要不要yield

    def assert_ticket(self, req, resp):
        if not resp['content']['legs']:
            raise parser_except.ParserException(parser_except.EMPTY_TICKET, "获得空的json内容")

    def format_time(self, dept_day, c):
        y = dept_day[:4]
        m = dept_day[4:6]
        d = dept_day[-2:]
        return m + c + d + c + y

    def parse_feng(self, req, resp):

        try:
            patt = re.compile('id="cachedResultsJson" type="application/json">(.*?)</script>')
            html_data = str(patt.findall(resp))[3:-2]
            html_data = html_data.replace('{"content":"{', '{"content":{')
            html_data = html_data.replace('","metaData":', ',"metaData":')
            html_data = html_data.replace(r'json\\":\\"{', 'json":{')
            html_data = html_data.replace(r'}}\\"},\\"resultToken', '}}},"resultToken')
            html_data = html_data.replace('\\', '')
            html_data = json.loads(html_data)
        except:
            html_data = {}

        try:
            self.ids = re.findall('id="originalContinuationId">(.*?)<', resp)[0]
            print self.ids
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "找不到ContinuationId")
        self.paging_url = self.paging_url_template % (self.host, self.ids)  # 这里要不要yield

        return html_data