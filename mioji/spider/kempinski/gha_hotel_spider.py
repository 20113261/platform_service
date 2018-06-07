# coding=utf-8

from lxml import etree
import requests
import re
import urllib
import urlparse
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room
import json
import datetime


class GhaSpider(Spider):
    source_type = 'ghaHotel'
    targets = {
        'hotel': {},
        'room': {}
    }
    old_spider_tag = {
        'ghaHotel': {'required': ['room', 'hotel']}
    }

    def __init__(self, task=None):

        self.list = []

        self.urls = {}
        super(GhaSpider, self).__init__(task)

    def get_parems(self):

        self.hotelid, Night, start_date = self.task.content.split("&")
        self.adults_num = len(self.task.ticket_info.get('room_info')[0].get('adult_info'))
        self.child_num = len(self.task.ticket_info.get('room_info')[0].get('child_info'))

        room_info = self.task.ticket_info.get('room_info', [])
        try:
            self.verify_room = self.task.ticket_info.get('verify_room').get('room_info', '')
        except:
            self.verify_room = ''

        checkin = datetime.datetime.strptime(start_date, "%Y%m%d")
        end_data =checkin + datetime.timedelta(days=int(Night))
        self.start_date = "{}-{}-{}".format(start_date[0:4], start_date[4:6], start_date[6:8])
        # self.end_date = "{}-{}-{}".format(end_date[0:4], end_date[4:6], end_date[6:8])
        self.end_date = end_data.strftime("%Y-%m-%d")
        if not room_info:

            raise parser_except.ParserException(12, '获取人数和房间数失败')
        data = {
            "hotel_code": self.hotelid,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        self.adults = 0
        for index, room in enumerate(room_info):
            data["rooms[{}][adults]".format(index + 1)] = len(room.get('adult_info', []))
            data["rooms[{}][children]".format(index + 1)] = len(room.get('child_info', []))
            if len(room.get('adult_info', [])) > self.adults:
                self.adults = len(room.get('adult_info', []))
            # print roomget('child_info', [])
            for index_c, age in enumerate(room.get('child_info', [])):
                data["child_ages[{}][{}]".format(index+1, index_c+1)] = age
        # print data
        return urllib.urlencode(data)

    def targets_request(self):

        self.parems = self.get_parems()

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_room)
        def get_html():
            return {
                "req": {
                    "url": "https://zh.discoveryloyalty.com/booking/select_rooms?"+self.parems,
                    "method": "get"
                },
                "key":"value",
            }
        yield get_html
        if self.verify_room:
            @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=self.parse_hotel)
            def get_detail():
                urls = []
                for url, datas in self.urls.items():
                    print 'url>>>>>' + url
                    print datas[0]
                    if datas[0].room_type == self.verify_room:
                        urls.append({
                            "req": {
                                "url": url,
                                "method": "get"
                            },
                            # 'user_handler': [self.parse_info],
                            "room":self.urls[url],
                        })
                return urls
            yield get_detail

    def parse_room(self, req, resp):
        if self.verify_room:
            select = etree.HTML(resp)
            room_list = select.xpath("//div[@class='Content-sidebar-fullWidthInner']/div[@class='RoomView RoomView--ibe']"
                                     "/div[@class='RoomView-body']")

            for index,room in enumerate(room_list):
                hotel_name = select.xpath("//div[@class='u-cf']/h3/a/text()")[0].replace("\n",'').strip()

                name = ''
                try:
                    name = room.xpath("./div[@class='RoomView-body-desc']/h4/text()")[0]
                except:
                    name = ''
                details_Id, rates_id = room.xpath("./div[@class='RoomView-body-cta']/div[@class='RoomView-btns']/div/bu"
                                                  "tton/@data-target")
                details = select.xpath("//div[@id='{}']".format(details_Id.replace("#",'')))[0].xpath('string(.)').strip()
                room_desc = ''.join(details).replace('\n', ' ').replace(" ", '').replace("+", '')
                rate = select.xpath("//div[@id='{}']/div[@class='RoomView RoomView--rates ']|//div[@id='{}']/div[@class="
                                    "'more-rates']/div[@class='RoomView RoomView--rates ']".format(rates_id.replace("#",''),
                                                                                                   rates_id.replace("#",'')))
                reststr = room.xpath("./div[@class='RoomView-body-desc']/span[@class='RoomView-body-subTitle']/text()")

                for rate_item in rate:
                    room = Room()
                    room_name = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-desc']/h4/text()")[0]
                    room.hotel_name = hotel_name
                    room.source = 'gha'
                    room.source_hotelid = self.hotelid
                    room.room_type = u"-".join([name])
                    self.room_type = room.room_type
                    room.room_desc = room_desc
                    if reststr:
                        restnum = re.findall('(\d+)', reststr[0])
                        if restnum:
                            room.rest = restnum[0]
                    else:
                        room.rest = '-1'
                    url = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/div/div/a/@href")
                    occupancy = re.findall(u'入住(\d+)',room_desc,re.S)
                    if occupancy:
                        room.occupancy = int(occupancy[0])
                    else:
                        room.occupancy = int(self.adults)

                    if u'特大' in room_desc and u'单人床' in room_desc:
                        room.bed_type = u'特大床或单人床'
                    elif u'特大' in room_desc and u'双床' in room_desc:
                        room.bed_type = u'特大床或单人床'
                    elif u"特大床" in room_desc or u"特大床" in room.hotel_name:
                        room.bed_type = u'特大床'
                    elif u"单人床" in room_desc or u'单人床' in room.hotel_name:
                        room.bed_type = u"单人床"
                    elif u'特大号床' in room_desc or u'特大号床' in room.hotel_name:
                        room.bed_type = u'特大床'
                    elif u'双人床' in room_desc or u'双人床' in room.hotel_name:
                        room.bed_type = u'双人床'
                    elif u'大床房' in room_desc or u'大床房' in room.hotel_name:
                        room.bed_type = u'大床房'
                    elif u'大床' in room_desc or u'大床' in room.hotel_name:
                        room.bed_type = u'大床'
                    else:
                        room.bed_type = 'NULL'
                    print room_desc
                    size = re.findall(u'(\d+)平方米',room_desc)
                    sizes = re.findall(u'(\d+)平方米平方英尺', room_desc)
                    sizey = re.findall(u'(\d+)平方英尺', room_desc)
                    print room_desc
                    size_info = ''
                    try:
                        try:
                            size_info = re.compile(u'(面积为\s*\d+[-至]*\d*\s*\W*[，。]{1})').findall(room_desc)[0]
                        except:
                            size_info = re.compile(u'(面积为\s*\d+[-至]*\d*\s*\W*)').findall(room_desc)[0]
                    except:
                        size_info = ''
                    if len(size_info) > 100:
                        size_info = size_info.split('，')[0]
                    print size_info
                    if size:
                        room.size = int(size[0])
                    if sizes:
                        room.size = round(int(sizes[0])/10.7639104, 2)
                    if sizey:
                        room.size = round(int(sizey[0]) / 10.7639104, 2)
                    room.check_in = self.start_date
                    room.check_out = self.end_date
                    # print room.hotel_name
                    # print details_Id,rates_id
                    self.urls["https://zh.discoveryloyalty.com" + url[0]] = [room, size_info]

        else:
            rooms = []

            select = etree.HTML(resp)

            room_list = select.xpath(
                "//*[@id='room-1']/div[@class='RoomView RoomView--ibe']"
                "/div[@class='RoomView-body']")
            print len(room_list)
            for index, room in enumerate(room_list):
                hotel_name = select.xpath("//div[@class='u-cf']/h3/a/text()")[0].replace("\n", '').strip()

                name = ''
                try:
                    name = room.xpath("./div[@class='RoomView-body-desc']/h4/text()")[0]
                except:
                    name = ''
                details_Id, rates_id = room.xpath("./div[@class='RoomView-body-cta']/div[@class='RoomView-btns']/div/bu"
                                                  "tton/@data-target")
                details = select.xpath("//div[@id='{}']".format(details_Id.replace("#", '')))[0].xpath(
                    'string(.)').strip()
                room_desc = ''.join(details).replace('\n', ' ').replace(" ", '').replace("+", '')
                rate = select.xpath(
                    "//div[@id='{}']/div[@class='RoomView RoomView--rates ']|//div[@id='{}']/div[@class="
                    "'more-rates']/div[@class='RoomView RoomView--rates ']".format(rates_id.replace("#", ''),
                                                                                   rates_id.replace("#", '')))
                reststr = room.xpath("./div[@class='RoomView-body-desc']/span[@class='RoomView-body-subTitle']/text()")
                print hotel_name, '===='
                for rate_item in rate:
                    room = Room()
                    room.real_source = 'gha'
                    room_name = ''
                    try:
                        room_name = \
                            rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-desc']/h4/text()")[0]
                    except:
                        room_name = ''
                    print room_name, '<><><><><>>'
                    room.hotel_name = hotel_name
                    room.source = 'gha'
                    room.source_hotelid = self.hotelid
                    room.room_type = u"".join([name])
                    self.room_type = room.room_type
                    room.room_desc = room_desc
                    if reststr:
                        restnum = re.findall('(\d+)', reststr[0])
                        if restnum:
                            room.rest = restnum[0]
                    else:
                        room.rest = '-1'
                    url = rate_item.xpath(
                        "./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/div/div/a/@href")
                    occupancy = re.findall(u'入住(\d+)', room_desc, re.S)
                    if occupancy:
                        room.occupancy = int(occupancy[0])
                    else:
                        room.occupancy = int(self.adults)

                    if u'特大' in room_desc and u'单人床' in room_desc:
                        room.bed_type = u'特大床或单人床'
                    elif u'特大' in room_desc and u'双床' in room_desc:
                        room.bed_type = u'特大床或单人床'
                    elif u"特大床" in room_desc or u"特大床" in room.hotel_name:
                        room.bed_type = u'特大床'
                    elif u"单人床" in room_desc or u'单人床' in room.hotel_name:
                        room.bed_type = u"单人床"
                    elif u'特大号床' in room_desc or u'特大号床' in room.hotel_name:
                        room.bed_type = u'特大床'
                    elif u'双人床' in room_desc or u'双人床' in room.hotel_name:
                        room.bed_type = u'双人床'
                    elif u'大床房' in room_desc or u'大床房' in room.hotel_name:
                        room.bed_type = u'大床房'
                    elif u'大床' in room_desc or u'大床' in room.hotel_name:
                        room.bed_type = u'大床'
                    else:
                        room.bed_type = 'NULL'

                    urls = "https://zh.discoveryloyalty.com" + url[0]
                    code = urlparse.parse_qs(urls)["fees_room_type"] + \
                           urlparse.parse_qs(urls)[
                               "fees_rate_code"]
                    room.source_roomid = ''.join(code)
                    print room_desc

                    sizes = None
                    sizey = None
                    sizesqm = None
                    size = re.findall(u'(\d+)平方米', room_desc)
                    if not size:
                        sizes = re.findall(u'(\d+)平方米平方英尺', room_desc)
                        if not sizes:
                            sizey = re.findall(u'(\d+)平方英尺', room_desc)
                            if not sizey:
                                sizesqm = re.findall(u'(\d+)sqm',room_desc)
                    size_info = ''
                    try:
                        size_info = re.compile(u'\s*(\d+\s*[-至]*\s*\d*\s*平方[米英尺]+)\s*').findall(room_desc)[0]
                    except:
                        try:
                            size_info = re.compile(u'\s*(\d+\s*[-至]*\s*\d*\s*)sqm').findall(room_desc)[0] + u'平方米'
                        except:
                            size_info = ''
                    if len(size_info) > 100:
                        size_info = size_info.split('，')[0]
                    print size_info
                    if size:
                        room.size = int(size[0])
                    if sizes:
                        room.size = round(int(sizes[0]) / 10.7639104, 2)
                    if sizey:
                        room.size = round(int(sizey[0]) / 10.7639104, 2)
                    if sizesqm:
                        room.size = round(int(sizesqm[0]),2)
                    room.check_in = self.start_date
                    room.check_out = self.end_date
                    room.pay_method = u'在线支付'
                    currency = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/"
                                                "div[@class='u-cf']/div[2]/div[contains(@class, 'RoomRates')]/div[@class='RoomRates-inner']/"
                                                "div[@class='RoomRates-cell']/div[@class='RoomRates-currency']/text()")[
                        0]
                    # room.price = price
                    prices = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/"
                                             "div[@class='u-cf']/div[2]/div[contains(@class, 'RoomRates')]/div[@class='RoomRates-inner']/"
                                             "div[@class='RoomRates-cell']/div[@class='RoomRates-rate']/strong/text()|./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/"
                                             "div[@class='u-cf']/div[2]/div[contains(@class, 'RoomRates')]/div[@class='RoomRates-inner']/"
                                             "div[@class='RoomRates-cell']/div[@class='RoomRates-rate']/strong//small/text()")

                    room.price = ''.join(prices).strip().replace(',', '')
                    room.currency = currency.replace('\n', '').strip()
                    room.others_info = json.dumps({
                            'extra': {
                                'breakfast': '',
                                'payment': u'在线支付',
                                'return_rule': room.return_rule,
                                'occ_des': '可以入住{}人'.format(room.occupancy),
                                'occ_num': json.dumps({'adult_num': self.adults_num, 'child_num': self.child_num}),
                                'size_info': size_info
                            }
                        },ensure_ascii=False)
                    rooms.append((room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                                  room.real_source, room.room_type, room.occupancy, room.bed_type, room.size,
                                  room.floor, \
                                  room.check_in, room.check_out, int(room.rest), float(room.price), float(room.tax),
                                  room.currency,
                                  room.pay_method, \
                                  room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                                  room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule,
                                  room.room_desc, \
                                  room.others_info, room.guest_info))

            return rooms

    def parse_hotel(self, req, resp):

        code = urlparse.parse_qs(req["req"]["url"])["fees_room_type"] + urlparse.parse_qs(req["req"]["url"])[
            "fees_rate_code"]
        room = req["room"][0]
        size_info = req['room'][1]
        print size_info
        room.source_roomid = ''.join(code)
        room.real_source = 'gha'

        select = etree.HTML(resp)
        spans = select.xpath("//div[@class='Grid-cell u-size3of12']")
        for span in spans:
            if span.xpath('./h4/text()'):
                if u'税' in span.xpath('./h4/text()')[0]:
                    if span.xpath('./span/text()'):
                        taxList = span.xpath('./span/text()')
                        room.tax = 0.00
                        for Rtax in taxList:
                            tax = re.findall("(\d*,*\d*\.\d*)",Rtax)[0]
                            room.tax += float(tax.replace(",",''))
                            room.currency = re.findall(r"([A-Z]+)", Rtax)[0]
                        room.tax = round(room.tax,2)
                    else:
                        room.tax = -1
                elif u'房' in span.xpath('./h4/text()')[0]:
                    priceList = span.xpath('./span/text()')
                    room.price = 0
                    for Rprice in priceList:
                        price = re.findall("(\d*,*\d*\.\d*)",Rprice)[0]
                        room.price += float(price.replace(",",''))
                        room.currency = re.findall(r"([A-Z]+)", Rprice)[0]
                    room.price = round(room.price,2)
        for li in select.xpath("//ul/li/text()"):

            room.room_desc += li.replace("+",'')
        # print room.room_desc
        if u"早餐" in room.room_desc:
            room.has_breakfast = "Yes"
            room.is_breakfast_free = "Yes"
        else:
            room.has_breakfast = "No"
            room.is_breakfast_free = "No"
        room.return_rule = select.xpath("//ul/li[2]/text()")[0]
        if room.has_breakfast == "Yes":
            breakfast = u'含早餐'
        else:
            breakfast = u"不含早餐"
        room.others_info = json.dumps({
                            'extra': {
                                'breakfast': breakfast,
                                'payment': u'在线支付',
                                'return_rule': room.return_rule,
                                'occ_des': '可以入住{}人'.format(room.occupancy),
                                'occ_num': json.dumps({'adult_num': room.occupancy, 'child_num': self.child_num}),
                                'size_info': size_info
                            }
                        },ensure_ascii=False)
        if u'不可取消' in room.return_rule:
            room.is_cancel_free = 'No'
        elif u'免扣':
            room.is_cancel_free = 'Yes'
        else:
            room.is_cancel_free = 'NULL'
        room.pay_method = u'在线支付'
        print self.verify_room,'-----verify_room'
        r_list = []
        # for data in self.urls.values():
        #     if data.room_type != self.verify_room:
        #         r_list.append((data.hotel_name, data.city, data.source, data.source_hotelid, data.source_roomid, \
        #                     data.real_source, data.room_type, data.occupancy, data.bed_type, data.size, data.floor, \
        #                     data.check_in, data.check_out, int(data.rest), data.price, data.tax, data.currency, data.pay_method, \
        #                     data.is_extrabed, data.is_extrabed_free, data.has_breakfast, data.is_breakfast_free, \
        #                     data.is_cancel_free, data.extrabed_rule, data.return_rule, data.change_rule, data.room_desc, \
        #                     data.others_info, data.guest_info))

        r_list.append((room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                 room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                 room.check_in, room.check_out, int(room.rest), room.price, room.tax, room.currency, room.pay_method, \
                 room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                 room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                 room.others_info, room.guest_info))

        return r_list



