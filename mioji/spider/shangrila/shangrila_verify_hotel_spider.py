# coding=utf-8
from lxml import etree
import re
import datetime
import json

from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.class_common import Room
from mioji.common import parser_except


class ShangRiLaSpider(Spider):
    source_type = 'shangrilaHotel'
    targets = {'hotel': {}}
    old_spider_tag = {'shangrilaHotel': {}}

    def __init__(self, task=None):
        self.item = dict()
        self.data = list()
        super(ShangRiLaSpider, self).__init__(task)

    def targets_request(self):
        content = self.task.content.split("&")
        try:
            room_info = self.task.ticket_info.get('room_info')[0]
        except:
            raise parser_except.ParserException(29, '获取人数和房间数失败')

        self.hotel_url, stay_nights, a_day = content[0], content[1], content[2]
        if not self.hotel_url.endswith('/'):
            self.hotel_url = '{}/'.format(self.hotel_url)

        self.hotel_url = "{}reservations/".format(self.hotel_url)
        self.arrivalDate = "{}/{}/{}".format(a_day[0:4], a_day[4:6], a_day[6:8])
        self.check_in = "{}-{}-{}".format(a_day[0:4], a_day[4:6], a_day[6:8])
        self.departureDate = str(datetime.datetime(int(a_day[0:4]), int(a_day[4:6]), \
                                                   int(a_day[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
        self.checkout = self.departureDate
        self.departureDate = self.departureDate.replace('-', '/')

        self.adults = int(room_info.get('occ', '1'))
        if self.adults > 3:
            raise parser_except.ParserException(29, "房间入住人数过多")
        self.rooms = int(room_info.get('num', '1'))
        if self.rooms > 5:
            raise parser_except.ParserException(29, "预订房间数目过多")
        self.allow_num = int(self.adults) * self.rooms

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def crawl_data():
            return {
                'req': {
                    # 'url': 'http://www.shangri-la.com/cn/cairns/shangrila/reservations/',
                    'url': self.hotel_url,
                    'method': 'get',

                },
                'user_handler': [self.parse_data]
            }

        yield crawl_data

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def crawl_detail():

            return {
                'req': {
                    'url': self.hotel_url,
                    'method': 'post',
                    'data': self.payload,

                },
                'user_handler': [self.parse_detail]
            }

        yield crawl_detail

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def crawl_info():
            return {
                'req': {
                    'url': '{}select-room-rate/'.format(self.hotel_url),
                    'method': 'get',

                },
                'user_handler': [self.parse_info]
            }

        yield crawl_info

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel, async=True)
        def crawl_extra():
            p = []
            for url, data in self.item.items():
                p.append({
                    'req': {
                        'url': url,
                        'method': 'get',

                    },
                    'room_info': data
                })
            return p

        yield crawl_extra

    def parse_data(self, req, resp):

        node = etree.HTML(resp)
        try:
            a = node.xpath('//a[contains(@class, "btn_show_availability")]/@href')[0]
        except:
            raise parser_except.ParserException(22, '代理失效')
        self.hotel_id = re.compile(r"'hotelName': '(.*)'").findall(resp)[0]
        b = re.compile(r"('.*?')").findall(a)[0]
        __VIEWSTATE = node.xpath('//input[@id="__VIEWSTATE"]/@value')[0]
        __EVENTVALIDATION = node.xpath('//input[@id="__EVENTVALIDATION"]/@value')[0]
        b = re.compile(r"'(.*)'").findall(b)[0]

        self.payload = {
            "__EVENTTARGET": b,

            "__VIEWSTATE": __VIEWSTATE,

            "__EVENTVALIDATION": __EVENTVALIDATION,

            "ctl00$ContentPlaceHolder1$ctlDateSelection$stayDtpCheckInOut$dtpArrival$hidDateValue": self.arrivalDate,
            "ctl00$ContentPlaceHolder1$ctlDateSelection$stayDtpCheckInOut$dtpDeparture$hidDateValue": self.departureDate,
            "ctl00$ContentPlaceHolder1$ctlDateSelection$roomAdultChildSelection$hidNumRooms": str(self.rooms),
        }

        for num in range(self.rooms):
            key1 = "ctl00$ContentPlaceHolder1$ctlDateSelection$roomAdultChildSelection$ctl0{}$ddlNumberOfAdults" \
                .format(str(num))
            key2 = "ctl00$ContentPlaceHolder1$ctlDateSelection$roomAdultChildSelection$ctl0{}$ddlNumberOfAdults".format(
                str(num))
            key3 = 'ctl00$ContentPlaceHolder1$ctlDateSelection$roomAdultChildSelection$ctl0{}$ddlNumberOfChild'.format(
                str(num))
            self.payload[key1] = str(self.allow_num)
            self.payload[key2] = str(self.adults)
            self.payload[key3] = '0'

    def parse_detail(self, req, resp):
        if "sold-out" in resp:
            raise parser_except.ParserException(29, "抱歉，您所查找的日期暂时没有房间提供")
        # cookie = self.browser.br.cookies.items()[0][1]
        # self.cookie = 'ASP.NET_SessionId={}'.format(cookie)
        # # print resp
        # # pass

    def parse_info(self, req, resp):

        node = etree.HTML(resp)

        # __VIEWSTATE = node.xpath('//input[@id="__VIEWSTATE"]/@value')[0]
        # __EVENTVALIDATION = node.xpath('//input[@id="__EVENTVALIDATION"]/@value')[0]
        # __VIEWSTATEGENERATOR = node.xpath('//input[@id="__VIEWSTATEGENERATOR"]/@value')[0]

        content_list = node.xpath('//div[contains(@class, "reservation-list-select-rates")]')

        hotel_name_info = node.xpath('//title/text()')[0]
        hotel_name = hotel_name_info.split('|')[-1]
        city = hotel_name.split('香格里拉')[0]

        for content in content_list:
            room_types = content.xpath('./div[contains(@class, "reservation-list-roomname")]/a/text()')[0]
            room_type_content = content.xpath(
                './div[contains(@class, "select-rate-row")]|./div[contains(@class, "detail_box")]/div[contains(@class, "select-rate-row")]')

            for room in room_type_content:

                room_type_more = room.xpath(
                    './span/div[contains(@class, "reservation-list-room-rates")]/div[1]/div[contains(@class, "reservation-list-roomrate")]/a/text()')[
                    0]
                has_breakfast = ''
                is_breakfast_free = ''
                if '早餐' in room_type_more:
                    has_breakfast = 'Yes'
                    is_breakfast_free = 'Yes'

                url = "http://www.shangri-la.com{}".format(room.xpath(
                    './span/div[contains(@class, "reservation-list-room-rates")]/div[1]/div[contains(@class, "reservation-list-roomrate")]/a/@href')[
                                                               0])
                print url

                bed_type = '|'.join(room.xpath(
                    './span/div[contains(@class, "reservation-list-room-rates")]/div[1]/div[contains(@class, "reservation-list-roombed")]/div[contains(@class, "reservation-list-bedtype")]/label/text()'))
                room_type = "{}-{}".format(room_types, room_type_more)
                price_info = room.xpath(
                    './span/div[contains(@class, "reservation-list-room-rates")]/div[1]/div[contains(@class, "reservation-list-roomrate")]/span[contains(@class, "price")]/text()')[
                    0]
                currency, price = price_info.split(" ")
                price = str(price).replace(',', '')
                # tax = '-1'

                #
                self.item[url] = [bed_type, room_type, currency, price, hotel_name, city, has_breakfast,
                                  is_breakfast_free]
        # print self.item

    def parse_hotel(self, req, resp):
        info = req['room_info']
        # print info
        rooms = []
        room = Room()
        # print resp

        node = etree.HTML(resp)

        room_desc = node.xpath(
            '//div[contains(@class, "TabbedPanelsContentGroup")]/div[1]/p/text()|//div[contains(@class, "TabbedPanelsContentGroup")]/div[1]/ul/li/text()')
        description = '香格里拉承诺:您向香格里拉酒店或度假酒店取得预订保证后，我们因任何原因不能向您提供房间，我们将全费安排您入住另一间酒店，酒店将为您提供免费拨打长途电话服务、转介您入住另一间酒店，以及安排交通接载您回来我们的酒店，也即是我们本来最希望您入住的酒店。 家庭计划:酒店的家庭计划向与父母入住同一房间的12岁以下儿童提供免费住宿，每间房最多可住两位儿童。儿童餐饮计划:城市及度假酒店：登记入住酒店的6岁以下儿童宾客在一位付费成人宾客陪同下可于全日餐厅享用自助餐点，无需额外付费，至多2名儿童用餐。增加的6岁以下儿童及所有6岁及6岁以上12岁以下儿童可享受自助餐半价优惠。未登记入住的客人之12岁以下儿童，于全日制餐厅享用自助餐可享50%优惠。'
        for desc in room_desc:
            desc = desc.replace('\r', '').replace('\n', '').strip()
            if desc:
                if '平方米' in desc:
                    self.size = re.compile(r'\d+').findall(desc)[0]
                description += desc
        # print description
        extra_info = node.xpath('//div[contains(@class, "TabbedPanelsContentGroup")]/div[3]/p/text()')

        room_descs = description.join(extra_info)
        try:

            descriptions = node.xpath('//div[contains(@class, "TabbedPanelsContentGroup")]/div[4]/p/text()')[0]
        except:
            raise parser_except.ParserException(22, '代理失效')
        # size = re.compile(r'\d+\.\d+').findall(description)
        # print self.size
        # room.city = '自己传'
        room.source = 'shangrila'
        room.source_hotelid = self.hotel_id
        room.source_roomid = ''
        room.bed_type = info[0]
        room.room_type = info[1]
        room.currency = info[2]
        room.price = info[3]
        room.hotel_name = info[4]
        room.city = info[5]
        room.has_breakfast = info[6]
        room.is_breakfast_free = info[7]
        room.tax = -1

        room.real_source = '香格里拉'
        room.occupancy = self.allow_num
        room.size = self.size
        room.floor = -1
        room.check_in = self.check_in
        room.check_out = self.checkout
        room.rest = -1
        room.is_extrabed = ''
        room.is_extrabed_free = ''
        room.is_cancel_free = 'No'
        room.room_desc = room_descs
        room.return_rule = description
        room.pay_method = '在线支付'
        room.extrabed_rule = ''
        room.change_rule = descriptions
        room.others_info = json.dumps({
            'extra': {
                'breakfast': '',
                'payment': '在线支付',
                'return_rule': room.return_rule,
                'occ_des': self.allow_num
            }
        })
        room.guest_info = 'NULL'
        room.hotel_url = self.hotel_url
        r_tuple = (
            room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, room.room_type,
            room.real_source, int(room.occupancy), room.bed_type, int(room.size), room.floor, room.check_in,
            room.check_out,
            room.rest, float(room.price), float(room.tax), room.currency, room.is_extrabed, room.is_extrabed_free,
            room.has_breakfast, room.is_breakfast_free, room.is_cancel_free, room.room_desc, room.return_rule,
            room.pay_method, room.extrabed_rule, room.change_rule, room.others_info, room.guest_info, room.hotel_url
        )
        rooms.append(r_tuple)
        return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    spider = ShangRiLaSpider()

    spider.task = task
    #              酒店url&入住日期&离开日期&
    task.content = 'http://www.shangri-la.com/cn/beijing/shangrila/&3&20181020&'

    task.ticket_info = {
        'room_info': [{
            # 房间数/房间&[成人数
            'occ': 1,
            'num': 1,
        }]
    }

    spider.crawl()
    print spider.code
    print spider.result
    # file = "{}_{}_{}_{}.csv".format(task.content.split('&')[1], task.content[2], task.ticket_info['room_info'][0]['occ']
    #                                 ,task.ticket_info['room_info'][0]['num'])
    # for r in spider.result['hotel']:
    #     with open(file, 'a') as f:
    #         for c in r:
    #             f.write(str(c))
    #             f.write(',')
    #         f.write('\n')

