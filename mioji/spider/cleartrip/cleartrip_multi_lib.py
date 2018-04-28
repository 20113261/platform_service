#!/usr/bin/env python
# encoding:utf-8

"""
Created on 2017年04月05日

@author: dongkai
"""

import datetime
import re
import time

import cleartrip_city_name_spider
from mioji.common.airline_common import Airline
from mioji.common.class_common import MultiFlight
from mioji.common.task_info import Task
from utils import seat_type_to_queryparam

cabin_dict_cn = {
    'E': '经济舱',
    'B': '商务舱',
    'F': '头等舱',
    'P': '超级经济舱'
}


def get_city_name(mj_city_id):
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = Task('cleartrip::cleartrip', mj_city_id)
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    city_info = spider.result['City'][0].get('v', '')
    return city_info


def multitrip_base_params(mj_task_class):
    """
    """
    task_content = mj_task_class.content
    ticket_info = mj_task_class.ticket_info
    mj_cabin = ticket_info.get('v_seat_type', 'E')

    content1 = task_content.split('|')[0]
    content2 = task_content.split('|')[1]
    dept_id_0, dest_id_0, deptdate0 = content1.split('&')
    dept_id_1, dest_id_1, deptdate1 = content2.split('&')

    ret = {
        "trip_type": "MultiCity",
        "type": "json",
        "ver": "V2",
        "multicity": True,
        # "cc": 1
           }

    ret["sd"] = format(time.time() * 1000, '.0f')
    ret["adults"] = ticket_info.get('adults', 2)
    ret["childs"] = ticket_info.get('childs', 0)
    ret["infants"] = ticket_info.get('infants', 0)
    ret["class"] = seat_type_to_queryparam(mj_cabin)
    ret["intl"] = "y"
    ret["num_legs"] = 2  # mioji multi support 2 legs

    # ret["origin1"] = get_city_name(dept_id_0)
    ret["from1"] = dept_id_0
    # ret["destination1"] = get_city_name(dest_id_0)
    ret["to1"] = dest_id_0
    ret["depart_date_1"] = "{0}/{1}/{2}".format(deptdate0[6:8],
                                                deptdate0[4:6],
                                                deptdate0[0:4])

    # ret["origin2"] = get_city_name(dept_id_1)
    ret["from2"] = dept_id_1
    # ret["destination2"] = get_city_name(dest_id_1)
    ret["to2"] = dest_id_1
    ret["depart_date_2"] = "{0}/{1}/{2}".format(deptdate1[6:8],
                                                deptdate1[4:6],
                                                deptdate1[0:4])
    ret['timeout'] = 3000

    return ret



