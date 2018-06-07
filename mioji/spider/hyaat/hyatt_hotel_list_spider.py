#coding:utf-8
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from lxml import etree
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW
from mioji.common.class_common import Hotel


class hyattListHotel(Spider):
    source_type = 'hyattListHotel'
    targets = {
        'hotel': {},
    }

    old_spider_tag = {
        'hyattListHotel': {'required': ['room']}
    }
    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_hotel)
        def get_location_data():
            return {
                'req': {
                    # 'url': 'https://www.hyatt.com/zh-CN/explore-hotels/partial?regionGroup=&categories=&brands=',
                    'url': 'https://www.hyatt.com/en-US/explore-hotels/partial?regionGroup=&categories=&brands=',
                    'method': 'get',
                    'headers': {
                        'ihg-language': 'zh-CN',
                        'accept': 'application/json, text/plain, */*',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                    },
                },
                # 'user_handler': [self.parse_hotel],
            }
        yield get_location_data

    def parse_hotel(self, req, resp):
        hotels = []
        data = etree.HTML(resp)
        hotel_names = data.xpath("//li[@class='property mb2']/a/text()")
        urls = data.xpath("//li[@class='property mb2']/a/@href")
        hotel_ids = data.xpath("//li[@class='property mb2']/@data-js-property")
        for hotel_name, hotel_id, url in zip(hotel_names, hotel_ids, urls):
            try:
                hotel_info = Hotel()
                hotel_info.hotel_name = hotel_name
                hotel_info.hotel_url = 'https:' + url
                hotel_info.hotel_id = hotel_id
                roomtuple = ((hotel_info.hotel_name).decode('raw-unicode-escape'), hotel_info.hotel_url, hotel_info.hotel_id)
                hotels.append(roomtuple)
            except Exception as e:
                print e
        # print(hotels)
        return hotels
if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new
    from mioji.common import spider

    # spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()
    task.ticket_info = {}

    spider = hyattListHotel(task)
    spider.crawl(required=['hotel'])
    print spider.code
    # print json.dumps(spider.result, ensure_ascii=False)
    print spider.result