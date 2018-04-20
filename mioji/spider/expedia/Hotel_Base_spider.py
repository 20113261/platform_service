#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''
from __future__  import division
from mioji.common.parser_except import ParserException
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common.logger import logger
setdefaultencoding_utf8()

from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
import re
import json
import time
from lxml import html as HTML
from mioji.common.class_common import Room
from mioji.common import parser_except

TASK_ERROR = 12
PROXY_NONE = 21
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
DATA_NONE = 24
UNKNOWN_TYPE = 25

availabilityErrors = {
    'defaultMessage':"22&&我们暂时无法搜索客房信息。请几分钟后再试一次。",
    'noRoomsAvailable':"29&&在您旅行期间，Expedia 智游网 上的客房已经订满。您可以选择新的日期，查看预订情况。",
    'roomsUnavailableForSelectedDates':"29&&在您旅行期间，Expedia 智游网 上的客房已经订满。您可以选择新的日期，查看预订情况。",
    'currencyChanged':"25&&因为酒店更改了他们的货币，我们无法更新您的预订。",
    'currencyCoversionFailed':"25&&真的很抱歉。我们无法转换该酒店的货币。请稍后再试一次。",
    'unavailableForCheckoutDate':"29&&该酒店在该时段不办理退房手续。请输入其他退房日期，或尝试附近的酒店。",
    'unavailableForCheckinDate':"29&&该酒店在该时段不办理入住手续。请输入其他入住日期，或尝试附近的酒店。",
    'minLimitOnNumberOfNights':"96&&延长住宿天数。该酒店对住宿天数有最低要求。更新天数以查看价格以及是否可以入住。",
    'limitOnMinimumLengthOfStay':"96&&延长住宿天数。该酒店对住宿天数有最低要求（未指定）。",
    'exceededNumberOfGuests':"29&&住客人数超出了房间能够接待的最大人数。",
    'onlyIndividualRoomBookingsAllowed':"29&&该酒店要求您每次预订一间房。",
    'maxLimitOnNumberOfNights':"96&&入住时间过长。减少晚数，或者尝试搜索附近的其他酒店。",
    'exceedsMaximumRooms': "29&&超过了最大预订房间数",
}




