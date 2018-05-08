#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import sys
import json
import datetime
from urllib import quote
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.class_common import Room
reload(sys)
sys.setdefaultencoding("utf-8")


class WhListSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'marriottListHotel'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'room': {'version': 'InsertHotel_room4'},
        'hotel':{}
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'marriottListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task)
        self.rooms = []
        self.cookie = {}

    def get_week_day(self, check_in):
        get_day = datetime.datetime(int(check_in[:4]), int(check_in[4:6].replace("0", "")), int(check_in[6:].replace("0", "")))
        init_day = datetime.datetime(1970, 01, 01)
        diff_day = (get_day - init_day).days
        week_day = diff_day % 7
        week_day += 4
        if week_day > 7:
            week_day %= 7
        else:
            week_day = week_day
        data_dict = {'1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日'}
        week_str = quote(data_dict[str(week_day)])
        return week_str

    def targets_request(self):
        # u can get task info from self.task
        task = self.task
        # is_new_type = task.ticket_info.get('is_new_type')
        # suggest_type = task.ticket_info.get('suggest_type')
        # if is_new_type:
        #     if suggest_type == 2:
        check_in = task.ticket_info.get('check_in')
        suggest = task.ticket_info.get('suggest')
        stay_nights = task.ticket_info.get('stay_nights')
        check_out_str = (datetime.datetime(int(check_in[:4]), int(check_in[4:6]), int(check_in[6:])) + datetime.timedelta(days=int(stay_nights))).strftime('%Y-%m-%d')
        suggest = json.loads(suggest)
        city = suggest.get('City')
        city = str(city)
        city_str = quote(city)
        StateCode = suggest.get('StateCode')
        if StateCode is None:
            StateCode = ""
        Country = suggest.get('Country')
        CountryCode = suggest.get('CountryCode')
        GeoCode = suggest.get('GeoCode').split(',')
        latitude = GeoCode[0]
        longitude = GeoCode[1]
        check_in_str = check_in[:4] + '-' + check_in[4:6] + '-' + check_in[6:]
        week_str = self.get_week_day(check_in)
        CityPopulation = suggest.get('CityPopulation')
        CityPopulationDensity = suggest.get('CityPopulationDensity')
        first_req_url = "https://www.marriott.com.cn/search/submitSearch.mi?searchType=InCity&groupCode=&searchRadius=&poiName=" \
                       "&poiCity=&recordsPerPage=20&for-hotels-nearme=%E9%9D%A0%E8%BF%91&destinationAddress.destination={0}+{1}%2C+{2}" \
                        "&singleSearch=true&singleSearchAutoSuggest=true&autoSuggestItemType=city&clickToSearch=false&destinationAddress.latitude={3}" \
                        "&destinationAddress.longitude={4}&destinationAddress.cityPopulation={15}&destinationAddress.cityPopulationDensity={16}&destinationAddress.city={5}" \
                        "&destinationAddress.stateProvince={6}&destinationAddress.country={7}&airportCode=&fromToDate={8}+%E6%9C%88+{9}%E6%97%A5%2C+{10}" \
                        "&fromToDate_submit={11}&fromDate={12}&toDate={13}&lengthOfStay={14}&roomCountBox=1&roomCount=1&guestCountBox=1&guestCount=1&clusterCode=none&corporateCode=".\
                        format(city_str, StateCode, Country, latitude, longitude, city_str, StateCode, CountryCode, check_in[4:6].replace("0", ""),
                              check_in[6:].replace("0", ""), week_str, check_in_str, check_in_str, check_out_str, stay_nights, CityPopulation, CityPopulationDensity)

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['hotel'])
        def first_request():
            return {'req': {'url': first_req_url,
                            },
                    'data': {'content_type': 'html'},
                    'user_handler': [self.get_total_page]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['hotel'], async=True)
        def second_request():
            total_page = self.total_page
            # cookies = self.get_cookies
            list_a = []
            for pages in range(2, total_page+1):
                list_a.append({'req': {'url': first_req_url + "&" + "page=" + str(pages)},
                        'data': {'content_type': 'html'},
                        })
            return list_a

        yield first_request
        # yield second_request
        if self.total_page >= 2:
            yield second_request

    def get_total_page(self, req, data):
        html_obj = data
        page_list = html_obj.xpath("//ul[@id='paging-selector']/li/a/@title")
        if page_list:
            self.total_page = int(page_list[-2])
        else:
            self.total_page = 0

    def parse_room(self,req,data):
        pass

    def parse_hotel(self, req, data):
        # 可以通过request binding=[]指定解析方法
        rooms = []
        html_obj = data
        hotel_old_id_list = html_obj.xpath("//div[@class='m-property-name-adress']/h3/@id")
        hotel_id_list = []
        for hotel_old_id in hotel_old_id_list:
            hotel_id = re.search(r"-([A-Z]+)", hotel_old_id).group(1)
            hotel_id_list.append(hotel_id)
        longtitude_list = html_obj.xpath("//input[@name='pushpin-long']/@value")
        latitude_list = html_obj.xpath("//input[@name='pushpin-lat']/@value")
        hotel_en_name_list = []
        hotel_en_name_node = html_obj.xpath("//span[@class='l-display-none']/text()")
        for hotel_en_name in hotel_en_name_node:
            hotel_en_name_list.append(hotel_en_name)
        hotel_url_list = []
        hotel_old_url_list = html_obj.xpath("//h3[@class='m-result-hotel-title t-font-s']/a/@href")
        for hotel_node in hotel_old_url_list:
            if re.match(r"h", hotel_node):
                hotel_url_list.append(hotel_node)
            else:
                hotel_url = "https://www.marriott.com.cn" + hotel_node
                hotel_url_list.append(hotel_url)
        hotel_info_list = []
        for hotel_info_tuple in zip(hotel_id_list, hotel_url_list, hotel_en_name_list, longtitude_list, latitude_list):
            hotel_info_list.append(list(hotel_info_tuple))
        for hotel_info in hotel_info_list:
            room = Room()
            room.source_hotelid = hotel_info[0]
            room.hotel_url = hotel_info[1] + "#####" + hotel_info[2] + "#####" + "longtitude=" + hotel_info[3] + "#####" + "latitude=" + hotel_info[4]
            hotel_tuple = (room.source_hotelid, room.hotel_url)
            rooms.append(hotel_tuple)

        return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
    task = Task()
    task.ticket_info = {
            "is_new_type": True,
            "suggest_type": 2,
            "suggest": '{"@type": "city", "City": "\u6c83\u4ec0\u672c", "StateCode": "ND", "CountryCode": "US", "Country": "USA", "GeoCode": "47.288731,-101.028311", "CityPopulation": "0.0", "CityPopulationDensity": "0.0"}',
            "check_in": '20180201',
            "stay_nights": '1',
            "occ": '2',
            'is_service_platform': True,
            'tid': '',
            'used_times': '',
        }
    spider = WhListSpider(task)
    spider.crawl()

    print spider.result



