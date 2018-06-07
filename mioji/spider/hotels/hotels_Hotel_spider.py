#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

import re
import datetime
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.spider import Spider, request, mioji_data, PROXY_FLLOW, PROXY_REQ
from mioji.common import parser_except
from mioji.common.class_common import Room
from lxml import html as HTML
from lxml import etree
import urllib
import urllib2
import json
from mioji.common.logger import logger

curr_dict = {'€': 'EUR', '£': 'GBP', '$': 'USD', 'HK$': 'HKD', 'JP¥': 'JPY', '￥': 'CNY',
             '₡': 'CRC', 'BS$': 'BSD', 'AU$': 'AUD', 'S$': 'SGD', 'Tk': 'BDT', 'US$': 'USD'}

num_pat = re.compile(r'(\d+)', re.S)
occ_pat = re.compile(r'最多(.*?)人入住', re.S)
# occ_pat = re.compile(r'可入住(.*?)人', re.S)

DATE_F = '%Y/%m/%d'
hd = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip,deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8,und;q=0.6',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'www.hotels.cn',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
}


def parse_string(st):
    """
        判断传入字符串是否有乱码
        :type st: str
        :return: str
        """
    if '�' in st:
        return ''
    return st.replace('\n', '').strip()


class test_room(Room):
    def __str__(self):
        for k,v in self.__dict__.items():
            print k,'=>',v
        return 'testEND'


def hasNumbers(s):
    '''
    检查字符串是否包含数字
    '''
    return any(char.isdigit() for char in s)


