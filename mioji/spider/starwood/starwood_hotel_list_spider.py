#coding:utf-8
import time
import datetime
import json
from lxml import etree
import urllib
import re
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Room, Hotel


class StarWoodListSpider(Spider):
    source_type = 'starwoodListHotel'
    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'starwoodListHotel': {'required': ['hotel']}
    }

    def __init__(self, task=None):
        self.page_store_key_list = []
        super(StarWoodListSpider, self).__init__(task)
        self.hotels = {}

    def targets_request(self):
        print self.task
        content = self.task.content.split('&')
        country = content[0]
        city = content[1]
        print(self.task.content, '==============================================')
        # arrive_date = content[2]
        # departure_date = content[3]
        # arrive_date_str = arrive_date[:3] + '年' + arrive_date[2:4] + '月' + arrive_date[:-3]
        # departure_date_str = departure_date[:3] + '年' + departure_date[2:4] + '月' + departure_date[:-3]


        url= 'https://www.starwoodhotels.com/preferredguest/search/results/detail.html'

        url = 'https://www.starwoodhotels.com/preferredguest/search/results/detail.html'
        if 'Caribbean' in country:
            params = '?iataNumber=&arrivalDate=&departureDate=&numberOfRooms=1&numberOfAdults=1&numberOfChildren=0' \
                     '&complexSearchField=Caribbean'
        else:
            params = 'iataNumber=&country={0}&stateProvince={1}&arrivalDate=&departureDate=' \
                     '&numberOfRooms=&numberOfAdults=&numberOfChildren='.format(country, city)
        # print url+params
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def crawl_first():
            return {
                'req': {
                    'url': url,
                    'method': 'get',
                    'params':  params,
                    'headers': {
                        'Accept-Language': 'en;q=0.8',
                        'Host': 'www.starwoodhotels.com',
                        'Cache-Control': 'max-age=0',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 '
                                      '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        # 'Upgrade-Insecure-Requests': 1,
                        'Connection': 'keep-alive',
                        'Content-Security-Policy': 'upgrade-insecure-requests'
                    },

                },
            }
        yield crawl_first

    def parse_hotel(self, req, resp):
        # print resp
        # if '很抱歉，没有符合您搜索条件的酒店' in resp:
            # raise parser_except.ParserException(29, '很抱歉，没有符合您搜索条件的酒店')
        # elif '您所需要的日期没有可用的喜达屋酒店' in resp:
        #     raise parser_except.ParserException(29, '您所需要的日期没有可用的喜达屋酒店, 重新选定日期')
        if 'We don’t have any Starwood hotels in this destination' in resp:
            raise parser_except.ParserException(29, '我们在此目的地未开设任何喜达屋酒店')
        elif 'there are no hotels that match your criteria' in resp:
            raise parser_except.ParserException(29, '没有符合您搜索条件的酒店')
        # print resp
        tree = etree.HTML(resp)
        rooms = []
        node_list = tree.xpath('//div[@class="propertyOuter"]')

        for node in node_list:
            hotel_info = Hotel()

            try:
                hotel_info.hotel_name = node.xpath('.//div[@class="propertyInner"]/div[@class="propertyDetails"]'
                                                   '/h2/a/text()')[0]

            except:
                hotel_info.hotel_name = node.xpath('.//div[@class="propertyInner"]/div[@class="propertyDetails"]'
                                                   '/h2/text()')[0]
            # print hotel_info.hotel_name
            try:
                hotel_info.hotel_name_en = node.xpath('.//div[@class="propertyInner"]/div[@class="propertyDetails"]'
                                                      '/h2/a/text()')[0]
                if hotel_info.hotel_name_en == '\n':
                    hotel_info.hotel_name_en = hotel_info.hotel_name
            except:
                hotel_info.hotel_name_en = 'NULL'
            address = node.xpath('.//div[@class="propertyInner"]/div[@class="propertyDetails"]'
                                 '/p[@class="propertyLocation"]/text()')
            address = [a.replace('\t', '').replace('\n', '').replace('\r', '').strip() for a in address[0].split(',')]
            if len(address) > 2:
                hotel_info.city = address[1]
                hotel_info.country = address[-1]
            else:
                hotel_info.city = address[0]
                hotel_info.country = address[1]
            hotel_info.source = 'starwood'.encode('utf-8')
            try:
                url = node.xpath('.//div[@class="propertyInner"]/div[@class="propertyDetails"]/h2/a/@href')[0]
                hotel_info.hotel_url = "https://www.starwoodhotels.com{}".format(url)
            except:
                url = node.xpath('.//div[@class="OneLinkKeepLinks"]/a/@href')[0]
                hotel_info.hotel_url = url
            # print url
            hotel_info.source_id = re.compile(r'\d+').findall(url.split('propertyID=')[-1])[0]
            # print hotel_info.source_id
            hotel_info.description = 'NULL'

            hotel_info.address = 'NULL'
            hotel_info.postal_code = 'NULL'
            hotel_info.img_items = 'NULL'
            hotel_info.check_in_time = 'NULL'
            hotel_info.check_out_time = 'NULL'

            # ======================
            hotel_info.brand_name = 'NULL'
            hotel_info.map_info = 'NULL'
            hotel_info.star = 'NULL'
            hotel_info.grade = 'NULL'
            hotel_info.review_num = 'NULL'
            hotel_info.has_wifi = 'NULL'
            hotel_info.is_wifi_free = 'NULL'
            hotel_info.has_parking = 'NULL'
            hotel_info.is_parking_free = 'NULL'
            hotel_info.service = 'NULL'
            hotel_info.accepted_cards = 'NULL'

            new_hotels = node.xpath('./div[@class="property"]//div[@class="rateOptionsOuter"]/'
                                    'div[@class="rateOptions"]/span')
            if new_hotels:
                break
            rooms_tuple = (
                hotel_info.hotel_name,
                hotel_info.hotel_name_en,
                hotel_info.source,
                hotel_info.source_id,
                hotel_info.brand_name,
                hotel_info.map_info,
                hotel_info.address,
                hotel_info.city,
                hotel_info.country,
                hotel_info.postal_code,
                hotel_info.star,
                hotel_info.grade,
                hotel_info.review_num,
                hotel_info.has_wifi,
                hotel_info.is_wifi_free,
                hotel_info.has_parking,
                hotel_info.is_parking_free,
                hotel_info.service,
                hotel_info.img_items,
                hotel_info.description,
                hotel_info.accepted_cards,
                hotel_info.check_in_time,
                hotel_info.check_out_time,
                hotel_info.hotel_url

            )
            rooms.append(rooms_tuple)
        return rooms


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new
    from mioji.common import spider
    spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = StarWoodListSpider()
    spider.task = task

    # task.content = 'Caribbean_region&'
    task.content = 'US&PA&'
    task.ticket_info = {'tid': 'demo', 'is_service_platform': True, 'is_new_type': False, 'used_times': (2,)}
    # task.ticket_info = {
    #         'room': 1,  # 15最大
    #         'adults': 1,  # 4最大
    #         'child': 0  # 4最大

    spider.crawl()
    print spider.code
    print spider.result['hotel']
    print len(spider.result)

