#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
@time 2017/10/25
'''

import re
import datetime
import urlparse
import json
from lxml.html import tostring
from ctrip_hotel_list_tag import Tag
from mioji.common.task_info import Task
from mioji.common.class_common import Room
from mioji.models.city_models import get_suggest_city
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class TestSpider(Spider):

    source_type = "ctripFilterHotel"
    targets = {"hotel": {'version': 'InsertHotel_room4'},
               "filter": {}}
    old_spider_tag = {'ctripListHotel': {'required': ['hotel']},
                      'ctripFilterHotel': {'required': ['filter']}}
    total_page = 0

    def targets_request(self):
        if self.task.ticket_info.get('is_new_type'):
            self.rooms = self.task.ticket_info.get('occ')
            night = self.task.ticket_info.get('stay_nights')
            check_in = self.task.ticket_info.get('check_in')
            hotel_url = self.task.ticket_info.get('suggest')
            self.checkIn = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])))[:10]
            self.checkOut = str(
                datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), int(check_in[6:])) + datetime.timedelta(
                    int(night)))[:10]
            if self.task.ticket_info.get('suggest_type') == 1:
                try:
                    cityId_Py = re.search(r'international/([a-zA-Z]+)([0-9]+)', hotel_url)
                    self.cityId = cityId_Py.group(2)
                    self.cityPy = cityId_Py.group(1)
                    self.mioji_city_id = 'NULL'
                except Exception as e:
                    cityId_Py = re.search(r'international/([0-9]+)', hotel_url)
                    self.cityId = cityId_Py.group(1)
                    self.cityPy = ""
                    self.mioji_city_id = 'NULL'
            else:
                suggest_json = self.task.ticket_info.get('suggest').split('|')
                self.cityId,self.cityPy = suggest_json[5],suggest_json[6]
                self.mioji_city_id = 'NULL'
            self.hotel_url = 'http://hotels.ctrip.com/international/' + self.cityPy + self.cityId
        else:
            taskcontent = self.task.content
            taskcontent = taskcontent.encode('utf-8')
            task_infos = taskcontent.split('&')
            self.mioji_city_id, self.rooms, stay_nights, check_in = task_infos[0], task_infos[1], task_infos[2], \
                                                                    task_infos[3]
            suggest_city = get_suggest_city('ctrip',str(self.mioji_city_id))
            is_new_type = suggest_city.get('is_new_type')
            self_p = suggest_city.get('suggest')
            if is_new_type == 0:
                self_p = self_p.split('|')
                self.cityId, self.cityPy = self_p[5], self_p[6]
            else:
                hotel_url = self_p.get('url')
                cityId_Py = re.search(r'international/([a-zA-Z]+)([0-9]+)', hotel_url)
                self.cityId = cityId_Py.group(2)
                self.cityPy = cityId_Py.group(1)
            self.checkOut = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]),
                                                  int(check_in[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
            self.checkIn = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
            self.hotel_url = 'http://hotels.ctrip.com/international/' + self.cityPy + self.cityId

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_filter)
        def get_tag():
            return {
                'req': {'url': self.hotel_url},
                'data': {'content_type': 'html'},
            }
        yield get_tag

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def first_page():
            return {
                'req': {'url': self.hotel_url},
                'data': {'content_type': 'html'},
                'user_handler': [self.get_total_page]
            }
        yield first_page

        if self.total_page > 0:
            @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_hotel)
            def tasker():
                pages = []
                for i in range(2, self.total_page + 1):
                    list_url = self.hotel_url + '/p{0}'.format(i)
                    pages.append({'req': {'url': list_url},
                                  'data': {'content_type': 'html'}})
                return pages
            yield tasker

    def parse_filter(self, req, data):
        res = []
        tag = Tag()
        tag.city_id = self.mioji_city_id
        tag.hotel_url = self.hotel_url
        break_fast = []
        breakfast_text_list = data.xpath(
            "//div[@data-type='hot']/div[@class='filter_item_bd']/div[@class='label_list']/label[@data-type='breakfast']/span[@class='txt']/text()")
        breakfast_value_list = data.xpath(
            "//div[@data-type='hot']/div[@class='filter_item_bd']/div[@class='label_list']/label[@data-type='breakfast']/@data-value")
        try:
            for breakfast in zip(breakfast_text_list, breakfast_value_list):
                break_dict = dict()
                break_dict['name'] = breakfast[0]
                break_dict['id'] = breakfast[1]
                break_fast.append(break_dict)
            tag.breakfast = break_fast
        except:
            pass
        hotel_star = []
        star_text_list = data.xpath(
            "//div[@data-type='star']/div[@class='filter_item_bd']/div[@class='label_list']/label/span/text()")
        star_value_list = data.xpath(
            "//div[@data-type='star']/div[@class='filter_item_bd']/div[@class='label_list']/label/@data-value")
        try:
            for star in zip(star_text_list, star_value_list):
                star_dict = dict()
                star_dict['key'] = star[0]
                star_dict['id'] = star[1]
                hotel_star.append(star_dict)
            tag.hotel_star = hotel_star
        except:
            pass
        others_info = []
        others_info_text_list = data.xpath(
            "//div[@class='filter_item filter_item_last']/div[@class='filter_item_bd']/a/text()")
        try:
            others_info_text_list.pop(0)
            for index, others in enumerate(others_info_text_list):
                index += 1
                others_dict = dict()
                others_dict['name'] = others
                others_list = []
                others_text_list = data.xpath(
                    "//div[@class='filter_item filter_item_last']/div[contains(@data-panel,'pnl')][%d]/label/span[@class='txt']/text()" % index)
                others_value_list = data.xpath(
                    "//div[@class='filter_item filter_item_last']/div[contains(@data-panel,'pnl')][%d]/label/@data-value" % index)
                for others_tuple in zip(others_text_list, others_value_list):
                    tuple_dict = dict()
                    tuple_dict['segment_name'] = others_tuple[0]
                    tuple_dict['segment_info'] = others_tuple[1]
                    others_list.append(tuple_dict)
                others_dict['tag_list'] = others_list
                others_info.append(others_dict)
            tag.others_info = others_info
        except:
            pass
        position = []
        position_name_list = data.xpath(
            "//div[@class='filter_item location_item']/div[@class='filter_item_bd']/a/text()")
        try:
            position_name_list.pop(0)
            for index, position_text in enumerate(position_name_list):
                index += 1
                position_dict = dict()
                position_dict['name'] = position_text
                position_list = []
                position_text_list = data.xpath(
                    "//div[@class='filter_item location_item']/div[contains(@data-panel,'pnl')][%d]/label/span[@class='txt']/text()" % index)
                position_value_list = data.xpath(
                    "//div[@class='filter_item location_item']/div[contains(@data-panel,'pnl')][%d]/label/@data-value" % index)
                if position_text_list:
                    for position_tuple in zip(position_text_list, position_value_list):
                        tuple_dict = dict()
                        tuple_dict['name'] = position_tuple[0]
                        tuple_dict['id'] = position_tuple[1]
                        position_list.append(tuple_dict)
                    position_dict['tag_list'] = position_list
                    position.append(position_dict)
                else:
                    subway_big_list = []
                    subway_line_list = data.xpath(
                        "//div[@class='filter_item location_item']/div[@data-panel='pnlMetro']/div[@class='subway_line']/a/text()")
                    for index, line_name in enumerate(subway_line_list):
                        subway_info_list = []
                        index += 1
                        subway_dict = dict()
                        subway_dict['segment_name'] = line_name
                        subway_text_list = data.xpath(
                            "//div[@class='filter_item location_item']/div[@data-panel='pnlMetro']/div[contains(@data-panel, 'pnl')][%d]/label/span[@class='txt']/text()" % index)
                        subway_value_list = data.xpath(
                            "//div[@class='filter_item location_item']/div[@data-panel='pnlMetro']/div[contains(@data-panel, 'pnl')][%d]/label/@data-value" % index)
                        for subway_tuple in zip(subway_text_list, subway_value_list):
                            tuple_dict = dict()
                            tuple_dict['name'] = subway_tuple[0]
                            tuple_dict['id'] = subway_tuple[1]
                            subway_info_list.append(tuple_dict)
                        subway_dict['segment_info'] = subway_info_list
                        subway_big_list.append(subway_dict)
                    position_dict['tag_list'] = subway_big_list
                    position.append(position_dict)
            tag.position = position
        except:
            pass
        res.append(tag.__dict__)
        return res

    def get_total_page(self, req, data):
        root = data
        page = root.xpath('//input[@class="c_page_num"]/@data-totalpage')
        destinationType = re.findall('window.DestinationType\s?=(\d);', tostring(root))
        self.destinationType = int(destinationType[0]) if len(destinationType) > 0 else -9999
        IsSuperiorCity = re.findall('"IsSuperiorCity"\s?:\s?(\d),', tostring(root))
        self.IsSuperiorCity = int(IsSuperiorCity[0]) if len(IsSuperiorCity)>0 else -9999
        self.total_page = int(page[0]) if len(page)>0 else 0

    def parse_hotel(self, req, data):
        root = data
        rooms = []
        hotel_names = root.xpath('//div[contains(@class, "hlist_item_name")]/a/text()')
        source_hotelids = root.xpath('//div[contains(@class, "hlist_item")]/@id')
        #prices = root.xpath('//div[contains(@class, "hlist_item_price")]/span/text()')
        prices = root.xpath('//div[@class="hlist_item_price"]/span/text()')
        urls = root.xpath('//a[contains(@class, "hlist_item_rcol")]/@href')
        for hotel_name, source_hotelid, price, hotel_url in zip(hotel_names, source_hotelids, prices, urls):
            try:
                hotel_info = Room()
                hotel_info.hotel_name = hotel_name
                hotel_info.city = self.mioji_city_id
                hotel_info.source = 'ctrip'.encode('utf-8')
                hotel_info.source_hotelid = source_hotelid
                hotel_info.check_in = self.checkIn
                hotel_info.check_out = self.checkOut
                hotel_info.price = price
                hotel_info.currency = 'CNY'.encode('utf-8')
                hotel_info.hotel_url = urlparse.urljoin('http://hotels.ctrip.com/international/tool/AjaxHotelList.aspx',
                                                        hotel_url)

                hotel_info.source_roomid = ''
                hotel_info.real_source = ''
                hotel_info.room_type = ''
                hotel_info.occupancy = ''
                hotel_info.bed_type = ''
                hotel_info.size = ''
                hotel_info.floor = ''
                hotel_info.rest = ''
                hotel_info.tax = ''
                hotel_info.pay_method = ''
                hotel_info.is_cancel_free = ''
                hotel_info.extrabed_rule = ''
                hotel_info.return_rule = ''
                hotel_info.change_rule = ''
                hotel_info.room_desc = ''
                hotel_info.others_info = ''
                hotel_info.guest_info = ''

                roomtuple = (hotel_info.hotel_name, hotel_info.city, hotel_info.source, hotel_info.source_hotelid, \
                             hotel_info.source_roomid, hotel_info.real_source, hotel_info.room_type,
                             hotel_info.occupancy, hotel_info.bed_type, hotel_info.size, \
                             hotel_info.floor, hotel_info.check_in, hotel_info.check_out, hotel_info.rest,
                             hotel_info.price, hotel_info.tax, hotel_info.currency, hotel_info.pay_method, \
                             hotel_info.is_extrabed, hotel_info.is_extrabed_free, hotel_info.has_breakfast,
                             hotel_info.is_breakfast_free, \
                             hotel_info.is_cancel_free, hotel_info.extrabed_rule, hotel_info.return_rule,
                             hotel_info.change_rule, hotel_info.room_desc, \
                             hotel_info.others_info, hotel_info.guest_info, hotel_info.hotel_url)
                rooms.append(roomtuple)
            except Exception as e:
                print e
        return rooms


if __name__ == '__main__':
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    # spider.slave_get_proxy = simple_get_socks_proxy
    task = Task()
    # contents = [
    #     '10009&1&1&20180328'
    # ]
    # task.content = contents[0]
    task.ticket_info = {
        'suggest_type': 1,
        'check_in': '20180622',
        'tid': 'demo',
        'stay_nights': '1',
        'is_new_type': True,
        'is_service_platform': True,
        'city_id': '60190',
        'suggest': 'http://hotels.ctrip.com/international/85635',
        'occ': '2',
        'used_times': (2,)}
    spider = TestSpider(task)
    ret = spider.crawl(required=['filter'])
    # print spider.result
    print json.dumps(spider.result, ensure_ascii=False)
    print spider.code


