#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17/1/20 上午9:36
# @Author  : sws
# @Site    : 
# @File    : hotellist_parse.py
# @Software: PyCharm

import datetime
import json
import sys
import urllib
import re

from mioji.common.class_common import Room
from mioji.common.logger import logger


currency_en = {'$': 'USD', '￥': 'CNY', '€': 'EUR', '£': 'GBP' }

def parse_hotelList_hotel(content):
    # print 222
    room = Room()
    room_list = []
    # print len(content)
    for co in content:
        try:
            hotel_url_raw = co['HL']

            room.source_hotelid = hotel_url_raw.split('/')[-3] + '/' + hotel_url_raw.split('/')[-2] + '/' + \
                                  hotel_url_raw.split('/')[-1]
            room.hotel_url = hotel_url_raw
        except Exception, e:
            print co
            logger.error('hoteltravel::name error ' + str(e))
            continue
        room_tuple = (room.source_hotelid, \
                      room.hotel_url)
        room_list.append(room_tuple)
    
    return room_list

def parse_hotelList_room(content, city, check_in, check_out, dur, occ, currency_rates):
    
    def currency_to_RMB(currency, price):
        """
            # 通过汇率表来完成对汇率的转换。
        """
        currency_price = 0
        
        for i in currency_rates:
            split_currency = i['value'].split('|')
            if split_currency[-1] == 'CN¥':
                print split_currency[1], '*'*100
                rmb = float(split_currency[1])
            if split_currency[0] == currency:
                print split_currency[1], '+'*100
                
                currency_price = float(split_currency[1])
        
        # 汇率表中都是对美元汇率
        price_to_rmb = float(price) / float(currency_price) * float(rmb)
        print 'price_to_rmb is {0}'.format(price_to_rmb)
        return price_to_rmb

    room = Room()
    room_list = []
    if not content:
        return room_list
    
    for co in content:
        try:
            room.hotel_name = co['HN'].encode('utf-8')
            print room.hotel_name
            room.source = 'hoteltravel'
            hotel_url_raw = co['HL'].encode('utf-8')
            hotel_name_raw = hotel_url_raw.split('/')[-1]
            room.source_hotelid = hotel_url_raw.split('/')[-3] + '/' + hotel_url_raw.split('/')[-2] + '/' + \
                                  hotel_url_raw.split('/')[-1]
        except Exception, e:
            logger.error('hoteltravel::name error' + str(e))
            pass

        room.city = city

        try:
            if co['hFD'].find('Restaurant') == -1:
                room.has_breakfast = 'Yes'
            else:
                room.has_breakfast = 'No'
            room.is_breakfast_free = 'No'

        except Exception, e:
            logger.error('hoteltravel::breakfast info error ' + str(e))
            pass
        room.check_in = str(check_in)[:10].replace('/', '-')
        room.check_out = str(check_out)[:10].replace('/', '-')
        try:
            room.is_extrabed = 'No'
            room.is_extrabed_free = 'No'
            room.price = str(float(co['CRR']) * float(dur))
        except Exception, e:
            try:
                room.is_extrabed = 'No'
                room.is_extrabed_free = 'No'
                price_info = co['CWH']
                price_pat = re.compile(r'(\d+.?\d+)')
                price = price_pat.findall(price_info)[0]
                room.price = float(price)
                for cu in currency_en.keys():
                    if cu in price_info:
                        room.currency = currency_en[cu]
                        break
                else:
                    continue

            except:
                logger.error('price error' + str(e))
                continue
        # print room.price
        try:
            price_info = co['CWH']
            print price_info
            for cu in currency_en.keys():
                if cu in price_info.encode('utf-8'):
                    print cu, '+++'
                    room.currency = currency_en[cu]
                    break
            else:
                continue
        except Exception as e:
            import traceback
            traceback.print_exc(e)
            logger.error('hoteltravel::currrnncy info error ' + str(e))
            continue

        if room.currency != 'CNY':
            # 货币转换成RMB
            try:
                price_to_rmb = currency_to_RMB(room.currency, room.price)
            except:
                # 如果没有在汇率表中找到对应的汇率，跳过
                continue
            if price_to_rmb:
                room.price = price_to_rmb
                room.currency = 'CNY'
        # print room.price
        # print room.currency

        try:
            room.room_desc = 'NULL'
            room.room_type = co['ADPRNB']
            room.real_source = 'hoteltravel'
        except Exception, e:
            logger.error('hoteltravel:: desc img error' + str(e))
            pass
        room.hotel_url = co['HL']
        room.occupancy = occ
        room_tuple = (
            room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, room.real_source,
            room.room_type, room.occupancy, room.bed_type, room.size, room.floor, room.check_in, room.check_out,
            room.rest,
            room.price, room.tax, room.currency, room.pay_method, room.is_extrabed, room.is_extrabed_free,
            room.has_breakfast, room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
            room.change_rule, room.room_desc, room.others_info, room.guest_info, room.hotel_url)
        room_list.append(room_tuple)
    print 33, room_list
    return room_list
