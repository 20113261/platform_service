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
        map_info_dict = dict(zip(map(lambda x: unicode(x), content['searchResults']['allHotelIds']),
                                 map(lambda x: u"{0},{1}".format(x[0], x[1]),
                                     content['searchResults']['allHotelCoords'])))
    except Exception as e:
        print str(e)
    # for keys,values in content.items():
    #     print keys,":",values
    #     if isinstance(values,dict):
    #         print "打印是字典的值"
    #         for key,value in values.items():
    #             print key,"---",value
    # for key_dict in content['searchResults']['retailHotelModels'][0:1]:
    #     for key,value in key_dict.items():
    #         print "key:",key,"value:",value
    #     print "*"*100
    # for keys,value in content['searchResults']['retailHotelModels'][0]['retailHotelPricingModel'].items():
    #     print "keys:",keys,"^^^^^","value:",value
    # for keys,value in content['searchResults']['retailHotelModels'][0]['ugcModel'].items():
    #     print "k:::",keys,"::::::","v:::",value
    #Tree = content['results']
    # for tree in Tree:
    #     room = Room()
    #     #room.source_hotelid = tree['retailHotelInfoModel']['hotelId']
    #
    #     #room.hotel_url = tree['infositeUrl']
    #
    #
    #     room_tuple = (room.source_hotelid, \
    #                   room.hotel_url)
    #     rooms.append(room_tuple)
    tree = content['searchResults']
    for i in xrange(len(tree['retailHotelModels'])):
        room = Room()
        room.source_hotelid = tree['retailHotelModels'][i]['hotelId']
        room.hotel_url = tree['retailHotelModels'][i]['infositeUrl']
        room_tuple = (room.source_hotelid,room.hotel_url)
        rooms.append(room_tuple)

    rooms = list(set(rooms))
    print len(rooms), "len(rooms)", '-' * 50
    return rooms

