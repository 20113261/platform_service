#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17/1/20 上午11:36
# @Author  : sws
# @Site    : 
# @File    : hotellist_parse.py
# @Software: PyCharm

import datetime
import json
import sys
import urllib
import re
import time

from mioji.common.class_common import Room
from mioji.common.logger import logger


def re_format_time(current_time, current_format, new_format):
    '''
        用于时间格式转换
        参数分别是要转换的时间，转换之前的格式，转换之后的格式
        eg：2014-10-01 %Y-%m-%d --> %d-%m-%Y
        转换之后的格式为 01/10/2014
    '''
    new_time = ''
    current_time = current_time.strip()
    try:
        time_temp = time.strptime(current_time, current_format)
        new_time = time.strftime(new_format, time_temp)
    except Exception, e:
        print e
        # traceback.print_exc(e)
        return new_time
    return new_time


def parse_hotels_hotel(roomdata):
    rooms = []
    try:
        json_rooms = roomdata
        for jr in json_rooms['ResultList']:
            room = Room()
            room.source_hotelid = jr['HotelID']
            room.hotel_url = 'https://www.agoda.com'+jr['HotelUrl']
            room_tuple = (room.source_hotelid, \
                          room.hotel_url)
            rooms.append(room_tuple)
        return rooms
    except Exception, e:
        # import traceback
        # traceback.print_exc(str(e))
        logger.error("agodaListHotel :: get_json_rooms. Error! %s" % e)

def parse_hotels_room(city_name, roomdata):
    rooms = []
    import json
    # print json.dumps(roomdata, ensure_ascii=False)
    # print '%$'*20, city_name,'^'*20,roomdata
    try:
        json_rooms = roomdata
        if json_rooms['SearchCriteria']['CheckInCultureDateText']:
            check_in = json_rooms['SearchCriteria']['CheckInCultureDateText'].split('/')
            check_in = check_in[0] + '-' + check_in[1] + '-' + check_in[2]
            check_in = re_format_time(''.join(check_in.split('-')), '%Y%m%d', '%Y-%m-%d')
            check_out = json_rooms['SearchCriteria']['CheckOutCultureDateText'].split('/')
            check_out = check_out[0] + '-' + check_out[1] + '-' + check_out[2]
            check_out = re_format_time(''.join(check_out.split('-')), '%Y%m%d', '%Y-%m-%d')
        elif json_rooms['SearchCriteria']['CheckIn']:
            check_in = json_rooms['SearchCriteria']['CheckIn'].split('-')
            check_in = check_in[0] + '-' + check_in[1] + '-' + check_in[2][:2]
            check_in = re_format_time(''.join(check_in.split('-')), '%Y%m%d', '%Y-%m-%d')
            check_out = json_rooms['SearchCriteria']['CheckOut'].split('-')
            check_out = check_out[0] + '-' + check_out[1] + '-' + check_out[2][:2]
            check_out = re_format_time(''.join(check_out.split('-')), '%Y%m%d', '%Y-%m-%d')
        for jr in json_rooms['ResultList']:
            # print '&*'*20,jr
            room = Room()
            # room.city = jr['CityName']
            room.city = city_name
            room.check_in = check_in
            room.check_out = check_out
            room.occupancy = json_rooms['SearchCriteria']['Adults']
            #print '$#'*20,room.occupancy
            room.source_hotelid = jr['HotelID']
            room.hotel_url = 'https://www.agoda.com' + jr['HotelUrl']            
            room.source = 'agoda'
            room.real_source = 'agoda'
            room.hotel_name = jr['FormattedDisplayPrice']
            room.room_type = 'NULL'
            # room.room_type = jr['HotelRoomTypeName'] if jr['HotelRoomTypeName'] else "NULL"
            # print 'roomtype:::::::',jr['HotelRoomTypeName']
            price = jr['FormattedDisplayPrice']
            #print 'price:AAAAA',price
            if price != None:
                price = price.replace(',', '') if ',' in price else price
            else:
                continue
            print 'priceBBBBBB',price
            room.price = int(price)
            print jr['Currency'], '-'*10
            room.currency = jr['Currency']
            if room.currency == "RMB":
                room.currency = "CNY"
            else:
                room.currency = jr['CurrencyCode']
            # 免费餐食等
            free_tems = jr.get('Freebies', {}).get('FreebiesItem', [])
            # free 免费项
            others_info = {'free': []}
            for free in free_tems:
                others_info['free'].append(free.get('Name', None))
                #logger.info('agodaListHotel FreebiesItems:{0}'.format(free.get('Name', None)))
            room.others_info = json.dumps(others_info)

            room.rest = jr['RemainingRooms']
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                          room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                          room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                          room.pay_method, \
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
            # print '---------------->>>>>>>>>>>>',rooms
        return rooms
    except Exception, e:
        # import traceback
        # traceback.print_exc(str(e))
        logger.error("agodaListHotel :: get_json_rooms. Error! %s" % e)