if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, simple_get_socks_proxy_new
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()


    # 酒店id&入住日期&离开日期&
    # task.content = 'ANUSM1&1&20180530'
    # task.content = 'PRPEN&1&20180713'
    task.content = 'PRMLA&1&20180713'
    task.content = 'THVH&1&20180526'
    task.content = 'VILER&1&20180526'
    task.content = 'WASSHO&1&20180526'
    task.content = 'TUSNTL&1&20180526'
    task.content = 'THSVGSAN&1&20180526'
    task.content = 'PPXMN&1&20180526'
    task.content = 'KIBKK1&1&20180526'
    task.content = 'PRPEN&1&20180526'

    task.ticket_info['room_info'] = [
                                {"adult_info": [33,],
                                 "child_info": [7,2]},
                                # {"adult_info": [33,22],
                                #  "child_info": [2,3]}
                                ]

    # task.ticket_info['verify_room'] = {
    #     'room_info': "豪华园景客房"
    # }
    spider = GhaSpider(task)
    spider.crawl()
    print spider.code
    print spider.result
    print json.dumps(spider.result['room'],ensure_ascii=False,indent=4)
    # with open('gha4.csv', 'a+') as f:
    #     for r in spider.result['hotel']:
    #         for c in r:
    #             f.write(json.dumps(c, ensure_ascii=False))
    #             f.write(',')
    #         f.write('\n')