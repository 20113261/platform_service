# coding=utf-8

from lxml import etree
import requests
import re
import datetime

from selenium import webdriver
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room


def get_cookie(hotel_url):
    cookie = ''
    wb = webdriver.PhantomJS()
    wb.get(hotel_url)
    cookies = wb.get_cookies()
    for cook in cookies:
        cookie += "{}={};".format(cook['name'], cook['value'])

    return cookie


class StarWoodSpider(Spider):
    source_type = 'starwoodHotel'
    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'starwoodHotel': {'required': ['room']}
    }

    def __init__(self, task=None):

        self.list = []
        super(StarWoodSpider, self).__init__(task)

    def targets_request(self):

        content = self.task.content.split("&")
        try:
            room_info = self.task.ticket_info.get('room_info')[0]
        except:
            raise parser_except.ParserException(29, '获取人数和房间数失败')

        self.id, stay_nights, a_day = content[0], content[1], content[2]
        self.arrivalDate = "{}-{}-{}".format(a_day[0:4], a_day[4:6], a_day[6:8])

        self.departureDate = str(datetime.datetime(int(a_day[0:4]), int(a_day[4:6]), \
                                               int(a_day[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
        adults = room_info.get('occ', '1')
        rooms = room_info.get('num', '1')
        self.allow_num = int(adults)*rooms
        self.first_url = 'https://www.starwoodhotels.com/preferredguest/room.html?departureDate={0}&refPage=' \
                         'property&ctx=search&arrivalDate={1}&priceMin=&iataNumber=&iATANumber=&sortOrder=&' \
                         'propertyId={2}&accessible=&numberOfRooms={3}&numberOfAdults={4}&bedType=' \
                         '&priceMax=&numberOfChildren=0&nonSmoking='.format(self.departureDate, self.arrivalDate,
                                                                            self.id, rooms, adults)

        self.hotel_url = 'https://www.starwoodhotels.com/preferredguest/property/overview/index.html?propertyID={}' \
                         ''.format(self.id)
        try:
            self.cookies = get_cookie(self.hotel_url)
        except:
            raise parser_except.ParserException(29, 'phantomjs加载出错')
        if not self.cookies:
            raise parser_except.ParserException(22, 'not get cookie')

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
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
                        'Upgrade-Insecure-Requests': '1',
                        'Pragma': 'no-cache',
                        'Connection': 'keep-alive',
                        'Cookie': self.cookies
                        # 'Cookie': 'aOmIj1jm=uniqueStateKey%3DAI_26BxiAQAAPGHgvmKqaKnOTek-L4zsCu65Fm2av6TMw7w7CfDGYBDUbQ98%26b%3Ddi14t4%26c%3DAIAC3xxiAQAA8Vi29htD3yuzlbVJWorYhyA1N5OejRCGg5Y-J13_fthzKWGr%26d%3D0%26a%3DAJzNCVoN_Sd3yVoq_SQ3nBoFiLdEgkV7bPwOr57a_mkf2fJpCqeDWx3E2MSJ03aqLNcDkbKl%253DC95fpnOWih7bFZGB2deWYjMvcOw2EOJvD%253DXkzlWJ-HAg-0OwxdEgkV_uNGOOOO'
                    },
                },
            }

        yield crawl_index

    def parse_bed(self, url):

        headers = {
            'Pragma': "no-cache",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/64.0.3282.186 Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Referer': self.first_url,
            # 'Cookie': "JSESSIONID=00008dOBxRq9VxqAgKnTZwQhxWt:16jpvqbgd;",
            'Cookie': self.cookies,
            'Connection': "keep-alive",
            'Cache-Control': "no-cache",
        }
        try:
            res = requests.get(url, headers=headers, timeout=3)
            node = etree.HTML(res.content)
            infos = ''.join(node.xpath('//div[@class="noteItemContent"]/ul/li/text()'))
        except:
            infos = ''
        return infos

    def parse_hotel(self, req, resp):

        node = etree.HTML(resp)
        rooms = []
        try:
            hotel_name = node.xpath('//span[@class="propertyName"]/a/text()')[0].strip()
        except:
            hotel_name = ''
        tree_list = node.xpath('//div[contains(@class, "roomContainer")]')

        for tree in tree_list:
            room = Room()
            city = ''
            source = '喜达屋'
            source_hotelid = self.id
            room_id = tree.xpath('.//div[@class="roomDetails"]/ul/li/a/@href')[0]
            source_roomid = re.findall(r'roomClassId=(\d+)', room_id)[0]

            room_type = tree.xpath('./h1/text()')[0]
            print room_type
            real_source = 'starwood'
            info_list = tree.xpath('./div[@class="roomBlock"]/div[@class="rateContainer "]//'
                                   'div[@class="rateDetailsBlock"]')

            for info in info_list:
                room.hotel_name = hotel_name
                room.city = city
                room.source = source
                room.source_hotelid = source_hotelid
                room.source_roomid = source_roomid

                room.real_source = real_source

                currency_price = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                            'span/span[@class="roomRate"]/text()')[0]

                try:
                    total_price = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                             'span/span[@class="roomTotal"]/text()')[0]
                    currency = ''.join(re.findall(r'([A-Za-z])', currency_price))
                    price = ''.join(re.findall(r'(\d+)', currency_price))
                    total_price = ''.join(re.findall(r'(\d+)', total_price))
                    tax = int(total_price) - int(price)
                except IndexError:
                    price_info = info.xpath('./div[contains(@class, "reserveNow")]//div[@class="details"]/a/'
                                            'span/span[@class="roomRate"]/text()')
                    price = price_info[0]
                    currency = 'Starpoints'
                    tax = ''
                    if 'USD' in price_info:
                        tax = price_info[-1]

                room.currency = currency
                room.occupancy = -1
                room.price = price
                room.tax = tax

                title = ''.join(info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/h3/text()'))
                title = title.replace('\t', '').replace('\r', '').replace('\n', '').strip()
                room.room_type = '{}|{}'.format(room_type, title)
                room.has_breakfast = 'NO'
                room.is_breakfast_free = 'NO'
                foods_res = ''
                if 'Breakfast' or '早餐' in title:
                    room.has_breakfast = 'YES'
                    room.is_breakfast_free = 'YES'
                    foods_res = '含早餐'
                elif 'Cool Summer' in title:
                    room.has_breakfast = 'YES'
                    room.is_breakfast_free = 'YES'
                    foods_res = 'Daily breakfast'

                cancel_info = ''.join(info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/ul/li[1]/text()'))
                room.is_cancel_free = 'NO'
                if 'Free cancellation' or '免费取消' in cancel_info:
                    room.is_cancel_free = 'YES'

                return_rule = info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/'
                                                 'ul/li/text()')
                return_rules = '|'.join([rule.replace('\t', '').replace('\n', '').replace('\r', '').strip()
                                        for rule in return_rule])
                room.return_rule = return_rules
                link = info.xpath('./div[@class="rateAttributes"]/div[@class="details"]/ul/li/a/@href')[0]
                links = 'https://www.starwoodhotels.com{}'.format(link)
                bed_info = self.parse_bed(links)
                room.bed_type = tree.xpath('./h2/span/text()')[0]
                room.is_extrabed = 'NO'
                room.is_extrabed_free = 'NO'
                room.extrabed_rule = bed_info
                if 'CNY' in bed_info or 'per night' in bed_info:
                    room.is_extrabed = 'YES'
                    room.is_extrabed_free = 'NO'
                    room.extrabed_rule = bed_info
                room.size = tree.xpath('.//div[@class="roomDetails"]/ul/li[@class="roomSize"]/text()')[0]
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
                room.others_info = {
                            'extra': {
                                'breakfast': foods_res,
                                'payment': '在线支付',
                                'return_rule': room.return_rule ,
                                'occ_des': self.allow_num
                            }
                        }
                room.guest_info = ''
                room.hotel_url = self.hotel_url

                room_tuple = (room.hotel_name, room.city, room.source, room.source_hotelid,
                              room.source_roomid, room.real_source, room.room_type, room.occupancy,
                              room.bed_type, room.size, room.floor, room.check_in, room.check_out,
                              room.rest, room.price, room.tax, room.currency, room.pay_method,
                              room.is_extrabed, room.is_extrabed_free, room.has_breakfast, room.is_breakfast_free,
                              room.is_cancel_free, room.extrabed_rule, room.return_rule, room.change_rule, room.room_desc,
                              room.others_info, room.guest_info, room.hotel_url)
                rooms.append(room_tuple)
        return rooms


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    spider = StarWoodSpider(task)

    #              酒店id&入住日期&离开日期&
    task.content = '3825&2&20180515'

    task.ticket_info = {
        'room_info': [{
            # 房间数&[成人数&儿童数
            'occ': 1,
            'num': 1,
        }]
    }
    spider.crawl()
    print spider.code
    print spider.result


