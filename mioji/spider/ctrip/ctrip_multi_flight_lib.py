#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mioji.common import parser_except
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

import re
import urllib
import operator
import json
from math import *
from mioji.common import parser_except
import mioji.common.suggestion as suggestion
from mioji.common.class_common import MultiFlight
from datetime import datetime
import traceback
# from ctrip_multiflight_validate_spider import CtripMultiFlightValidateSpider
from mioji.common.task_info import Task
from base_data import port_city

F_DEPT_ID = 'txtBeginCityCode{0}'
F_DEPT_NAME = 'txtBeginAddress{0}'
F_DEST_ID = 'txtEndCityCode{0}'
F_DEST_NAME = 'txtEndAddress{0}'
F_DEPT_DATE = 'txtDatePeriod{0}'

OD_PARAMS = [F_DEPT_ID, F_DEPT_NAME, F_DEST_ID, F_DEST_NAME, F_DEPT_DATE]


def port_to_city(task_content):
    template = '{}&{}&{}'
    sep = '|'
    result_list = list()
    for item in task_content.split('|'):
        port_from, port_to, date = item.split('&')
        result_list.append(template.format(port_city.get(port_from,port_from),
                                           port_city.get(port_to,port_to),
                                           date))
    return sep.join(result_list)

def create_multi_search_params(task):
    flight_no = task.ticket_info.get('flight_no', '')
    # if not flight_no:
    #     raise parser_except.ParserException(12, '验证航班必须提供航班号')
    params = {'FlightWay': 'M', 'Quantity': 1, 'ChildQuantity': 0,
              'InfantQuantity': 0, 'drpSubClass': 'Y_S', 'IsFavFull': '', 'mkt_header': ''}
    ods = []
    task.content = port_to_city(task.content)
    for od_str in task.content.split('|'):
        od = get_od_info(od_str)
        ods.append(od)

    ods.append(('', '', '', '', ''))

    for od_index, od in enumerate(ods):
        od_params_keys = [k.format(od_index + 1) for k in OD_PARAMS]
        for k, v in zip(od_params_keys, od):
            params[k] = v

    return params


def get_od_info(od_str):
    dept_id, dest_id, dept_date = od_str.split('&')
    dept_id, dest_id, dept_date = dept_id.lower(), dest_id.lower(), re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3',
                                                                           dept_date)
    dept_info, dest_info = get_city_no(dept_id.upper()), get_city_no(dest_id.upper())
    dept_id, dest_id = dept_info['city_id'], dest_info['city_id']
    dept_name, dest_name = dept_info['city_name'], dest_info['city_name']
    dept_name = urllib.quote(dept_name.decode('utf8').encode('gbk'))
    dest_name = urllib.quote(dest_name.decode('utf8').encode('gbk'))
    return dept_id, dept_name, dest_id, dest_name, dept_date


def get_city_no(city_id):
    if city_id in suggestion.suggestion['ctrip']:
        return suggestion.suggestion['ctrip'][city_id]


def get_promotion(tip):  # tips里面有几项就会在网页上显示几项。现在只爬第一项的。到但是
    __content = '特惠专享'
    if 'Type' in tip:
        if tip['Type'] == 'TEXT':
            __content = tip['Text']
        elif tip['Type'] == 'BUSS':
            __content = '商务优选'
        elif tip['Type'] == 'AIRLINE':
            __content = tip['Content'] + "（航空公司官网）"
        elif tip['Type'] == 'STU':
            __content = '留学生票'
        elif tip['Type'] == 'HUI':
            __content = tip['Text'] if 'Text' in tip else tip['Content']
        else:
            pass
    return __content


# ctrip 去重逻辑
def remove_duplicate(tickets):
    all_flights = {}
    for x in tickets:
        key = x[0] + '|' + x[13]
        if key not in all_flights:
            all_flights[key] = x
        elif all_flights[key][10] > x[10]:
            all_flights[key] = x
    ll = []
    for x in all_flights:
        ll += [all_flights[x]]
    return ll


# 携程航班号会在数字和航班号之前padding 0，这个func把添加的0去掉， MU088 -> MU88
def handle_flight_no(flight_no):
    ret = [flight_no[:2]]
    padding = True
    for i in range(2, len(flight_no)):
        if flight_no[i] == '0' and padding:
            pass
        else:
            padding = False
            ret.append(flight_no[i])
    return ''.join(ret)


