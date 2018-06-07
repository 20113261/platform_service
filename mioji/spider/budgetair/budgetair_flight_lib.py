#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年03月30日

@author: hourong
"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
from mioji.common import parser_except
from mioji.common.class_common import Flight

cabin_dict = {'E': 'Y', 'B': 'B', 'F': 'F', 'P': 'Y'}
seat_type_dict = {'Economy': '经济舱', 'Premium Economy': '经济舱'}
class_dict = {'Economy': 'E', 'Business': 'B', 'First': 'F', 'Premium Economy': 'E'}


def parse_task(task_content):
    task_content = task_content.encode('utf-8')
    try:
        task_list = task_content.split('&')
        dept_id, dest_id, dept_day = task_list[0], task_list[1], task_list[2]
        if len(task_list) > 3:
            person_age_list = task_list[5].split('_')
            person_nu = int(task_list[3])
            cabin_class = cabin_dict[task_list[4]]
            infant_nu, child_nu, adult_nu = (0, 0, 0)
            try:
                for i in range(person_nu):
                    if (float(person_age_list[i]) == -1) or (float(person_age_list[i]) > 11):
                        adult_nu += 1
                    elif float(person_age_list[i]) >= 2:
                        child_nu += 1
                    else:
                        infant_nu += 1
            except Exception, e:
                # logger.error('adult_nu, child_nu, infant_nu获取have errors %s' % e)
                pass
        else:
            infant_nu, child_nu, adult_nu = (0, 0, 1)
            cabin_class = 'Y'
    except Exception, e:
        raise parser_except.ParserException(parser_except.PROXY_INVALID, "ctrip_multi::代理错误，未抓回数据")

    dept_day_url = dept_day
    return {
        'dept_id': dept_id,
        'dest_id': dest_id,
        'dept_day': dept_day,
        'dept_day_url': dept_day_url,
        'adult_nu': adult_nu,
        'child_nu': child_nu,
        'infant_nu': infant_nu,
        'cabin_class': cabin_class
    }


def get_dur(dur):
    """
    1240==>12h40m===>12*3600+40*60
    """
    H = dur[:2]
    M = dur[2:]
    dur = int(H) * 3600 + int(M) * 60
    return dur


def parser_page(root, dept_day, child_nu, adult_nu, infant_nu, dept_id, dest_id, **kwargs):
    flight = Flight()
    tickets = []

    root0 = root['_embedded']['Options']
    flight_info = root0
    for each in flight_info:
        each_info = each['OutboundOptions']
        for ele in each_info:
            dur = get_dur(ele['Duration'])
            dept_time = ele['DepartureDateTime']
            dest_time = ele['ArrivalDateTime']
            dept_day = dept_time[:dept_time.find('T')]
            stop = ele['NrOfStops']
            stop_info = ele['SegmentOptions']
            stop = len(stop_info) - 1
            rest = ele['NrOfSeatsAvailable']
            if rest is None:
                rest = -1
            elif rest == 0:
                rest = 9
            else:
                pass
            stop_time, stop_id, flight_no = '', '', ''
            plane_type, flight_corp, seat_type = '', '', ''
            real_class, daydiff = '', ''
            for ele_stop in stop_info:
                stop_time += '|' + ele_stop['DepartureDateTime'] + '_' + ele_stop['ArrivalDateTime']
                try:
                    seat_type += '_' + seat_type_dict[ele_stop['Class']]
                except:
                    seat_type += '_' + ele_stop['Class']

                try:
                    plane_type += '_' + ele_stop['Plane']
                except:
                    plane_type += '_' + 'NULL'
                stop_id += '|' + ele_stop['Departure']['Code'] + '_' + ele_stop['Arrival']['Code']
                # print "Class: %s"% ele_stop['Class']
                real_class += '_' + class_dict[ele_stop['Class'].strip()]
                try:  # 有时候会取到None type
                    flight_no += '_' + ele_stop['Carrier']['Code'].strip() + ele_stop['FlightNumber']
                except:
                    flight_no += '_' + ele_stop['FlightNumber']
                try:
                    flight_corp += '_' + ele_stop['Carrier']['DisplayName'].strip()
                except:
                    flight_corp += '_' + "NULL"
            daydiff_list = stop_time[1:].split('|')
            for ele_daydiff in daydiff_list:
                list = ele_daydiff.split('_')
                if list[0][:list[0].find('T')] == list[-1][:list[-1].find('T')]:
                    daydiff += '_' + '0'
                else:
                    daydiff += '_' + '1'

            price_info = each['Fares'][0]
            currency = price_info['CurrencyCode']
            all_price = price_info['PaxFares']
            for ele_price in all_price:
                ticket_type = ele_price['PaxType']
                price = ele_price['TicketPrice']
                tax = ele_price['AirportTax']

                flight.rest = rest
                flight.currency = currency
                flight.price = price
                flight.tax = tax
                flight.source = 'budgetair::budgetair'
                flight.daydiff = daydiff[1:]
                flight.flight_no = flight_no[1:]
                flight.real_class = real_class[1:]
                flight.stop_id = stop_id[1:]
                flight.plane_type = plane_type[1:]
                flight.seat_type = seat_type[1:]
                flight.stop_time = stop_time[1:]
                flight.dept_id = dept_id
                flight.dest_id = dest_id
                flight.dur = dur
                flight.dept_time = dept_time
                flight.dest_time = dest_time
                flight.stop = stop
                flight.dept_day = dept_day
                flight_tuple = flight.to_tuple()
                tickets.append(flight_tuple)
    return tickets
