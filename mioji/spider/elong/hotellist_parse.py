#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月27日

@author: dujun
'''

import re
import json
from mioji.common.class_common import Room
from mioji.common.func_log import func_time_logger

room_dict = {1: '单人间', 2: '双人间', 3: '三人间', 4: '四人间'}

@func_time_logger
def parse_hotels_hotel(content):
    rooms = []
    try:
        print type(content)
        room = Room()
        # content = json.loads(content)
        for tree in content['hotelList']:
            room.source_hotelid = tree['hotelId']
            room.hotel_url = 'http://ihotel.elong.com/' + tree['hotelId'] + '/'
            # room.source = 'elong'
            # room.city = mioji_city_id
            # hotelLowestPrice 还需要处理等于None的时候
            if tree['hotelLowestPrice'] == '0' or tree['hotelLowestPrice'] is None:
                room.rest = -10
                # room_tuple = (room.source, room.source_hotelid, \
                #               room.hotel_url, room.city)
                # rooms.append(room_tuple)
                room_tuple = (room.source_hotelid, \
                              room.hotel_url)
                rooms.append(room_tuple)
                continue

            room_tuple = (room.source_hotelid, \
                          room.hotel_url)
            rooms.append(room_tuple)
    except Exception as e:
        print str(e)

    return rooms

def parse_hotels_room(hotel_id, content, check_in,  check_out, nights, person_num, city):
    rooms = []
    try:
        print type(content)
        
        # content = json.loads(content)
        for tree in content['hotelList']:
            room = Room()
            room.check_in = str(check_in)[:10].replace('/', '-')
            room.check_out = str(check_out)[:10].replace('/', '-')
            room.source_hotelid = tree['hotelId']
            room.hotel_url = 'http://ihotel.elong.com/' + tree['hotelId'] + '/'
            room.source = 'elong'
            room.real_source = 'elong'
            room.room_type = room_dict[int(person_num)]
            room.occupancy = person_num
            room.currency = 'CNY'
            room.hotel_name = tree['hotelNameCn']
            room.city = city
            room.others_info = tree['district']
            # hotelLowestPrice 还需要处理等于None的时候
            if tree['hotelLowestPrice'] == '0' or tree['hotelLowestPrice'] is None:
                continue
            room.price = tree['hotelLowestPrice']  # tree['promotionInfo'][0]['originPrice']
            # print room.price
            room.price = float(room.price) * float(nights)
	    if int(room.price) <= 0:
	    	continue
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                          room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                          room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                          room.rest, room.price, room.tax, room.currency, room.pay_method, \
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
    except Exception as e:
        print str(e)
    # print rooms[0]
    return rooms
