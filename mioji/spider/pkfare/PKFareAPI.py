# coding: utf8

import StringIO
import base64
import datetime
import gzip
import hashlib
import json
import re
import requests
import types
from mioji.common.class_common import Flight
from mioji.common.class_common import MultiFlight
from mioji.common.class_common import RoundFlight
from mioji.common.logger import logger
from mioji.common import parser_except


#############可变配置项###############
# api机器测试账号已经测试通过，在请求前确认是否用以下账号，并在请求时进行加密，以及请求url是否正确
g_partner_id = 'q9ih05Lel3vdmeNm4LoXDmG998s='
g_partner_key = 'YjI0YTk4NDUxZDE4OTJhMzVhOTIyNzY0NjI0N2IzMzE='
# g_shopping_api= 'http://api.pkfare.com/shopping'
g_shopping_api = 'http://open.pkfare.com/apitest/shopping'
########################################


class Handler:

    # def __init__(self, task=None, g_partner_id=g_partner_id, g_partner_key=g_partner_key, g_shopping_api=g_shopping_api):
    #     self.m_partner_id = g_partner_id
    #     self.m_partner_key = g_partner_key
    #     self.m_shopping_api = g_shopping_api
    #     self.task = task
    #     self._itinerary_count = 0
    #     return
    def __init__(self, task=None):
        self.task = task
        self._itinerary_count = 0
        
        return

    def get_auth(self, ticket_info):
        # 修改原有的错误逻辑，增加auth初始值
        auth = self.task.ticket_info.get('auth', {})
        if isinstance(auth, types.StringTypes):
            auth = json.loads(auth)
        elif isinstance(auth, types.DictType):
            auth = auth
        else:
            logger.info('不合法auth:',auth)
        
        self.m_partner_id = auth.get('partner_id', "")
        self.m_partner_key = auth.get('partner_key', '')
        self.m_shopping_api = auth.get('url', '')

        if not self.m_partner_id or not self.m_partner_key or not self.m_shopping_api:
            raise parser_except.ParserException(121, '无认证信息')

    def getPayKey(self, ticket_info):
        #redis_key = self.task.redis_key
        redis_key = self.task.redis_key
        id = self._itinerary_count
        self._itinerary_count += 1
        return {'redis_key': redis_key, 'id': id}

    def getSignCode(self):
        m = hashlib.md5()
        rule_str = self.m_partner_id + self.m_partner_key
        m.update(rule_str)
        return m.hexdigest()

    def getAges(self, age_str):
        ret_list = []
        if isinstance(age_str, (str, unicode)):
            ages = age_str.split('_')
            for age in ages:
                ret_list.append(float(age))
        return ret_list

    def get3rdCabin(self, ori_cabin):
        if ori_cabin == 'B':
            return 'Business'
        elif ori_cabin == 'F':
            return 'First'
        elif ori_cabin == 'E':
            return 'Economy'
        elif ori_cabin == 'P':
            return 'PremiumEconomy'
        else:
            return 'Economy'

    def getMiojiCabin(self, ori_cabin):
        cabin = ori_cabin.lower()
        if cabin == 'business':
            return 'B'
        elif cabin == 'economy':
            return 'E'
        elif cabin == 'first':
            return 'F'
        elif cabin == 'premiumeconomy':
            return 'P'
        else:
            return 'NULL'

    def makeFlightRequest(self, section, ticket_info):
        req_param = {}
        # Authentication
        authentication = {}
        authentication['partnerId'] = self.m_partner_id
        authentication['sign'] = self.getSignCode()
        req_param['authentication'] = authentication
        # search
        search = {}
        cnt = 1
        cnt_child = 0
        cnt_baby = 0
        if 'v_count' in ticket_info and isinstance(ticket_info['v_count'], int):
            cnt = ticket_info['v_count']
        '''
        ages = self.getAges(ticket_info['v_age'])
        if cnt < len(ages):
            cnt = len(ages)
        for age in ages:
            if age >= 2 and age <= 12:
                cnt_child += 1
            elif age < 2:
                cnt_baby += 1
        search['adults'] = cnt - cnt_child - cnt_baby
        search['children'] = cnt_child
        '''
        search['adults'] = ticket_info['v_count']
        search['children'] = 0
        # SearchAirLegs
        searchAirLegs = []
        cabin = ''
        if isinstance(ticket_info['v_seat_type'], (unicode, str)):
            cabin = self.get3rdCabin(ticket_info['v_seat_type'])
        for sec in section:
            flightRange = {}
            flightRange['origin'] = sec[0]
            flightRange['destination'] = sec[2]
            flightRange['departureDate'] = sec[1]  # yyyy-MM-dd
            flightRange['cabinClass'] = cabin
            searchAirLegs.append(flightRange)
        search['searchAirLegs'] = searchAirLegs
        # 合并参数
        req_param['search'] = search
        # 转json字符串
        req_str = json.dumps(req_param)
        # print('原始请求:' + req_str)

        return base64.b64encode(req_str)

    def decodeGzip(self, data):
        stream = StringIO.StringIO(data)
        f = gzip.GzipFile(mode='rb', fileobj=stream)
        ret = f.read()  # 读取解压缩后数据
        f.close()
        stream.close()
        return ret

    def fetchDateTime(self, ori_date):
        pos = ori_date.find(' ')
        return (ori_date[0:pos], ori_date[pos + 1:])

    def getSecondFromM(self, m):
        if isinstance(m, int):
            return 60 * m
        return 0

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
        ret.price = -1
        ret.tax = -1
        ret.surcharge = -1
        ret.promotion = 'NULL'
        ret.currency = 'CNY'
        ret.seat_type = ''
        ret.real_class = ''
        ret.package = 'NULL'
        ret.stop_id = ''
        ret.stop_time = ''
        ret.daydiff = ''
        ret.source = 'pkfare::pkfare'
        ret.return_rule = '退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。'
        ret.stop = -1
        ret.share_flight = ''
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
        ret.price = -1
        ret.tax = -1
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
        ret.source = 'pkfare::pkfare'
        ret.return_rule = '退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。'
        ret.stop_A = -1
        ret.stop_B = -1
        ret.share_flight_A = ''
        ret.share_flight_B = ''
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
        ret.price = -1
        ret.tax = -1
        ret.surcharge = -1
        ret.promotion = 'NULL'
        ret.currency = 'CNY'
        ret.seat_type = ''
        ret.real_class = ''
        ret.package = 'NULL'
        ret.stop_id = ''
        ret.stop_time = ''
        ret.daydiff = ''
        ret.source = 'pkfare::pkfare'
        ret.return_rule = '退改政策以最终线下沟通结果为准。'
        ret.change_rule = '退改政策以最终线下沟通结果为准。'
        ret.stop = ''
        ret.share_flight = ''
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
            flight.share_flight = flight.share_flight.rstrip('_')
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
            flight.share_flight_A = flight.share_flight_A.rstrip('_')
            flight.share_flight_B = flight.share_flight_B.rstrip('_')
        elif isinstance(flight, MultiFlight):
            flight.seat_type = flight.seat_type.rstrip('_')
            flight.real_class = flight.real_class.rstrip('_')
            flight.flight_no = flight.flight_no.rstrip('_')
            flight.plane_type = flight.plane_type.rstrip('_')
            flight.flight_corp = flight.flight_corp.rstrip('_')
            flight.stop_id = flight.stop_id.rstrip('|')
            flight.stop_time = flight.stop_time.rstrip('|')
            flight.daydiff = flight.daydiff.rstrip('_')
            flight.share_flight = flight.share_flight.rstrip('_')
        return

    def parseRangeSegmentCount(self, cnt):
        return re.split('-|,', cnt)

    def parseFlights(self, ret_dict, flights):
        if 'data' not in ret_dict or not ret_dict['data'] or 'flights' not in ret_dict['data']:
            return
        for flight in ret_dict['data']['flights']:
            flights[flight['flightId']] = flight

    def parseSegments(self, ret_dict, segments):
        if 'data' not in ret_dict or not ret_dict['data'] or'segments' not in ret_dict['data']:
            return
        for seg in ret_dict['data']['segments']:
            segments[seg['segmentId']] = seg
        return

    def getReturnRule(self, solution):
        if 'afterSaleRule' in solution and isinstance(solution['afterSaleRule'], dict) and 'refundNotes' in solution[
                'afterSaleRule'] and isinstance(solution['afterSaleRule']['refundNotes'], (unicode, str)):
            return solution['afterSaleRule']['refundNotes']
        return '退改政策以最终线下沟通结果为准。'

    def getChangeRule(self, solution):
        if 'afterSaleRule' in solution and isinstance(solution['afterSaleRule'], dict) and 'changeNotes' in solution[
                'afterSaleRule'] and isinstance(solution['afterSaleRule']['changeNotes'], (unicode, str)):
            return solution['afterSaleRule']['changeNotes']
        return '退改政策以最终线下沟通结果为准。'

    def getShareFlight(self, seg):
        if 'codeShare' in seg and seg['codeShare'] == 'Y' and 'opFltNo' in seg and isinstance(seg['opFltNo'], (
                unicode, str)) and 'opFltAirline' in seg and isinstance(seg['opFltAirline'], (unicode, str)):
            return seg['opFltAirline'] + seg['opFltNo']
        else:
            return 'NULL'

    def parseOW(self, ret_dict, ticket_info):
        ret_list = []
        # 1，解析flights和segments
        flights = {}
        self.parseFlights(ret_dict, flights)
        segments = {}
        self.parseSegments(ret_dict, segments)
        if not ret_dict['data']:
            return []
        # 2，开始生成交通方案列表
        len_solution = len(ret_dict['data']['solutions'])
        for i in range(0, len_solution):
            # print '结果'+str(i)
            payInfo = {}
            ret = self.createFlight()
            solution = ret_dict['data']['solutions'][i]
            ret.price = solution['adtFare']
            payInfo['adtFare'] = solution['adtFare']
            ret.tax = solution['adtTax']
            payInfo['adtFare'] = solution['adtTax']
            ret.currency = solution['currency']
            ret.surcharge = solution['qCharge'] + solution['tktFee'] + solution['platformServiceFee'] + solution[
                'merchantFee']
            ret.return_rule = self.getReturnRule(solution)
            ret.change_rule = self.getChangeRule(solution)
            # journey_0
            # 遍历flight
            len_flight = len(solution['journeys']['journey_0'])
            for j in range(0, len_flight):
                flight_key = solution['journeys']['journey_0'][j]
                flight = flights[flight_key]
                # 遍历segment
                len_segment = len(flight['segmengtIds'])
                airline = []
                arrival = []
                arrivalDate = []
                arrivalTime = []
                bookingCode = []
                departure = []
                departureDate = []
                departureTime = []
                flightNum = []
                for k in range(0, len_segment):
                    seg_key = flight['segmengtIds'][k]
                    # print seg_key
                    seg = segments[seg_key]
                    ret.stop += 1
                    ret.flight_no += seg['airline'] + seg['flightNum'] + '_'
                    airline.append(seg['airline'])
                    flightNum.append(seg['flightNum'])
                    ret.plane_type += seg['equipment'] + '_'
                    ret.flight_corp += seg['airline'] + '_'
                    if j == 0 and k == 0:
                        ret.dept_id = seg['departure']
                        ret.dept_day = seg['strDepartureDate']
                        ret.dept_time = seg['strDepartureDate'] + \
                            'T' + seg['strDepartureTime'] + ':00'
                    if j == len_flight - 1 and k == len_segment - 1:
                        ret.dest_id = seg['arrival']
                        ret.dest_day = seg['strArrivalDate']
                        ret.dest_time = seg['strArrivalDate'] + \
                            'T' + seg['strArrivalTime'] + ':00'
                    ret.seat_type += seg['cabinClass'] + '_'
                    ret.real_class += seg['bookingCode'] + '_'
                    bookingCode.append(seg['bookingCode'])
                    ret.stop_id += seg['departure'] + \
                        '_' + seg['arrival'] + '|'
                    ret.stop_time += seg['strDepartureDate'] + 'T' + seg['strDepartureTime'] + ':00_' + seg[
                        'strArrivalDate'] + 'T' + seg['strArrivalTime'] + ':00|'
                    ret.daydiff += str(
                        self.daysBetweenDate(seg['strDepartureDate'], seg['strArrivalDate'], '%Y-%m-%d')) + '_'

                    departure.append(seg['departure'])
                    departureDate.append(seg['strDepartureDate'])
                    departureTime.append(seg['strDepartureTime'])
                    arrival.append(seg['arrival'])
                    arrivalDate.append(seg['strArrivalDate'])
                    arrivalTime.append(seg['strArrivalTime'])

                    ret.share_flight += self.getShareFlight(seg) + '_'
                others_info = {}
                payInfo = {}
                others_info['paykey'] = self.getPayKey(ticket_info)
                others_info['type'] = 'flight_one_way'
                payInfo['airline'] = []
                payInfo['airline'].append('_'.join(airline))
                payInfo['arrival'] = []
                payInfo['arrival'].append('_'.join(arrival))
                payInfo['arrivalDate'] = []
                payInfo['arrivalDate'].append('_'.join(arrivalDate))
                payInfo['arrivalTime'] = []
                payInfo['arrivalTime'].append('_'.join(arrivalTime))
                payInfo['bookingCode'] = []
                payInfo['bookingCode'].append('_'.join(bookingCode))
                payInfo['departure'] = []
                payInfo['departure'].append('_'.join(departure))
                payInfo['departureDate'] = []
                payInfo['departureDate'].append('_'.join(departureDate))
                payInfo['departureTime'] = []
                payInfo['departureTime'].append('_'.join(departureTime))
                payInfo['flightNum'] = []
                payInfo['flightNum'].append('_'.join(flightNum))
                others_info['payInfo'] = payInfo
                ret.others_info = json.dumps(others_info)
            # 后处理
            self.afterProcess(ret)
            # ret.dump()
            ret_list.append(ret)
        return ret_list

    def parseRT(self, ret_dict, ticket_info):
        ret_list = []
        # 1，解析flights和segments
        flights = {}
        self.parseFlights(ret_dict, flights)
        segments = {}
        self.parseSegments(ret_dict, segments)

        # 2，开始生成交通方案列表
        if not ret_dict['data']:
            return []
        len_solution = len(ret_dict['data']['solutions'])
        for i in range(0, len_solution):
            # print '结果'+str(i)
            ret = self.createRoundFlight()
            solution = ret_dict['data']['solutions'][i]
            ret.price = solution['adtFare']
            ret.tax = solution['adtTax']
            ret.currency = solution['currency']
            ret.surcharge = solution['qCharge'] + solution['tktFee'] + solution['platformServiceFee'] + solution[
                'merchantFee']
            ret.return_rule = self.getReturnRule(solution)
            ret.change_rule = self.getChangeRule(solution)

            others_info = {}
            payInfo = {}
            others_info['paykey'] = self.getPayKey(ticket_info)
            others_info['type'] = 'flight_return'
            payInfo['airline'] = []
            payInfo['arrival'] = []
            payInfo['arrivalDate'] = []
            payInfo['arrivalTime'] = []
            payInfo['bookingCode'] = []
            payInfo['departure'] = []
            payInfo['departureDate'] = []
            payInfo['departureTime'] = []
            payInfo['flightNum'] = []

            # journey_0
            # 遍历flight
            len_flight = len(solution['journeys']['journey_0'])
            for j in range(0, len_flight):

                airline = []
                arrival = []
                arrivalDate = []
                arrivalTime = []
                bookingCode = []
                departure = []
                departureDate = []
                departureTime = []
                flightNum = []

                flight_key = solution['journeys']['journey_0'][j]
                flight = flights[flight_key]
                # 遍历segment
                len_segment = len(flight['segmengtIds'])
                for k in range(0, len_segment):
                    seg_key = flight['segmengtIds'][k]
                    # print seg_key
                    seg = segments[seg_key]
                    ret.stop_A += 1
                    ret.flight_no_A += seg['airline'] + seg['flightNum'] + '_'
                    ret.plane_no_A += seg['equipment'] + '_'
                    ret.airline_A += seg['airline'] + '_'
                    if j == 0 and k == 0:
                        ret.dept_id = seg['departure']
                        ret.dept_day = seg['strDepartureDate']
                        ret.dept_time_A = seg['strDepartureDate'] + \
                            'T' + seg['strDepartureTime'] + ':00'
                    if j == len_flight - 1 and k == len_segment - 1:
                        ret.dest_id = seg['arrival']
                        ret.dest_time_A = seg['strArrivalDate'] + \
                            'T' + seg['strArrivalTime'] + ':00'
                    ret.seat_type_A += seg['cabinClass'] + '_'
                    ret.real_class_A += seg['bookingCode'] + '_'
                    ret.stop_id_A += seg['departure'] + \
                        '_' + seg['arrival'] + '|'
                    ret.stop_time_A += seg['strDepartureDate'] + 'T' + seg['strDepartureTime'] + ':00_' + seg[
                        'strArrivalDate'] + 'T' + seg['strArrivalTime'] + ':00|'
                    ret.daydiff_A += str(
                        self.daysBetweenDate(seg['strDepartureDate'], seg['strArrivalDate'], '%Y-%m-%d')) + '_'

                    departure.append(seg['departure'])
                    departureDate.append(seg['strDepartureDate'])
                    departureTime.append(seg['strDepartureTime'])
                    arrival.append(seg['arrival'])
                    arrivalDate.append(seg['strArrivalDate'])
                    arrivalTime.append(seg['strArrivalTime'])
                    airline.append(seg['airline'])
                    flightNum.append(seg['flightNum'])
                    bookingCode.append(seg['bookingCode'])
                    ret.share_flight_A += self.getShareFlight(seg) + '_'
                payInfo['airline'].append('_'.join(airline))
                payInfo['arrival'].append('_'.join(arrival))
                payInfo['arrivalDate'].append('_'.join(arrivalDate))
                payInfo['arrivalTime'].append('_'.join(arrivalTime))
                payInfo['bookingCode'].append('_'.join(bookingCode))
                payInfo['departure'].append('_'.join(departure))
                payInfo['departureDate'].append('_'.join(departureDate))
                payInfo['departureTime'].append('_'.join(departureTime))
                payInfo['flightNum'].append('_'.join(flightNum))
            # journey_1
            # 遍历flight
            len_flight = len(solution['journeys']['journey_1'])
            for j in range(0, len_flight):
                flight_key = solution['journeys']['journey_1'][j]
                flight = flights[flight_key]
                # 遍历segment
                len_segment = len(flight['segmengtIds'])
                airline = []
                arrival = []
                arrivalDate = []
                arrivalTime = []
                bookingCode = []
                departure = []
                departureDate = []
                departureTime = []
                flightNum = []
                for k in range(0, len_segment):
                    seg_key = flight['segmengtIds'][k]
                    # print seg_key
                    seg = segments[seg_key]
                    ret.stop_B += 1
                    ret.flight_no_B += seg['airline'] + seg['flightNum'] + '_'
                    ret.plane_no_B += seg['equipment'] + '_'
                    ret.airline_B += seg['airline'] + '_'
                    if j == 0 and k == 0:
                        ret.dest_day = seg['strDepartureDate']
                        ret.dept_time_B = seg['strDepartureDate'] + \
                            'T' + seg['strDepartureTime'] + ':00'
                    if j == len_flight - 1 and k == len_segment - 1:
                        ret.dest_time_B = seg['strArrivalDate'] + \
                            'T' + seg['strArrivalTime'] + ':00'
                    ret.seat_type_B += seg['cabinClass'] + '_'
                    ret.real_class_B += seg['bookingCode'] + '_'
                    ret.stop_id_B += seg['departure'] + \
                        '_' + seg['arrival'] + '|'
                    ret.stop_time_B += seg['strDepartureDate'] + 'T' + seg['strDepartureTime'] + ':00_' + seg[
                        'strArrivalDate'] + 'T' + seg['strArrivalTime'] + ':00|'
                    ret.daydiff_B += str(
                        self.daysBetweenDate(seg['strDepartureDate'], seg['strArrivalDate'], '%Y-%m-%d')) + '_'
                    ret.share_flight_B += self.getShareFlight(seg) + '_'
                    departure.append(seg['departure'])
                    departureDate.append(seg['strDepartureDate'])
                    departureTime.append(seg['strDepartureTime'])
                    arrival.append(seg['arrival'])
                    arrivalDate.append(seg['strArrivalDate'])
                    arrivalTime.append(seg['strArrivalTime'])
                    airline.append(seg['airline'])
                    flightNum.append(seg['flightNum'])
                    bookingCode.append(seg['bookingCode'])
                    ret.share_flight_A += self.getShareFlight(seg) + '_'
                payInfo['airline'].append('_'.join(airline))
                payInfo['arrival'].append('_'.join(arrival))
                payInfo['arrivalDate'].append('_'.join(arrivalDate))
                payInfo['arrivalTime'].append('_'.join(arrivalTime))
                payInfo['bookingCode'].append('_'.join(bookingCode))
                payInfo['departure'].append('_'.join(departure))
                payInfo['departureDate'].append('_'.join(departureDate))
                payInfo['departureTime'].append('_'.join(departureTime))
                payInfo['flightNum'].append('_'.join(flightNum))
            others_info['payInfo'] = payInfo
            ret.others_info = json.dumps(others_info)
            # 后处理
            self.afterProcess(ret)
            # ret.dump()
            ret_list.append(ret)
        return ret_list

    def parseOJ(self, ret_dict, ticket_info):
        ret_list = []
        # 1，解析flights和segments
        flights = {}
        self.parseFlights(ret_dict, flights)
        segments = {}
        self.parseSegments(ret_dict, segments)

        # 2，开始生成交通方案列表
        if not ret_dict['data']:
            return []
        len_solution = len(ret_dict['data']['solutions'])
        for i in range(0, len_solution):
            # print '结果'+str(i)
            adid = json.dumps({'paykey': self.getPayKey(ticket_info), 'type': 'flight_multi'})
            ret = self.createMultiFlight()
            solution = ret_dict['data']['solutions'][i]
            ret.price = solution['adtFare']
            ret.tax = solution['adtTax']
            ret.currency = solution['currency']
            ret.surcharge = solution['qCharge'] + solution['tktFee'] + solution['platformServiceFee'] + solution[
                'merchantFee']
            len_journey = len(solution['journeys'])
            # 遍历journey
            last_jk = 'journey_0'
            for m in range(0, len_journey):
                jk = 'journey_' + str(m)
                if jk not in solution['journeys']:
                    continue
                if last_jk != jk:
                    ret.flight_no = ret.flight_no.rstrip('_') + '&'
                    ret.plane_type = ret.plane_type.rstrip('_') + '&'
                    ret.flight_corp = ret.flight_corp.rstrip('_') + '&'
                    ret.dept_id += '&'
                    ret.dest_id += '&'
                    ret.dept_day += '&'
                    ret.dept_time += '&'
                    ret.dest_time += '&'
                    ret.dur += '&'
                    ret.seat_type = ret.seat_type.rstrip('_') + '&'
                    ret.real_class = ret.real_class.rstrip('_') + '&'
                    ret.stop_id = ret.stop_id.rstrip('|') + '&'
                    ret.stop_time = ret.stop_time.rstrip('|') + '&'
                    ret.daydiff = ret.daydiff.rstrip('_') + '&'
                    ret.stop += '&'
                    ret.share_flight = ret.share_flight.rstrip('_') + '&'
                    ret.return_rule += '&'
                    ret.change_rule += '&'
                    last_jk = jk
                journey = solution['journeys'][jk]
                ret.dur += '-1'
                ret.return_rule = self.getReturnRule(solution)
                ret.change_rule = self.getChangeRule(solution)
                stop = -1
                # 遍历flight
                len_flight = len(journey)
                for j in range(0, len_flight):
                    flight_key = journey[j]
                    flight = flights[flight_key]
                    # 遍历segment
                    len_segment = len(flight['segmengtIds'])
                    for k in range(0, len_segment):
                        seg_key = flight['segmengtIds'][k]
                        # print seg_key
                        seg = segments[seg_key]
                        stop += 1
                        ret.flight_no += seg['airline'] + \
                            seg['flightNum'] + '_'
                        ret.plane_type += seg['equipment'] + '_'
                        ret.flight_corp += seg['airline'] + '_'
                        if j == 0 and k == 0:
                            ret.dept_id += seg['departure']
                            ret.dept_day += seg['strDepartureDate']
                            ret.dept_time += seg['strDepartureDate'] + \
                                'T' + seg['strDepartureTime'] + ':00'
                        if j == len_flight - 1 and k == len_segment - 1:
                            ret.dest_id += seg['arrival']
                            ret.dest_time += seg['strArrivalDate'] + \
                                'T' + seg['strArrivalTime'] + ':00'
                            ret.stop += str(stop)
                        ret.seat_type += seg['cabinClass'] + '_'
                        ret.real_class += seg['bookingCode'] + '_'
                        ret.stop_id += seg['departure'] + \
                            '_' + seg['arrival'] + '|'
                        ret.stop_time += seg['strDepartureDate'] + 'T' + seg['strDepartureTime'] + ':00_' + seg[
                            'strArrivalDate'] + 'T' + seg['strArrivalTime'] + ':00|'
                        ret.daydiff += str(
                            self.daysBetweenDate(seg['strDepartureDate'], seg['strArrivalDate'], '%Y-%m-%d')) + '_'
                        ret.share_flight += self.getShareFlight(seg) + '_'
                        ret.others_info = adid
            # 后处理
            self.afterProcess(ret)
            # ret.dump()
            ret_list.append(ret)
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

    def searchFlight(self, mode, section, ticket_info):
        ret_list = []

        # 1,构造请求
        req_params = self.makeFlightRequest(section, ticket_info)

        # 2，发请求
        params = {'param': req_params}
        
        resp = requests.get(self.m_shopping_api, params=params)
        json_str = self.decodeGzip(resp.content)
        # json_str = open('case.txt','r').read()

        # 3,解析返回结果
        ret_dict = json.loads(json_str)
        if 'errorCode' not in ret_dict or ret_dict['errorCode'] != '0':
            if 'errorMsg' in ret_dict:
                print u'返回错误:' + ret_dict['errorMsg']
            else:
                print u'返回错误: 错误ID为' + ret_dict['errorCode']
            return ret_list
        if mode == 'OW':
            return self.parseOW(ret_dict, ticket_info)
        elif mode == 'RT':
            return self.parseRT(ret_dict, ticket_info)
        elif mode == 'OJ':
            return self.parseOJ(ret_dict, ticket_info)
        else:
            return ret_list

    def get_request_parameters(self, section, ticket_info):
        self.get_auth(ticket_info)
        req_params = self.makeFlightRequest(section, ticket_info)
        params = {'param': req_params}
        headers = {'User-Agent': 'python-requests/2.10.0'}
        self.m_shopping_api = self.m_shopping_api + '/shopping'
        return {'method': 'get', 'url': self.m_shopping_api, 'params': params}

    def parse_resp(self, mode, ret_dict, ticket_info):
        if mode == 'OW':
            return self.parseOW(ret_dict, ticket_info)
        elif mode == 'RT':
            return self.parseRT(ret_dict, ticket_info)
        elif mode == 'OJ':
            return self.parseOJ(ret_dict, ticket_info)

    def searchFlight_test(self, mode, section, ticket_info):
        ret_list = []

        req_params = self.get_request_parameters(section, ticket_info)

        params = req_params['params']
        resp = requests.get(self.m_shopping_api, params=params)
        json_str = self.decodeGzip(resp.content)

        ret_dict = json.loads(json_str)
        return self.parse_resp(mode, ret_dict, ticket_info)


if __name__ == '__main__':
    from mioji.common.utils import httpset_debug
    httpset_debug()
    result = Handler().searchFlight('OJ', [('HKG', '2017-07-01', 'SIN'), ('SIN', '2017-07-07', 'SHA')],
                                    {'v_seat_type': 'E', 'v_age': '20_18_3_-1'})
    # result = Handler().searchFlight_test('OW', [('HKG', '2017-07-10', 'SIN')],
    #                                 {'v_seat_type': 'E', 'v_age': '20_18_3_-1'})
    lr = len(result)
    for i in range(0, min(lr, 10)):
        print '#######<', i, '>\n', result[i].to_tuple()
        pass
