#coding:utf-8

"""
'734384 & 1 & 1 & 20170623'
"""


ctx = dict()
ctx["url"] = "http://hotels.ctrip.com/international/tool/AjaxHotelList.aspx"
ctx["method"] = "post"

ctx["data"] = {
    "checkIn": "2017-07-19",
    "checkOut": "2017-07-20",
    "destinationType": 1,
    "cityId": 192,
    # "cityPY": "paris",
    "rooms": 2,
    "childNum": 1,
    "pageIndex": 1
}

ctx["headers"] = {
    "Origin": "http://hotels.ctrip.com",
    "Referer": "http://hotels.ctrip.com/hotel/paris192",
    "Host": "hotels.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}

import datetime
import json
import logging
from mioji.common.class_common import Room
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.task_info import Task
from mioji.common import parser_except
from mioji.common.logger import logger


class TestSpider(Spider):

    source_type = "xxx"
    targets = {"hotel": {'version': 'InsertHotel_room4'}}
    last_page = 0
    total_page = 1
    cityId = '' 
    checkIn = ''
    checkOut = ''
        
    def targets_request(self):
        taskcontent = self.task.content
        taskcontent = taskcontent.encode('utf-8')
        #'734384&1&1&20170623'
        task_infos = taskcontent.split('&')
        self.cityId, rooms, stay_nights, check_in = task_infos[0], task_infos[1], task_infos[2], task_infos[3]
        self.checkOut = str(datetime.datetime(int(check_in[0:4]), int(check_in[4:6]), \
                                    int(check_in[6:])) + datetime.timedelta(days=int(stay_nights)))[:10]
        self.checkIn = check_in[0:4] + '-' + check_in[4:6] + '-' + check_in[6:]
        ctx['data']['checkIn'], ctx['data']['checkOut'], ctx['data']['cityId'], \
                                ctx['data']['rooms'],ctx['data']['childNum'] = self.checkIn, self.checkOut, self.cityId, rooms, rooms
        print ctx
        print 'ctx'*10

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_hotel)
        def req_handler():
            # 处理页码
            while self.last_page < self.total_page or self.last_page < 14:
                # last_page = 1
                self.last_page += 1
                ctx["data"]["pageIndex"] = self.last_page
                logger.info("crawlling %r total page: %r", self.last_page, self.total_page)
                yield {"req": ctx}
        yield req_handler

    def parse_hotel(self, req, payload):
        rooms = []
        data = json.loads(payload, encoding='gb2312')
        # 更新页码
        self.total_page = data["totalPage"]
        hotel_id_price_list = data["DigDataEDMString"]["htllist"]
        hotel_list = data["HotelPositionJSON"]
        # 拼接酒店价格 国内的价格是拼的，国外的直接就可以有
        # tmp_dict = {i["hotelid"]: i["amount"] for i in hotel_id_price_list}
        # for i in hotel_list:
        #     i["amount"] = tmp_dict.get(i["id"])
        # 把返回数据添加到 result 里面 hotel 是在 targets 里面定义的
        # with open('hotel_list.json', 'w') as w:
        #     json.dump(hotel_list,w)
        #数据筛选
        for i in hotel_list:
            hotel_info = Room()
            hotel_info.hotel_name = i['name'].encode('utf-8')
            hotel_info.city = self.cityId
            hotel_info.source = 'ctrip'.encode('utf-8')
            hotel_info.source_hotelid = i['id']
            hotel_info.check_in = self.checkIn
            hotel_info.check_out = self.checkOut
            hotel_info.price = i['price'].encode('utf-8')
            hotel_info.currency = 'CNY'.encode('utf-8')

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
            hotel_info.hotel_url = ''
            roomtuple = (hotel_info.hotel_name, hotel_info.city, hotel_info.source, hotel_info.source_hotelid,\
          hotel_info.source_roomid, hotel_info.real_source, hotel_info.room_type, hotel_info.occupancy, hotel_info.bed_type, hotel_info.size, \
          hotel_info.floor, hotel_info.check_in, hotel_info.check_out, hotel_info.rest, hotel_info.price, hotel_info.tax, hotel_info.currency, hotel_info.pay_method, \
          hotel_info.is_extrabed, hotel_info.is_extrabed_free, hotel_info.has_breakfast, hotel_info.is_breakfast_free, \
          hotel_info.is_cancel_free, hotel_info.extrabed_rule, hotel_info.return_rule, hotel_info.change_rule, hotel_info.room_desc,  \
          hotel_info.others_info,hotel_info.guest_info, hotel_info.hotel_url)
            
            rooms.append(roomtuple)
            # with open("rooms.json", "w+") as f:
            #     json.dump(rooms, f)
        return rooms


if __name__ == "__main__":
    task = Task()
    task.content = '228&1&1&20180425'
    spider = TestSpider(task)
    ret= spider.crawl()
    # with open("ret_data.json", "w") as f:
    #     json.dump(spider.result, f)


