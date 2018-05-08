# coding=utf-8

from lxml import etree
import requests
import re
import urllib
import urlparse
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room


class GhaSpider(Spider):
    source_type = 'ghaHotel'
    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'ghaHotel': {'required': ['room']}
    }

    def __init__(self, task=None):

        self.list = []
        super(GhaSpider, self).__init__(task)
        self.task = task
        self.parems = self.get_parems()
        self.urls = {}

    def get_parems(self):

        self.hotelid, start_date, end_date = self.task.content.split("&")
        room_info = self.task.ticket_info.get('room_info', [])
        self.start_date = "{}-{}-{}".format(start_date[0:4], start_date[4:6], start_date[6:8])
        self.end_date = "{}-{}-{}".format(end_date[0:4], end_date[4:6], end_date[6:8])
        if room_info:
            self.adults = room_info[0].get('occ', '1')
            rooms = room_info[0].get('num', '1')
        else:
            raise parser_except.ParserException(29, '获取人数和房间数失败')
        data = {
            "hotel_code": self.hotelid,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        for room in range(int(rooms)):
            data["rooms[{}][adults]".format(room+1)] = self.adults
            data["rooms[{}][children]".format(room+1)] = "0"
        return urllib.urlencode(data)

    def targets_request(self):

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_html():
            return {
                "req": {
                    "url": "https://zh.gha.com/booking/select_rooms?"+self.parems,
                    "method": "get"
                },
                'user_handler': [self.parse_info],
                "key":"value",
            }
        yield get_html

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=self.parse_hotel)
        def get_detail():
            urls = []
            for url in self.urls.keys():
                urls.append({
                    "req": {
                        "url": url,
                        "method": "get"
                    },
                    'user_handler': [self.parse_info],
                    "room":self.urls[url],
                })
            return urls
        yield get_detail

    def parse_info(self, req, resp):

        select = etree.HTML(resp)
        details_list = select.xpath("//div[@class='Content-sidebar-fullWidthInner']/div[@class='RoomView RoomView--ibe"
                                    "']/div[@class='RoomView-body']")
        room_list = select.xpath("//div[@class='Content-sidebar-fullWidthInner']/div[@class='RoomView RoomView--ibe']"
                                 "/div[@class='RoomView-body']")

        for index,room in enumerate(room_list):
            name = room.xpath("./div[@class='RoomView-body-desc']/h4/text()")[0]
            details_Id, rates_id = room.xpath("./div[@class='RoomView-body-cta']/div[@class='RoomView-btns']/div/bu"
                                              "tton/@data-target")
            details = select.xpath("//div[@id='{}']/text()".format(details_Id.replace("#",'')))
            room_desc = details[0].strip()
            rate = select.xpath("//div[@id='{}']/div[@class='RoomView RoomView--rates ']|//div[@id='{}']/div[@class="
                                "'more-rates']/div[@class='RoomView RoomView--rates ']".format(rates_id.replace("#",''),
                                                                                               rates_id.replace("#",'')))
            reststr = room.xpath("./div[@class='RoomView-body-desc']/span[@class='RoomView-body-subTitle']/text()")

            for rate_item in rate:
                room = Room()
                room_name = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-desc']/h4/text()")[0]
                room.hotel_name = u"-".join([name,room_name])
                room.source = 'gha'
                room.source_hotelid = self.hotelid
                room.room_type = room_name
                room.room_desc = room_desc
                if reststr:
                    restnum = re.findall('(\d+)', reststr[0])
                    if restnum:
                        room.rest = restnum[0]
                else:
                    room.rest = '-1'
                url = rate_item.xpath("./div[@class='RoomView-body']/div[@class='RoomView-body-cta']/div/div/a/@href")
                self.urls["https://zh.gha.com"+url[0]] = room
                room_desc = room_desc.replace(' ', '')
                occupancy = re.findall(u'入住(\d+)',room_desc,re.S)
                if occupancy:
                    room.occupancy = int(occupancy[0])
                else:
                    room.occupancy = int(self.adults)

                if u'特大' in room_desc and u'单人床' in room_desc:
                    room.bed_type = u'特大床或单人床'
                elif u'特大' in room_desc and u'双床' in room_desc:
                    room.bed_type = u'特大床或单人床'
                elif u"特大床" in room_desc:
                    room.bed_type = u'特大床'
                elif u"单人床" in room_desc:
                    room.bed_type = u"单人床"
                elif u'特大号床' in room_desc:
                    room.bed_type = u'特大床'
                elif u'双人床' in room_desc:
                    room.bed_type = u'双人床'
                else:
                    room.bed_type = 'NULL'
                size = re.findall(u'(\d+)平方米',room_desc)
                if size:
                    room.size = size[0]
                room.check_in = self.start_date
                room.check_out = self.end_date
                # print room.hotel_name
                # print details_Id,rates_id

    def parse_hotel(self, req, resp):
        room = req["room"]
        code = urlparse.parse_qs(req["req"]["url"])["fees_room_type"]+urlparse.parse_qs(req["req"]["url"])["fees_rate_code"]
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
        has_breakfast = select.xpath("//ul/li[1]/text()")[0]
        if u"早餐" in has_breakfast:
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
        room.other_infos = {
                            'extra': {
                                'breakfast': breakfast,
                                'payment': u'在线支付',
                                'return_rule': room.return_rule,
                                'occ_des': room.occupancy
                            }
                        }
        room.pay_method = u'在线支付'
        return [(room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid, \
                 room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor, \
                 room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency, room.pay_method, \
                 room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free, \
                 room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc, \
                 room.other_infos, room.guest_info)]


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()


    # 酒店id&入住日期&离开日期&
    task.content = 'KICKG1&20180324&20180328'

    task.ticket_info = {
        'room_info': [{
            # 房间数&成人数&儿童数
            'occ': 1,
            'num': 1,
        }]
    }
    spider = GhaSpider(task)
    spider.crawl()
    print spider.code
    print spider.result
    import json
    with open('sss.json','w') as w:
        w.write(json.dumps(spider.result,ensure_ascii=False))
