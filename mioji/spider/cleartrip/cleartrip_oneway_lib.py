#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年04月05日

@author: dongkai
"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
import time
import urllib
import json
# from cleartrip_city_name_spider import ClearTripCityNameSpider
import cleartrip_city_name_spider
from datetime import datetime
from mioji.common import parser_except
from mioji.common.task_info import Task
from mioji.common.class_common import Flight
from mioji.common.airline_common import Airline
from utils import seat_type_to_queryparam

real_class_map = dict(E='经济舱', B='商务舱', F='头等舱')


def compute_day_diff(stop_datetimes):
    day_diffs = []
    for i in xrange(0, len(stop_datetimes), 2):
        if stop_datetimes[i].day == stop_datetimes[i + 1].day:
            day_diffs.append('0')
        else:
            day_diffs.append('1')
    return '_'.join(day_diffs)


def content_parser(task):
    try:
        task_content = task.content
        task_content_split = task_content.split('&')
        dept_id, dest_id, dept_day_str = task_content_split[:3]
        dept_datetime = datetime.strptime(dept_day_str, '%Y%m%d')
        task_dict = dict(dept_id=dept_id.strip(),
                         dest_id=dest_id.strip(), dept_datetime=dept_datetime)

        ticket_info = task.ticket_info
        task_dict['cabinclass'] = seat_type_to_queryparam(ticket_info.get('v_seat_type', 'E'))

        if not task_content_split[3:]:
            return task_dict

        cabin_class_map = dict(E='Economy')
        task_dict['cabinclass'] = cabin_class_map[task_content_split[4]]
        for age in task_content_split[5].split('_'):
            age = int(age)
            if age >= 18:
                task_dict['adults'] = task_dict.get('adults', 0) + 1
            elif age <= 2:
                task_dict['infants'] = task_dict.get('infants', 0) + 1
            else:
                task_dict['childs'] = task_dict.get('childs', 0) + 1
        return task_dict
    except Exception:
        raise parser_except.ParserException(parser_except.TASK_ERROR, 'cleartrip_oneway::代理错误，未抓回数据')


def get_referer_url(task_dict):
    dept_id = task_dict['dept_id']
    dest_id = task_dict['dest_id']
    dept_datetime = task_dict['dept_datetime']
    adults = task_dict.get('adults', 1)
    childs = task_dict.get('childs', 0)
    infants = task_dict.get('infants', 0)
    cabinclass = task_dict.get('cabinclass', 'Economy')
    dept_daystr = dept_datetime.strftime('%d/%m/%Y')
    timestamp = format(time.time() * 1000, '.0f')
    url_referer_t = 'https://www.cleartrip.sa/flights/international/results?from={dept_id}&to={dest_id}&depart_date={dept_daystr}&adults={adults}&childs={childs}&infants={infants}&class={cabinclass}&airline=&carrier=&intl=y&sd={timestamp}'.format(
        **locals())

    return url_referer_t


def get_json_url(task_dict):
    url_intlairjson0_t = 'https://www.cleartrip.sa/flights/results/intlairjson?trip_type=OneWay&origin={dept_city}&from={dept_id}&destination={dest_city}&to={dest_id}&depart_date={dept_daystr}&adults={adults}&childs={childs}&infants={infants}&class={cabinclass}&airline=&carrier=&ver=V2&type=json&intl=y&sd={timestamp}&page=&search_ver=V2&cc=1&rhc=1'

    dept_id = task_dict['dept_id']
    dest_id = task_dict['dest_id']
    dept_datetime = task_dict['dept_datetime']
    adults = task_dict.get('adults', 1)
    childs = task_dict.get('childs', 0)
    infants = task_dict.get('infants', 0)
    cabinclass = task_dict.get('cabinclass', 'Economy')
    dept_daystr = dept_datetime.strftime('%d/%m/%Y')

    timestamp = format(time.time() * 1000, '.0f')

    task = Task('cleartrip::cleartrip', dept_id)
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = task
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dept_city_unescaped = spider.result['City'][0].get('v', '')
    dept_city = urllib.quote_plus(dept_city_unescaped, safe='()')
    task = Task('cleartrip::cleartrip', dest_id)
    spider = cleartrip_city_name_spider.ClearTripCityNameSpider()
    spider.task = task
    spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dest_city_unescaped = spider.result['City'][0].get('v', '')
    dest_city = urllib.quote_plus(dest_city_unescaped, safe='()')
    #dept_daystr = dept_datetime.strftime('%d%%2F%m%%2F%Y')
    dept_daystr = dept_datetime.strftime('%d/%m/%Y')
    url_intlairjson0 = url_intlairjson0_t.format(**locals())

    return url_intlairjson0, dest_city, dept_city