def parse_flight(data, user_datas=None, fliter_func=lambda x: True):
    all_flights = []
    for node in data['FlightList']:
        # 航班信息
        flight = MultiFlight()
        flight.flight_no = []
        flight.plane_no = []
        flight.airline = []
        flight.share_flight = []
        dept_times = []
        dest_times = []
        dept_dest_id_list = []
        dept_dest_time_list = []
        day_diffs = []
        flight_corp = []
        CraftType = []
        for flightNode in node['FlightDetail']:
            flightNo = handle_flight_no(flightNode['FlightNo'])
            flight.flight_no.append(flightNo)
            # 共享航班
            if 'CarrierFlightNo' in flightNode:
                flight.share_flight.append(
                    handle_flight_no(flightNode['CarrierFlightNo']))
            else:
                flight.share_flight.append(flightNo)

            flight.airline.append(flightNode['AirlineCode'])

            flight.plane_no.append(flightNode['CraftType'])
            dept_time = datetime.strptime(
                flightNode['DepartTime'], '%Y-%m-%d %H:%M:%S')
            dept_times.append(str(dept_time).replace(' ', 'T', ))
            dest_time = datetime.strptime(
                flightNode['ArrivalTime'], '%Y-%m-%d %H:%M:%S')
            dest_times.append(str(dest_time).replace(' ', 'T', ))
            daydiff = '0'
            if str(dept_time)[0:10] != str(dest_time)[0:10]:
                daydiff = '1'
            day_diffs.append(daydiff)
            dept_dest_time_list.append(str(dept_time).replace(
                ' ', 'T', ) + '_' + str(dest_time).replace(' ', 'T', ))
            dept_dest_id_list.append(
                flightNode['DPort'] + '_' + flightNode['APort'])
            flight_corp.append(flightNode['AirlineName'])
            CraftType.append(flightNode['CraftType'])
        flight.plane_type = '_'.join(CraftType)
        flight.flight_corp = '_'.join(flight_corp)
        flight.stop = len(dept_dest_id_list) - 1
        flight.dept_id = dept_dest_id_list[0].split('_')[0]
        flight.dest_id = dept_dest_id_list[-1].split('_')[-1]
        flight.flight_no = '_'.join(flight.flight_no)

        flight.share_flight = '_'.join(flight.share_flight)
        if flight.flight_no == flight.share_flight:
            flight.share_flight = 'NULL'
        flight.airline = '_'.join(flight.airline)
        flight.plane_no = '_'.join(flight.plane_no)

        flight.dept_time = dept_times[0]
        flight.dest_time = dest_times[-1]
        flight.dept_day = flight.dept_time.split('T')[0]

        flight.dur = int(node["FlightTime"]) * 60
        flight.currency = "CNY"
        flight.source = "ctrip::ctrip"

        flight.stop_id = '|'.join(dept_dest_id_list)
        flight.stop_time = '|'.join(dept_dest_time_list)
        flight.daydiff = '_'.join(day_diffs)
        for i in range(len(node["FareList"])):
            ClassInfo = []
            try:
                ClassInfo.append(node["FareList"][i][
                                     "ClassName"].encode('utf-8'))
                ClassInfo *= flight.stop + 1
            except:
                for classInfo in node["FareList"][i]["ClassInfo"]:
                    ClassInfo.append(classInfo['ClassName'].encode('utf-8'))

            flight.seat_type = '_'.join(ClassInfo)
            try:
                flight.price = node['FareList'][i]["AdultPrice"]
                flight.tax = node['FareList'][i]["AdultTax"]
                adults, childs, infants = user_datas
                if childs > 0 or infants > 0:
                    flight.others_info = generate_other_infos(user_datas, node['FareList'][i])
                    # print flight.others_info
                # flight.price = node['FareList'][i]["Price"]
                # flight.tax = node['FareList'][i]["Tax"]
            except:
                flight.price = node['FareList'][i]["Price"]
                flight.tax = node['FareList'][i]["Tax"]
            flight.real_class = flight.seat_type

            if 'Tips' in node['FareList'][i]:
                flight.promotion = get_promotion(node['FareList'][i]['Tips'][0])

            if fliter_func(flight.flight_no):
                # 如果需要验证，则新生成验证爬虫，并进行抓取
                # try:
                #     remark = node['FareList'][i][
                #         'RebookRefund']['RemarkParameter']
                #     task = Task('ctripmultiFlightValidate', remark)
                #     spider = CtripMultiFlightValidateSpider()
                #     spider.task = task
                #     res, _ = spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
                #     flight.return_rule = flight.change_rule = res['Validate']
                # except:
                #     pass  # 拿不到信息不做处理
                flight_list = list(flight.to_tuple())
                flight_list.append(node["FareList"][i]["Parameter"])
                all_flights.append(tuple(flight_list))
                flight.seat_type = ''

    return all_flights


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


def get_filter(filter_key='flight_no', flight_no='', max_count=5):
    if filter_key == 'flight_no':
        return lambda x : x == flight_no
    elif filter_key == 'pre_request':
        current_count = [0]
        def counter_func(no_necessary_arg):
            current_count[0] += 1
            return current_count[0] <= max_count
        return counter_func
    else:
        return lambda x: True

if __name__ == '__main__':
    # from mioji.common.task_info import Task
    #
    # content = 'BJS&OSL&20170329|LIS&BJS&20170404'
    # task = Task('source', content)
    # print create_multi_search_params(task)
    # print u'\u5317'
    # import os
    # path = os.getcwd()
    # with open(path + '/tmp2.josn', 'r') as fd:
    #     data = json.load(fd)
    #     val = parse_flight(data, 'LH723_LH1754')
    #     print json.dumps(val, ensure_ascii=False)

    content = 'BJS&LON&20181117|MAN&BJS&20181124'
    task = Task('ctripmultiFlight', content)
    task.ticket_info = {'v_seat_type': 'F'}
    print create_multi_search_params(task)