#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月27日

@author: dujun
'''

import re, json
from mioji.common.logger import logger
from mioji.common.class_common import Room
from mioji.common.func_log import func_time_logger

num_pat = re.compile(r'(\d+)', re.S)
occ_pat = re.compile(r'最多(.*?)人入住', re.S)
room_dict = {1: '单人间', 2: '双人间', 3: '三人间', 4: '四人间'}


@func_time_logger
def parse_hotels_room(dom, check_in, check_out, night, person_num, city):
    rooms = []
    cont = 0
    try:
        total_num = dom.find_class('sr_header')[0].xpath('./h1/text()')[0]
        total_num = total_num.split('共')[1].split('家')[0].replace(',', '').strip()
        total_num = int(total_num.replace(',',''))
        print total_num
    except Exception as e:
        print e
        total_num = 15
    try:
        currency = dom.find_class('user_center_option')[1].xpath('./input/@value')[0]
    except Exception, e:
        logger.debug('parse currency 1 error:{0}'.format(e))
        print 'try...'
        try:
            currency = dom.find_class('user_center_option uc_currency')[0].xpath('./input/@value')[0]
        except Exception, e:
            logger.debug('parse currency 2 error:{0}'.format(e))
            currency = 'CNY'





    for tree in dom.find_class('sr_item sr_item_new'):
        #// *[ @ id = "hotellist_inner"] / div[2]
        room = Room()
        room.check_in = str(check_in)[:10].replace('/', '-')
        room.check_out = str(check_out)[:10].replace('/', '-')
        room.source_hotelid = str(tree.xpath('./@data-hotelid')[0])

        room.source = 'booking'
        room.real_source = 'booking'
        try:
            room.currency = str(currency)
        except:
            pass
        try:
            room.hotel_url = 'http://www.booking.com' + tree.find_class('hotel_name_link url')[0].xpath('./@href')[0]
            # print room.hotel_url, 'hhh'
        except:
            pass
        try:
            room.hotel_name = tree.find_class('sr-hotel__name')[0].xpath('./text()')[0].strip()
        except:
            pass
        room.room_type = room_dict[int(person_num)]
        try:
            room.room_type = tree.find_class('room_link')[0].xpath('./text()')[0].replace('\n', '')
        except:
            pass
        try:
            room.room_type = tree.find_class('b-recommended-room__title')[0].xpath('./text()')[0].replace('\n', '')
        except:
            pass
        try:
            dd = tree.find_class('sr_max_occupancy')[0].xpath('./i/@data-title')
            room.occupancy = occ_pat.findall(dd[0])[0]
        except:
            try:
                dd = occ_pat.findall(tree.find_class('occupancy-value')[0].xpath('./text()')[0].replace('\n', '').strip())
                room.occupancy = occ_pat.findall(dd[0])[0]
            except:
                try:
                    room.occupancy = \
                        occ_pat.findall(tree.find_class('sr_max_occupancy jq_tooltip')[0].xpath('./@data-title')[0])[0]
                except:
                    try:
                        room.occupancy = str(
                            len(tree.find_class('sr_max_occupancy')[0].find_class('occupancy_adults')[0].xpath('.//i')))
                    except:
                        room.occupancy = person_num
        nusm = 1
        try:
            nusm = num_pat.findall(tree.find_class('rooms-value')[0].xpath('./text()')[0].replace('\n', '').strip())[0]
        except:
            pass

        # free 免费项
        others_info = {'free': []}
        if room.room_type == '':
            room.room_type = room_dict[int(person_num)]
        try:
            reinforcement_list = tree.xpath('//*[@class="sr_room_reinforcement"]/text()')
            for rein in reinforcement_list:
                #logger.info('bookingListHotel reinforcement:{0}'.format(rein.strip()))
                others_info['free'].append(rein.strip())

            if '包括早餐' in reinforcement_list:
                room.has_breakfase = 'Yes'
                room.is_breakfast_free = 'Yes'
            room.others_info = json.dumps(others_info)
        except:
            pass
        try:
            ssw = tree.find_class('b-recommended-room__info-message-text')[0].xpath('./text()')[0]
            if '免费取消' in ssw:
                room.return_rule, room.is_cancel_free = ssw, 'Yes'
        except:
            pass
        try:
            sswx = tree.find_class('sr_room_reinforcement sr-free-canc-bg')[0].xpath('./text()')[0].replace('\n', '')
            if '免费取消' in sswx:
                room.return_rule, room.is_cancel_free = sswx, 'Yes'
        except:
            pass
            # print room.has_breakfast ,room.is_breakfast_free,room.return_rule
        try:
            room.rest = tree.find_class('num_left_hold')[0].xpath('./text()')[0]
        except:
            pass
        room.city = city
        try:
            
            price = ''.join(tree.xpath('.//strong[contains(@class, "price")]')[0].xpath('./b/text()')).replace('\n', '').replace(',', '').strip()
            print 'price:', price
            #print tree.xpath('.//strong[contains(@class, "price")][0]/b/text()')
            room.price = num_pat.findall(price)[0]

            # import pdb
            # pdb.set_trace()
        except Exception, e:
            logger.debug('parse price 1 error:{0}'.format(e))
            try:
                price = ''.join(tree.find_class('sr-prc--num sr-prc--final')[0].xpath('./text()')).replace(',','').strip()
                room.price = num_pat.findall(price)[0]
            except Exception, e:
                logger.debug('parse price 2 error:{0}'.format(e))
                try:
                    price_info = ''.join(tree.find_class('totalPrice')[0].xpath('./span/text()')).replace(',', '')
                    room.price = num_pat.findall(price_info)[-1]
                except Exception, e:
                    logger.debug('parse price 3 error:{0}'.format(e))
                    # 如果没有找到价格，
                    # import pdb
                    # pdb.set_trace() 
                    continue
                    
        if int(room.occupancy) < int(person_num):
            cont += 1
            continue
        if int(nusm) > 1:
            cont += 1
            continue

        room.tax = 0
        room_tuple = (
            str(room.hotel_name), str(room.city), str(room.source),
            str(room.source_hotelid), str(room.source_roomid),
            str(room.real_source), str(room.room_type), int(room.occupancy),
            str(room.bed_type), float(room.size), int(room.floor), str(room.check_in),
            str(room.check_out), int(room.rest), float(room.price), float(room.tax),
            str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free),
            str(room.has_breakfast), str(room.is_breakfast_free),
            str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule), str(room.change_rule),
            str(room.room_desc), str(room.others_info), str(room.guest_info), str(room.hotel_url)
            )
        if int(room.price) == 1:
            logger.debug('The hotel price is 1')

        # print '@@@@@@'*20, room.hotel_name, room.price
        # print '&*&*', room.hotel_name
        # print '%$%$', room.price
        rooms.append(room_tuple)
    if int(total_num) < len(rooms):
        print 'hotel is {0}'.format(len(rooms[:int(total_num)]))
        return rooms[:int(total_num)]
    else:
        print 'hotel is {0}'.format(len(rooms))
        return rooms

def parse_hotels_url(dom):
    hotel_list = []
    result = []
    try:
        total_num = dom.find_class('sr_header')[0].xpath('./h1/text()')[0]
        total_num = total_num.split('共')[1].split('家')[0]
        total_num = int(total_num.replace(',',''))
        print total_num
    except Exception as e:
        print e
        total_num = 15
    try:
        hotel_ele_list = dom.find_class('sr_item sr_item_new')
        if hotel_ele_list == []:
            return hotel_list
    except Exception, e:
        # logger.error('bookingCrawlParser :: no hotel parsed at this page. city_id : %s. error : %s ' % (city_id, str(e)))
        return hotel_list

    for each_hotel_ele in hotel_ele_list:
        try:
            hotel_id = each_hotel_ele.xpath('@data-hotelid')
            if hotel_id is None or hotel_id == []:
                continue
            try:
                hotel_url = 'http://www.booking.com' + each_hotel_ele.find_class('hotel_name_link url')[0].xpath('./@href')[0]
                # print hotel_url, 'xxx'
            except Exception, e:
                raise e
            result.append((str(hotel_id[0]), hotel_url))
        except Exception, e:
            import traceback
            print 'ss', traceback.format_exc()

    if int(total_num) < len(result):
        print 'hotel is {0}'.format(len(result[:int(total_num)]))
        return result[:int(total_num)]
    else:
        print 'hotel is {0}'.format(len(result))
        return result
