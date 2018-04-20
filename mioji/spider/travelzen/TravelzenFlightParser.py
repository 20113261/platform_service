# coding: utf8

import datetime
import hashlib
import json
import re
import time
import copy

import requests

from mioji.common.class_common import Flight
from mioji.common.class_common import MultiFlight
from mioji.common.class_common import RoundFlight
# from class_common import Flight
# from class_common import MultiFlight
# from class_common import RoundFlight

############配置项##################
test_api = 'http://api.test.travelzen.com/tops-openapi-for-customers/service/flight/international'
online_api = 'http://apis.travelzen.com/service/flight/international'
# g_account = '5941e779f47ba45ac43f84a2'
# g_pwd = 'g0e9ax1h'
# g_ret_type = 'JSON'
####################################


class Handler:
    # m_api = g_api
    # m_account = g_account
    # m_pwd = g_pwdå
    # m_ret_type = g_ret_type

    def __init__(self, task=None, api=test_api, account='5941e779f47ba45ac43f84a2', passwd='g0e9ax1h', *args, **kwargs):
        self.m_api = api
        self.m_account = account
        self.m_pwd = passwd
        self.m_ret_type = 'JSON'

        self._itinerary_count = 0
        self.task = task


    def getSignCode(self, timeStamp):
        m = hashlib.md5()
        rule_str = "tzOpenapi" + "signCode" + self.m_pwd + "timeStamp" + timeStamp + "userName" + self.m_account + "tzOpenapi"
        m.update(rule_str)
        return m.hexdigest()

    def makeRequestInternational(self, mode, section, ticket_info):
        req_param = {}
        # requestMetaInfo
        requestMetaInfo = {}
        requestMetaInfo['userName'] = self.m_account
        timestamp = str(int(time.time()))
        requestMetaInfo['timeStamp'] = timestamp
        requestMetaInfo['signCode'] = self.getSignCode(timestamp)
        requestMetaInfo['responseDataType'] = self.m_ret_type
        req_param['requestMetaInfo'] = requestMetaInfo

        # FlightSearchRequest
        flightSearchRequest = {}
        flightSearchRequest['flightRangeType'] = mode
        flightRangeAry = []
        for sec in section:
            flightRange = {}
            flightRange['fromCity'] = sec[0]
            flightRange['toCity'] = sec[2]
            flightRange['fromDate'] = sec[1]  # yyyy-MM-dd
            flightRangeAry.append(flightRange)
        flightSearchRequest['flightRange'] = flightRangeAry
        if isinstance(ticket_info['v_seat_type'], unicode) or isinstance(ticket_info['v_seat_type'], str):
            flightSearchRequest['cabinRank'] = self.get3rdCabin(ticket_info['v_seat_type'])
        # flightSearchRequest['checkDirect'] = "true"
        # flightSearchRequest['adtCounts'] = "5"
        # flightSearchRequest['chdCounts'] = "0"
        # flightSearchRequest['openingTime'] = "true"
        # flightSearchRequest['changePNR'] = "true"
        # flightSearchRequest['passengerNature'] = "UNLIMITED"

        req_param['FlightSearchRequest'] = flightSearchRequest
        return req_param

    def fetchDateTime(self, ori_date):
        pos = ori_date.find(' ')
        return (ori_date[0:pos], ori_date[pos + 1:])

    def getSecondFromHHMM(self, ori_time):
        pos = -1
        if isinstance(ori_time, unicode) or isinstance(ori_time, str):
            pos = ori_time.find(":")
            if pos != -1:
                h = int(ori_time[0:pos])
                m = int(ori_time[pos + 1:])
                return 3600 * h + m * 60
        return 0

    def getMiojiCabin(self, ori_cabin):
        if ori_cabin == 'Y':
            return 'E'
        elif ori_cabin == 'C':
            return 'B'
        elif ori_cabin == 'F':
            return 'F'
        else:
            return 'NULL'

    def get3rdCabin(self, ori_cabin):
        if ori_cabin == 'B':
            return 'C'
        elif ori_cabin == 'F':
            return 'F'
        else:
            return 'Y'

    def daysBetweenDate(self, from_date, to_date, fmt):
        d1 = datetime.datetime.strptime(from_date, fmt)
        d2 = datetime.datetime.strptime(to_date, fmt)
        return (d2 - d1).days

    def createFlight(self):
        ret = Flight()
        ret.flight_no = ''
        ret.plane_type = ''
        ret.flight_corp = ''
        ret.dept_id = ''
        ret.dest_id = ''
        ret.dept_day = ''
        ret.dept_time = ''
        ret.dest_time = ''
        ret.dur = -1
        ret.rest = -1
        ret.price = 99999999
        ret.tax = 99999999
        ret.surcharge = -1
        ret.promotion = 'NULL'
        ret.currency = 'CNY'
        ret.seat_type = ''
        ret.real_class = ''
        ret.package = 'NULL'
        ret.stop_id = ''
        ret.stop_time = ''
        ret.daydiff = ''
        ret.source = 'travelzen::travelzen'
        ret.return_rule = '退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。'
        ret.stop = 0
        ret.share_flight = 'NULL'
        ret.stopby = 'NULL'
        ret.baggage = 'NULL'
        ret.transit_visa = 'NULL'
        ret.reimbursement = 'NULL'
        ret.flight_meals = 'NULL'
        ret.ticket_type = 'NULL'
        ret.others_info = 'NULL'
        return ret

    def createRoundFlight(self):
        ret = RoundFlight()
        ret.flight_no_A = ''
        ret.flight_no_B = ''
        ret.airline_A = ''
        ret.airline_B = ''
        ret.plane_no_A = ''
        ret.plane_no_B = ''
        ret.dept_id = ''
        ret.dest_id = ''
        ret.dept_day = ''
        ret.dest_day = ''
        ret.dept_time_A = ''
        ret.dest_time_A = ''
        ret.dept_time_B = ''
        ret.dest_time_B = ''
        ret.dur_A = -1
        ret.dur_B = -1
        ret.price = 99999999
        ret.tax = 99999999
        ret.rest = -1
        ret.surcharge = -1
        ret.promotion = 'NULL'
        ret.currency = 'CNY'
        ret.seat_type_A = ''
        ret.seat_type_B = ''
        ret.real_class_A = ''
        ret.real_class_B = ''
        ret.package = 'NULL'
        ret.stop_id_A = ''
        ret.stop_id_B = ''
        ret.stop_time_A = ''
        ret.stop_time_B = ''
        ret.daydiff_A = ''
        ret.daydiff_B = ''
        ret.source = 'travelzen::travelzen'
        ret.return_rule = '退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。'
        ret.stop_A = 0
        ret.stop_B = 0
        ret.share_flight_A = 'NULL'
        ret.share_flight_B = 'NULL'
        ret.stopby_A = 'NULL'
        ret.stopby_B = 'NULL'
        ret.baggage = 'NULL'
        ret.transit_visa = 'NULL'
        ret.reimbursement = 'NULL'
        ret.flight_meals = 'NULL'
        ret.ticket_type = 'NULL'
        ret.others_info = 'NULL'
        return ret

    def createMultiFlight(self):
        ret = MultiFlight()
        ret.flight_no = ''
        ret.plane_type = ''
        ret.flight_corp = ''
        ret.dept_id = ''
        ret.dest_id = ''
        ret.dept_day = ''
        ret.dept_time = ''
        ret.dest_time = ''
        ret.dur = ''
        ret.rest = -1
        ret.price = 99999999
        ret.tax = 99999999
        ret.surcharge = -1
        ret.promotion = 'NULL'
        ret.currency = 'CNY'
        ret.seat_type = ''
        ret.real_class = ''
        ret.package = 'NULL'
        ret.stop_id = ''
        ret.stop_time = ''
        ret.daydiff = ''
        ret.source = 'travelzen::travelzen'
        ret.return_rule = '退改政策以最终线下沟通结果为准。&退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。&退改政策以最终线下沟通结果为准。'
        ret.stop = ''
        ret.share_flight = 'NULL'
        ret.stopby = 'NULL'
        ret.baggage = 'NULL'
        ret.transit_visa = 'NULL'
        ret.reimbursement = 'NULL'
        ret.flight_meals = 'NULL'
        ret.ticket_type = 'NULL'
        ret.others_info = 'NULL'
        return ret

    def afterProcess(self, flight):
        if isinstance(flight, Flight):
            flight.seat_type = flight.seat_type.rstrip('_')
            flight.real_class = flight.real_class.rstrip('_')
            flight.flight_no = flight.flight_no.rstrip('_')
            flight.plane_type = flight.plane_type.rstrip('_')
            flight.flight_corp = flight.flight_corp.rstrip('_')
            flight.stop_id = flight.stop_id.rstrip('|')
            flight.stop_time = flight.stop_time.rstrip('|')
            flight.daydiff = flight.daydiff.rstrip('_')
        elif isinstance(flight, RoundFlight):
            flight.seat_type_A = flight.seat_type_A.rstrip('_')
            flight.seat_type_B = flight.seat_type_B.rstrip('_')
            flight.real_class_A = flight.real_class_A.rstrip('_')
            flight.real_class_B = flight.real_class_B.rstrip('_')
            flight.flight_no_A = flight.flight_no_A.rstrip('_')
            flight.flight_no_B = flight.flight_no_B.rstrip('_')
            flight.plane_no_A = flight.plane_no_A.rstrip('_')
            flight.plane_no_B = flight.plane_no_B.rstrip('_')
            flight.airline_A = flight.airline_A.rstrip('_')
            flight.airline_B = flight.airline_B.rstrip('_')
            flight.stop_id_A = flight.stop_id_A.rstrip('|')
            flight.stop_id_B = flight.stop_id_B.rstrip('|')
            flight.stop_time_A = flight.stop_time_A.rstrip('|')
            flight.stop_time_B = flight.stop_time_B.rstrip('|')
            flight.daydiff_A = flight.daydiff_A.rstrip('_')
            flight.daydiff_B = flight.daydiff_B.rstrip('_')
        elif isinstance(flight, MultiFlight):
            flight.seat_type = flight.seat_type.rstrip('_')
            flight.real_class = flight.real_class.rstrip('_')
            flight.flight_no = flight.flight_no.rstrip('_')
            flight.plane_type = flight.plane_type.rstrip('_')
            flight.flight_corp = flight.flight_corp.rstrip('_')
            flight.stop_id = flight.stop_id.rstrip('|')
            flight.stop_time = flight.stop_time.rstrip('|')
            flight.daydiff = flight.daydiff.rstrip('_')
        if flight.price == 99999999:
            flight.price = -1
        if flight.tax == 99999999:
            flight.tax = -1
        return

    def parseRangeSegmentCount(self, cnt):
        return re.split('-|,', cnt)

    def getPayKey(self, ticket_info):
        redis_key = self.task.redis_key
        id = self._itinerary_count
        self._itinerary_count += 1
        return {'redis_key': redis_key, 'id': id}

    def getPayInfo(self, dept_city_list, arr_city_list, policy_id, limit_query_id, is_special_price,
                   is_taken_seat, child_face_price, airline_company, is_share_flight):
        pay_info = {
            'dept_city': dept_city_list,
            'dest_city': arr_city_list,
            'policyID': policy_id,
            'LimitQueryID': limit_query_id,
            'is_special_price': is_special_price,
            'is_taken_seat': is_taken_seat,
            'child_face_price': child_face_price,
            'airline_company': airline_company,
            'is_share_flight': is_share_flight
        }
        return pay_info

    def parseOW(self, ret_dict, ticket_info):
        ret_list = []
        len_flightSegmentResult = len(ret_dict['FlightSearchResponse']['flightSegmentResult'])
        for i in range(0, len_flightSegmentResult):
            # print '结果' + str(i)
            ret = self.createFlight()
            result = ret_dict['FlightSearchResponse']['flightSegmentResult'][i]
            len_segmentList = len(result['segmentList'])
            ret.stop = len_segmentList - 1
            airline_corp = result['airlineCompany']
            freight_rule_query_id = result['freightRuleQueryID']
            from_city = result['segmentList'][0]['fromCity']
            to_city = result['segmentList'][0]['toCity']
            is_share_flight = result.get('shareFlightNo', False)
            # segmentList 机票行程
            for j in range(0, len_segmentList):
                seg = result['segmentList'][j]
                cabin = 'NULL'
                cabin_real = 'NULL'
                if seg['cabinRank'] is not None:
                    cabin = seg['cabinRank']
                if seg['cabinCode'] is not None:
                    cabin_real = seg['cabinCode']
                len_flightScheduled = len(seg['flightScheduled'])
                for k in range(0, len_flightScheduled):
                    schedule = seg['flightScheduled'][k]
                    ret.flight_no += schedule['flightNo'] + '_'
                    ret.plane_type += schedule['planeModel'] + '_'
                    ret.flight_corp += airline_corp + '_'
                    ret.seat_type += cabin + '_'
                    ret.real_class += cabin_real + '_'
                    ret.rest = schedule['remainSeatCount']
                    ret.stop_id += schedule['fromAirport'] + '_' + schedule['toAirport'] + '|'
                    from_date = self.fetchDateTime(schedule['fromDate'])
                    to_date = self.fetchDateTime(schedule['toDate'])
                    ret.stop_time += from_date[0] + 'T' + from_date[1] + ':00_' + to_date[0] + 'T' + to_date[1] + ':00|'
                    ret.daydiff += str(self.daysBetweenDate(from_date[0], to_date[0], '%Y-%m-%d')) + '_'
                    if j == 0 and k == 0:
                        ret.dept_id = schedule['fromAirport']
                        ret.dept_day = from_date[0]
                        ret.dept_time = from_date[0] + 'T' + from_date[1] + ':00'
                    if j == len_segmentList - 1 and k == len_flightScheduled - 1:
                        ret.dest_id = schedule['toAirport']
                        ret.dest_time = to_date[0] + 'T' + to_date[1] + ':00'
            # policyReturnPoint 机票价格政策
            len_policyReturnPoint = len(result['policyReturnPoint'])
            for m in range(0, len_policyReturnPoint):
                policy = result['policyReturnPoint'][m]
                if policy['passengerType'] == 'ADU':
                    ret_cpy = copy.copy(ret)
                    ret_cpy.price = policy['facePrice']
                    ret_cpy.tax = policy['tax']
                    policy_id = policy['policyId']
                    is_special_price = result.get('specialPrice', False)
                    is_taken_seat = result.get('takenSeat', False)
                    child_face_price = result.get('childFacePrice', 0)
                    ret_cpy.others_info = json.dumps({
                        'paykey': self.getPayKey(ticket_info),
                        'payInfo': self.getPayInfo([from_city], [to_city], policy_id, freight_rule_query_id,
                                                     is_special_price, is_taken_seat, child_face_price, airline_corp,
                                                   [is_share_flight]),
                        'type': 'flight_one_way'
                    })
                    # 后处理
                    self.afterProcess(ret_cpy)
                    ret_list.append(ret_cpy)
        return ret_list

    def parseRT(self, ret_dict, ticket_info):
        """往返"""
        ret_list = []
        len_flightSegmentResult = len(ret_dict['FlightSearchResponse']['flightSegmentResult'])
        for i in range(0, len_flightSegmentResult):
            # print '结果' + str(i)
            ret = self.createRoundFlight()
            result = ret_dict['FlightSearchResponse']['flightSegmentResult'][i]
            rs_list = self.parseRangeSegmentCount(result['rangeSegmentCount'])
            if len(rs_list) < 4:
                print('rangeSegmentCount不合法')
                continue
            len_segmentList = len(result['segmentList'])
            ret.stop_A = int(rs_list[1]) - 1
            ret.stop_B = int(rs_list[3]) - 1
            airline_corp = result['airlineCompany']
            freight_rule_query_id = result['freightRuleQueryID']
            from_city = []
            to_city = []
            is_share_flight = []
            # segmentList 机票行程
            return_rule_list = []
            for j in range(0, len_segmentList):
                seg = result['segmentList'][j]
                correspondRange = seg['correspondRange']
                correspondSegment = seg['correspondSegment']
                cabin = 'NULL'
                cabin_real = 'NULL'
                if seg['cabinRank'] is not None:
                    cabin = seg['cabinRank']
                if seg['cabinCode'] is not None:
                    cabin_real = seg['cabinCode']
                len_flightScheduled = len(seg['flightScheduled'])
                is_share_flight.append(result.get('shareFlightNo', False))
                for k in range(0, len_flightScheduled):
                    schedule = seg['flightScheduled'][k]
                    from_date = self.fetchDateTime(schedule['fromDate'])
                    to_date = self.fetchDateTime(schedule['toDate'])
                    if correspondRange == 1:
                        ret.flight_no_A += schedule['flightNo'] + '_'
                        ret.airline_A += airline_corp + '_'
                        ret.plane_no_A += schedule['planeModel'] + '_'
                        if correspondSegment == 1 and k == 0:
                            ret.dept_id = schedule['fromAirport']
                            from_city.append(seg['fromCity'])
                            from_city.append(seg['toCity'])
                            ret.dept_day = from_date[0]
                            ret.dept_time_A = from_date[0] + 'T' + from_date[1] + ':00'
                        if correspondSegment == int(rs_list[1]) and k == len_flightScheduled - 1:
                            ret.dest_id = schedule['toAirport']
                            to_city.append(seg['toCity'])
                            to_city.append(seg['fromCity'])
                            ret.dest_time_A = to_date[0] + 'T' + to_date[1] + ':00'
                        ret.seat_type_A += cabin + '_'
                        ret.real_class_A += cabin_real + '_'
                        ret.stop_id_A += schedule['fromAirport'] + '_' + schedule['toAirport'] + '|'
                        ret.stop_time_A += from_date[0] + 'T' + from_date[1] + ':00_' + to_date[0] + 'T' + to_date[
                            1] + ':00|'
                        ret.daydiff_A += str(self.daysBetweenDate(from_date[0], to_date[0], '%Y-%m-%d')) + '_'
                    elif correspondRange == 2:
                        ret.flight_no_B += schedule['flightNo'] + '_'
                        ret.airline_B += airline_corp + '_'
                        ret.plane_no_B += schedule['planeModel'] + '_'
                        if correspondSegment == 1 and k == 0:
                            ret.dest_day = from_date[0]
                            ret.dept_time_B = from_date[0] + 'T' + from_date[1] + ':00'
                        if correspondSegment == int(rs_list[3]) and k == len_flightScheduled - 1:
                            ret.dest_time_B = to_date[0] + 'T' + to_date[1] + ':00'
                        ret.seat_type_B += cabin + '_'
                        ret.real_class_B += cabin_real + '_'
                        ret.stop_id_B += schedule['fromAirport'] + '_' + schedule['toAirport'] + '|'
                        ret.stop_time_B += from_date[0] + 'T' + from_date[1] + ':00_' + to_date[0] + 'T' + to_date[
                            1] + ':00|'
                        ret.daydiff_B += str(self.daysBetweenDate(from_date[0], to_date[0], '%Y-%m-%d')) + '_'
                        # ret.rest = schedule['remainSeatCount']
            # policyReturnPoint 机票价格政策
            len_policyReturnPoint = len(result['policyReturnPoint'])
            for m in range(0, len_policyReturnPoint):
                policy = result['policyReturnPoint'][m]
                if policy['passengerType'] == 'ADU':
                    ret_cpy = copy.copy(ret)
                    ret_cpy.price = policy['facePrice']
                    ret_cpy.return_rule = "退改政策以最终线下沟通结果为准。"
                    ret_cpy.change_rule = "退改政策以最终线下沟通结果为准。"
                    ret_cpy.tax = policy['tax']
                    policy_id = policy['policyId']
                    is_special_price = result.get('specialPrice', False)
                    is_taken_seat = result.get('takenSeat', False)
                    child_face_price = result.get('childFacePrice', 0)
                    ret_cpy.others_info = json.dumps({
                        'paykey': self.getPayKey(ticket_info),
                        'payInfo': self.getPayInfo(from_city, to_city, policy_id, freight_rule_query_id,
                                                     is_special_price, is_taken_seat, child_face_price, airline_corp,
                                                   is_share_flight),
                        'type': 'flight_return'
                    })

                    # 后处理
                    self.afterProcess(ret_cpy)
                    ret_list.append(ret_cpy)
        return ret_list

    def parseOJ(self, ret_dict, section, ticket_info):
        ret_list = []
        len_section = len(section)
        len_flightSegmentResult = len(ret_dict['FlightSearchResponse']['flightSegmentResult'])
        for i in range(0, len_flightSegmentResult):
            # print '结果' + str(i)
            ret = self.createMultiFlight()
            result = ret_dict['FlightSearchResponse']['flightSegmentResult'][i]
            rs_list = self.parseRangeSegmentCount(result['rangeSegmentCount'])
            if len(rs_list) < 2 * len_section:
                print('rangeSegmentCount不合法')
                continue
            len_segmentList = len(result['segmentList'])
            airline_corp = result['airlineCompany']
            freight_rule_query_id = result['freightRuleQueryID']
            from_city = []
            to_city = []
            is_share_flight = []
            last_range = 1
            default_null_list = ['NULL']
              # 就是到最后把没赋值的那些东西赋值上NULL&NULL之类的东西
            # segmentList 机票行程
            for j in range(0, len_segmentList):
                seg = result['segmentList'][j]
                correspondRange = seg['correspondRange']
                correspondSegment = seg['correspondSegment']
                cabin = 'NULL'
                cabin_real = 'NULL'
                is_share_flight.append(result.get('shareFlightNo', False))
                if seg['cabinRank'] is not None:
                    cabin = seg['cabinRank']
                if seg['cabinCode'] is not None:
                    cabin_real = seg['cabinCode']
                len_flightScheduled = len(seg['flightScheduled'])

                for k in range(0, len_flightScheduled):
                    schedule = seg['flightScheduled'][k]
                    from_date = self.fetchDateTime(schedule['fromDate'])
                    to_date = self.fetchDateTime(schedule['toDate'])
                    if correspondRange != last_range:
                        last_range = correspondRange
                        ret.flight_no = ret.flight_no.rstrip('_') + '&'
                        ret.plane_type = ret.plane_type.rstrip('_') + '&'
                        ret.flight_corp = ret.flight_corp.rstrip('_') + '&'
                        ret.seat_type = ret.seat_type.rstrip('_') + '&'
                        ret.real_class = ret.real_class.rstrip('_') + '&'
                        ret.stop_id = ret.stop_id.rstrip('|') + '&'
                        ret.stop_time = ret.stop_time.rstrip('|') + '&'
                        ret.daydiff = ret.daydiff.rstrip('_') + '&'
                        ret.dept_id += '&'
                        ret.dest_id += '&'
                        ret.dept_day += '&'
                        ret.dept_time += '&'
                        ret.dest_time += '&'
                        ret.dur += '-1' + '&'
                        ret.stop += '&'
                        default_null_list.append('NULL')
                    ret.flight_no += schedule['flightNo'] + '_'
                    ret.plane_type += schedule['planeModel'] + '_'
                    ret.flight_corp += airline_corp + '_'
                    ret.seat_type += cabin + '_'
                    ret.real_class += cabin_real + '_'
                    ret.stop_id += schedule['fromAirport'] + '_' + schedule['toAirport'] + '|'
                    ret.stop_time += from_date[0] + 'T' + from_date[1] + ':00_' + to_date[0] + 'T' + to_date[1] + ':00|'
                    ret.daydiff += str(self.daysBetweenDate(from_date[0], to_date[0], '%Y-%m-%d')) + '_'
                    # ret.rest = schedule['remainSeatCount']
                    if correspondSegment == 1 and k == 0:
                        ret.dept_id += schedule['fromAirport']
                        from_city.append(seg['fromCity'])
                        ret.dept_day += from_date[0]
                        ret.dept_time += from_date[0] + 'T' + from_date[1] + ':00'
                        ret.stop += str(int(rs_list[(correspondRange - 1) * 2 + 1]) - 1)
                    if correspondSegment == int(
                            rs_list[(correspondRange - 1) * 2 + 1]) and k == len_flightScheduled - 1:
                        ret.dest_id += schedule['toAirport']
                        to_city.append(seg['toCity'])
                        ret.dest_time += to_date[0] + 'T' + to_date[1] + ':00'
            ret.dur += '-1'

            default_null = '&'.join(default_null_list)
            # ret.return_rule = '&'.join(return_rule_list)
            # ret.change_rule = '&'.join(return_rule_list)
            ret.package  = ret.share_flight = ret.stop = ret.share_flight = \
                ret.stopby = ret.baggage = ret.transit_visa = ret.reimbursement = ret.flight_meals =\
                ret.ticket_type = default_null
            # policyReturnPoint 机票价格政策
            len_policyReturnPoint = len(result['policyReturnPoint'])
            for m in range(0, len_policyReturnPoint):
                policy = result['policyReturnPoint'][m]
                if policy['passengerType'] == 'ADU':
                    ret_cpy = copy.copy(ret)
                    ret_cpy.price = policy['facePrice']
                    ret_cpy.tax = policy['tax']
                    policy_id = policy['policyId']
                    is_special_price = result.get('specialPrice', False)
                    is_taken_seat = result.get('takenSeat', False)
                    child_face_price = result.get('childFacePrice', 0)
                    ret_cpy.others_info = json.dumps({
                        'paykey': self.getPayKey(ticket_info),
                        'payInfo': self.getPayInfo(from_city, to_city, policy_id, freight_rule_query_id,
                                                     is_special_price, is_taken_seat, child_face_price, airline_corp,
                                                   is_share_flight),
                        'type': 'flight_multi'
                    }) + "&NULL"
                    # 后处理
                    self.afterProcess(ret_cpy)
                    ret_list.append(ret_cpy)
        return ret_list

    '''
    ######对外入口: 国际机票######
    mode: string 可以为"OW","OJ"或者"RT" 其中OW(单程)|OJ(联程)|RT(往返)
    section: 元组tuple的数组 里面元素分别为:
        fromCityCode: string 出发城市的城市三字码
        fromDate: string 出发日期 格式为"yyyy-MM-dd"
        toCityCode: string 目的城市的城市三字码
    ticket_info: dict 爬虫传来的高级搜索参数 
    '''

    def searchInternational(self, mode, section, ticket_info):
        ret_list = []
        if mode != 'OW' and mode != 'OJ' and mode != 'RT':
            print('参数错误:请求飞机的类型必须是OW(单程)|OJ(联程)|RT(往返)中的一种')
            return ret_list

        # 1,构造请求
        req_params = self.makeRequestInternational(mode, section, ticket_info)
        req_str = json.dumps(req_params)
        print('请求:' + req_str)

        # 2，发请求
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(self.m_api, headers=headers, data=req_str)
        # json_str = open('case.txt','r').read()

        # 3,解析请求
        ret_dict = json.loads(resp.text)
        # ret_dict = json.loads(json_str);
        if 'responseMetaInfo' not in ret_dict or 'resultCode' not in ret_dict['responseMetaInfo']:
            print('返回格式错误:responseMetaInfo')
            return ret_list
        elif ret_dict['responseMetaInfo']['resultCode'] != "0":
            print'返回出错:', ret_dict['responseMetaInfo']['reason']
            return ret_list
        if mode == 'OW':
            return self.parseOW(ret_dict, ticket_info)
        elif mode == 'RT':
            return self.parseRT(ret_dict, ticket_info)
        elif mode == 'OJ':
            return self.parseOJ(ret_dict, section, ticket_info)
        else:
            return ret_list

    def get_post_parameters(self, mode, section, ticket_info):
        ret_list = []
        if mode != 'OW' and mode != 'OJ' and mode != 'RT':
            print('参数错误:请求飞机的类型必须是OW(单程)|OJ(联程)|RT(往返)中的一种')
            return ret_list

        req_params = self.makeRequestInternational(mode, section, ticket_info)
        req_str = json.dumps(req_params)
        # print('请求:' + req_str)

        headers = {'Content-Type': 'application/json'}
        return {'method': 'post','url': self.m_api, 'headers': headers, 'data':req_str}

    def parse_resp(self, ret_dict, mode, section, *args, **kwargs):
        if mode == 'OW':
            return self.parseOW(ret_dict, *args, **kwargs)
        elif mode == 'RT':
            return self.parseRT(ret_dict, *args, **kwargs)
        elif mode == 'OJ':
            return self.parseOJ(ret_dict, section, *args, **kwargs)
        else:
            raise Exception('不正确的解析类型')

    def get_change_rule_params(self, query_id):
        """
        获取退改规则请求
        :return: 
        """
        timestamp = str(int(time.time()))
        var = {
            'url': self.m_api,
            'method': 'post', 'json': {
                "requestMetaInfo": {
                    "userName": self.m_account,
                    "timeStamp": timestamp,
                    "signCode": self.getSignCode(timestamp),
                    "responseDataType": self.m_ret_type
                },
                "EndorsementQueryRequest": {
                    "freightLimitQueryID": query_id,
                }
            }
        }
        return var