@func_time_logger
def parse_hotels_room(content, city, check_in, nights, check_out, person_num):
    rooms = []
    try:
        map_info_dict = dict(zip(map(lambda x: unicode(x), content['searchResults']['allHotelIds']),
                                 map(lambda x: u"{0},{1}".format(x[0], x[1]),
                                     content['searchResults']['allHotelCoords'])))
        print "allHotelIds:",content['searchResults']['allHotelIds']
        print "allHotelCorrds",content['searchResults']['allHotelCorrds']
    except Exception as e:
        print str(e)

    '''
    for tree in Tree:
        room = Room()
        room.source_hotelid = tree['retailHotelInfoModel']['hotelId']
        room.check_in = str(check_in)[:10].replace('/', '-')
        room.check_out = str(check_out)[:10].replace('/', '-')
        room.source = 'expedia'
        room.real_source = 'expedia'
        room.city = city
        room.hotel_url = tree['infositeUrl']
        retailPricing = tree['retailHotelPricingModel']
        if not retailPricing.has_key(u'priceFormatted'):
            priceWithoutFormatted = "未抓取到价格"
        else:
            priceWithoutFormatted = retailPricing['priceFormatted']
        #priceWithoutFormatted = retailPricing[u'priceFormatted']  #  网页发生变化，原来格式化的价格现在不是格式化的，前面还有价格符号
        try:
            price = re.search(r'[0-9,]+', priceWithoutFormatted).group()  # 这里的price是格式化之后的
        except Exception, e:
            price = ''

        others_info = {}
        try:
            others_info['drrMessage'] = retailPricing['drrMessage']
        except:
            pass
        try:
            others_info['map_info'] = map_info_dict[room.source_hotelid]
        except:
            pass
        room.others_info = json.dumps(others_info)
        room.room_desc = tree['retailHotelInfoModel']['hotelDescription']
        # currency_str = retailPricing['currencySymbol']
        # 原来单独的价格符号没有了，现在从非格式化的价格中获取价格符号
        currency_str = re.match(r'(\D*)', priceWithoutFormatted).group()
        if currency_str == 'HK$':
            currency = 'HKD'
        else:
            currency = currency_str
        room.currency = currency
        if room.currency == '-' or room.currency == None:
	    currency = 'HKD'
        retailInfo = tree['retailHotelInfoModel']  #
        try:
            hotel_name_cn = retailInfo['localizedHotelName']
        except Exception, e:
            hotel_name_cn = retailInfo['hotelName']
        room.hotel_name = hotel_name_cn
        if price == '':
            room.price = -1
            room.rest = -10
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                          room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                          room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                          room.rest, room.price, room.tax, room.currency, room.pay_method, \
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
            continue
        if ',' in price:
            price = price.replace(',', '')
        try:
            rest = retailInfo['numberOfRoomsLeftForUrgencyMsg']
            if int(rest) == 0:
                rest = -1
        except Exception, e:
            rest = -1
        room.rest = rest
        room.price = float(price) * float(nights)
        room.room_type = room_dict[int(person_num)]
        room.occupancy = person_num
        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                      room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                      room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                      room.rest, room.price, room.tax, room.currency, room.pay_method, \
                      room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                      room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                      room.others_info, room.guest_info, room.hotel_url)
        rooms.append(room_tuple)
    rooms = list(set(rooms))
    print len(rooms), "len(rooms)", '-' * 50
    return rooms
    '''
    tree = content['searchResults']
    for i in xrange(len(tree['retailHotelModels'])):
        room = Room()
        room.source_hotelid = tree['retailHotelModels'][i]['hotelId']
        room.hotel_url = tree['retailHotelModels'][i]['infositeUrl']
        #print len(tree['retailHotelModels']), len(tree['allHotelIds']), len(set(tree['allHotelIds']))
        # room_tuple = (room.source_hotelid, room.hotel_url)
        # append多了一次！
        # rooms.append(room_tuple)
        room.check_in = str(check_in)[:10].replace('/', '-')
        room.check_out = str(check_out)[:10].replace('/', '-')
        room.source = 'expedia'
        room.real_source = 'expedia'
        room.city = city
        room.hotel_url = tree['retailHotelModels'][i]['infositeUrl']
        retailPricing = tree['retailHotelModels'][i]['retailHotelPricingModel']
        if not retailPricing.has_key(u'priceFormatted'):
            priceWithoutFormatted = "-1"
        else:
            priceWithoutFormatted = retailPricing['priceFormatted']
        try:
            price = re.search(r'[0-9,]+', priceWithoutFormatted).group()  # 这里的price是格式化之后的
        except Exception, e:
            price = ''

        others_info = {}
        try:
            if retailPricing.has_key('drrMessage'):
                others_info['drrMessage'] = retailPricing['drrMessage']
            else:
                others_info['drrMessage'] = ''
        except:
            pass
        try:
            others_info['map_info'] = map_info_dict[room.source_hotelid]
        except:
            pass
        room.others_info = json.dumps(others_info)
        #room.room_desc = tree['retailHotelModels'][i]['hotelDescription']
        room.room_desc = ''
        # currency_str = retailPricing['currencySymbol']
        # 原来单独的价格符号没有了，现在从非格式化的价格中获取价格符号
        currency_str = re.match(r'(\D*)', priceWithoutFormatted).group()
        if currency_str == 'HK$':
            currency = 'HKD'
        else:
            currency = currency_str
        room.currency = currency
        retailInfo = tree['retailHotelModels'][i]  #
        try:
            hotel_name_cn = retailInfo['retailHotelInfoModel']['localizedHotelName']
        except Exception, e:
            hotel_name_cn = retailInfo['ugcModel']['hotelName']
        room.hotel_name = hotel_name_cn
        if room.currency == '-' or room.currency == None:
            continue
        if price == '':
            room.price = -1
            room.rest = -10
            room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                          room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                          room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                          room.rest, room.price, room.tax, room.currency, room.pay_method, \
                          room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                          room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                          room.others_info, room.guest_info, room.hotel_url)
            rooms.append(room_tuple)
            continue
        if ',' in price:
            price = price.replace(',', '')
        try:
            rest = retailInfo['retailHotelInfoModel']['numberOfRoomsLeftForUrgencyMsg']
            if int(rest) == 0:
                # 不表示无房，表示剩余充足
                rest = 9
        except Exception, e:
            rest = -1
        room.rest = rest
        room.price = float(price) * float(nights)
        room.room_type = room_dict[int(person_num)]
        room.occupancy = person_num
        if room.currency == '-' or room.currency == None:
            continue
        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                      room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                      room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                      room.rest, room.price, room.tax, room.currency, room.pay_method, \
                      room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                      room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                      room.others_info, room.guest_info, room.hotel_url)
        rooms.append(room_tuple)
    rooms = list(set(rooms))
    return rooms
