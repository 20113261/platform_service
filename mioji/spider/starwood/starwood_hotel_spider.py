# coding=utf-8

from lxml import etree
import re
import datetime
import json
from selenium import webdriver
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room
import csv


def get_cookie(hotel_url):
    cookie = ''

    # dcap = dict(DesiredCapabilities.PHANTOMJS)
    # dcap["phantomjs.page.settings.loadImages"] = False  # 禁止加载图片
    # driver = webdriver.PhantomJS(service_log_path='/search/spider_log/rotation/selenium/ghostdriver.log',
    #                              service_args=['--cookies-file=/search/spider_log/rotation/selenium/', ])
    #
    driver = webdriver.PhantomJS()
    try:
        driver.get(hotel_url)
    except:
        driver.quit()
    cookies = driver.get_cookies()
    for cook in cookies:
        cookie += "{}={};".format(cook['name'], cook['value'])
    # driver.quit()
    driver.close()

    return cookie


class StarWoodSpider(Spider):
    source_type = 'starwoodHotel'
    targets = {
        'hotel': {},
        'room': {}
    }
    old_spider_tag = {
        'starwoodHotel': {'required': ['room', 'hotel']}
    }

    def __init__(self, task=None):
        self.item = {}
        super(StarWoodSpider, self).__init__(task)

    def targets_request(self):

        content = self.task.content.split("&")

        room_info = self.task.ticket_info.get('room_info')

        self.id, self.stay_nights, a_day = content[0], content[1], content[2]
        self.arrivalDate = "{}-{}-{}".format(a_day[0:4], a_day[4:6], a_day[6:8])
        self.departureDate = str(datetime.datetime(int(a_day[0:4]), int(a_day[4:6]), \
                                                   int(a_day[6:])) + datetime.timedelta(days=int(self.stay_nights)))[:10]
        self.adults = len(room_info[0].get('adult_info', []))
        self.childs = len(room_info[0].get('child_info', []))
        try:
            self.verify_room = self.task.ticket_info.get('verify_room').get('room_info',[])[0]
        except:
            self.verify_room = ''
        rooms = len(room_info)
        self.allow_num = int(self.adults) * rooms
        self.first_url = 'https://www.starwoodhotels.com/preferredguest/room.html?departureDate={0}&refPage=' \
                         'property&ctx=search&arrivalDate={1}&priceMin=&iataNumber=&iATANumber=&sortOrder=&' \
                         'propertyId={2}&accessible=&numberOfRooms={3}&numberOfAdults={4}&bedType=' \
                         '&priceMax=&numberOfChildren={5}&nonSmoking='.format(self.departureDate, self.arrivalDate,
                                                                            self.id, rooms, self.adults, self.childs)

        self.hotel_url = 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html?propertyID={}' \
                         ''.format(self.id)

        self.cookies = get_cookie(self.hotel_url)

        if not self.cookies:
            raise parser_except.ParserException(27, 'not get cookie')

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def crawl_index():
            return {
                'req': {
                    'url': self.first_url,
                    'method': 'get',
                    'headers': {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Host': 'www.starwoodhotels.com',
                        'Referer': self.hotel_url,
                        # 'Upgrade-Insecure-Requests': '1',
                        'Pragma': 'no-cache',
                        # 'Connection': 'keep-alive',
                        'Cookie': self.cookies
                        # 'Cookie': 'aOmIj1jm=uniqueStateKey%3DAI_26BxiAQAAPGHgvmKqaKnOTek-L4zsCu65Fm2av6TMw7w7CfDGYBDUbQ98%26b%3Ddi14t4%26c%3DAIAC3xxiAQAA8Vi29htD3yuzlbVJWorYhyA1N5OejRCGg5Y-J13_fthzKWGr%26d%3D0%26a%3DAJzNCVoN_Sd3yVoq_SQ3nBoFiLdEgkV7bPwOr57a_mkf2fJpCqeDWx3E2MSJ03aqLNcDkbKl%253DC95fpnOWih7bFZGB2deWYjMvcOw2EOJvD%253DXkzlWJ-HAg-0OwxdEgkV_uNGOOOO'
                    },
                },
                'user_handler': [self.parse_info]
            }

        yield crawl_index
        # print self.item

        # for url, data in self.item.items():
        #     print url, data

        # print self.item.items()

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_room, async=True)
        def crawl_info():
            p = []
            for url, data in self.item.items():

                p.append({
                    'req': {
                        'url': url,
                        'method': 'get',
                        'headers': {
                            'Pragma': "no-cache",
                            'Accept-Encoding': "gzip, deflate, br",
                            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                            'Referer': self.first_url,
                            # 'Cookie': "JSESSIONID=00008dOBxRq9VxqAgKnTZwQhxWt:16jpvqbgd;",
                            'Cookie': self.cookies,
                            'Cache-Control': "no-cache",
                        },
                    },
                    'rooma': data
                })
            return p


        yield crawl_info

    def parse_info(self, req, resp):
        node = etree.HTML(resp)
        error_text = node.xpath("//div[@class='altAvailabilityMsg']/text()")
        if error_text:
            raise parser_except.ParserException(29, 'error task')
        else:
            try:
                hotel_name = node.xpath('//span[@class="propertyName"]/a/text()')[0].strip()
            except:
                hotel_name = ''
            tree_list = node.xpath('//div[contains(@class, "roomContainer")]')
            r_list = []
            for tree in tree_list:
                room = Room()
                city = ''
                source = 'starwood'
                source_hotelid = self.id
                try:
                    room_id = tree.xpath('./div[@class="roomBlock"]/div[@class="rateContainer "]/div[contains(@class, "rateDetails")]/@data-rateplanid')[0]
                except:
                    room_id = ''

                room_type = tree.xpath('./h1/text()')[0]
                real_source = 'starwood'
                info_list = tree.xpath('./div[@class="roomBlock"]/div[@class="rateContainer "]//'
                                       'div[@class="rateDetailsBlock"]')

                for info in info_list:
                    room.hotel_name = hotel_name
                    room.city = city
                    room.source = source
                    room.source_hotelid = source_hotelid
                    room.source_roomid = room_id

                    room.real_source = real_source

                    currency_price = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                                'span/span[@class="roomRate"]/text()')[0]

                    try:
                        total_price = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                                 'span/span[@class="roomTotal"]/text()')[0]
                    except:
                        total_price = currency_price
                    try:

                        currency = ''.join(re.findall(r'([A-Za-z])', currency_price))
                        price = ''.join(re.findall(r'(\d+)', currency_price))
                        total_price = ''.join(re.findall(r'(\d+)', total_price))
                        tax = int(total_price) - int(price)
                        if tax == 0:
                            tax = -1

                    except:
                        price_info = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                                'span/span[@class="roomRate"]/text()')
                        price = price_info[0]
                        currency = 'Starpoints'
                        tax = -1
                        if 'USD' in price_info:
                            tax = price_info[-1]

                    room.currency = currency
                    room.occupancy = int(self.adults)
                    room.price = float(price.replace(',', ''))*int(self.stay_nights)
                    # print room.priceq
                    room.tax = float(tax)
                    # print room.price.replace(',', '')
                    # print room.tax

                    title = ''.join(info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/h3/text()'))
                    title = title.replace('\t', '').replace('\r', '').replace('\n', '').strip()
                    room.bed_type = tree.xpath('./h2/span/text()')[0]

                    room.room_type = '{}'.format(room_type)
                    room.has_breakfast = 'NO'
                    room.is_breakfast_free = 'NO'
                    foods_res = ''
                    if 'breakfast' in title or '早餐' in title:
                        room.has_breakfast = 'YES'
                        room.is_breakfast_free = 'YES'
                        foods_res = title
                    elif 'Cool Summer' in title:
                        room.has_breakfast = 'YES'
                        room.is_breakfast_free = 'YES'
                        foods_res = 'Daily breakfast'
                    # print title, foods_res

                    cancel_info = ''.join(
                        info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/ul/li[1]/text()'))
                    room.is_cancel_free = ''
                    # if 'Free cancellation' or '免费取消' in cancel_info:
                    #     room.is_cancel_free = 'YES'

                    return_rule = info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/'
                                             'ul/li/text()')
                    return_rules = ''.join([rule.replace('\t', '').replace('\n', '').replace('\r', '').strip()
                                            for rule in return_rule[:1]])
                    room.return_rule = return_rules
                    link = info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/ul/li/a/@href')[0]
                    links = 'https://www.starwoodhotels.com{}'.format(link)

                    # room.size = tree.xpath('.//div[@class="roomDetails"]/ul/li[@class="roomSize"]/text()')[0]
                    try:
                        size = tree.xpath('.//div[@class="roomDetails"]/ul/li[@class="roomSize"]/text()')[0]
                        size_info = size
                        sizes = re.compile(r'(\d+)').findall(size)
                        size_data = sizes[-1]
                        if '-' in size:
                            size_data = sizes[-2]
                        room.size = int(size_data)
                    except:
                        size_info = ''
                        room.size = -1

                    room.floor = -1
                    room.check_in = self.arrivalDate
                    room.check_out = self.departureDate
                    room.rest = -1

                    room.change_rule = ''
                    try:
                        room.room_desc = '|'.join(tree.xpath('.//div[@class="roomDetails"]/ul/li/text()')[1:-2])
                    except:
                        room.room_desc = ''
                    room.pay_method = '在线支付'
                    room.others_info = json.dumps({
                        'extra': {
                            'breakfast': foods_res,
                            'payment': '在线支付',
                            'return_rule': room.return_rule,
                            'occ_des': '',
                            'occ_num':json.dumps({'adult_num': self.adults, 'child_num': self.childs}),
                            'size_info': size_info
                        }
                    })
                    room.guest_info = ''
                    room.hotel_url = self.hotel_url
                    self.item[links] = dict(
                        hotel_name=room.hotel_name,
                        city=room.city,
                        source=room.source,
                        source_hotelid=room.source_hotelid,
                        source_roomid=room.source_roomid,
                        real_source=room.real_source,
                        currency=room.currency,
                        occupancy=room.occupancy,
                        price=room.price,
                        tax=room.tax,
                        room_type=room.room_type,
                        has_breakfast=room.has_breakfast,
                        is_breakfast_free=room.is_breakfast_free,
                        is_cancel_free=room.is_cancel_free,
                        return_rule=room.return_rule,
                        bed_type=room.bed_type,
                        size=room.size,
                        floor=room.floor,
                        check_in=room.check_in,
                        check_out=room.check_out,
                        rest=room.rest,
                        change_rule=room.change_rule,
                        room_desc=room.room_desc,
                        pay_method=room.pay_method,
                        others_info=room.others_info,
                        guest_info=room.guest_info,
                        hotel_url=room.hotel_url,
                    )

    def parse_hotel(self, req, resp):
        pass

    def parse_room(self, req, resp):
        # print '-----'
        room = Room()
        rooms = []
        room_info = req['rooma']

        room.hotel_name = room_info["hotel_name"]
        room.city = room_info["city"]
        room.source = room_info["source"]
        room.source_hotelid = room_info["source_hotelid"]
        room.source_roomid = room_info["source_roomid"]
        room.real_source = room_info["real_source"]
        room.currency = room_info["currency"]
        room.occupancy = room_info["occupancy"]
        room.price = room_info["price"]
        room.tax = room_info["tax"]
        room.room_type = room_info["room_type"]
        room.has_breakfast = room_info["has_breakfast"]
        room.is_breakfast_free = room_info["is_breakfast_free"]
        room.is_cancel_free = room_info["is_cancel_free"]
        room.return_rule = room_info["return_rule"]
        room.bed_type = room_info["bed_type"]
        room.size = room_info["size"]
        room.floor = room_info["floor"]
        room.check_in = room_info["check_in"]
        room.check_out = room_info["check_out"]
        room.rest = room_info["rest"]
        room.change_rule = room_info["change_rule"]
        room.room_desc = room_info["room_desc"]
        room.pay_method = room_info["pay_method"]
        room.others_info = room_info["others_info"]
        room.guest_info = room_info["guest_info"]
        room.hotel_url = room_info["hotel_url"]
        # print room.price
        node = etree.HTML(resp)
        bed_info = ''.join(node.xpath('//div[@class="noteItemContent"]/ul/li/text()'))
        room.is_extrabed = 'NO'
        room.is_extrabed_free = 'NO'
        room.extrabed_rule = bed_info
        if 'CNY' in bed_info or 'per night' in bed_info:
            room.is_extrabed = 'YES'
            room.is_extrabed_free = 'NO'
            room.extrabed_rule = bed_info

        r_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid, \
                                  room.source_roomid, room.real_source, room.room_type, int(room.occupancy), \
                                  room.bed_type, int(room.size), int(room.floor), room.check_in, room.check_out, \
                                  int(room.rest), float(room.price), float(room.tax), room.currency, room.pay_method, \
                                  room.is_extrabed, room.is_extrabed_free, room.has_breakfast, \
                                  room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, \
                                  room.return_rule, room.change_rule, room.room_desc, \
                                  room.others_info, room.guest_info)
        rooms.append(r_tuple)
        return rooms


if __name__ == "__main__":
    from mioji.common.task_info import Task
    # from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    spider = StarWoodSpider(task)
    #              酒店id&入住日期&离开日期&
    task.content = '3192&1&20180526'

    task.ticket_info = {
        'room_info': [
            {'adult_info': [33, 33], 'child_info': [7, ]},
            # {'adult_info': [33, 22], 'child_info': [7, 12]}
        ]
    }
    # task.ticket_info['verify_room'] = {
    #     'room_info': ['豪华客房（无烟）']
    # }

    spider.crawl()
    print spider.code
    print json.dumps(spider.result, ensure_ascii=False)
    with open('starwood3.csv', 'a+') as f:
        for r in spider.result['hotel']:
            for c in r:
                f.write(json.dumps(c, ensure_ascii=False))
                f.write(',')
            f.write('\n')
    # with open('starwood.csv', 'a+') as f:
        # f.write(json.dumps(spider.result['hotel'], ensure_ascii=False))