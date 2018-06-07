#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import re
import json
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.class_common import Room
from lxml import html
reload(sys)
sys.setdefaultencoding('utf-8')


class WhSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'marriottHotel'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertHotel_room4
        'room': {'version': 'InsertHotel_room4'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'marriottHotel': {'required': ['room']}
    }

    def targets_request(self):
        first_req_url = "https://www.marriott.com.cn/reservation/availabilitySearch.mi?accountId=&propertyCode=laxld&hwsCurrency=USD&isHwsGroupSearch=true&isSearch=false&numberOfNights=1&miniStoreAvailabilitySearch=false&dateFormatPattern=&fromDate=2018-01-06&toDate=2018-01-08&flexibleDateSearch=false&numberOfRooms=1&numberOfGuests=1&clusterCode=none&corporateCode=&groupCode=&useRewardsPoints=false&flushSelectedRoomType=true"
        # u can get task info from self.task
        task = self.task
        wh_cookie = "ZMz286iJ=uniqueStateKey%3DALZ_YbRgAQAA7-NZZi4phYUmhe7MFcXoj_7BfdpRI8xdnmDXa_l8lLminNDC%26b%3D18cysl%26c%3DAEBjRrRgAQAAeeStdfahEqznabxY90l4a873SvyUCrvjANFKfP_4ur85ypXF%26d%3D0%26a%3DPGhvCtHe0ocUej6NFy9uZmPbCsgC9ljkq7STs-8oCakICt1keJ3SMmRFqelYvTFW6Dp%253DDs1BNoWjEf3-xllgxmmlFBD0lj-2KSaa9tj7TbP%253DJjkmybIjAkdUCpc01EVFYbql%253DC; mbox=PC#784fb2a82d26425a82de9c46e9be734d.24_11#1522630779|check#true#1514854839|session#8f888668e0ad4faf8c64a613af71f40e#1514856639;"
        @request(retry_count=3, proxy_type=PROXY_REQ, binding=['room'])
        def first_request():
            return {'req': {'url': first_req_url,
                    'headers': {'Cookie': wh_cookie}
                    },
                    'data': {'content_type': 'html'},
                    }

        return [first_request]

    def parse_room(self, req, data):
        rooms = []
        room = Room()
        html_obj = data
        hotel_name = html_obj.xpath("//h1[@class='hotel-name']/span/span/text()")[0]
        if hotel_name:
            room.hotel_name = hotel_name
        content = html.tostring(data)
        source_hotelid = re.search(r"marshaCode=([A-Z]+)", content).group(1)
        if source_hotelid:
            room.source_hotelid = source_hotelid
        room_type_list = html_obj.xpath("//div[@class='l-rate-middle-column']/div/h3/text()")
        if room_type_list:
            room_type_str = ""
            for room_type in room_type_list:
                room_type_str += room_type.strip() + " | "
            room.room_type = room_type_str
        huobi_str = html_obj.xpath("//span[@class='nightly t-nightly']/text()")[0]
        if huobi_str:
            huobi_str2 = re.search(r"([A-Z]+)", huobi_str).group(1)
            room.currency = huobi_str2
        year_str = "20"
        stay_date = html_obj.xpath("//p[@class='m-your-stay is-hidden-ml l-clear']/text()")[2].strip()
        if stay_date:
            stay_date_list = stay_date.split(",")
            stay_date_list2 = stay_date_list[0].split(" - ")
            check_in = year_str + stay_date_list2[0]
            check_out = year_str + stay_date_list2[1]
            room.check_in = check_in
            room.check_out = check_out
        room.source = "wanhao"
        hotel_tuple = (room.hotel_name, room.source_hotelid, room.source, room.room_type, room.currency, room.check_in, room.check_out)
        rooms.append(hotel_tuple)
        return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug
    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
    task = Task()
    spider = WhSpider(task)
    spider.crawl()
    print json.dumps(spider.result, ensure_ascii=False)