class hotelsSpider(Spider):
    source_type = 'hotelsHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room3'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'hotelsHotel': {'required': ['room']}
    }

    def targets_request(self):

        cid = self.task.ticket_info.get('cid', None)
        booking_info = ''
        taskcontent = self.task.content
        taskcontent = taskcontent.encode('utf8')
        task_list = taskcontent.split('&&')
        city_name_zh, country_name_zh, city_id, hotel_id, nights, check_in = task_list
        # if city_name_zh == 'NULL':
        #     raise parser_except.ParserException(parser_except.TASK_ERROR, "任务错误")

        adults = self.task.ticket_info.get('occ', '2')
        room_num = self.task.ticket_info.get('room_count', '1')
        children = 0
        for i in range(0, int(room_num)):
            booking_info += '&q-room-' + str(i) + '-adults=' + str(adults)
            booking_info += '&q-room-' + str(i) + '-children=' + str(children)
        check_out = datetime.datetime(int(check_in[0:4]), int(check_in[4:6]),
                                      int(check_in[6:8]))
        check_out = str(check_out + datetime.timedelta(days=int(nights)))[0:10]
        check_in = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:8]

        city_name = urllib2.quote(city_name_zh)
        param_list = [city_name, city_id, hotel_id, check_in, check_out, booking_info]
        self.user_datas['hotel_id'] = hotel_id
        self.user_datas['check_in'] = check_in
        self.user_datas['check_out'] = check_out
        self.user_datas['nights'] = nights
        self.user_datas['city_name_zh'] = city_name_zh
        self.user_datas['cid'] = cid
        url = 'http://www.hotels.cn/hotel/details.html?q-localised-check-out={0}&q-localised-check-in={1}&hotel-id={2}&tab=description{3}'.format(param_list[4], param_list[3], param_list[2], param_list[-1])
        self.user_datas['url1'] = url
        '''
        # 获取并拼接url
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_url_page():
            self.user_datas['url'] = url
            return {
                'req': {'url': url, 'headers': hd},
                'user_handler': [self.get_page]
            }
        '''
        # 返回最终的结果，在parse_page中处理网页返回的数据并整理成房间信息
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=[self.parse_room])
        def get_city_page():
            url_get = self.user_datas['url1']
            print url_get
            return {'req': {'url': url_get, 'headers': hd},
                    'data': {'content_type': 'string'}
                    }

        return [get_city_page]

    def parse_hotel(self, req, data):
        pass

    def parse_room(self, req, data):
        return self.parseRoom(data, self.user_datas['hotel_id'], self.user_datas['check_in'],
                               self.user_datas['check_out'], self.user_datas['nights'], self.user_datas['city_name_zh'],
                               self.user_datas['cid'])

    def get_price(self, content):
        price_json = re.findall(r'var commonDataBlock = (.*?),"event"', content, re.S)[0] + '}'
        all_price = json.loads(price_json)['property']
        online_method = "网上付款"
        local_method = "到店付款"
        all_pays = []
        all_pay = []
        for price in all_price['rooms']:
            data_rateplan_id = dict(price).get('ratePlanIds')[0]
            cny_price = dict(dict(price).get('price')).get('value')
            city_tax = dict(dict(price).get('additionalFees')).get('cityTax')
            total_price = float(cny_price) + float(city_tax)
            try:
                dict(dict(price).get('ecPriceLocalCurrency'))
                all_pays.append((data_rateplan_id, total_price, online_method))
            except Exception:
                all_pays.append((data_rateplan_id, total_price, local_method))
            all_pay.append(all_pays[-1])
        return all_pay

    def parseRoom(self, content, hotel_id, check_in, check_out, nights, city_name, cid):
        rooms = []
        content = content.decode('utf-8')
        room = test_room()
        page = content
        # judge = HTML.fromstring(content)
        # r = judge.find_class('rooms')
        # if r == []:
        #    return rooms
        if content.find('在 Hotels.com 好订网上已无空房') > -1 or content.find(u'在 Hotels.com 好订网 上无空房') > -1:
            return []
        self.all_price = self.get_price(content)
        try:
            root = HTML.fromstring(content)
            try:
                print root
                root_path = root.get_element_by_id('rooms')
                room_types_list = root_path.xpath('table')[0].find_class('room')
                print room_types_list
                print '##'
            except:
                print 'this is not id'
                rooms = self.parse_room1(root, city_name, hotel_id, check_in, check_out, nights, content, cid)
                return rooms
        except Exception, e:
            logger.error(e)
            return rooms

        for each_type_room in room_types_list:
            try:
                hotel_name = root.find_class('vcard item')[0].xpath('h1/text()')[0]
                room.hotel_name = hotel_name[:hotel_name.find('(')].strip()

                room_type_path = each_type_room.find_class('room-type')[0]
                room.room_type = room_type_path.xpath('h3/text()')[0].encode('utf-8')

                try:
                    room.source_roomid = \
                    each_type_room.find_class('room-images has-multiple-images')[0].xpath('@data_photo-set_id')[0]
                except Exception, e:
                    pass

                try:
                    check_in_pattern = re.compile(r'<li>入住时间(.*?)</li>')
                    check_in_time = '入住时间' + check_in_pattern.findall(page.encode('utf-8'))[0].encode('utf-8')
                except Exception, e:
                    check_in_time = 'NULL'
                print 'check_in', check_in_time
                try:
                    check_out_pattern = re.compile(r'退房时间(.*?)</li>')
                    check_out_time = '退房时间' + check_out_pattern.findall(page.encode('utf-8'))[0].encode('utf-8')
                except Exception, e:
                    check_out_time = 'NULL'

                print 'check_out_time', check_out_time

                try:
                    bed_type_path = room_type_path.find_class('room-beds')[0]
                    room.bed_type = bed_type_path.xpath('ul[1]/li/text()')[0]

                    try:
                        extra_bed_content = bed_type_path.xpath('h5[2]/text()')[0]
                        if '可提供加床服务' in extra_bed_content:
                            room.is_extrabed = 'Yes'
                        if '可提供加床服务' in extra_bed_content and '免费' in extra_bed_content:
                            room.is_extrabed = 'Yes'
                            room.is_extrabed_free = 'Yes'
                    except Exception, e:
                        pass
                except:
                    continue

                print 'room.bed_type', room.bed_type
                try:
                    desc_content = each_type_room.find_class('room-information-container')[0]
                    room.room_desc = desc_content.text_content().encode('utf-8')
                    room.room_desc = room.room_desc.replace('\n', '').replace('  ', '')
                except:
                    pass

                rooms_list = each_type_room.xpath('tr')
                if len(rooms_list) <= 1:
                    continue

                for each_room in rooms_list[:-1]:
                    try:
                        try:
                            occupancy_temp = each_room.find_class('room-occupancy')[0]
                            print '~@'*20, occupancy_temp
                            occupancy_str = occupancy_temp.xpath('li/span')[0].text_content().encode('utf-8')
                            print '*%'*20, occupancy_str
                            occ_temp = occ_pat.findall(occupancy_str)[0].strip()
                            room.occupancy = int(occ_temp)
                        except Exception, e:
                            print str(e)
                            room.occupancy = -1

                        price_path = each_room.find_class('rate-pricing')[0]
                        price_content = price_path.find_class('current-price')[0].xpath('strong/text()')[0].encode(
                            'utf-8')
                        price_content = price_content.replace(',', '')
                        room.price = int(num_pat.findall(price_content)[0]) * int(nights)
                        '''
                        try:
                            room.tax = int(room.price * tax_dict[city_name])
                        except Exception, e:
                            logger.info('hotelsHotel :: tax error, city_name : ' + city_name)
                            print str(e)
                            room.tax = -1
                        '''
                        try:
                            rest_content = price_path.find_class('cta-message')[0].text_content().encode('utf-8')
                            rest_d = {}
                            rest_d['rest'] = ''
                            rest_d['rest'] = rest_content
                            room.others_info = json.dumps(rest_d)
                            room.rest = int(num_pat.findall(rest_content)[0])
                        except Exception, e:
                            room.rest = -1

                        try:
                            feature_content = each_room.find_class('rate-features')[0].text_content().encode('utf-8')

                            if '免费取消' in feature_content:
                                room.is_cancel_free = 'Yes'

                            if '早餐' in feature_content:
                                room.has_breakfast = 'Yes'

                            if '包含早餐' in feature_content:
                                room.has_breakfast = 'Yes'
                                room.is_breakfast_free = 'Yes'
                        except:
                            pass

                        room.city = cid
                        room.source = 'hotels'
                        room.source_hotelid = hotel_id
                        room.real_source = 'hotels'
                        room.currency = 'CNY'
                        room.check_in = check_in
                        room.check_out = check_out
                        room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                                      room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                                      room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                                      room.rest, room.price, room.tax, room.currency, room.pay_method, \
                                      room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                                      room.is_breakfast_free, \
                                      room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule,
                                      room.room_desc, \
                                      room.others_info, room.guest_info)
                        rooms.append(room_tuple)
                    except Exception, e:
                        print str(e)
                        continue

            except Exception, e:
                print str(e)
                continue

        return rooms

    def get_infos(self, room, all_infos, planlist):
        for each in planlist:
            rateplan_id = each.find_class('rateplan')[0].xpath('@data-rateplan-id')[0]
            all_infos[rateplan_id] = dict()
            try:
                return_rule = each.find_class('cancellation')[0].xpath('strong/span/text()')[0].strip()
            except Exception, e:
                return_rule = 'NULL'
            room.return_rule = return_rule
            room.change_rule = return_rule
            all_infos[rateplan_id]["return_rule"] = return_rule
            all_infos[rateplan_id]["change_rule"] = return_rule
            try:
                options = each.find_class('options')[0]
                text = options.text_content()
            except:
                text = 'NULL'
            if '免费取消' in text:
                room.is_cancel_free = 'Yes'
            if '不会获得任何退款' in text:
                room.is_cancel_free = 'No'
            if '早餐' in text:
                room.has_breakfast = 'Yes'
            else:
                room.has_breakfast = 'No'
            if '早餐' in text and '包含早餐' in text:
                room.is_breakfast_free = 'Yes'
            if "包含早餐住宿期间提供早餐" in text:
                breakfast_infor = "包含早餐住宿期间提供早餐"
                all_infos[rateplan_id]['breakfast_infor'] = breakfast_infor
            else:
                all_infos[rateplan_id]['breakfast_infor'] = ""
            cancel = each.find_class('cancellation')[0]
            cancelcontent = cancel.xpath('./strong/text()')[0].encode('utf-8')
            all_infos[rateplan_id]["is_cancel_free"] = room.is_cancel_free
            all_infos[rateplan_id]["has_breakfast"] = room.has_breakfast
            all_infos[rateplan_id]["is_breakfast_free"] = room.is_breakfast_free
            try:
                related_clauses_tmp1 = ''
                related_clauses_detail_tmp1 = ''
                related_clauses_detail_tmp1 = each.find_class('cancellation')[0].xpath('./strong/span/text()')[0].encode('utf-8').replace(' ', '')
            except:
                related_clauses_tmp1 = ''

            try:
                related_clauses_tmp2 = ''
                related_clauses_detail_tmp2 = ''
                related_clauses_list2 = each.find_class('rateplan-features')[0].getchildren()
                for each_clauses in related_clauses_list2:
                    related_clauses_tmp2 += each_clauses.xpath('./span[1]/text()')[0].encode('utf-8') + '||'
                    related_clauses_detail_tmp2 += each_clauses.xpath('./span[2]/text()')[0].encode('utf-8') + '||'
            except Exception, e:
                related_clauses_tmp2 = ''
            related_clauses = ''
            related_clauses_detail = ''
            if related_clauses_tmp1 != '':
                related_clauses += related_clauses_tmp1 + '||'
            if related_clauses_tmp2 != '':
                related_clauses += related_clauses_tmp2
            all_infos[rateplan_id]["related_clauses"] = related_clauses[:-2]

            if related_clauses_detail_tmp1 != '':
                related_clauses_detail += related_clauses_detail_tmp1 + '||'
            if related_clauses_detail_tmp2 != '':
                related_clauses_detail += related_clauses_detail_tmp2
            all_infos[rateplan_id]["related_clauses_detail"] = related_clauses_detail[:-2]
        return all_infos

    def parse_room1(self, root, city_name, hotel_id, check_in, check_out, nights, page, cid):
        rooms = []
        try:
            html_rooms = root.find_class('rooms')[0]
        except Exception, e:
            return rooms
        print 'room count', len(html_rooms)
        print 'point room count'
        numofroom = html_rooms.getchildren()
        for each_room in numofroom:
            print each_room
            print '####'
            room = self.get_room1(each_room, root, city_name, hotel_id, check_in, check_out, nights, page, cid)
            print 'point ####'
            rooms.extend(room)
        return rooms

    def get_room1(self, html_room, root, city_name, hotel_id, check_in, check_out, nights, page, cid):
        res = []
        room = test_room()
        print 'point_get_room1'
        vcard = root.find_class('vcard')[0]
        vcard = vcard.xpath('h1[1]/text()')[0]
        room.hotel_name = vcard[:vcard.find('(')].strip()
        room.city = cid
        room.source = 'hotels'
        room.source_hotelid = hotel_id
        room.source_roomid = 'NULL'
        room.real_source = 'hotels'

        try:
            check_in_pattern = re.compile(r'<li>入住时间(.*?)</li>')
            check_in_time = '入住时间' + check_in_pattern.findall(page.encode('utf-8'))[0].encode('utf-8')
        except Exception, e:
            check_in_time = 'NULL'

        try:
            check_out_pattern = re.compile(r'退房时间(.*?)</li>')
            check_out_time = '退房时间' + check_out_pattern.findall(page.encode('utf-8'))[0].encode('utf-8')
        except Exception, e:
            check_out_time = 'NULL'


        try:
            room_info = html_room.find_class('room-info')[0]
        except Exception, e:
            print str(e)

        try:
            room.room_type = room_info.xpath('.//h3/text()')[0].encode('utf-8').strip()
        except Exception, e:
            print "*" * 20, str(e)
        try:
            occupas = html_room.find_class('occupancy-info')[0].xpath('./strong/text()')[0].strip()#已修改
            print '~~~~~~>>>>>>>>>', occupas
            # logger.info(occupa)
            r = re.compile('(\d+)')
            m = r.findall(occupas)
            occupa = int(m[0])
        except Exception, e:
            occupa = -1
        try:
            occupac = html_room.find_class('occupancy-info')[0].xpath('./text()')[0].strip()
            print '~~~~~~>>>>>>>>>', occupac
        except Exception:
            pass
        # print '___________>>>>>>>>>>>>>'
        room.occupancy = occupa#已修改
        # print '___________>>>>>>>>>>>>>',room.occupancy
        logger.debug(occupa)
        logger.info(room.occupancy)
        try:
            bullet = html_room.find_class('bulleted')[0].xpath('li[1]/text()')[0].strip()
            room.bed_type = bullet
        except Exception, e:
            print str(e)
        'room.bed_type', room.bed_type
        room.size = -1
        room.floor = -1
        room.check_in = check_in
        room.check_out = check_out
        room.rest = -1
        room.currency = 'CNY'

        try:
            room_size_desc = html_room.find_class('room-description resp-module bulleted')[0].xpath('./ul/text()')[
                0].encode('utf-8')
            if hasNumbers(room_size_desc):
                pass
            else:
                room_size_desc = ''
        except Exception, e:
            print str(e)
            room_size_desc = ''


        try:
            room_detail_tmp = html_room.find_class('room-description resp-module bulleted')[0].xpath('./ul/b')
            room_desc = html_room.find_class('room-description resp-module bulleted')[0].xpath('./ul/text()')
            room_detail = ''
            i = 1
            for each_desc in room_detail_tmp:
                desc = room_desc[i].encode('utf-8').strip('')
                item = each_desc.text_content().encode('utf-8')
                i += 1
                room_detail += item + desc + '||'

        except Exception, e:
            print str(e)

        room_detail = room_detail[:-2]

        try:
            room_info = html_room.find_class('room-and-hotel-info')[0]
            text = room_info.text_content()
            if '可提供加床服务' in text:
                room.is_extrabed = 'Yes'

            if '可提供加床服务' in text and '免费' in text:
                room.is_eaxtrabed_free = 'Yes'
        except Exception, e:
            pass
        desc = html_room.find_class('additional-room-info')[0]
        desc = desc.text_content().replace('\n', '').replace('  ', '')
        room.room_desc = desc
        planlist = html_room.find_class('rateplans')[0]

        all_infos = {}
        ll = self.get_infos(room, all_infos, planlist)
        # print ll
        for eacha in self.all_price:
            related_clauses = ""
            related_clauses_detail = ""
            if eacha[0] in ll.keys():
                if eacha[2] == '\xe7\xbd\x91\xe4\xb8\x8a\xe4\xbb\x98\xe6\xac\xbe':
                    room.pay_method = "网上支付"
                    pay_method = room.pay_method
                    room.price = float(eacha[1]) * int(nights)
                    related_clauses = ll[eacha[0]]['related_clauses']
                    related_clauses_detail = ll[eacha[0]]["related_clauses_detail"]
                    try:
                        room.return_rule = ll[eacha[0]]['return_rule']
                        room.change_rule = ll[eacha[0]]['change_rule']
                    except Exception:
                        pass
                    room.is_cancel_free = ll[eacha[0]]["is_cancel_free"]
                    room.has_breakfast = ll[eacha[0]]["has_breakfast"]
                    room.is_breakfast_free = ll[eacha[0]]["is_breakfast_free"]
                    breakfast_infor = ll[eacha[0]]['breakfast_infor']

                elif eacha[2] == '\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe':
                    room.pay_method = "到店支付"
                    pay_method = room.pay_method
                    room.price = float(eacha[1]) * int(nights)
                    related_clauses = ll[eacha[0]]['related_clauses']
                    related_clauses_detail = ll[eacha[0]]["related_clauses_detail"]
                    try:
                        room.return_rule = ll[eacha[0]]['return_rule']
                        room.change_rule = ll[eacha[0]]['change_rule']
                    except Exception:
                        pass
                    room.is_cancel_free = ll[eacha[0]]["is_cancel_free"]
                    room.has_breakfast = ll[eacha[0]]["has_breakfast"]
                    room.is_breakfast_free = ll[eacha[0]]["is_breakfast_free"]
                    breakfast_infor = ll[eacha[0]]['breakfast_infor']

                other_info_dict = {}
                other_info_dict['check_in_time'] = check_in_time
                other_info_dict['check_out_time'] = check_out_time
                other_info_dict['room_size'] = room_size_desc
                other_info_dict['room_detail'] = room_detail
                other_info_dict['related_clauses'] = related_clauses
                other_info_dict['related_clauses_detail'] = related_clauses_detail
                other_info_dict['extra'] = list()
                other_info_dict['extra'].append({'breakfast': breakfast_infor})
                other_info_dict['extra'].append({'payment': pay_method})
                other_info_dict['extra'].append({'return_rule': room.return_rule})
                other_info_dict['extra'].append({'occ_des': occupas + occupac})
                room.others_info = json.dumps(other_info_dict)
                room.city = cid
                # print room.city
                room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                              room.source_roomid, room.real_source, room.room_type, room.occupancy, \
                              room.bed_type, room.size, room.floor, room.check_in, room.check_out, \
                              room.rest, room.price, room.tax, room.currency, room.pay_method, \
                              room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                              room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule,
                              room.room_desc, \
                              room.others_info, room.guest_info)
                res.append(room_tuple)
        return res

