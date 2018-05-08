#!usr/bin/env python
# coding=UTF-8
'''
	@author: corazon(Peibo Xu)
	@date: 2015-11-17
    @update: 2017-04-13
    @update author: dongkai
	@desc:
		cheapAirParser
'''

import re
import time
import urllib
import json
import time
import traceback
import itertools
from datetime import datetime

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()

# from cleartrip_city_name_spider import ClearTripCityNameSpider
from cheapair_name_spider import CheapairCityNameSpider
from mioji.common import parser_except
from mioji.common.task_info import Task
from mioji.common.class_common import Flight
from mioji.common.airline_common import Airline

month = {'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04', 'MAY': '05', 'JUN': '06',
         'JUL': '07', 'AUG': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'}


cabin = {'F': '头等舱', 'C': '商务舱', 'W': '超级经济舱', 'Y': '经济舱'}


def build_search_args(task_info):
    """
    """
    dept_id = task_info["dept_id"]
    dest_id = task_info["dest_id"]
    dept_date = convert_date(task_info["dept_date"])

    airport_spider = CheapairCityNameSpider()
    dept_task = Task("cheapair:cheapair", dept_id)
    dest_task = Task("cheapair:cheapair", dest_id)

    airport_spider.task = dept_task
    airport_spider.crawl(
        cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dept_info = airport_spider.city_info
    dept_loc = dept_info[0]["LocID"]

    airport_spider.task = dest_task
    airport_spider.crawl(
        cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    dest_info = airport_spider.city_info
    dest_loc = dest_info[0]["LocID"]

    query_args = {"legs": [{"date": dept_date,
                            "fromLocId": dept_loc,
                            "toLocId": dest_loc}
                           ],
                  "numpax": "10000", # 单个成人
                  "cabinRequested": "Y", # 仓位
                  "filters": {"timeFilters": [],
                              "selectedFlights": [],
                              "airlineView": "YY",
                              "maxStops": -1,
                              "airportsToExclude": [[]],
                              "alliances": []},
                  "legNum": 1,
                  "refundableOnly": False,
                  "getAdUnits": ["ASR"],
                  "condenseResponse": True,
                  "searchId": -1}
    args = {"legNum": 1,
            "_": str(int(time.time() * 1000)),
            "queryparams": json.dumps(query_args),
            # "queryparams": query_args,
            }

    return args


def convert_date(mj_date):
    """
    convert mioji date to %Y-%m-%d
    """
    dept_datetime = datetime.strptime(mj_date, "%Y%m%d")
    # %F = %Y-%m-%d
    return dept_datetime.strftime("%F")


def convert_task(task_content, ticket_info):
    """
    """
    content_list = task_content.split("&")
    task_info = {"dept_id": content_list[0],
                 "dest_id": content_list[1],
                 "dept_date": content_list[2],
                 "cabin": ticket_info.get("cabin", "Y"),
                 "adults": ticket_info.get("adult", "1")
                 }
    return task_info


def search_json_parse(page_json):
    """
    """
    tickets = []
    source = "cheapair::cheapair"
    flights = page_json["flights"]

    currency = 'USD'
    for flight_info in flights:
        flight = Flight()
        flight_no = []
        flight_aircorp = []
        stop_id1 = []
        stop_time1 = []
        plane_type = []
        seat_type = []
        daydiff = []
        for segment_info in flight_info['segments']:
            flight_no.append(
                segment_info['airlineCode'] + str(segment_info['flightNumber']))
            flight_aircorp.append(
                segment_info['airlineName'] if segment_info.has_key('airlineName') else 'NULL')
            stop_id1.append(
                segment_info['fromCode'] + '_' + segment_info['toCode'])
            plane_type.append(segment_info['aircraftTypeName'] if segment_info.has_key(
                'aircraftTypeName') else 'NULL')
            stop_dept_time1 = segment_info['departs'].split(' ')
            stop_dest_time1 = segment_info['arrives'].split(' ')
            stop_time1.append('T'.join(stop_dept_time1) +
                              '_' + 'T'.join(stop_dest_time1))
            seat_type.append(segment_info['cabinSeatString'])
            daydiff.append(str(segment_info['dayChange']))
        flight.seat_type = '_'.join(seat_type)
        flight.stop = flight_info['numStops']
        flight.price = flight_info['fares'][0]['baseFare']
        flight.tax = flight_info['fares'][0]['tax']
        flight.flight_no = '_'.join(flight_no)
        flight.flight_corp = '_'.join(flight_aircorp)
        flight.plane_type = '_'.join(plane_type)
        flight.dept_id = flight_info['segments'][0]['fromCode']
        flight.dest_id = flight_info['segments'][-1]['toCode']
        flight.dept_day = flight_info['segments'][0]['departs'][:10]
        dept_time_info = flight_info['segments'][0]['departs'].split(' ')
        dest_time_info = flight_info['segments'][-1]['arrives'].split(' ')
        flight.dept_time = 'T'.join(dept_time_info)
        flight.dest_time = 'T'.join(dest_time_info)
        flight.currency = currency
        flight.dur = int(flight_info['duration']) * 60
        flight.stop_id = '|'.join(stop_id1)
        flight.stop_time = '|'.join(stop_time1)
        flight_daydiff = '_'.join(daydiff)
        flight.source = source
        flight.real_class = '_'.join(seat_type)
        flight_tuple = (
            flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id, flight.dest_id, flight.dept_day,
            flight.dept_time, flight.dest_time, flight.dur, flight.rest, flight.price, flight.tax, flight.surcharge,
            flight.promotion, flight.currency, flight.seat_type, flight.real_class, flight.package, flight.stop_id,
            flight.stop_time, flight.daydiff, flight.source, flight.return_rule, flight.change_rule, flight.stop,
            flight.share_flight, flight.stopby, flight.baggage, flight.transit_visa, flight.reimbursement,
            flight.flight_meals, flight.ticket_type, flight.others_info
        )
        tickets.append(flight_tuple)
    return tickets
