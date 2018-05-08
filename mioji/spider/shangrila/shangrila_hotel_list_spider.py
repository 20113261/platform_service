# coding=utf-8
from lxml import etree

from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.class_common import Hotel

item = {}


class ShangRiLaListSpider(Spider):

    source_type = 'shangrilaListHotel'
    targets = {'hotel': {}}
    old_spider_tag = {
        'shangrilaListHotel': {
            'required': ['hotel']
        }
    }

    def targets_request(self):

        list_url = 'http://www.shangri-la.com/cn/find-a-hotel/'

        list_url_json = 'http://www.shangri-la.com/AllHotelsJson.json?lang=cn&hj=1'

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def crawl_list():
            return {
                'req': {
                    'url': list_url,
                    'method': 'get',
                    'headers': {
                        'Pragma':'no-cache',
                        'Accept-Language':'zh-CN,zh;q=0.9,en;q=0.8',
                        'Upgrade-Insecure-Requests':'1',
                        'Host': 'www.shangri-la.com',
                        'Referer': 'http://www.shangri-la.com/cn/?WT.mc_id=SLIM_201703_GLOBAL_SEM_BAIDU_SLIM-Brand(SC)_Brand-Exact_%CF%E3%B8%F1%C0%EF%C0%AD_SC&gclid=CICL4vfp7dkCFQnjvAodrU4GKA&gclsrc=ds',

                    }
                },
                'user_handler': [self.parse_list]

            }
        yield crawl_list

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel)
        def crawl_list_json():
            return {
                'req': {
                    'url': list_url_json,
                    'method': 'get',
                    'headers': {
                        'Host': 'www.shangri-la.com',
                        'Pragma': 'no-cache',
                        'Referer': 'http://www.shangri-la.com/cn/find-a-hotel/'
                    }
                },
                'data': {'content_type': 'json'}

            }

        yield crawl_list_json

    def parse_list(self, req, resp):
        node_list = etree.HTML(resp)
        tree_list = node_list.xpath('//div[contains(@class, "AccordionPanel")]/div[contains(@class, "AccordionPanelContent")]/ul/li/a')
        for tree in tree_list:
            hotel_url = tree.xpath('./@href')
            hotel_name = tree.xpath('./text()')
            if hotel_url:
                item[hotel_name[0]] = hotel_url[0] if 'http' in hotel_url[0] else 'http://www.shangri-la.com{}'.format(hotel_url[0])

    def parse_hotel(self, req, resp):
        rooms = []

        for hotel_info in resp:
            hotel = Hotel()
            hotel.hotel_name = hotel_info['Name']
            hotel.source = 'sharngrila'
            hotel.source_id = hotel_info['Code']
            hotel.country = hotel_info['Country']
            hotel.hotel_url = item[hotel.hotel_name]
            content = "{}&{}&{}&{}&".format(hotel.hotel_url, hotel.hotel_name, hotel.source_id, hotel.country)
            rooms_tuple = (
                hotel.source_id,
                content,
            )
            rooms.append(rooms_tuple)
        return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy
    spider.slave_get_proxy = simple_get_socks_proxy


    task = Task()
    spider = ShangRiLaListSpider()
    spider.task = task
    task.content = ''
    spider.crawl()
    print spider.code
    print spider.result['hotel']