if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy
    task = Task()
    # task_list = ['楠迪&&斐济&&1635865&&264656&&2&&20171110',
    #              '马赛&&法国&&510502&&227700&&1&&20171206',
    #              'NULL&&NULL&&NULL&&142983&&1&&20171220',
    #              ]
    task.content = 'NULL&&NULL&&NULL&&142983&&3&&20171219'
    task.ticket_info = {'cid': 1}
    spider = hotelsSpider()
    spider.task = task
    spider.crawl()
    print spider.crawl()
    print spider.result
    # index = 0
    # for t in task_list:
    #     print str(index) + '=' * 10
    #     index += 1
    #     task.content = t
    #     task.ticket_info = {'cid': 1}
    #     spider = hotelsSpider()
    #     spider.task = task
    #     spider.crawl()
    #     import time
    #     time.sleep(2)
    #     print spider.crawl()
    #     print spider.result
    # print spider.first_url()

#[(u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 1 \xe5\xbc\xa0\xe7\x89\xb9\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 3, u'1 \u5f20\u7279\u5927\u5e8a', -1, -1, '2017-10-10', '2017-10-11', -1, 1302.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'Yes', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'1 \u5f20\u7279\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL'), (u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 2 \xe5\xbc\xa0\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 5, u'2 \u5f20\u5927\u5e8a', -1, -1, '2017-10-10', '2017-10-11', -1, 1439.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'Yes', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'2 \u5f20\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL')]}, 0)
#[(u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 1 \xe5\xbc\xa0\xe7\x89\xb9\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 3, 'NULL', -1, -1, '2017-10-10', '2017-10-11', -1, 1302.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'Yes', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'1 \u5f20\u7279\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL'), (u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 2 \xe5\xbc\xa0\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 5, 'NULL', -1, -1, '2017-10-10', '2017-10-11', -1, 1439.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'Yes', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'2 \u5f20\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL')]
#[(u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 1 \xe5\xbc\xa0\xe7\x89\xb9\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 3, u'\u7279\u5927\u5e8a', -1, -1, '2017-10-10', '2017-10-11', -1, 1302.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'NULL', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'1 \u5f20\u7279\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL'), (u'\u8d1d\u65af\u7279\u97e6\u65af\u7279\u516c\u56ed\u5e7f\u573a\u8ff7\u4f60\u5957\u623f\u9152\u5e97', 1, 'hotels', '163102', 'NULL', 'hotels', '\xe6\xa0\x87\xe5\x87\x86\xe5\xae\xa2\xe6\x88\xbf, 2 \xe5\xbc\xa0\xe5\xa4\xa7\xe5\xba\x8a, \xe6\x97\xa0\xe7\x83\x9f\xe6\x88\xbf, \xe5\x86\xb0\xe7\xae\xb1\xe5\x92\x8c\xe5\xbe\xae\xe6\xb3\xa2\xe7\x82\x89', 5, u'2 \u5f20\u5927\u53f7\u5e8a', -1, -1, '2017-10-10', '2017-10-11', -1, 1439.0, -1.0, 'CNY', '\xe7\xab\x8b\xe5\x8d\xb3\xe4\xbb\x98\xe6\xac\xbe\xe6\x88\x96\xe5\x88\xb0\xe5\xba\x97\xe4\xbb\x98\xe6\xac\xbe', 'NULL', 'NULL', 'Yes', 'Yes', 'Yes', 'NULL', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'\u60a8\u53ef\u5728 2017-10-07\u4e4b\u524d\u514d\u8d39\u53d6\u6d88\u6b64\u9884\u8ba2\u3002\u5982\u5728\u4e0a\u8ff0\u65e5\u671f\u540e\u53d6\u6d88\u6216\u66f4\u6539\u9884\u8ba2\uff0c\u53ef\u80fd\u9700\u8981\u652f\u4ed8\u4e00\u5b9a\u8d39\u7528\u3002\u6b64\u5916\uff0c\u5982\u679c\u60a8\u63d0\u65e9\u9000\u623f\u6216\u6ca1\u6709\u5165\u4f4f\u9152\u5e97\uff0c\u6211\u4eec\u5c06\u65e0\u6cd5\u9000\u6b3e\u3002', u'2 \u5f20\u5927\u5e8a\u7f51\u7edc - \u514d\u8d39\u65e0\u7ebf\u548c\u6709\u7ebf\u4e0a\u7f51\u63a5\u5165\u670d\u52a1 \u5a31\u4e50 - \u6709\u7ebf\u9891\u9053\u9910\u996e - \u51b0\u7bb1\u3001\u5fae\u6ce2\u7089\u548c\u5496\u5561\u58f6/\u8336\u5177\u6d74\u5ba4 - \u79c1\u4eba\u6d74\u5ba4\u5907\u6709\u6dcb\u6d74/\u6d74\u7f38\u7ec4\u5408\u3001\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u548c\u5439\u98ce\u673a\u5b9e\u7528 - \u6c99\u53d1\u5e8a\u3001\u514d\u8d39\u5e02\u8bdd\u548c\u71a8\u6597\u53ca\u71a8\u677f\uff1b\u5982\u6709\u9700\u8981\uff0c\u53ef\u63d0\u4f9b\u514d\u8d39\u5a74\u513f\u5e8a/\u5c0f\u7ae5\u5e8a\u8212\u9002\u8bbe\u65bd/\u670d\u52a1 - \u7a7a\u8c03\u548c\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01\u65e0\u70df\u5ba2\u623f\u53ef\u8981\u6c42\u63d0\u4f9b\u8fde\u901a\u623f/\u6bd7\u90bb\u623f\uff0c\u89c6\u4f9b\u5e94\u60c5\u51b5\u800c\u5b9a\u5ba2\u623f\u8be6\u7ec6\u4fe1\u606f\u51b0\u7bb1\u5439\u98ce\u673a\u7535\u89c6\u623f\u5185\u6052\u6e29\u63a7\u5236\uff08\u7a7a\u8c03\uff09\u7a7a\u8c03\u6bcf\u65e5\u5ba2\u623f\u6e05\u6d01 (\u6bcf\u65e5)\u514d\u8d39 WiFi\u514d\u8d39\u513f\u7ae5\u5e8a/\u5a74\u513f\u5e8a\u514d\u8d39\u5e02\u8bdd\u514d\u8d39\u6d17\u6d74\u7528\u54c1\u6ce1\u5496\u5561/\u8336\u7528\u5177\u4e66\u684c\u63d0\u4f9b\u8fde\u901a\u623f/\u76f8\u90bb\u623f\u5fae\u6ce2\u7089\u6709\u7ebf\u7535\u89c6\u670d\u52a1\u71a8\u6597/\u71a8\u8863\u677f', '{"room_size": "", "related_clauses_detail": "\\u60a8\\u53ef\\u57282017-10-07\\u4e4b\\u524d\\u514d\\u8d39\\u53d6\\u6d88\\u6b64\\u9884\\u8ba2\\u3002\\u5982\\u5728\\u4e0a\\u8ff0\\u65e5\\u671f\\u540e\\u53d6\\u6d88\\u6216\\u66f4\\u6539\\u9884\\u8ba2\\uff0c\\u53ef\\u80fd\\u9700\\u8981\\u652f\\u4ed8\\u4e00\\u5b9a\\u8d39\\u7528\\u3002\\u6b64\\u5916\\uff0c\\u5982\\u679c\\u60a8\\u63d0\\u65e9\\u9000\\u623f\\u6216\\u6ca1\\u6709\\u5165\\u4f4f\\u9152\\u5e97\\uff0c\\u6211\\u4eec\\u5c06\\u65e0\\u6cd5\\u9000\\u6b3e\\u3002||\\u6b64\\u623f\\u95f4\\u63d0\\u4f9b\\u514d\\u8d39 WiFi||\\u4f4f\\u5bbf\\u671f\\u95f4\\u63d0\\u4f9b\\u65e9\\u9910", "related_clauses": "\\u514d\\u8d39 WiFi||\\u5305\\u542b\\u65e9\\u9910", "check_in_time": "\\u5165\\u4f4f\\u65f6\\u95f4\\u5f00\\u59cb\\u4e8e 3:00 PM", "room_detail": "\\u7f51\\u7edc ||\\u5a31\\u4e50 - \\u6709\\u7ebf\\u9891\\u9053||\\u9910\\u996e - \\u51b0\\u7bb1\\u3001\\u5fae\\u6ce2\\u7089\\u548c\\u5496\\u5561\\u58f6/\\u8336\\u5177||\\u6d74\\u5ba4 - \\u79c1\\u4eba\\u6d74\\u5ba4\\u5907\\u6709\\u6dcb\\u6d74/\\u6d74\\u7f38\\u7ec4\\u5408\\u3001\\u514d\\u8d39\\u6d17\\u6d74\\u7528\\u54c1\\u548c\\u5439\\u98ce\\u673a||\\u5b9e\\u7528 - \\u6c99\\u53d1\\u5e8a\\u3001\\u514d\\u8d39\\u5e02\\u8bdd\\u548c\\u71a8\\u6597\\u53ca\\u71a8\\u677f\\uff1b\\u5982\\u6709\\u9700\\u8981\\uff0c\\u53ef\\u63d0\\u4f9b\\u514d\\u8d39\\u5a74\\u513f\\u5e8a/\\u5c0f\\u7ae5\\u5e8a||\\u8212\\u9002\\u8bbe\\u65bd/\\u670d\\u52a1 - \\u7a7a\\u8c03\\u548c\\u6bcf\\u65e5\\u5ba2\\u623f\\u6e05\\u6d01", "check_out_time": "\\u9000\\u623f\\u65f6\\u95f4\\u4e3a 11:00"}', 'NULL')]}, 0)


