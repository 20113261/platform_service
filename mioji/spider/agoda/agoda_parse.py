#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月27日

@author: dujun
'''

import re
import json
import sys
import traceback
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.class_common import Room
from mioji.common import parser_except
from lxml import html as HTML
from lxml import etree
import time
from mioji.common.logger import logger
import re

deltag = re.compile(r"<[^>]+>", re.S) # 删掉退改规则标签


def new_parse_page(page, days, check_in, check_out, adult, cid):
    logger.info("进入新的解析")
    rooms = []
    mioji_hotel_info = Room()
    tree = HTML.fromstring(page, parser=etree.HTMLParser(encoding='utf-8'))
    try:
        hotel_id = tree.xpath('//section[@id="recommended-properties-container"]/script/text()')[0]
        hotel_id = int(re.findall('hotelId: (.*?),', hotel_id, re.S)[0])
    except:
        raise parser_except.ParserException(29, "未找到酒店id，现情况为无房")
    try:
        masterRooms = re.findall('masterRooms:(.*),', page)[0]
    except:
        raise parser_except.ParserException(29, "未解析到masterRooms")
    mioji_hotel_info.source_hotelid = hotel_id
    mioji_hotel_info.source = 'agoda'
    mioji_hotel_info.real_source = 'agoda'
    mioji_hotel_info.hotel_name = tree.xpath(
        "//title/text()")[0].split('-')[0].encode('utf8')
    mioji_hotel_info.city = cid
    page_num = len(masterRooms)
    if page_num == 0:
        raise parser_except.ParserException(29, "无此房型")
    masterRooms = json.loads(masterRooms)
    try:
        for rooms_info in masterRooms:
            mioji_hotel_info.room_type = rooms_info['name']
            # mioji_hotel_info.occupancy = rooms_info['maxOccupancyInGroup']
            mioji_hotel_info.source_roomid = rooms_info['id']
            try:
                mioji_hotel_info.bed_type = rooms_info['bedConfigurationSummary']['title']
            except:
                mioji_hotel_info.bed_type = rooms_info['name']

            size = [i['title'] for i in rooms_info['features'] if i['symbol'] == "ficon-sqm"]

            try:
                if len(size):
                    mioji_hotel_info.size = re.match(r'[0-9]+', size[0].strip()).group(0)
                    print "房间面积：", mioji_hotel_info.size
            except:
                mioji_hotel_info.size = -1
            mioji_hotel_info.floor = -1
            mioji_hotel_info.check_in = check_in
            mioji_hotel_info.check_out = check_out
            for room_info in rooms_info['groupRoom']:
                for room in room_info['rooms']:
                    mioji_hotel_info.occupancy = room['adults']
                    mioji_hotel_info.price = room['totalPrice']['display']
                    mioji_hotel_info.rest = room['availability']
                    mioji_hotel_info.currency = room['currency']
                    mioji_hotel_info.tax = 0.0
                    mioji_hotel_info.pay_method = '在线支付'

                    #解析加床政策
                    try:
                        desc_info = room['extraBedMessage']
                        desc_info = re.findall(r"[\x80-\xff]+[A-Z]*[0-9]*", desc_info)
                        desc_info = ''.join(desc_info)

                        desc_info_str = re.findall(r'(【.*)', desc_info)[0]
                        # print desc_info_str
                        # 此处正则匹配的汉字为utf8下的，加床费每晚单价为RMB0
                        is_extrabed_free = re.findall(
                            r'[\x80-\xff]*[A-Z]+[0-9]+', desc_info)[0]
                        # print is_extrabed_free
                        is_extrabed_free_num = re.findall(
                            r'[0-9]+', is_extrabed_free)[0]
                        # print 'is_extrabed_free_num', is_extrabed_free_num
                        if is_extrabed_free_num == 0:
                            mioji_hotel_info.is_extrabed_free = 'Yes'
                        else:
                            mioji_hotel_info.is_extrabed_free = 'No'
                    except:
                        # 加床政策解析，没解到
                        desc_info_str = ''
                        mioji_hotel_info.is_extrabed_free = 'No'

                    is_extrabed = room['isBlockCustomerToModifyExtrabeds']
                    if is_extrabed == False:
                        mioji_hotel_info.is_extrabed = 'Yes'
                    else:
                        mioji_hotel_info.is_extrabed = 'No'

                    features = room['features']
                    mioji_hotel_info.is_breakfast_free = 'No'
                    mioji_hotel_info.is_cancel_free = 'No'
                    for i in features:
                        if i['type'] == 0:
                            mioji_hotel_info.has_breakfast = 'Yes'
                            mioji_hotel_info.is_breakfast_free = 'Yes'
                        if i['type'] == 5:
                            if i['title'] == u"取消政策":
                                mioji_hotel_info.is_cancel_free = 'Yes'
                            else:
                                mioji_hotel_info.is_cancel_free = 'NULL'
                            mioji_hotel_info.return_rule = i['description']
                            mioji_hotel_info.change_rule = i['description']
                            # mioji_hotel_info.change_rule = ''.join(
                            #     re.findall(r"[\x80-\xff]+[A-Z]*[0-9]*", change_rule))
                        if i['type'] == 3:
                            mioji_hotel_info.pay_method = "到店支付"

                        if i['type'] == 4:
                            mioji_hotel_info.pay_method = "支付方式"

                    if mioji_hotel_info.pay_method == '':
                        mioji_hotel_info.pay_method = '在线支付'


                    mioji_hotel_info.extrabed_rule = desc_info
                    taxesAndSurcharges = room['taxesAndSurcharges']['title']
                    mioji_hotel_info.room_desc = str(
                        taxesAndSurcharges) + '|' + desc_info_str
                    mioji_hotel_info.others_info = json.dumps({
                        "extra":{
                            'breakfast': "包含早餐" if mioji_hotel_info.has_breakfast == 'Yes' else "",
                            'payment': mioji_hotel_info.pay_method,
                            'return_rule': mioji_hotel_info.return_rule,
                            'occ_des': room_info['rooms'][0]['occupancyMessage']
,
                        }
                    })
                    mioji_hotel_info.guest_info = 'NULL'
                    if mioji_hotel_info.size != -1:
                        mioji_hotel_info.room_desc = mioji_hotel_info.room_desc + '|房间面积：' + mioji_hotel_info.size
                    room = mioji_hotel_info
                    roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                                 room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                                 room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                                 room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                                 room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                                 room.change_rule, room.room_desc, room.others_info, room.guest_info)
                    rooms.append(roomtuple)
    except:
        print traceback.format_exc()

    return rooms


def parse_page(page, days, check_in, check_out, adult, cid):

    print '进入解析'
    try:
        rooms = []
        mioji_hotel_info = Room()
        tree = HTML.fromstring(page, parser=etree.HTMLParser(encoding='utf-8'))
        # hotel_name  #hotelname 输出中文异常
        true = 'True'
        false = 'False'
        null = 'None'
        isDataReady = 'isDataReady'
        filters = 'filters'
        masterRooms = 'masterRooms'
        taxesAndSurcharges = 'taxesAndSurcharges'
        try:
            hotel_id = tree.xpath('//section[@id="recommended-properties-container"]/script/text()')[0]
            hotel_id = int(re.findall('hotelId: (.*?),', hotel_id, re.S)[0])
        except:
            raise parser_except.ParserException(29, "未找到酒店id，现情况为无房")
        try:
            masterRooms = re.findall('masterRooms:(.*),',page)[0]
        except:
            raise parser_except.ParserException(29, "未解析到masterRooms")
        mioji_hotel_info.source_hotelid = hotel_id
        mioji_hotel_info.source = 'agoda'
        mioji_hotel_info.real_source = 'agoda'
        mioji_hotel_info.hotel_name = tree.xpath(
            "//title/text()")[0].split('-')[0].encode('utf8')
        mioji_hotel_info.city = cid
        # room_info
        page_num = len(masterRooms)
        if page_num == 0:
            raise parser_except.ParserException(29, "无此房型")
        masterRooms = json.loads(masterRooms)
        try:
            for rooms_info in masterRooms:
                # try:
                # agoda_hotelId_info = rooms_info['roomThumbnail']['src'].split('/')
                # except:
                #     print "这个人无用的东西又导致了错误"
                mioji_hotel_info.room_type = rooms_info['name']
                # mioji_hotel_info.occupancy = rooms_info['maxOccupancyInGroup']
                mioji_hotel_info.source_roomid = str(rooms_info['id'])

                try:
                    mioji_hotel_info.bed_type = rooms_info['bedConfigurationSummary']['title']
                except:
                    mioji_hotel_info.bed_type = rooms_info['name']


                size = [i['title'] for i in rooms_info['features'] if i['symbol'] == "ficon-sqm"]
                try:
                    if len(size):
                        mioji_hotel_info.size = re.match(r'[0-9]+',size[0].strip()).group(0)
                        print "房间面积：",mioji_hotel_info.size
                except:
                    mioji_hotel_info.size = -1
                mioji_hotel_info.floor = -1
                mioji_hotel_info.check_in = check_in
                mioji_hotel_info.check_out = check_out
                for room_info in rooms_info['rooms']:
                    mioji_hotel_info.occupancy = room_info['adults']
                    mioji_hotel_info.rest = room_info['availability']
                    mioji_hotel_info.price = room_info['totalPrice']['display']
                    # try:
                    #     for i in room_info['taxesAndSurchargesList']:
                    #         if len(i) == 5 or len(i) == 6:
                    #             tax = re.search(r'[0-9]+', i).group()
                    #             tax = int(tax)
                    #             mioji_hotel_info.tax = mioji_hotel_info.price * tax * 0.01
                    #         elif '税' in i or 'Tax' in i:
                    #             tax = re.search(r'[0-9]+', i).group()
                    #             tax = int(tax)
                    #             mioji_hotel_info.tax = tax
                    # except:
                    mioji_hotel_info.tax = 0.0
                    # import pdb
                    # pdb.set_trace()
                    mioji_hotel_info.currency = room_info['currency']
                    mioji_hotel_info.pay_method = '在线支付'
                    # 此为加床政策和重要提醒
                    try:
                        # "<strong> 加床费每晚单价为RMB0</strong><br><br>【重要提示】如入住人数超过客房限制，0岁及以上客人必须使用加床。",
                        desc_info = room_info['extraBedMessage']
                        desc_info = re.findall(r"[\x80-\xff]+[A-Z]*[0-9]*", desc_info)
                        desc_info = ''.join(desc_info)
                        # print desc_info
                        # [重要提示] 如入住人数超过客房限制，0岁及以上客人必须使用加床。"
                        desc_info_str = re.findall(r'(【.*)', desc_info)[0]
                        # print desc_info_str
                        # 此处正则匹配的汉字为utf8下的，加床费每晚单价为RMB0
                        is_extrabed_free = re.findall(
                            r'[\x80-\xff]*[A-Z]+[0-9]+', desc_info)[0]
                        # print is_extrabed_free
                        is_extrabed_free_num = re.findall(
                            r'[0-9]+', is_extrabed_free)[0]
                        # print 'is_extrabed_free_num', is_extrabed_free_num
                        if is_extrabed_free_num == 0:
                            mioji_hotel_info.is_extrabed_free = 'Yes'
                        else:
                            mioji_hotel_info.is_extrabed_free = 'No'
                    except:
                        # 加床政策解析，没解到
                        desc_info_str = ''
                        mioji_hotel_info.is_extrabed_free = 'No'
                    is_extrabed = room_info['isBlockCustomerToModifyExtrabeds']
                    if is_extrabed == false:
                        mioji_hotel_info.is_extrabed = 'Yes'
                    else:
                        mioji_hotel_info.is_extrabed = 'No'
                    features = room_info['features']
                    mioji_hotel_info.has_breakfast = 'No'
                    mioji_hotel_info.is_breakfast_free = 'No'
                    mioji_hotel_info.is_cancel_free = 'No'
                    pay_method = ""
                    for i in features:
                        if i['type'] == 0:
                            mioji_hotel_info.has_breakfast = 'Yes'
                            mioji_hotel_info.is_breakfast_free = 'Yes'
                        if i['type'] == 5:
                            if u'不可退款' in i['title']:
                                mioji_hotel_info.is_cancel_free = 'No'
                            else: # xxx日之前取消，详情存在otherinfo
                                mioji_hotel_info.is_cancel_free = 'NULL'
                            description = deltag.sub('', i['description'])
                            mioji_hotel_info.return_rule = description
                            mioji_hotel_info.change_rule = description  # 获取取消详情
                            # mioji_hotel_info.change_rule = ''.join(
                            #     re.findall(r"[\x80-\xff]+[A-Z]*[0-9]*", change_rule))
                        if i['type'] == 3:
                            mioji_hotel_info.pay_method = "到店支付"

                        if i['type'] == 4:
                            if i['title']:
                                mioji_hotel_info.pay_method = "在线支付"

                                pay_method = i['title']
                            else:
                                mioji_hotel_info.pay_method = "支付方式"


                        
                    if mioji_hotel_info.pay_method == '':
                        mioji_hotel_info.pay_method = '在线支付'
                    mioji_hotel_info.extrabed_rule = desc_info
                    taxesAndSurcharges = room_info['taxesAndSurcharges']['title']
                    mioji_hotel_info.room_desc = str(
                        taxesAndSurcharges) + '|' + desc_info_str

                    if pay_method:
                        mioji_hotel_info.others_info = json.dumps({
                            "extra": {
                                'breakfast': "包含早餐" if mioji_hotel_info.has_breakfast == 'Yes' else "",
                                'payment': pay_method,
                                'return_rule': mioji_hotel_info.return_rule,
                                'occ_des': room_info['occupancyMessage']
                            }
                        })
                    else:
                        mioji_hotel_info.others_info = json.dumps({
                            "extra": {
                                'breakfast': "包含早餐" if mioji_hotel_info.has_breakfast == 'Yes' else "",
                                'payment': mioji_hotel_info.pay_method,
                                'return_rule': mioji_hotel_info.return_rule,
                                'occ_des': room_info['occupancyMessage']
                            }
                        })


                    mioji_hotel_info.guest_info = 'NULL'
                    if mioji_hotel_info.size != -1:
                        mioji_hotel_info.room_desc = mioji_hotel_info.room_desc + '|房间面积：' + mioji_hotel_info.size
                    room = mioji_hotel_info
                    roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                                 room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                                 room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                                 room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                                 room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                                 room.change_rule, room.room_desc, room.others_info, room.guest_info)
                    rooms.append(roomtuple)
        except Exception as e:
            print traceback.format_exc()
    except Exception as e:
        print traceback.format_exc()
    print "程序结束"
    if not rooms:
        rooms = new_parse_page(page, days, check_in, check_out, adult, cid)
    # if not rooms:
    #     rooms = num1_parse_page(page, days, check_in, check_out, adult, cid)
    return rooms

# def num1_parse_page(page, days, check_in, check_out, adult, cid)