class BaseHotelSpider(Spider):
    # def __init__(self, task=None):
    #     Spider.__init__(self, task)
    #     self.cid = self.task.ticket_info.get('cid', None)

    def first_params(self):
        return {}

    def targets_request(self):

        self.setting()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            return {
                'req': {'url': self.urltmp, 'params': self.first_params()},
                'user_handler': [self.process_paging_url]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_room, new_session=self.api_newsession())
        def get_tickets_page():
            page_api = {
                'req': {
                    'url': self.json_url
                },
                'data': {'content_type': 'json'},
            }
            if hasattr(self, 'mc1'):
                page_api['req']['cookies'] = {'MC1': self.mc1}
            return page_api

        return [first_page, get_tickets_page]

    def process_paging_url(self, req, data):
        html_page = data
        self.html_page = data


        if 'infosite.token' not in html_page:
            raise ParserException(UNKNOWN_TYPE, '网站可能改版')
        else:
            token = re.findall(r"infosite.token = '(.+?)'", html_page)[0]
        # if re.findall(r"infosite.token = '(.+?)'", html_page)[0] is None:
        #     raise ParserException(22, '网页结构不对，重试吧')
        # else:
        # token = re.findall(r"infosite.token = '(.+?)'", html_page)[0]
        self.hotel_name = re.findall(r"infosite.hotelName =(.*?);", data, re.S)[0].strip()
        brandid = re.findall(r"infosite.hotelBrandId = '(\d+)'", html_page)[0]
        try:
            tla = re.search(r'infosite.tla = "([a-zA-Z]+)"', html_page).group(1)
        except AttributeError:
            tla = ""
        # self.guid = re.findall(r'GUID: "(.*?)"', html_page)[0]
        ts = str(int(time.time() * 10 ** 3))

        guest_params_str = ''
        temp_str = '&adults=' + str(self.occ) + '&children=' + str(self.children)
        for i in xrange(self.room_count):
            guest_params_str += temp_str

        url_json = self.json_url.format(
            self.source_id, token, brandid, self.check_in_new,
            self.check_out_new, ts, guest_params_str, tla)

        self.json_url = url_json

    def setting(self):
        pass

    def parse_hotel(self, req, data):
        pass

    def api_newsession(self):
        return False

    def parse_room(self, req, data):
        """ 将data中的信息拿出来， 如果有错误信息 根据data直接抛出对应的错误吗"""
        # data = data['offers']
        print 123
        logger.info("进入parser_room, availabilityErrors.keys:{0}".format(availabilityErrors))
        logger.info("data:{0}".format(data))
        
        for error in availabilityErrors.keys():
            if error in str(data):
                err_num = re.findall('(\d+)&&.*?', availabilityErrors[error])[0]
                err_str = re.findall("\d+&&(.+)", availabilityErrors[error])[0]
                logger.info("err_num: {0}{1}, err_str: {2}{3}".format(err_num, type(err_num), err_str, type(err_str)))
                raise ParserException(int(err_num), str(err_str))
                logger.info("err_num, err_str 格式正确")
        data = data['offers']

        expedia_room_parse = self.expedia_room_parse(self.html_page, data, self.source_id, self.city, self.check_in, self.check_out,
                                       self.dur, self.hotel_name, self.task_list, self.occ, self.cid)
        logger.info("expedia_room_parse: {0}".format(expedia_room_parse))
        return expedia_room_parse

    def expedia_room_parse(self, html_page, json_page, hotel_id, city, check_in, check_out, dur, hotel_name, task_list,
                           occ_info, cid):
        rooms = []
        result = {}
        result['para'] = {'room': rooms}
        result['error'] = 0

        source = 'expedia'
        real_source = 'expedia'
        check_in = check_in
        check_out = check_out
        hotel_name = hotel_name
        # for ed in City:
        #     if City[ed]['city_name_en'].lower == city.lower():
        #         city = City[ed]['city_name_zh']
        #         break
        source_hotelid = hotel_id
        try:
            room_desc_list = re.findall(r"var roomsAndRatePlans = (.*);", html_page)
            room_desc_list = json.loads(room_desc_list[0])
        except:
            result['error'] = 25
            return result
        tree = HTML.fromstring(html_page)
        # open('html_page', 'w').write(html_page)
        # img_urls
        try:
            img_urls = ''
            img_list = tree.xpath('//*[contains(@class, "hero xl")]/@src \
                                    |//*[contains(@class, "hero xl")]/@data-src')
            img_urls = '|'.join(['http:' + it for it in img_list])
            # print len(img_list)
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            img_urls = ''
        # review_nums
        # print img_urls
        try:
            review_nums = 0
            review_num_info = tree.xpath('//span[@itemprop="reviewCount"]/text()')[0].encode('utf-8')
            # print review_num_info
            review_nums = int(re.findall(r'(\d+)', review_num_info.replace(',', ''))[0])
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            review_nums = 0
        # print review_nums
        # check_in_time check_out_time
        try:
            check_in_time = check_out_time = ''
            check_in_list = tree.xpath('//*[@data-section="checkIn"]//text()')
            for cl in check_in_list:
                if u'入住时间开始于' in cl:
                    check_in_time = cl
                    break
            check_out_list = tree.xpath('//*[@data-section="checkOut"]//text()')
            for cl in check_out_list:
                if u'退房时间为' in cl:
                    check_out_time = cl
                    break
                    # print check_in_time, "check_in_time"
                    # print check_out_time, "check_out_time"
        except:
            pass
        try:
            hotel_name = self.clean_data(tree.xpath('//*[@id="hotel-name"]/text()')[0]).encode('utf-8')
        except:
            pass
        try:
            city = self.clean_data(re.findall(r"city: '(.*?)'", html_page)[0])
        except Exception, e:
            pass
        # print room_desc_list
        temp_room_desc_list = {}
        print room_desc_list['rooms']
        for _, rl in room_desc_list['rooms'].iteritems():
            temp_room_desc_list[rl['roomTypeCode']] = rl

        room_list = json_page
        for rl in room_list:
            # 空房间
            try:
                sold_out = rl['soldOut']
                if sold_out:
                    continue
            except:
                pass
            # 是否可以预定
            try:
                bookable = rl['bookable']
            except:
                continue
            room = Room()

            room.source = self.source
            room.real_source = self.source
            room.check_in = check_in
            room.check_out = check_out
            room.hotel_name = hotel_name
            room.source_hotelid = source_hotelid
            try:
                if rl['maxGuests'] > 0:
                    room.occupancy = rl['maxGuests']
                else:
                    room.occupancy = occ_info
            except:
                pass
            try:
                # 最后的总价格
                # 返回的是多间多晚的价格，在此除以房间数。因房间数不同，可能会对价格造成影响。
                task_num = int(self.task.ticket_info['room_info'][0]["num"])
                room.price = float(rl['totalPriceWithTaxesAndFees']['amount'] / task_num)
            except:
                pass
            try:
                room.currency = rl['totalPriceWithTaxesAndFees']['currency'].encode('utf-8')
                if room.currency == '-' or room.currency == None:
                    continue
            except:
                continue
                pass
            try:
                if rl['numberOfRoomsLeft'] > 0:
                    room.rest = rl['numberOfRoomsLeft']
            except:
                pass
            # 如果rl['refundable'] 不存在那么refundable就是''
            refundable = False
            try:
                refundable = rl['refundable']
            except:
                pass
            if refundable is False:
                room.is_cancel_free = "No".encode('utf-8')
                room.return_rule = room.change_rule = u'此特别折扣价不予退款。如果选择变更或取消此预订，不会退还任何款项。'.encode('utf-8')

            try:
                if rl['freeCancellable']:
                    room.is_cancel_free = 'NULL'.encode('utf-8')
                    return_rule = u'如果在 ' + rl['cancellationWindowDate'] + u" " + rl['cancellationWindowTime'] + u" (" + \
                                  rl['cancellationTimeZoneName'] + u"）之后取消或变更，或订房后未入住，则需支付等于预订付款总额的酒店费用。"
                    room.return_rule = room.change_rule = return_rule.encode('utf-8')
                else:
                    room.is_cancel_free = 'NULL'.encode('utf-8')
            except Exception, e:
                pass

            try:
                room_type_code = rl['roomTypeCode']
                temp_room_desc = temp_room_desc_list[room_type_code]
            except:
                pass
            try:
                room.room_desc = ''.join(self.clean_data(rd) for rd in temp_room_desc['description']).encode('utf-8')
                room.room_desc += "如果您预订的酒店已包含下面的收费项目，请忽视下面关于该项目的收费信息".encode('utf-8')
                room.room_desc += tree.xpath('//*[@id="policies-and-fees"]//*[@data-section="fees"]')[0].xpath('string(.)').encode(
                    'utf-8')  # 收费详情
            except:
                pass
            try:
                room.room_type = temp_room_desc['name'].encode('utf-8')
                if not room.room_type:
                    # 有可能room中房型name为空字符串，做个容错处理
                    room.room_type = rl['roomName']
            except:
                room.room_type = rl['roomName']
                pass
            try:
                room.size = int(temp_room_desc['roomSquareMeters'])
            except:
                pass
            try:
                room.bed_type = '||'.join(self.clean_data(rd) for rd in temp_room_desc['beddingOptions']).encode(
                    'utf-8')
            except:
                pass
            try:
                fac_list = ''.join(rl['amenities'].values()).lower()

                breakpath = tree.xpath('//*[@id="policies-and-fees"]//*[@data-section="fees"]//*[@class="paragraph-hack"]/ul/li') # 获取其他可选设施/服务
                b_descript = filter(lambda x: 'breakfast' in x.xpath('string()') or '早餐' in x.xpath('string()'), breakpath) # 过滤出早餐信息
                b_descript = b_descript[0].xpath('string()') if len(b_descript)>0 else None

                if u'早餐' in fac_list or 'breakfast' in fac_list: # 接口只拿到了包含早餐的信息
                    room.has_breakfast = "Yes".encode('utf-8')
                    room.is_breakfast_free = 'Yes'.encode('utf-8')
                elif b_descript is not None:
                    room.has_breakfast = "NULL".encode('utf-8') # 收费早餐的信息
                    room.is_breakfast_free = 'No'.encode('utf-8')
                else:
                    pass
            except:
                pass
            try:
                room.pay_method = rl['offerType'].encode('utf-8') # 5 是到店付款 13 是合作商的 1是自己的在线付款
                if room.pay_method == "1":
                    room.pay_method = "在线支付"
                elif room.pay_method == "5":
                    room.pay_method = "到店支付"
                else:
                    room.pay_method = "支付方式"
            except:
                pass
            others_info = {}
            try:
                others_info['check_in_time'] = check_in_time.encode('utf-8')
                others_info['check_out_time'] = check_out_time.encode('utf-8')
                others_info['img_urls'] = img_urls.encode('utf-8')
                others_info['review_nums'] = review_nums

                _maxtotal = temp_room_desc['bedsAndRoomOccupancyInfo']['maxRoomOcc']['total']
                _maxchildren = temp_room_desc['bedsAndRoomOccupancyInfo']['maxRoomOcc']['children']
                room.occupancy = temp_room_desc['bedsAndRoomOccupancyInfo']['maxRoomOcc']['adults']
                if _maxchildren > 0:
                    occ_des = "房间可容纳{}位住客，最多{}名儿童".format(_maxtotal, _maxchildren)
                else:
                    occ_des = "房间可容纳{}位住客".format(_maxtotal)

                if room.has_breakfast == 'Yes':
                    if room.is_breakfast_free == 'Yes':
                        o_breakfast = '包含早餐'
                    else:
                        o_breakfast = b_descript
                else:
                    o_breakfast = ''
                others_info["extra"] = {
                    "breakfast": o_breakfast,
                    "payment": room.pay_method,
                    "return_rule": room.return_rule,
                    "occ_des": occ_des,
                }
                room.others_info = json.dumps(others_info)
            except:
                pass
            room.city = cid
            room_tuple = (str(room.hotel_name), str(room.city), str(room.source), \
                          str(room.source_hotelid), str(room.source_roomid), \
                          str(room.real_source), str(room.room_type), int(room.occupancy), \
                          str(room.bed_type), float(room.size), int(room.floor), str(room.check_in), \
                          str(room.check_out), int(room.rest), float(room.price), float(room.tax), \
                          str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free), \
                          str(room.has_breakfast), str(room.is_breakfast_free), \
                          str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule),
                          str(room.change_rule), \
                          str(room.room_desc), str(room.others_info), str(room.guest_info))
            rooms.append(room_tuple)
        return rooms

    def clean_data(self, st):
        if st == '\n' or len(st.strip()) == 0:
            return ''
        st = re.sub(r'<(.*?)>', '', st)
        return st.replace('\n', '').strip()


if __name__ == '__main__':
    pass
