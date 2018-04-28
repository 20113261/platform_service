#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

import datetime
import math
import re
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from mioji.common.task_info import Task
from mioji.common.class_common import RoundFlight
from mioji.common.logger import logger
from mioji.common.template.GetDayDiff import GetDaydiff
from mioji.common.template.GetAirline import GetAirline
# 关闭神烦的warning
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# from pricelineRoundFlight_util import GetAirline, GetDaydiff

seat_dict = {'ECO': '经济舱', 'BUS': '商务舱', 'FST': '头等舱', 'PEC': '超级经济舱'}
class_code_dict = {'E': 'ECO', 'B': 'BUS', 'F': 'FST', 'P': 'PEC'}


class PricelineRoundFlightSpider(Spider):
    source_type = "pricelineRoundFlight"

    targets = {
        'Flight': {'version': 'InsertRoundFlight2'}
    }
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'pricelineRoundFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        super(PricelineRoundFlightSpider, self).__init__(task)
        # 初始化任务
        self.task = task
        self.head_id = 1
        self.offset = 40
        self.end_id = self.offset

    def get_trip_detail(self, ticket_info):
        ret = {}
        airline_set = set()
        if 'flight_no' in ticket_info:
            ret['dept_flight_no'] = ticket_info['flight_no'].split('_')
            for flight_no in ret['dept_flight_no']:
                airline_set.add(flight_no[:2])
        if 'dept_time' in ticket_info and 'dest_time' in ticket_info:
            dept_time = datetime.datetime.strptime(ticket_info['dept_time'], '%Y%m%d_%H:%M')
            arr_time = datetime.datetime.strptime(ticket_info['dest_time'], '%Y%m%d_%H:%M')
            dept_time, arr_time = self.get_time_range(dept_time, arr_time)
            ret['dept_trip_time'] = {
                'dept_date': dept_time.strftime('%Y-%m-%d'),
                'dept_time': dept_time.strftime('%H:%M'),
                'arr_date': arr_time.strftime('%Y-%m-%d'),
                'arr_time': arr_time.strftime('%H:%M')
            }
        if 'ret_flight_no' in ticket_info:
            ret['ret_flight_no'] = ticket_info['ret_flight_no'].split('_')
            for flight_no in ret['ret_flight_no']:
                airline_set.add(flight_no[:2])
        if 'ret_dept_time' in ticket_info and 'ret_dest_time' in ticket_info:
            dept_time = datetime.datetime.strptime(ticket_info['ret_dept_time'], '%Y%m%d_%H:%M')
            arr_time = datetime.datetime.strptime(ticket_info['ret_dest_time'], '%Y%m%d_%H:%M')
            dept_time, arr_time = self.get_time_range(dept_time, arr_time)
            ret['ret_trip_time'] = {
                'dept_date': dept_time.strftime('%Y-%m-%d'),
                'dept_time': dept_time.strftime('%H:%M'),
                'arr_date': arr_time.strftime('%Y-%m-%d'),
                'arr_time': arr_time.strftime('%H:%M')
            }
        if airline_set:
            ret['airlines'] = airline_set
        return ret

    def targets_request(self):
        self.pare_paras()
        homeurl = 'https://www.priceline.com/'
        carurl = 'https://www.priceline.com/m/fly/search/' \
                 + self.dept_id + '-' + self.dest_id + '-' + self.dept_day + '/' + self.dest_id + '-' + self.dept_id + '-' + \
                 self.return_day + '/?cabin-class=' + self.seat + '&num-adults=' + str(self.adults)
        if self.childs:
            carurl += '&num-children=' + str(self.childs)

        header_cookie = {
            'Content-Type': 'application/json;charset=UTF-8',

            'Referer': carurl,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }
        self.user_datas['has_next'] = True

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_token():
            """
            获取token
            """
            return {
                'req': {'url': carurl, 'headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36', }},
                'data': {'content_type': 'string'},
                'user_handler': [self.get_token]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_session():
            """
                获取session_id
            """
            sess_url = 'https://www.priceline.com/m/fly/search/' + \
                       self.dept_id + '-' + self.dest_id + '-' + self.dept_day + '/' + self.dest_id + '-' + self.dept_id + '-' + \
                       self.return_day + '/'
            # +dept_id+'-'+dest_id+'-'+dept_day+'/'+dest_id+'-'+dept_id+'-'+return_day+'/'
            # print sess_url
            return {
                'req': {'url': sess_url, 'headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36', }},
                'data': {'content_type': 'string'},
            }
            # header_cookie['token-payload'] = self.user_datas['token']

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_Sec_detail_pre_url():
            """
            第一个请求，拿到search_id
            """
            url = 'https://www.priceline.com/m/fly/search/api/listings'

            # print 'xxxxxx'

            post_data = '{"airSearchReq":{"requestId":"1fa660133cbe55a89996feff494e4609","clientSessionId":"b028f20747b63a3e98eb0bfdbe458aeb","trip":{"disclosure":"DISCLOSED","slice":[{"id":1,"departDate":"' + self.dept_day1 + '","origins":{"location":"' + self.dept_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dest_id + '","type":"AIRPORT"}},{"id":2,"departDate":"' + self.return_day1 + '","origins":{"location":"' + self.dest_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dept_id + '","type":"AIRPORT"}}]},"expressDeal":{"slice":[{"id":1,"departDate":"' + self.dept_day1 + '","origins":{"location":"' + self.dept_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dest_id + '","type":"AIRPORT"}},{"id":2,"departDate":"' + self.return_day1 + '","origins":{"location":"' + self.dest_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dept_id + '","type":"AIRPORT"}}],"openJawAllowed":true,"allowedAlternates":["AIRPORT"]},"passenger":[{"type":"ADT","numOfPax":' + str(
                self.adults) + '}],"searchOptions":{"jetOnly":false,"numOfStops":7,"cabinClass":"' + self.seat + '","includeFusedItineraries":true},"liveSearchForAlternateDates":false,"liveSearchExpDealsForAlternateDates":false,"displayParameters":{"sliceRefId":[1,2],"lowerBound":' + str(
                self.head_id) + ',"upperBound":' + str(
                self.end_id) + '},"filter":{"alternates":{"excludeDates":true,"excludeAirports":true}},"sortPrefs":[{"priority":1,"type":"PRICE","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":2,"order":"ASC"}],"includeAlternateSummary":false,"includeFullTripSummary":true,"includeFilteredTripSummary":true,"includeSliceSummary":true,"advDuplicateTimesItinFilter":true,"advSameDepartureItinFilter":true,"advSimDepartSimDurationItinFilter":true,"referrals":[{"external":{"refClickId":null,"refId":"DIRECT","referralSourceId":"DT"}}]}}'
            # print post_data, 'xxxxx'
            header_cookie['token-payload'] = self.user_datas['token']
            return {
                'req': {
                    'url': url,
                    'method': "post",
                    'data': post_data,
                    'headers': header_cookie
                },
                'data': {'content_type': 'json'},
                'user_handler': [self.handle_base_search_rsp]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['Flight'])
        def get_Sec_detail():
            requests_infos = self.user_datas['requests_infos']
            # print requests_infos, '='*100
            url = 'https://www.priceline.com/m/fly/search/api/listings'
            # print '1'*10
            header_cookie['token-payload'] = self.user_datas['token']
            while self.user_datas['has_next']:
                post_data = self.make_filter_post_data(requests_infos, self.trip_detail, self.head_id, self.end_id)
                # task = Task()

                yield {
                    'req': {'url': url, 'data': post_data,
                            'headers': header_cookie,
                            'method': "post",
                            },
                    'data': {'content_type': 'json'},
                    'user_handler': [self.Sec_detail_handle],
                }
                self.head_id = self.end_id + 1
                self.end_id += self.offset
                # task.extra = {'url':url, 'post_data':post_data}
                # result = Princeline_Deep_Spider(task).crawl()[0]['PricelineRountFlight_detail']
                # result_list.extend[result]
                # if len(result) < self.offset and  self.end_id > 200:
                # break

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['Flight'])
        def get_detail():

            url = 'https://www.priceline.com/m/fly/search/api/listings'
            header_cookie['token-payload'] = self.user_datas['token']
            while self.user_datas['has_next']:
                post_data = self.get_post_data()
                # post_data = '{"airSearchReq":{"requestId":"1fa660133cbe55a89996feff494e4609","clientSessionId":"b028f20747b63a3e98eb0bfdbe458aeb","trip":{"disclosure":"DISCLOSED","slice":[{"id":1,"departDate":"2017-07-02","origins":{"location":"CKG","type":"AIRPORT"},"destinations":{"location":"HAM","type":"AIRPORT"}},{"id":2,"departDate":"2017-07-14","origins":{"location":"HAM","type":"AIRPORT"},"destinations":{"location":"CKG","type":"AIRPORT"}}]},"expressDeal":{"slice":[{"id":1,"departDate":"2017-07-02","origins":{"location":"CKG","type":"AIRPORT"},"destinations":{"location":"HAM","type":"AIRPORT"}},{"id":2,"departDate":"2017-07-14","origins":{"location":"HAM","type":"AIRPORT"},"destinations":{"location":"CKG","type":"AIRPORT"}}],"openJawAllowed":true,"allowedAlternates":["AIRPORT"]},"passenger":[{"type":"ADT","numOfPax":2}],"searchOptions":{"jetOnly":false,"numOfStops":7,"cabinClass":"ECO","includeFusedItineraries":true},"liveSearchForAlternateDates":false,"liveSearchExpDealsForAlternateDates":false,"displayParameters":{"sliceRefId":[1,2],"lowerBound":161,"upperBound":200},"filter":{"alternates":{"excludeDates":true,"excludeAirports":true}},"sortPrefs":[{"priority":1,"type":"PRICE","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":2,"order":"ASC"}],"includeAlternateSummary":false,"includeFullTripSummary":true,"includeFilteredTripSummary":true,"includeSliceSummary":true,"advDuplicateTimesItinFilter":false,"advSameDepartureItinFilter":false,"advSimDepartSimDurationItinFilter":false,"referrals":[{"external":{"refClickId":"","refId":"DIRECT","referralSourceId":"DT"}}]}}'
                # print post_data, '555555'
                yield {
                    'req': {'url': url, 'data': post_data,
                            'headers': header_cookie,
                            'method': "post"
                            },
                    'data': {'content_type': 'json'},
                    'user_handler': [self.detail_handle]
                }
                self.end_id += self.offset
                self.head_id = self.end_id - self.offset + 1
                # break

        if 'dept_trip_time' in self.trip_detail and 'ret_trip_time' in self.trip_detail:  # 有时间的，需要用时间过滤
            # print '555555'*100
            return [get_token, get_session, get_Sec_detail_pre_url, get_Sec_detail]
        else:
            # print 'hhhh'*100
            return [get_token, get_session, get_detail]

    def pare_paras(self):
        task = self.task
        content = task.content
        ticket_info = task.ticket_info
        self.seat_type = ticket_info.get('v_seat_type', 'E')
        self.count = int(ticket_info.get('v_count', '2'))
        self.age = ticket_info.get('v_age', '_'.join(['-1'] * self.count))
        self.hold_seat = ticket_info.get('v_hold_seat', '_'.join(['1'] * self.count))
        self.dept_id, self.dest_id, self.dept_day, self.return_day = task.content.split('&')

        self.dept_datetime = datetime.datetime.strptime(self.dept_day, '%Y%m%d')
        self.return_datetime = datetime.datetime.strptime(self.return_day, '%Y%m%d')
        self.dept_day1 = self.dept_datetime.strftime('%Y-%m-%d')
        self.return_day1 = self.return_datetime.strftime('%Y-%m-%d')
        age_list = [int(math.ceil(float(x))) for x in self.age.split('_')]
        self.childs = 0
        self.children = [x for x in age_list if 0 <= x < 18]
        if self.children:
            self.childs = '%d' % (len(self.children))

        self.adults = len([x for x in age_list if x >= 18 or x == -1])
        self.seat = class_code_dict[self.seat_type]

        self.trip_detail = self.get_trip_detail(task.ticket_info)

    def handle_base_search_rsp(self, req, data):
        payload = data
        ret = {'airlines': []}
        ret['searchSessionKey'] = payload['airSearchRsp']['searchSessionKey']
        # 提取 airline的数据
        for airline_info in payload['airSearchRsp']['airline']:
            if not airline_info['baggageContentAvailable']:
                continue
            ret['airlines'].append(airline_info['code'])
        self.user_datas['requests_infos'] = ret

    def get_token(self, req, data):
        """
        解析token
        """

        pat = re.compile(r'<meta name="jwt" content="(.*?)">')
        token = pat.findall(data)[0]
        # header_cookie['token-payload'] = token
        self.user_datas['token'] = token

    def get_post_data(self):
        postdata_str = '{"airSearchReq":{"requestId":"1fa660133cbe55a89996feff494e4609","clientSessionId":"b028f20747b63a3e98eb0bfdbe458aeb","trip":{"disclosure":"DISCLOSED","slice":[{"id":1,"departDate":"' + self.dept_day1 + '","origins":{"location":"' + self.dept_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dest_id + '","type":"AIRPORT"}},{"id":2,"departDate":"' + self.return_day1 + '","origins":{"location":"' + self.dest_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dept_id + '","type":"AIRPORT"}}]},"expressDeal":{"slice":[{"id":1,"departDate":"' + self.dept_day1 + '","origins":{"location":"' + self.dept_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dest_id + '","type":"AIRPORT"}},{"id":2,"departDate":"' + self.return_day1 + '","origins":{"location":"' + self.dest_id + '","type":"AIRPORT"},"destinations":{"location":"' + self.dept_id + '","type":"AIRPORT"}}],"openJawAllowed":true,"allowedAlternates":["AIRPORT"]},"passenger":[{"type":"ADT","numOfPax":' + str(
            self.adults) + '}],"searchOptions":{"jetOnly":false,"numOfStops":7,"cabinClass":"' + self.seat + '","includeFusedItineraries":true},"liveSearchForAlternateDates":false,"liveSearchExpDealsForAlternateDates":false,"displayParameters":{"sliceRefId":[1,2],"lowerBound":' + str(
            self.head_id) + ',"upperBound":' + str(
            self.end_id) + '},"filter":{"alternates":{"excludeDates":true,"excludeAirports":true}},"sortPrefs":[{"priority":1,"type":"PRICE","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":2,"order":"ASC"}],"includeAlternateSummary":false,"includeFullTripSummary":true,"includeFilteredTripSummary":true,"includeSliceSummary":true,"advDuplicateTimesItinFilter":false,"advSameDepartureItinFilter":false,"advSimDepartSimDurationItinFilter":false,"referrals":[{"external":{"refClickId":"","refId":"DIRECT","referralSourceId":"DT"}}]}}'

        return postdata_str

    def Sec_detail_handle(self, req, data):
        json_data = data
        if json_data["resultMessage"] != "Success" or "slice" not in json_data['airSearchRsp']:
            self.user_datas['has_next'] = False

        count = len(data['airSearchRsp']['pricedItinerary'])
        if count < self.offset or self.end_id + self.offset > 200:
            self.user_datas['has_next'] = False

    def detail_handle(self, req, data):
        # print data
        json_data = data
        if json_data["resultMessage"] != "Success" or "slice" not in json_data['airSearchRsp']:
            self.user_datas['has_next'] = False

        count = len(json_data['airSearchRsp']['pricedItinerary'])
        if count < self.offset or self.end_id + self.offset > 200:
            self.user_datas['has_next'] = False

    def make_filter_post_data(self, request_infos, trip_detail, head_id, end_id):

        def build_filter(obj, trip_detail, airlines=[]):
            if 'airlines' in trip_detail and airlines:
                logger.info('航空公司过滤')
                for code in airlines:
                    if code in trip_detail['airlines']:
                        airlines.remove(code)
                obj['sliceFilters'][0]['excludedCarriers'] = airlines
                obj['sliceFilters'][1]['excludedCarriers'] = airlines
            else:
                obj['sliceFilters'][0]['inclusiveDepartTimeFilterStart'] = trip_detail['dept_trip_time']['dept_time']
                obj['sliceFilters'][0]['inclusiveArriveTimeFilterEnd'] = trip_detail['dept_trip_time']['arr_time']
            return obj

        base_post_data = '{"airSearchDisplayReq":{"requestId":"b1f57619c446a216713e5545b8445bf6","clientSessionId":"8d5352109ebc346bbdf3552bb5cc5127","searchId":"1","displayParameters":{"sliceRefId":[],"lowerBound":' + str(
            head_id) + ',"upperBound":' + str(
            end_id) + ',"includeExpressDeals":true},"filter":{"sliceFilters":[{"sliceId":1,"numOfStops":7},{"sliceId":2,"numOfStops":7}],"alternates":{"excludeDates":true,"excludeAirports":true}},"itineraryType":"ROUND_TRIP","searchOptions":{"includeFusedItineraries":true},"sortPrefs":[{"priority":1,"type":"PRICE","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":1,"order":"ASC"},{"priority":1,"type":"DEPARTTIME","sliceRefId":2,"order":"ASC"}],"includeAlternateSummary":false,"includeFullTripSummary":true,"includeFilteredTripSummary":true,"includeSliceSummary":true,"advDuplicateTimesItinFilter":true,"advSameDepartureItinFilter":true,"advSimDepartSimDurationItinFilter":true,"referrals":[{"external":{"refClickId":null,"refId":"DIRECT","referralSourceId":"DT"}}]}}'
        payload = json.loads(base_post_data)
        payload['airSearchDisplayReq']['filter'] = build_filter(payload['airSearchDisplayReq']['filter'], trip_detail,
                                                                request_infos['airlines'])
        payload['airSearchDisplayReq']['searchSessionKey'] = request_infos['searchSessionKey']
        return json.dumps(payload).replace(' ', '')

    def get_time_range(self, dept_time, arr_time):
        beginning = dept_time.replace(hour=0, minute=20, second=0, microsecond=0)
        end = arr_time.replace(hour=23, minute=40, second=0, microsecond=0)
        if dept_time > beginning:
            dept_time = dept_time - datetime.timedelta(minutes=20)
        else:
            dept_time = dept_time.replace(hour=0, minute=0, second=0, microsecond=0)
        if arr_time < end:
            arr_time = arr_time + datetime.timedelta(minutes=20)
        else:
            arr_time = arr_time.replace(hour=23, minute=59, second=0, microsecond=0)
        return dept_time, arr_time

    def parse_Flight(self, req, data):
        get_airline = GetAirline()
        get_daydiff = GetDaydiff()

        tickets = []
        # print data
        json_data = data
        if json_data["resultMessage"] != "Success":
            return tickets

        dict_ow = {}
        if "slice" not in json_data['airSearchRsp']:
            return tickets
        for x in json_data['airSearchRsp']["slice"]:
            dict_ow[x["uniqueSliceId"]] = x
        dict_info = {}
        for x in json_data['airSearchRsp']['segment']:
            dict_info[x['uniqueSegId']] = x
        currency = json_data['airSearchRsp']['pointOfSale']['currency']
        for offer in json_data['airSearchRsp']['pricedItinerary']:
            flight = RoundFlight()

            flight.price = offer["pricingInfo"]["totalFare"] + offer["pricingInfo"]["fees"][0]["amount"]
            flight.rest = offer['numSeats']
            dept_oneway = dict_ow[offer['slice'][0]['uniqueSliceId']]
            dest_oneway = dict_ow[offer['slice'][1]['uniqueSliceId']]

            flight.dur_A = int(dept_oneway['duration']) * 60
            flight.dur_B = int(dest_oneway['duration']) * 60
            stop_idA, stop_idB, stop_timeA, stop_timeB, plane_noA, plane_noB, flight_noA, flight_noB, seat_typeA, seat_typeB = \
                [], [], [], [], [], [], [], [], [], []

            for dd in dept_oneway['segment']:
                ddinfo = dict_info[dd['uniqueSegId']]
                stop_timeA.append(ddinfo['departDateTime'] + '_' + ddinfo['arrivalDateTime'])
                stop_idA.append(ddinfo['origAirport'] + '_' + ddinfo['destAirport'])
                plane_noA.append(ddinfo['equipmentCode'])
                flight_noA.append(ddinfo['marketingAirline'] + ddinfo['flightNumber'])
                seat_typeA.append(seat_dict[dd['cabinClass']])

            for dd in dest_oneway['segment']:
                ddinfo = dict_info[dd['uniqueSegId']]
                stop_timeB.append(ddinfo['departDateTime'] + '_' + ddinfo['arrivalDateTime'])
                stop_idB.append(ddinfo['origAirport'] + '_' + ddinfo['destAirport'])
                plane_noB.append(ddinfo['equipmentCode'])
                flight_noB.append(ddinfo['marketingAirline'] + ddinfo['flightNumber'])
                seat_typeB.append(seat_dict[dd['cabinClass']])
            flight.dept_id = stop_idA[0].split('_')[0]
            flight.dest_id = stop_idA[-1].split('_')[-1]
            flight.dept_day = self.dept_day1
            flight.dest_day = self.return_day1
            flight.tax = 0
            flight.currency = currency
            flight.source = 'priceline::priceline'
            flight.stop_A = len(stop_idA) - 1
            flight.stop_B = len(stop_idB) - 1

            flight.flight_no_A = '_'.join(flight_noA)
            flight.flight_no_B = '_'.join(flight_noB)
            flight.plane_no_A = '_'.join(plane_noA)
            flight.plane_no_B = '_'.join(plane_noB)
            flight.dept_time_A = stop_timeA[0].split('_')[0]
            flight.dest_time_A = stop_timeA[-1].split('_')[-1]
            flight.dest_time_B = stop_timeB[-1].split('_')[-1]
            flight.dept_time_B = stop_timeB[0].split('_')[0]
            flight.real_class_A = flight.seat_type_A = '_'.join(seat_typeA)
            flight.real_class_B = flight.seat_type_B = '_'.join(seat_typeB)
            flight.stop_id_A = '|'.join(stop_idA)
            flight.stop_id_B = '|'.join(stop_idB)
            flight.stop_time_A = '|'.join(stop_timeA)
            flight.stop_time_B = '|'.join(stop_timeB)

            flight.daydiff_A = get_daydiff.GetDaydiff(flight.stop_time_A)
            flight.daydiff_B = get_daydiff.GetDaydiff(flight.stop_time_B)
            flight.airline_A = get_airline.GetAirline(flight.flight_no_A)
            flight.airline_B = get_airline.GetAirline(flight.flight_no_B)

            result = (flight.dept_id, flight.dest_id, flight.dept_day, flight.dest_day, flight.price, flight.tax,
                      flight.surcharge, flight.promotion, flight.currency, flight.source, flight.return_rule,
                      flight.flight_no_A, flight.airline_A, flight.plane_no_A, flight.dept_time_A, flight.dest_time_A,
                      flight.dur_A, flight.seat_type_A, flight.real_class_A, flight.stop_id_A, flight.stop_time_A,
                      flight.daydiff_A, flight.stop_A, flight.flight_no_B, flight.airline_B, flight.plane_no_B,
                      flight.dept_time_B, flight.dest_time_B, flight.dur_B, flight.seat_type_B, flight.real_class_B,
                      flight.stop_id_B, flight.stop_time_B, flight.daydiff_B, flight.stop_B, flight.change_rule,
                      flight.share_flight_A, flight.share_flight_B, flight.stopby_A, flight.stopby_B, flight.baggage,
                      flight.transit_visa, flight.reimbursement, flight.flight_meals, flight.ticket_type,
                      flight.others_info, flight.rest)
            tickets.append(result)
        return tickets


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, httpset_debug

    mioji.common.spider.get_proxy = simple_get_http_proxy
    httpset_debug()
    task = Task()
    # task.content = 'CKG&HAM&20170702&20170714'

    task.content = 'CAN&TXL&20170702&20170714'
    task.source = 'pricelineround'
    # task.ticket_info = {
    #     "ret_flight_no": "TK1724_TK72",
    #     "ret_dept_time": "20170325_19:00",
    #     "env_name": "offline",
    #     "ret_seat_type": "经济舱|经济舱",
    #     "scene": "pay",
    #     "v_count": 1,
    #     "qid": "1484278907171",
    #     "dest_time": "20170317_13:40",
    #     "v_seat_type": "E",
    #     "seat_type": "经济舱|经济舱",
    #     "flight_no": "TK73_TK1725",
    #     "dept_time": "20170316_23:10",
    #     "pay_method": "mioji",
    #     "ret_dest_time": "20170326_16:55",
    #     "md5": "6bacb08e725ddd248c681aa2e047f1fd"
    # }

    task.source = "pricelineround"
    s = PricelineRoundFlightSpider()
    s.task = task
    s.crawl()
    print s.crawl()
    print s.result
