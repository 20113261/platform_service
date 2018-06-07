# -*- coding: utf-8 -*-

from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Hotel
from lxml import etree


class GhaListSpider(Spider):
    source_type = 'ghaListHotel'
    targets = {
        'hotel': {},
    }

    old_spider_tag = {
        'ghaListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(GhaListSpider, self).__init__(task)
        self.hotels = {}
        self.task = task

    def targets_request(self):
        content = self.task.content
        cityid, city, self.country = content.split("&")
        if city:
            url = "https://zh.discoveryloyalty.com/ajaxgha/get_country_hotels/{}?related_object=state".format(cityid)
        else:
            url = "https://zh.discoveryloyalty.com/ajaxgha/get_country_hotels/{}".format(cityid)

        @request(retry_count=3,proxy_type=PROXY_REQ,binding=self.parse_hotel)
        def get_hotel():
            print url
            return {
                "req": {
                    "url": url,
                    "method": "get"
                },
            }
        yield get_hotel

    def parse_hotel(self, req, resp):
        select = etree.HTML(resp)
        item_list = select.xpath("//div[@class='DestinationResults-list']/div[@class='RoomView RoomView--destination']")
        hotels = []
        for item in item_list:
            hotel_info = Hotel()
            hotel_info.city = item.xpath("./div[2]/div/p/text()")[0]
            hotel_info.hotel_name = item.xpath("./div[2]/div/h3/a/text()")[0]
            hotel_info.country = self.country
            hotel_info.source_id = item.xpath("./div[2]/div/h3/a/@data-gtm-id")[0]
            url = item.xpath("./div[2]/div/h3/a/@href")[0]
            hotel_info.hotel_url = "https://zh.gha.com"+url
            hotel_info.hotel_name_en = url.split("/")[-1].replace("-",' ')
            hotel_info.source = 'gha'.encode('utf-8')
            hotel_info.star = 'NULL'
            hotel_info.review_num = "NULL"
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
            hotels.append(rooms_tuple)
        return hotels


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new
    from mioji.common import spider
    # spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = GhaListSpider()
    spider.task = task

    task.content = '227605&达鲁环礁&马尔代夫'
    task.ticket_info = {'tid': 'demo', 'is_service_platform': True, 'is_new_type': False, 'used_times': (2,)}

    spider.crawl()
    print spider.code
    print spider.result
    print len(spider.result)
