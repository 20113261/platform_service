#!/usr/bin/env python
# coding=utf-8

import re
import json
import sys
import operator
import traceback
import urllib
from math import *
from common.logger import logger
from common.class_common import RoundFlight
from common.common import get_proxy
from util.Browser2 import MechanizeCrawler as mc
from common.suggestion import suggestion
import datetime

reload(sys)
sys.setdefaultencoding('utf-8')


def __calsecond(hms):
    dur = 0
    hms_list = hms.split(':')
    dur = int(hms_list[0]) * 3600 + int(hms_list[1]) * 60 + int(hms_list[2])
    return dur


def GetDaydiff(time_list):

    daydiff = ''
    temp_list = time_list.split('|')

    for each in temp_list:

        each_list = each.split('_')
        each_list_0 = each_list[0].split('T')
        each_list_1 = each_list[1].split('T')
        if each_list_0[0] == each_list_1[0]:
            if __calsecond(each_list_0[1]) >= __calsecond(each_list_1[1]):
                daydiff += '1_'
            else:
                daydiff += '0_'
        else:
            daydiff += '1_'
    return daydiff[:-1]


def ctripRound_Parser(dept_id, dest_id, dept_info, dest_info, dept_date, dest_date):
    result = {}
    tickets = []
    result['ticket'] = tickets
    result['error'] = 0
    result['proxy'] = 'NULL'

    obj = mc()
    # obj.set_debug(True)

    p = get_proxy(source='ctripRoundFlight')
    if p is None or p == '':
        result['error'] = 21
        return result
    result['proxy'] = p
    obj.set_proxy(p)

    try:
        homecity_name = dept_info['city_name']
        destcity_name = dest_info['city_name']
    except Exception, e:
        logger.info('ctripRound Error:', e)
        result['error'] = 27
        return result

    dept_en = dept_info['city_en_name']
    dest_en = dest_info['city_en_name']
    Search = 'http://flights.ctrip.com/international/round-%s-%s-%s-%s?%s&%s&y_s' % (dept_id, dest_id, dept_id.lower(), dest_id.lower(), dept_date, dest_date)
    Referer = 'http://flights.ctrip.com/international/'
    Search_1 = 'http://flights.ctrip.com/international/AjaxRequest/SearchFlights/AsyncSearchHandlerSOAII.ashx'
    postdata0 = {}
    postdata0['FlightWay'] = 'D'
    postdata0['homecity_name'] = homecity_name
    # postdata0['HomeCityID'] = '1'
    postdata0['destcity1_name'] = destcity_name
    # postdata0['destcityID'] = '192'
    postdata0['DDatePeriod1'] = dept_date
    postdata0['ADatePeriod1'] = dest_date
    postdata0['Quantity'] = '1'
    postdata0['ChildQuantity'] = '0'
    postdata0['InfantQuantity'] = '0'
    postdata0['drpSubClass'] = 'Y'
    postdata0['IsFavFull'] = ''
    postdata0['mkt_header'] = ''
    obj.add_referer(Referer)
    try:
        page0, error = obj.req('post', Search, postdata0, paras_type=0, html_flag=True)
        if error:
            raise Exception(error)
        postdata = get_postdata(page0)
    except Exception, e:
        logger.info(e)
        result['error'] = 22
        return result
    try:
        obj.add_header({'Content-Type': 'application/x-www-form-urlencoded'})
        page, error = obj.req('post', Search_1, postdata, paras_type=2, html_flag=True)
        if error:
            raise Exception(error)
        page = obj.resp.text
        tickets += get_tickets(page, dept_date, dest_date)

        postdata = postdata.replace('SearchToken=1', 'SearchToken=2')
        page, error = obj.req('post', Search_1, postdata, paras_type=2, html_flag=True)
        if error:
            raise Exception(error)
        page = obj.resp.text
        tickets += get_tickets(page, dept_date, dest_date)

        postdata = postdata.replace('SearchToken=2', 'SearchToken=3')
        page, error = obj.req('post', Search_1, postdata, paras_type=2, html_flag=True)
        if error:
            raise Exception(error)
        page = obj.resp.text
        tickets += get_tickets(page, dept_date, dest_date)
    except Exception as e:
        logger.info(e)
        result['error'] = 24
        return result
    return result


