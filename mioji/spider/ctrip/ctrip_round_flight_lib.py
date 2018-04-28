#!/usr/bin/env python
# coding=utf-8
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

import re
import json
import sys
import operator
import traceback
import urllib
from math import *
from mioji.common.suggestion import suggestion
from mioji.common import parser_except
from mioji.common.class_common import RoundFlight
import datetime
from base_data import port_city


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


def get_tickets(infos, dept_date, dest_date, user_datas=None):
    tickets = []
    try:
        all_flights = infos['RoundTripFlightList']
    except Exception, e:
        if infos['SearchStatus']['Result'] == 0:
            return tickets
        else:
            raise parser_except.ParserException(parser_except.DATA_NONE, "ctripRoundFlight::ctripRoundFlight 未返回数据")

    for every_flight in all_flights:
        roundflight = RoundFlight()
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
            dept_Time = str(
                datetime.datetime.strptime(each['DepartTime'], '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            dest_Time = str(
                datetime.datetime.strptime(each['ArrivalTime'], '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
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
            dept_Time = str(
                datetime.datetime.strptime(each['DepartTime'], '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
            dest_Time = str(
                datetime.datetime.strptime(each['ArrivalTime'], '%Y-%m-%d %H:%M:%S')).replace(' ', 'T')
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

        for fare in every_flight['FareList']:
            # price = fare['Price']
            # tax = fare['Tax']
            # roundflight.price = price
            # roundflight.tax = tax
            try:
                roundflight.price = fare['AdultPrice']
                roundflight.tax = fare['AdultTax']
                adults, childs, infants = user_datas
                # print adults, childs, infants
                if childs > 0 or infants > 0:
                    roundflight.others_info = generate_other_infos(user_datas, fare)
                # print roundflight.others_info
            except:
                roundflight.price = fare['Price']
                roundflight.tax = fare['Tax']
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
            tickets.append(roundflight.to_tuple())
    return tickets

def generate_other_infos(user_datas, fare):
    adults, childs, infants = user_datas
    results = 'Adult:(Price:%s, Tax:%s)' % (fare['AdultPrice'], fare['AdultTax'])
    if childs:
        results += ', Child:(Price:%s, Tax:%s)' % (fare['ChildPrice'], fare['ChildTax'])
        if infants:
            results += ', Infant:(Price:%s, Tax:%s)' % (fare['InfPrice'], fare['InfTax'])
    else:
        results += ', Infant:(Price:%s, Tax:%s)' % (fare['ChildPrice'], fare['ChildTax'])
    return results

def task_parser(task_content):
    try:
        infos = task_content.strip().split('&')
        dept_port, dest_port = infos[0], infos[1]
        dept_city = port_city.get(dept_port, dept_port)
        dest_city = port_city.get(dest_port, dest_port)
        dept_date = infos[2][:4] + '-' + infos[2][4:6] + '-' + infos[2][6:]
        dest_date = infos[3][:4] + '-' + infos[3][4:6] + '-' + infos[3][6:]
    except Exception:
        raise parser_except.ParserException(parser_except.TASK_ERROR, "CtripRoundFlight::任务解析失败")
    try:
        dept_info = suggestion['ctrip'][dept_city]
        dest_info = suggestion['ctrip'][dest_city]
        dept_city = dept_info['city_en_name']
        dest_city = dest_info['city_en_name']
    except Exception:
        raise parser_except.ParserException(51, "用三字码无法从网站拿到 suggestion")
    return dept_city, dest_city, dept_info, dest_info, dept_date, dest_date


def ctripRound_request_parser(content):
    result = -1
    return result


def get_post_data(html_text):
    condition = re.search("condition\s*=\s*'([^']+)'", html_text).group(1)
    try:
        condition = json.loads(condition.decode('latin-1').encode('utf8'))
    except:
        condition = json.loads(condition)

    if condition is None:
        raise parser_except.ParserException(parser_except.DATA_NONE, 'ctripRound::未获取需要的 condition')

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
    while v1 > 30:
        v1 %= 10
    pat_process2 = re.compile(regexp_t.format(var=v2_name), re.S)
    process2 = pat_process2.findall(html_text)
    for op, val in process2:
        to_eval = pat_eval.sub(r'\1(\3)*\2', val)
        v2 = op_dict[op](v2, int(eval(to_eval)))
    v2 = -v2 if v2 < 0 else v2
    while v2 > 30:
        v2 %= 10

    searchkey = list(searchkey)
    searchkey.insert(v1, searchkey.pop(v2))
    searchkey = ''.join(searchkey).encode()
    condition['SearchKey'] = searchkey
    condition = json.dumps(condition).replace(' ', '')
    # urllib.quote(condition, safe='()')
    # postdata = 'SearchMode=TokenSearch&condition={0}&DisplayMode=RoundTripGroup&SearchToken=1'.format(condition)
    return condition  # postdata
    # return postdata


if __name__ == '__main__':
    # from mioji.common.task_info import Task
    #
    # task = Task()
    # task.content = 'BJS&LAX&20170615&20170626'
    # task.source = 'ctripRoundFlight'
    #
    # print task_parser(task.content)
    import json

    info = json.load(open('/tmp/data'))
    print get_tickets(info, None, None)[0][7]
