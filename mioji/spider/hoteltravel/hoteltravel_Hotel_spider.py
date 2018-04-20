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
# from city_common import City
import random
import json


DATE_F = '%Y/%m/%d'
hd = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip,deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8,und;q=0.6',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'www.hoteltravel.com',
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


class hoteltravelSpider(Spider):
    source_type = 'hoteltravelHotel'
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
        'hoteltravelHotel': {'required': ['room']}
    }

    def targets_request(self):
        try:
            cid = self.task.ticket_info.get('cid', None)
            self.user_datas['cid'] = cid
            self.user_datas['occ'] = self.task.ticket_info.get('occ', 2)
            taskcontent = self.task.content
            task_list = taskcontent.split('&')
            self.user_datas['source_id'], self.user_datas['daydiff'], self.user_datas['dept_time'] = task_list[0], task_list[1], task_list[2]
            if len(task_list) > 3:
                self.user_datas['total_nu'], self.user_datas['room_nu'], self.user_datas['age_list'], self.user_datas['occ'] = task_list[3], task_list[4], task_list[5], task_list[6]
                age_list = self.user_datas['age_list'].split('|')
                self.user_datas['adult_nu'], self.user_datas['child_nu'] = 0, 0
                for ele in age_list:
                    ele_list = ele.split('_')
                    for i in ele_list:
                        if int(i) > 12:
                            self.user_datas['adult_nu'] += 1
                        else:
                            self.user_datas['child_nu'] += 1
            else:
                self.user_datas['room_nu'], self.user_datas['adult_nu'], self.user_datas['child_nu'] = 1, 2, 0
            dept_time = datetime.datetime.strptime(self.user_datas['dept_time'], '%Y%m%d')
            dest_time = dept_time + datetime.timedelta(int(self.user_datas['daydiff']))
            dept_time = dept_time.strftime('%d%m%Y')
            dest_time = dest_time.strftime('%d%m%Y')
            self.user_datas['dept_time'] = dept_time
            self.user_datas['dest_time'] = dest_time
            self.user_datas['dept_day'] = dept_time[:2] + '/' + dept_time[2:4] + '/' + dept_time[6:]
            self.user_datas['dest_day'] = dest_time[:2] + '/' + dest_time[2:4] + '/' + dest_time[6:]
            self.user_datas['rooms'] = []
        except Exception as e:
            raise parser_except.ParserException(parser_except.TASK_ERROR, msg='hoteltravelHotel::  {0}'.format(e))


        # 获取并拼接url
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_url_page():
            url0 = 'http://www.hoteltravel.com/cn/' + self.user_datas['source_id']
            self.user_datas['url'] = url0
            return {
                'req': {'url': url0, 'headers': hd},
                'user_handler': [self.get_page]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def currency_to_RMB():
            url = "http://www.hoteltravel.com/utility/currencyexchange.aspx?"
            return {
                'req': {
                    'url': url,
                    'headers': hd
                },
                'data': {'content_type': 'string'},
                'user_handler': [self.parser_currency_to_RMB]
            }


        # 返回最终的结果，在parse_page中处理网页返回的数据并整理成房间信息
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['room'])
        def get_city_page():
            url_get = self.user_datas['url1']
            print url_get
            return {'req': {'url': url_get, 'headers': hd},
                    'data': {'content_type': 'string'},
                    }

        return [currency_to_RMB, get_url_page, get_city_page]

    def parser_currency_to_RMB(self, req, data):
        page = data.split('"')[1][:-1]
        page = eval(page)
        self.user_datas['currency_rates'] = page

    def parse_hotel(self, req, data):
        pass

    def parse_room(self, req, data):
        source_hotelid = self.user_datas['source_id']
        page_hotel = self.user_datas['page_hotel']
        return self.parse_page(page_hotel, data,
                               self.user_datas['dept_time'], self.user_datas['dest_time'],
                               source_hotelid, self.user_datas['daydiff'], self.user_datas['occ'],
                               self.user_datas['cid'], self.user_datas['currency_rates']
                               )

    def get_page(self, req, data):
        page_hotel = data
        self.user_datas['page_hotel'] = data
        root_id = HTML.fromstring(page_hotel)
        city_name_lower = self.user_datas['source_id'].split('/')[1]

        random_num = random.random()
        try:
            hotel_id = root_id.get_element_by_id('hpHotelCode').xpath('./@value')[0]
        except Exception as e:
            print str(e)
            # 返回无数据异常22
        # url1 = 'http://www.hoteltravel.com/hotelgetratesv5/getrates.aspx?htc=' + hotel_id + '&lng=cn&arrdt=' + self.user_datas['dept_day'] + '&deptdt=' + self.user_datas['dest_day'] + '&norm=' + str(self.user_datas['room_nu']) + '&occ=' + str(self.user_datas['adult_nu']) + '|' + str(self.user_datas['child_nu']) + '&req=DMC&ci=' + tri_code + '&sid=' + str(random_num)
        url1 = 'http://www.hoteltravel.com/hotelgetratesv5/getrates.aspx?htc=' + hotel_id + '&lng=cn&arrdt=' + self.user_datas['dept_day'] + '&deptdt=' + self.user_datas['dest_day'] + '&norm=' + str(self.user_datas['room_nu']) + '&occ=' + str(self.user_datas['adult_nu']) + '|' + str(self.user_datas['child_nu']) + '&req=DMC'  + '&sid=' + str(random_num)
        self.user_datas['url1'] = url1

    def parse_page(self, page_hotel, page_room, dept_time, dest_time, source_hotelid, daydiff, occ, cid, currency_rates):
        """
        页面解析
        :return: str
        """

        def currency_to_RMB(currency, price):
            """
                # 通过汇率表来完成对汇率的转换。
            """
            currency_price = 0
            temp_currency = ''
            # rmb =
            print currency
            for i in currency_rates:
                split_currency = i['value'].split('|')
                if split_currency[-1] == 'CN¥':
                    print split_currency[1], '*' * 100
                    rmb = float(split_currency[1])
                if split_currency[-1] == currency:
                    print split_currency[-1], '+' * 100

                    currency_price = float(split_currency[1])
                    print currency_price, '='*100
                    temp_currency = "CNY"
            # 汇率表中都是对美元汇率
            price_to_rmb = float(price) / float(currency_price) * float(rmb)
            print 'price_to_rmb is {0}'.format(price_to_rmb)
            return price_to_rmb, temp_currency

        rooms = []
        try:
            root_hotel = HTML.fromstring(page_hotel, parser=etree.HTMLParser(encoding='utf-8'))
            root_room = HTML.fromstring(page_room, parser=etree.HTMLParser(encoding='utf-8'))
            hotel_name = root_hotel.xpath('//*[@id="hotel-detail"]//text()')[0]
            hotel_name = parse_string(hotel_name.encode('raw-unicode-escape'))
        except Exception as e:
            pass
            # 页面无法解析或酒店名没有获得,认为没有数据,由于代理原因导致没有抓取到需要的酒店详情页抛出22异常

        room_desc = ''
        try:
            room_desc_list = root_hotel.xpath("//*[@id='roomFacilities']/*//li/text()")
            room_desc = '||'.join(parse_string(rl) for rl in room_desc_list if rl != '\n' and len(rl.strip())).encode('raw-unicode-escape')

        except Exception as e:
            pass
        city = root_hotel.xpath('//*[@id="search_bc"]/li[3]/a/span[1]/text()')[0].strip().encode('utf8')
        dl_list = root_room.xpath('//dl[@class="detail  clearfix"]')
        div_list = root_room.xpath('//*[@aria-labelledby="conditions"]')
        check_in = dept_time[-4:] + '-' + dept_time[2:4] + '-' + dept_time[:2]
        check_out = dest_time[-4:] + '-' + dest_time[2:4] + '-' + dest_time[:2]
        for dl, div in zip(dl_list, div_list):
            room = Room()
            # room_type
            room_type = ''
            try:
                room_type = dl.xpath('./dd[@class="col-xs-12 col-sm-3"]/h5/text()')[0]
                room_type = parse_string(room_type)
            except Exception as e:
                pass
            print 'room_type',room_type
            price = -1
            try:
                price_info = div.xpath("./*//*[@class='price']/text()")[0].strip()
                print price_info
                currency = price_info[:price_info.find(' ')].strip().encode('utf-8')
                print currency, '0'*10
                price = price_info[price_info.find(' ') + 1:]
                if ',' in price:
                    price = price.replace(',', '')

                price, currency =  currency_to_RMB(currency, price)

            except Exception as e:
                print e
                currency = ''

                # 如果价格，或者货币出错，直接跳过。
                continue

            try:
                price_descs = div.xpath("./*//*[@class='col-xs-12 col-sm-12 col-md-12 col-lg-12']/p[5]/text()")[
                    0].strip()
                price_descs = parse_string(price_descs)
            except Exception as e:
                price_descs = ''

            policy_info = ''
            try:
                policy_info_list = div.xpath('./*//*[@class="col-xs-12 col-sm-12 col-md-12 col-lg-12"]/p[4]//text()')
                policy_info = '||'.join(parse_string(pl) for pl in policy_info_list if pl != '\n' and len(pl.strip()))
            except Exception as e:
                pass

            try:
                include_info_list = dl.xpath("./*[@class='col-xs-6 col-sm-2 small']//text()")
                include_info = ''.join(parse_string(il) for il in include_info_list if il != '\n' and len(il.strip()))
            except Exception as e:
                include_info = ''

            if '含早餐' in include_info:
                has_breakfast = is_breakfast_free = 'Yes'
            else:
                has_breakfast = is_breakfast_free = 'No'
            return_rule = ''
            try:
                return_rule = div.xpath('./*//*[@class="col-xs-12 col-sm-12 col-md-12 col-lg-12"]/p[4]//text()')[0]
                return_rule = parse_string(return_rule)
            except Exception as e:
                pass

            if '获得全额退款' in return_rule or '免费取消' in return_rule or '100％退款' in return_rule:
                is_cancel_free = 'Yes'
            else:
                is_cancel_free = 'No'
            if occ == '':
                occ = '-1'
            room.check_in = check_in
            room.check_out = check_out
            if len(has_breakfast):
                room.has_breakfast = has_breakfast.strip()
            if len(is_breakfast_free):
                room.is_breakfast_free = is_breakfast_free
            if len(currency):
                room.currency = currency.strip()
            if price != -1:
                room.price = float(price) * float(daydiff)
            if len(room_desc):
                room.room_desc = room_desc
            others_info = {}
            others_info['price_descs'] = price_descs.encode('utf-8')
            others_info['policy_info'] = policy_info.encode('utf-8')
            room.others_info = json.dumps(others_info)
            room.occupancy = occ
            if len(return_rule):
                room.return_rule = return_rule.strip().encode('utf-8')
            room.change_rule = room.return_rule
            if len(is_cancel_free):
                room.is_cancel_free = is_cancel_free.encode('utf-8')
            room.pay_method = '预付'.encode('utf-8')
            if len(room_type):
                room.room_type = room_type.strip().encode('utf-8')
            room.source_hotelid = source_hotelid.encode('utf-8')
            room.city = cid
            room.hotel_name = hotel_name.encode('utf-8')
            room.source = 'hoteltravel'
            room.real_source = 'hoteltravel'
            print room.city
            wait_insert_info = (
            str(room.hotel_name), str(room.city), str(room.source),
            str(room.source_hotelid), str(room.source_roomid),
            str(room.real_source), str(room.room_type), int(room.occupancy),
            str(room.bed_type), float(room.size), int(room.floor), str(room.check_in),
            str(room.check_out), int(room.rest), float(room.price), float(room.tax),
            str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free),
            str(room.has_breakfast), str(room.is_breakfast_free),
            str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule), str(room.change_rule),
            str(room.room_desc), str(room.others_info), str(room.guest_info)
            )
            rooms.append(wait_insert_info)
            # print 'rooms is {0}'.format(rooms)
        return rooms

if __name__ == '__main__':
    from mioji.common.task_info import Task
    import json

    task = Task()
    task = Task()
    task_list = [#'japan/nagoya/nagoya_tokyu_hotel.htm&3&20170504&',
                 #'austria/salzburg/der_salzburger_hof.htm&3&20170504&',
                 #'austria/vienna/flemings_deluxe_hotel_wien_city_vinflh.htm&3&20170604&',
                 "japan/tokyo/keio_plaza_tokyo_hotel.htm&1&20170520"
                 ]
    index = 0
    for t in task_list:
        print str(index) + '=' * 10
        index += 1
        task.content = t
        task.ticket_info = {'cid': 1}
        spider = hoteltravelSpider()
        spider.task = task
        print spider.crawl()
        a =  spider.result
        print
        print
        print a
        print len(a['room'])
        # open('xx.json', 'w').write(json.dumps(a))

    # print spider.first_url()