def process_contents(contents_raw):
    contents = {}
    for content_i, content_r in contents_raw.iteritems():
        content = contents[content_i] = {}
        content['dur'] = content_r['dr']
        content['from'] = content_r['fr']
        content['to'] = content_r['to']
        s_datestr = re.search('\d{8}_\d{2}:\d{2}', content_r['fk']).group()
        content['s_datetime'] = datetime.strptime(s_datestr, '%d%m%Y_%H:%M')
        e_datestr = content_r['ad'] + content_r['a']
        content['e_datetime'] = datetime.strptime(e_datestr, '%d/%m/%Y%H:%M')
        content['flight_no'] = re.search('[a-zA-Z0-9]+-\d+', content_r['fk']).group()
        try:
            content['flight_corp'] = Airline[re.search('[a-zA-Z0-9]+', content['flight_no']).group()]
        except:
            content['flight_corp'] = re.search('[a-zA-Z0-9]+', content['flight_no']).group()
        content['type'] = content_r['fk'][-1]
    return contents


def page_parser(page_dict):
    contents_raw = page_dict['content']
    contents = process_contents(contents_raw)
    fare = page_dict['fare']
    currency = page_dict['jsons']['searchType']['disp_currency']

    flight_tuples = []
    for mapping in page_dict['mapping']['onward']:
        flight = Flight()
        flight_nos = []
        plane_types = []
        flight_corps = []
        durs = []
        seat_types = []
        real_classes = []
        stop_ids = []
        stop_datetimes = []
        ticket_i = mapping['f']
        for content_i in mapping['c'][0]:

            content = contents[content_i]

            flight_nos.append(content['flight_no'].replace('-', ''))
            plane_types.append('NULL')

            flight_corps.append(content['flight_corp'])

            durs.append(content['dur'])

            real_classes.append(real_class_map[content['type']])
            if real_class_map[content['type']] == '经济舱':
                seat_types.append('E')
            elif real_class_map[content['type']] == '商务舱':
                seat_types.append('B')
            elif real_class_map[content['type']] == '头等舱':
                seat_types.append('P')
            else:
                seat_types.append('NULL')

            stop_ids.append(content['from'])
            stop_ids.append(content['to'])
            stop_datetimes.append(content['s_datetime'])
            stop_datetimes.append(content['e_datetime'])

        stop_times = [x.strftime('%Y-%m-%dT%H:%M:%S') for x in stop_datetimes]
        daydiff = compute_day_diff(stop_datetimes)

        flight.flight_no = '_'.join(flight_nos)
        flight.plane_type = '_'.join(plane_types)
        flight.flight_corp = '_'.join(flight_corps)
        flight.dept_id = stop_ids[0]
        flight.dest_id = stop_ids[-1]
        flight.dept_day = stop_datetimes[0].strftime('%Y-%m-%d')
        flight.dept_time = stop_times[0]
        flight.dest_time = stop_times[-1]
        flight.dur = sum(map(int, durs))
        flight.price = fare[ticket_i][fare[ticket_i]['dfd']]['pr']
        flight.tax = 0
        flight.currency = currency
        flight.seat_type = '_'.join(seat_types)
        flight.real_class = '_'.join(real_classes)
        flight.seat_type = flight.real_class
        flight.stop_id = '|'.join('%s_%s' % tuple(stop_ids[i:i + 2]) for i in xrange(0, len(stop_ids), 2))
        flight.stop_time = '|'.join('%s_%s' % tuple(stop_times[i:i + 2]) for i in xrange(0, len(stop_times), 2))
        flight.daydiff = daydiff
        flight.source = 'cleartrip::cleartrip'
        flight.stop = len(flight_nos) - 1

        flight_tuple = (flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id, \
                        flight.dest_id, flight.dept_day, flight.dept_time, flight.dest_time, flight.dur, \
                        flight.rest, flight.price, flight.tax, flight.surcharge, flight.promotion, flight.currency, \
                        flight.seat_type, flight.real_class, flight.package, flight.stop_id, flight.stop_time, \
                        flight.daydiff, flight.source, flight.return_rule, flight.change_rule, flight.stop, \
                        flight.share_flight, flight.stopby, flight.baggage, flight.transit_visa, \
                        flight.reimbursement, flight.flight_meals, flight.ticket_type, flight.others_info)
        flight_tuples.append(flight_tuple)

    return flight_tuples


if __name__ == '__main__':
    task_dict = content_parser('TXL&PEK&20170415')
    print get_referer_url(task_dict)
    print get_json_url(task_dict)
