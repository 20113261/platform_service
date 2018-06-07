#coding:utf-8
import time
import datetime
import json

from mioji.common import logger
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_NONE, PROXY_FLLOW




class IhgHotelSpider(Spider):
    source_type = 'holidayHotel'
    targets = {
        'hotel': {},
    }
    old_spider_tag = {
        'holidayListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        super(IhgHotelSpider, self).__init__(task)
        self.query_data = {}
        self.city_info = {}
        self.hotels = {}
        self.type_error = False  # flag， 用来控制重试循环的终止
        self.max_retries = 5     # 当遇到解析bug时候的重试次数

    def targets_request(self):
        self.post_data = {"version":"1.3","checkDailyPointsCost":"true","corporateId":"","stay":{"travelAgencyId":"99602392","dateRange":{"start":"2017-12-20","end":"2018-01-26"},"rateCode":"6CBARC","children":0,"adults":2,"rooms":2},"radius":62.137,"bulkAvailability":True,"marketingRates":"","location":{"lng":113.264385,"lat":23.12911,"location":"Guangzhou, Guangdong, China"}}

        @request(retry_count=3, proxy_type=PROXY_NONE)
        def get_location_data():
            """
            得到所属城市的坐标和位置，用来调用第二次接口的请求
            如果能把对面所有城市的数据融合出来，可以不用打这个接口直接从我们的数据库拿到数据
            """
            return {
                'req': {
                    'url': 'https://apis.ihg.com/locations/v1/destinations',
                    'method': 'get',
                    'headers': {
                        'ihg-language': 'zh-CN',
                        'accept': 'application/json, text/plain, */*',
                        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'x-ihg-api-key': 'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y'
                    },
                    'params': {'destination': '{}'.format(self.query_data['city'])}
                },
                'user_handler': [self.parse_city],
                'data': {'content_type': 'json'}
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel)
        def get_hotel_data():
            """
            根据城市得到数据
            """
            return {
                'req': {
                    'url': 'https://apis.ihg.com/guest-api/v1/ihg/cn/zh/search',
                    'method': 'post',
                    'headers': {
                        'accept':'application/json, text/plain, */*',
                        'Content-Type':'application/json; charset=UTF-8',
                        'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                        'ihg-language': 'zh-CN',
                        'x-ihg-api-key':'se9ym5iAzaW8pxfBjkmgbuGjJcr3Pj6Y',
                        'x-ihg-mws-api-token':'58ce5a89-485a-40c8-abf4-cb70dba4229b',
                    },
                    'data': json.dumps(self.post_data),
                },
                'data': {'content_type': 'json'}
            }
        self.fetch_ticket_info()
        yield get_location_data
        self.construct_post_data()
        yield get_hotel_data
        # 有一种罕见的bug导致get_hotel_data得到的是上一次的数据
        while self.type_error and self.max_retries > 0:
            logger.logger.debug("开始重新尝试解析resp，剩余重试次数" + str(self.max_retries))
            self.construct_post_data()
            yield get_hotel_data
            self.max_retries -= 1
        # 说明retry次数用尽了还没能解析成功
        if not self.max_retries:
            logger.logger.debug("无法得到城市的酒店列表，被封禁")
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, '被封禁')

    def fetch_ticket_info(self):
            """
            得到查询的data
            """
            check_in = self.task.ticket_info.get('check_in')
            datetime_check_in = datetime.datetime.strptime(check_in, '%Y%m%d')
            stay_nights = self.task.ticket_info.get('stay_nights')
            delta = datetime.timedelta(int(stay_nights))
            datetime_check_out = datetime_check_in + delta
            dest_city = self.task.ticket_info.get('dest_city') or json.loads(self.task.ticket_info.get('suggest', '{}')).get('suggestion', '')
            occ = self.task.ticket_info.get('occ')

            room = self.task.ticket_info.get('room_info', {}).get('num', '') or self.task.ticket_info.get('room_count', 1)
            check_in, check_out = str(datetime_check_in).split(' ')[0], str(datetime_check_out).split(' ')[0]
            self.query_data = dict(check_in=check_in, check_out=check_out, adults=occ, city=dest_city, room=room)

    def construct_post_data(self):
        """
        根据第一个请求构造第二个请求的data
        """
        self.post_data['location']['lng'], self.post_data['location']['lat'], self.post_data['location']['location'] = \
            self.city_info['longitude'], self.city_info['latitude'], self.city_info['clarifiedLocation']
        self.post_data['stay']['adults'], self.post_data['stay']['rooms'] = \
            self.query_data['adults'], self.query_data['room']
        self.post_data['stay']['dateRange']['start'], self.post_data['stay']['dateRange']['end'] = \
            self.query_data['check_in'], self.query_data['check_out']

    def response_error(self,req, resp, error):
        if resp.status_code == 500 and resp.content == '[{"sl_translate":"message,localizedMessage,title","message":"There was a problem getting search results","localizedMessage":"There was a problem getting search results","code":"700"}]':
            raise parser_except.ParserException(parser_except.EMPTY_TICKET, '没有搜索结果')
        print

    def parse_hotel(self, req, resp):
        """
        解析得到的hotels数据
        """
        try:
            all_hotels = resp['hotels']
        except TypeError as e:
            logger.logger.error("解析的时候遇到了resp是上一次数据的bug, msg: " + str(e))
            self.city_info = resp[0]
            self.type_error = True
            return
        base_url = 'https://www.ihg.com/holidayinnexpress/hotels/cn/zh/{}/hoteldetail'
        hotels = []
        for i in all_hotels:
            hotel_url = base_url.format(i['hotelCode'].lower())
            source_hotelid = i['hotelCode']
            self.hotels.setdefault(source_hotelid, {
                'name': i['name'],
                'city': i['city'],
                'url': hotel_url
            })
            detail_url = 'https://apis.ihg.com/hotels/v1/profiles/{}/details'.format(source_hotelid)
            hotels.append((source_hotelid, hotel_url + '#####' + detail_url))
        return hotels

    def parse_city(self, req, resp):
        self.city_info = resp[0]


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    # 城市英文名
    task.content = 'guangzhou&2&2&20180121'
    # 城市中文名
    # task.content = '洛杉矶&2&2&20180121'
    # 机场三字码
    # task.content = 'LAX&2&2&20180121'

    """
    content格式：【城市名称（英文/中文）或者机场三字码】&【人数】&【天数】&【check in】
    """

    task.ticket_info = {
        'is_new_type': True,
        'suggest_type': 2,
        # 'suggest': {"hits": 2, "countryCode": "0001", "longitude": -84.083298, "label": "London, KY, United States", "rank": 2.968756356707367, "suggestion": "London, KY, United States", "destinationType": "CITY", "latitude": 37.128899, "type": "B"},
        'suggest': '''{"hits": 2, "countryCode": "0925", "longitude": -0.12714, "label": "London, United Kingdom", "rank": 10.0, "suggestion": "London, United Kingdom", "destinationType": "CITY", "latitude": 51.506321, "type": "B"}''',
        'dest_city': '巴黎',
        'check_in': '20180518',
        # 'check_out': '20180120',
        'stay_nights': '2',
        'occ': '1',
        'tid': 'demo',
        'used_times': 0
        # 'room_count': '1'
    }

    task.source = 'ihg'
    spider = IhgHotelSpider()
    spider.task = task
    print spider.crawl()
    print spider.result

    task.ticket_info = {
        'room_count': 2
    }
