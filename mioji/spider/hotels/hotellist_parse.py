#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月27日

@author: dujun
'''


import re
import json
import traceback
from mioji.common.class_common import Room
from mioji.common.func_log import func_time_logger

from lxml import html as HTML

room_dict = {1: '单人间', 2: '双人间', 3: '三人间', 4: '四人间'}

currency_en = {'$': 'USD', '￥': 'CNY', '€': 'EUR', '£': 'GBP', 'H': 'HKD'}

@func_time_logger
def parse_hotelList_hotel(content):
    rooms = []
    room = Room()
    # print 999, type(content)
    if 'searchResults' in str(content):
        page = content
        result_list = page['data']['body']['searchResults']['results']
    else:
        return rooms
    for res in result_list:
        room.hotel_name = res['name'].split('(')[0].strip()
        room.source_hotelid = res['id']

        room.hotel_url = 'http://zh.hotels.com' + res['urls']['pdpDescription']
        room_tuple = (room.source_hotelid, \
                      room.hotel_url)
        rooms.append(room_tuple)
    rooms = list(set(rooms))
    return rooms


@func_time_logger
def parse_hotelList_room(content, check_in, check_out, nights, person_num, city):

    rooms = []
    room = Room()
    print type(content), 'hh'*50
    if 'searchResults' in str(content):
        # page = json.loads(content[content.find('{'):-2])
        result_list = content['data']['body']['searchResults']['results']
        print len(result_list), 'result_list'
    else:
        return rooms

    try:
        for res in result_list:
            room.hotel_name = res['name'].split('(')[0].strip()
            room.source_hotelid = res['id']
            price = res.get('ratePlan', {}).get('price', {}).get('current', {})
            print price
            if ',' in price:
                price = price.replace(',', '')
            room.price = '-1'
            try:
                if not price[0].isdigit():

                    room.currency = currency_en[price[0].encode('utf8')]
                    if room.currency == 'HKD':
                        room.price = price[0][3:]
                    else:
                        room.price = price[0][1:]
                    room.price = price[3:]
                else:
                    room.currency = currency_en[price[-1].encode('utf8')]
                    room.price = price[:-1]
            except Exception as e:
                print traceback.format_exc(e)


            room.price = float(room.price) * float(nights)
            room.source = 'hotels'
            room.check_in = str(check_in)[:10].replace('/', '-')
            room.check_out = str(check_out)[:10].replace('/', '-')
            room.city = city
            room.room_type = room_dict[int(person_num)]
            room.occupancy = person_num
            if "specialDeal" in res['deals']:
                if '早餐' in res.get('deals', {}).get("specialDeal", []):
                    room.has_breakfast = 'Yes'
                    room.is_breakfast_free = 'Yes'
            if res.get('ratePlan', {}).get("features", {}).get('freeCancellation', None):
                room.return_rule = '免费取消'
            if res.get('ratePlan', {}).get("features", {}).get('paymentPreference', None):
                room.pay_method = '立即付款或到店付款'
            room.real_source = 'hotels'
            room.hotel_url = 'http://zh.hotels.com' + res.get('urls', {}).get("pdpDescription", '')
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                          room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                          room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                          room.rest, room.price, room.tax, room.currency, room.pay_method, \
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
        rooms = list(set(rooms))
    except Exception as e:
        print traceback.format_exc(e)

    return rooms

