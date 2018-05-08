#coding:utf-8
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from lxml import etree
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Hotel


class FourseasonsListHotel(Spider):
    source_type = 'fourseasonsListHotel'
    targets = {
        'hotel': {},
    }

    old_spider_tag = {
        'fourseasonsListHotel': {'required': ['room']}
    }
    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_hotel)
        def get_location_data():
            return {
                'req': {
                    # 'url': 'https://www.fourseasons.com/alt/apps/fshr/shared/property-list/zh/properties.17605.json',
                    'url': 'https://www.fourseasons.com/alt/apps/fshr/shared/property-list/en/properties.17605.json',
                    'method': 'get',
                    'headers': {
                        'ihg-language': 'zh-CN',
                        'accept': 'application/json, text/plain, */*',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                    },
                },
                'data': {'content_type': 'json'},
            }
        yield get_location_data

    def parse_hotel(self, req, resp):
        hotel_urls = []
        url = 'https://www.fourseasons.com'
        for hotel in resp:
            path = hotel['path']
            hotel_url = url + path
            hotel_id = path.split('/')
            one = (hotel_url,hotel_id[2])
            hotel_urls.append(one)
        return hotel_urls
if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new,simple_get_socks_proxy
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    task.ticket_info = {}

    spider = FourseasonsListHotel(task)
    spider.crawl(required=['hotel'])
    print spider.code
    # print json.dumps(spider.result, ensure_ascii=False)
    print spider.result