def get_tickets(page, dept_date, dest_date):
    tickets = []
    if page:
        infos = json.loads(page)
    else:
        return tickets
    try:
        all_flights = infos['RoundTripFlightList']
    except Exception, e:
        if infos['SearchStatus']['Result'] == 0:
            return tickets
        else:
            logger.debug(traceback.format_exc())
            result['error'] = 24
            return result

    cabin = '经济舱'
    for every_flight in all_flights:
        roundflight = RoundFlight()
        no_p = re.compile(r'([A-Z]+\d+)')
        flight_nos = every_flight['FlightInfoKeys']
        flight_detail_A = infos['FlightInfoDic'][flight_nos[0]]
        flight_detail_B = infos['FlightInfoDic'][flight_nos[1]]
        flight_no_A = '_'.join([i['FlightNo'] for i in flight_detail_A['FlightDetail']])
        flight_no_B = '_'.join([i['FlightNo'] for i in flight_detail_B['FlightDetail']])
        stop_time_A = []
        stop_time_B = []
        stop_id_A = []
        stop_id_B = []
        flight_type_A = []
        flight_type_B = []
        airlines_a = []
        airlines_b = []

        for each in flight_detail_A['FlightDetail']:
            dept_port = each['DPort']
            dest_port = each['APort']
            stop_id_A.append(dept_port + '_' + dest_port)
            dept_Time = str(datetime.datetime.strptime(each['DepartTime'].encode('utf-8'), '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            dest_Time = str(datetime.datetime.strptime(each['ArrivalTime'].encode('utf-8'), '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            stop_time_A.append(dept_Time + '_' + dest_Time)

            CraftType_A = each['CraftType']
            flight_type_A.append(CraftType_A)
            airline_a = each['AirlineName']
            airlines_a.append(airline_a)
        stop_id_A = '|'.join(stop_id_A)
        stop_time_A = '|'.join(stop_time_A)
        flight_type_A = '_'.join(flight_type_A)
        airlines_A = '_'.join(airlines_a)

        for each in flight_detail_B['FlightDetail']:
            dept_port = each['DPort']
            dest_port = each['APort']
            stop_id_B.append(dept_port + '_' + dest_port)
            dept_Time = str(datetime.datetime.strptime(each['DepartTime'].encode('utf-8'), '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            dest_Time = str(datetime.datetime.strptime(each['ArrivalTime'].encode('utf-8'), '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            stop_time_B.append(dept_Time + '_' + dest_Time)
            CraftType_B = each['CraftType']
            flight_type_B.append(CraftType_B)
            airline_b = each['AirlineName']
            airlines_b.append(airline_b)

        stop_id_B = '|'.join(stop_id_B)
        stop_time_B = '|'.join(stop_time_B)
        flight_type_B = '_'.join(flight_type_B)
        airlines_B = '_'.join(airlines_b)
        stop_A = flight_no_A.count('_')
        stop_B = flight_no_B.count('_')
        currency = 'CNY'
        source = 'ctrip::ctrip'

        roundflight.dept_id = stop_id_A.split('_')[0]
        roundflight.dest_id = stop_id_A.split('_')[len(stop_id_A.split('_')) - 1]
        roundflight.dept_day = dept_date
        roundflight.dest_day = dest_date
        roundflight.currency = currency
        roundflight.source = source
        roundflight.flight_no_A = flight_no_A
        roundflight.airline_A = airlines_A
        roundflight.plane_no_A = flight_type_A
        stop_time_A_list = stop_time_A.split('_')
        roundflight.dept_time_A = stop_time_A_list[0]
        roundflight.dest_time_A = stop_time_A_list[len(stop_time_A_list) - 1]
        roundflight.real_class_A = '_'.join(['NULL'] * (stop_A + 1))
        roundflight.stop_id_A = stop_id_A
        roundflight.stop_time_A = stop_time_A
        roundflight.daydiff_A = GetDaydiff(stop_time_A)
        roundflight.stop_A = stop_A
        roundflight.flight_no_B = flight_no_B
        roundflight.airline_B = airlines_B
        roundflight.plane_no_B = flight_no_B
        roundflight.plane_no_B = flight_type_B
        stop_time_B_list = stop_time_B.split('_')
        roundflight.dept_time_B = stop_time_B_list[0]
        roundflight.dest_time_B = stop_time_B_list[len(stop_time_B_list) - 1]
        roundflight.real_class_B = '_'.join(['NULL'] * (stop_B + 1))
        roundflight.stop_id_B = stop_id_B
        roundflight.stop_time_B = stop_time_B
        roundflight.daydiff_B = GetDaydiff(stop_time_B)
        roundflight.stop_B = stop_B
        roundflight.share_flight_A = '_'.join(['NULL'] * (stop_A + 1))
        roundflight.share_flight_B = '_'.join(['NULL'] * (stop_B + 1))
        roundflight.stopby_A = '_'.join(['NULL'] * (stop_A + 1))
        roundflight.stopby_B = '_'.join(['NULL'] * (stop_B + 1))

        # promotioin
        for fare in every_flight['FareList']:
            price = fare['Price']
            tax = fare['Tax']
            roundflight.price = price
            roundflight.tax = tax
            airCabin_a = []
            airCabin_b = []
            try:
                if 'ClassName' in fare:
                    clsName = fare['ClassName']
                    roundflight.seat_type_A = '_'.join([clsName for i in range(stop_A + 1)])
                    roundflight.seat_type_B = '_'.join([clsName for i in range(stop_B + 1)])
                elif 'ClassInfo' in fare:
                    for classInfo in fare['ClassInfo']:
                        if classInfo['SegmentNo'] == 1:
                            airCabin_a.append(classInfo['ClassName'])
                        elif classInfo['SegmentNo'] == 2:
                            airCabin_b.append(classInfo['ClassName'])
                    roundflight.seat_type_A = '_'.join(clsName for clsName in airCabin_a)
                    roundflight.seat_type_B = '_'.join(clsName for clsName in airCabin_b)

            except Exception:
                logger.exception('仓位解析失败')
                continue
            tip = {}
            try:
                tip = fare["Tips"][0]
            except:
                pass
            if 'Text' in tip:
                roundflight.promotion = tip['Text']
            elif 'Type' in tip and tip['Type'] == 'BUSS':
                roundflight.promotion = '商务优选'
            elif 'Type' in tip and tip['Type'] == 'STU':
                roundflight.ticket_type = '留学生票'
                roundflight.promotion = '留学生票'
            elif 'Type' in tip and tip['Type'] == 'TEXT':
                roundflight.promotion = '特惠推荐'
            else:
                roundflight.promotion = 'NULL'
            roundflight.real_class_A = roundflight.seat_type_A
            roundflight.real_class_B = roundflight.seat_type_B
            roundflight_tuple = (roundflight.dept_id, roundflight.dest_id, roundflight.dept_day,
                                 roundflight.dest_day, roundflight.price, roundflight.tax, roundflight.surcharge,
                                 roundflight.promotion, roundflight.currency, roundflight.source,
                                 roundflight.return_rule, roundflight.flight_no_A, roundflight.airline_A,
                                 roundflight.plane_no_A, roundflight.dept_time_A, roundflight.dest_time_A,
                                 roundflight.dur_A, roundflight.seat_type_A, roundflight.real_class_A,
                                 roundflight.stop_id_A, roundflight.stop_time_A, roundflight.daydiff_A,
                                 roundflight.stop_A, roundflight.flight_no_B, roundflight.airline_B,
                                 roundflight.plane_no_B, roundflight.dept_time_B, roundflight.dest_time_B,
                                 roundflight.dur_B, roundflight.seat_type_B, roundflight.real_class_B,
                                 roundflight.stop_id_B, roundflight.stop_time_B, roundflight.daydiff_B,
                                 roundflight.stop_B, roundflight.change_rule, roundflight.share_flight_A,
                                 roundflight.share_flight_B, roundflight.stopby_A, roundflight.stopby_B,
                                 roundflight.baggage, roundflight.transit_visa, roundflight.reimbursement,
                                 roundflight.flight_meals, roundflight.ticket_type,
                                 roundflight.others_info, roundflight.rest)
            tickets.append(roundflight.to_tuple())
    return tickets


def ctripRound_task_parser(taskcontent):

    result = {}
    tickets = []
    result['ticket'] = tickets
    result['error'] = 0
    result['proxy'] = 'NULL'

    try:
        infos = taskcontent.strip().split('&')
        dept_city = infos[0]
        dest_city = infos[1]
        dept_date = infos[2][:4] + '-' + infos[2][4:6] + '-' + infos[2][6:]
        dest_date = infos[3][:4] + '-' + infos[3][4:6] + '-' + infos[3][6:]
    except Exception, e:
        result['error'] = 12
        return result
    try:
        dept_info = suggestion['ctrip'][dept_city]
        dest_info = suggestion['ctrip'][dest_city]
    except:
        result['error'] = 51
        return result
    result = ctripRound_Parser(dept_city, dest_city, dept_info, dest_info, dept_date, dest_date)
    return result


def ctripRound_request_parser(content):
    result = -1
    return result


def get_postdata(html_text):
    condition = re.search("condition\s*=\s*'([^']+)'", html_text).group(1)
    try:
        condition = json.loads(condition)
    except:
        condition = json.loads(condition.decode('gb2312').encode('utf8'))
    searchkey = condition['SearchKey']
    for segment in condition['SegmentList']:
        tmplist = segment['DCity'].split('|')
        tmplist[1] = tmplist[3]
        segment['DCity'] = '|'.join(tmplist)
        tmplist = segment['ACity'].split('|')
        tmplist[1] = tmplist[3]
        segment['ACity'] = '|'.join(tmplist)

    res = re.search(r'var\s+(\w+)\s*=1\s*,\s*(\w+)\s*=\s*1', html_text).groups()
    v1_name, v2_name = res
    v1 = v2 = 1

    op_dict = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.div}
    regexp_t = "{var}\s*=\s*{var}\s*([*/+-])=\s*eval.*?'(\w+\|\w+\|\w+\|\w+\|\w+)'"
    pat_eval = re.compile('\w+\|\w+\|(\w+)\|(\w+)\|(\w+)')
    # v1
    pat_process1 = re.compile(regexp_t.format(var=v1_name), re.S)
    process1 = pat_process1.findall(html_text)
    for op, val in process1:
        to_eval = pat_eval.sub(r'\1(\3)*\2', val)
        v1 = op_dict[op](v1, int(eval(to_eval)))
    v1 = -v1 if v1 < 0 else v1
    while v1 > 30: v1 %= 10

    # v2
    pat_process2 = re.compile(regexp_t.format(var=v2_name), re.S)
    process2 = pat_process2.findall(html_text)
    for op, val in process2:
        to_eval = pat_eval.sub(r'\1(\3)*\2', val)
        v2 = op_dict[op](v2, int(eval(to_eval)))
    v2 = -v2 if v2 < 0 else v2
    while v2 > 30: v2 %= 10

    searchkey = list(searchkey)
    searchkey.insert(v1, searchkey.pop(v2))
    searchkey = ''.join(searchkey).encode()

    # condition = re.sub('(?<="SearchKey":")[^"]+(?=")', searchkey, condition)
    condition['SearchKey'] = searchkey
    condition = json.dumps(condition).replace(' ', '')
    urllib.quote(condition, safe='()')
    postdata = 'SearchMode=TokenSearch&condition={0}&DisplayMode=RoundTripGroup&SearchToken=1'.format(condition)
    return postdata


if __name__ == '__main__':
    pass