def parse_content(data, adult):
    tickets = []
    fare = data['fare']
    mapping = data['mapping']['onward']
    content = data['content']
    currency = data['jsons']['searchType']['disp_currency']
    for ticket in mapping:
        multiflight = MultiFlight()
        index = ticket['f']
        code_info = ticket['c']
        # 获得fare的具体信息
        fare_info = fare[index]
        fare_key = fare_info['dfd']
        fare_info = fare_info[fare_key]
        price = fare_info['pr']
        flight_no = ''
        stop_id = ''
        stop_time = ''
        real_class = ''
        for trip in code_info:
            every_flight_no_res = ''
            every_stop_time = ''
            every_stop_id = ''
            every_real_class = ''
            for every_code in trip:
                detail_info = content[every_code]
                fk_tmp_info = detail_info['fk'].split('_')
                each_dept_date = fk_tmp_info[-3]
                each_dept_time = fk_tmp_info[-2]
                each_real_class = cabin_dict_cn[fk_tmp_info[-1]]
                each_flight_no = fk_tmp_info[-4]
                each_dest_date = detail_info['ad']
                each_dest_time = detail_info['a']
                each_dur = detail_info['dr']
                each_stop_id = detail_info['fr'] + '_' + detail_info['to']
                each_time = each_dept_date[4:8] + '-' + each_dept_date[2:4] + '-' + each_dept_date[
                                                                                    :2] + 'T' + each_dept_time + ':00' + '_' + \
                            each_dest_date.split('/')[2] + '-' + each_dest_date.split(
                    '/')[1] + '-' + each_dest_date.split('/')[0] + 'T' + each_dest_time + ':00'
                every_real_class += each_real_class + '_'
                every_flight_no_res += each_flight_no + '_'
                every_stop_id += each_stop_id + '|'
                every_stop_time += each_time + '|'
            real_class += every_real_class.rstrip('_') + '&'
            flight_no += every_flight_no_res.rstrip('_') + '&'
            stop_id += every_stop_id.rstrip('|') + '&'
            stop_time += every_stop_time.rstrip('|') + '&'
        real_class = real_class.rstrip('&')
        flight_no = flight_no.rstrip('&')
        stop_id = stop_id.rstrip('&')
        stop_time = stop_time.rstrip('&')
        multiflight.flight_no = flight_no.replace('-', '')
        multiflight.stop_id = stop_id
        multiflight.stop_time = stop_time
        multiflight.real_class = real_class
        multiflight.price = float(price / int(adult))
        multiflight.tax = 0
        multiflight.currency = currency
        multiflight.source = 'cleartrip::cleartrip'
        dept, dest = multiflight.stop_id.split('&')
        dept_id_0 = dept.split('_')[0]
        dest_id_0 = dept.split('_')[-1]
        dept_id_1 = dest.split('_')[0]
        dest_id_1 = dest.split('_')[-1]
        multiflight.dept_id = dept_id_0 + '&' + dept_id_1
        multiflight.dest_id = dest_id_0 + '&' + dest_id_1
        multiflight.dept_day = '&'.join(map(lambda x: x.split('_')[0].split(
            'T')[0], multiflight.stop_time.split('&'))).encode('utf-8')
        multiflight.dept_time = '&'.join(map(lambda x: x.split(
            '_')[0], multiflight.stop_time.split('&'))).encode('utf-8')
        multiflight.dest_time = '&'.join(map(lambda x: x.split(
            '_')[-1], multiflight.stop_time.split('&'))).encode('utf-8')
        flight_corp = re.sub('[\d\-]+', '', multiflight.flight_no)
        multiflight.flight_corp = re.sub(
            r'[A-Z]+', lambda x: Airline.get(x.group(), x.group()), flight_corp)
        multiflight.plane_type = re.sub(
            r'[\d\-A-Z]+', 'NULL', multiflight.flight_no)
        multiflight.seat_type = multiflight.real_class
        multiflight.daydiff = re.sub(r'[\d:T\-_]+', lambda x: str(
            (datetime.datetime.strptime(x.group().split('_')[1], '%Y-%m-%dT%H:%M:%S') -
             datetime.datetime.strptime(x.group().split('_')[0], '%Y-%m-%dT%H:%M:%S')).days),
                                     multiflight.stop_time).replace('|', '_')

        multiflight.return_rule = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.change_rule = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.baggage = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.ticket_type = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.others_info = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.stopby = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.stop = '&'.join(str(x.count('_'))
                                    for x in multiflight.daydiff.split('&'))
        multiflight.transit_visa = re.sub(
            '[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.reimbursement = re.sub(
            '[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.package = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.share_flight = re.sub(
            '[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.promotion = re.sub('[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.flight_meals = re.sub(
            '[\d_]+', 'NULL', multiflight.daydiff)
        multiflight.dur = re.sub(r'[\d:T\-_\|]+', lambda x: str((datetime.datetime.strptime(x.group().split('_')[-1],
                                                                                            '%Y-%m-%dT%H:%M:%S') - datetime.datetime.strptime(
            x.group().split('_')[0], '%Y-%m-%dT%H:%M:%S')
                                                                 ).days * 24 * 3600 + (
                                                                    datetime.datetime.strptime(x.group().split('_')[-1],
                                                                                               '%Y-%m-%dT%H:%M:%S') - datetime.datetime.strptime(
                                                                        x.group().split('_')[0],
                                                                        '%Y-%m-%dT%H:%M:%S')).seconds),
                                 multiflight.stop_time)

        tickets.append(multiflight.to_tuple())
    return tickets
