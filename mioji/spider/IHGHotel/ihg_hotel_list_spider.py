#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import datetime
import json
import sys
import re
from lxml import etree
from mioji.common.class_common import Room

sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
import datetime
from mioji.common.task_info import creat_hotelParams
from mioji.common.spider import Spider, request, mioji_data, PROXY_FLLOW, PROXY_REQ


# from mioji.models.city_models import get_suggest_city
# from mioji.common import parser_except
# from mioji.common import logger
# import hotellist_parse
# import datetime
# from datetime import timedelta

def crate_params(ci, start_date, end_date, city_id, person_num, hashParam, ins):
    params = {
        'destination': ci,
        'startDate': start_date,
        'endDate': end_date,
        'regionId': city_id,
        'adults': str(person_num),
        'hashParam': '',
        'sort': 'recommended',
        'page': str(ins),
        'hsrIdentifier': 'HSR'
    }


class IhgListSpider(Spider):
    source_type = 'ihgListHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room4'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ihgListHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task)
        self.rooms = []

    def targets_request(self):
        tid = self.task.ticket_info['tid']
        used_times = self.task.ticket_info['used_times']

        # 'suggest': 'https://www.ihg.com/hotels/cn/zh/reservation/searchresult?srb_u=1&qCiD=%s&qCiMy=%s&qCoD=%s&qCoMy=%s&qRms=%s&qAAR=6CBARC&qAdlt=%s&qDest=%s'
        @request(retry_count=3, proxy_type=PROXY_REQ, user_retry_count=10,
                 store_page_name="city_first_page_{}_{}".format(tid, used_times))
        def get_pre_request():
            return {'req': {'url': 'https://www.ihg.com/hotels'}}

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['hotel', 'room'], user_retry_count=10,
                 store_page_name="city_first_page_{}_{}".format(tid, used_times))
        def get_first_page():
            check_in = self.task.ticket_info.get('check_in')
            datetime_check_in = datetime.datetime.strptime(check_in, '%Y%m%d')
            stay_nights = self.task.ticket_info.get('stay_nights')
            delta = datetime.timedelta(int(stay_nights))
            datetime_check_out = datetime_check_in + delta
            check_out = datetime_check_out.strftime('%Y%m%d')
            check_in_year = check_in[0:4]
            check_out_year = check_out[0:4]
            check_in_month = check_in[4:6]
            cimy_month = '0' + str(int(check_in_month) - 1) if int(check_in_month) - 1 < 10 else str(check_in_month)
            check_out_month = check_out[4:6]
            comy_month = '0' + str(int(check_out_month) - 1) if int(check_out_month) - 1 < 10 else str(check_out_month)
            cid = check_in[6:8]
            cimy = cimy_month + check_in_year
            cod = check_out[6:8]
            comy = comy_month + check_out_year

            dest_city = json.loads(self.task.ticket_info.get('suggest', '{}')).get('suggestion', '')

            occ = self.task.ticket_info.get('occ')
            room_count = 1
            url = 'https://www.ihg.com/hotels/cn/zh/reservation/searchresult/all?srb_u=1&qCiD=%s&qCiMy=%s&qCoD=%s&qCoMy=%s&qRms=%s&qAAR=6CBARC&qAdlt=%s&qDest=%s'
            search_url = url % (cid, cimy, cod, comy, room_count, occ, dest_city)
            # print search_url
            return {'req': {'url': search_url,
                            'headers': {
                                # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                                'authority': 'www.ihg.com',
                                'method': 'GET',
                                'path': '/hotels/cn/zh/reservation',
                                'scheme': 'https',
                                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                                'cache-control': 'max-age=0',
                                'upgrade-insecure-requests': '1'
                            }
                            }
                    }

        yield get_pre_request
        yield get_first_page

        # if self.next_page:
        #     @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=['hotel', 'room'])
        #     def get_next_page():
        #         # url = 'https://www.ihg.com/hotels/cn/zh/reservation/searchresult/more?&qDest=纽约城, NY, 美国&qChld=0&qAAR=6CBARC&qGRM=0&qRms=1&srb_u=1&qAdlt=1&qCiMy=002018&qCoD=01&qCiD=29&qCoMy=012018&qRpn=2&ajax=true'
        #         while self.next_page:
        #             yield {'req': {'url': self.next_page}}
        #
        #     yield get_next_page

    def parse_hotel(self, req, resp):
        # with open('ihg.html', 'w') as f:
        #     f.write(resp)
        html = etree.HTML(resp)
        # self.next_page = None
        # if 'showMoreResultsSpan' in resp:
        #     next_url = html.xpath('//span[@class="showMoreResultsSpan"]/a[@id="showAllLink"]/@href')[0]
        #     print next_url
        #     if next_url:
        #        self.next_page = 'https://www.ihg.com/' + next_url
        # else:
        resRows = html.xpath('//div[contains(@class,"resRow")]//a[contains(@class,"detailsLink")]')
        for row in resRows:
            room = Room()
            room.source_hotelid = row.xpath('./@name')[0]
            room.hotel_name = row.xpath('/@title')
            room.hotel_url = row.xpath('./@href')[0]
            if 'holiday' in room.hotel_url:
                self.result['holiday_filter'].append(room.hotel_url)
                continue
            print room.hotel_url
            url2 = 'https://www.ihg.com/hotels/cn/zh/reservation/searchresult/viewhoteldetail/%s?qDest=%s&qRpn=1&qChld=0&qAAR=6CBARC&qRms=1&srb_u=1&qAdlt=1&qCiMy=002018&qCoD=20&qCiD=18&qCoMy=002018'
            dest = re.findall(r'qDest=([^&]*)', room.hotel_url)[0]
            print dest
            url2 = url2 % (room.source_hotelid, dest)
            room_tuple = (room.source_hotelid, "{}#####{}".format(room.hotel_url, url2))
            self.rooms.append(room_tuple)
        return self.rooms

    def parse_room(self, req, resp):
        pass


if __name__ == "__main__":
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, simple_get_http_proxy

    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy

    task = Task()
    task.ticket_info = {
        'is_new_type': True,
        'suggest_type': 2,
        # 'suggest': {"hits": 2, "countryCode": "0001", "longitude": -84.083298, "label": "London, KY, United States", "rank": 2.968756356707367, "suggestion": "London, KY, United States", "destinationType": "CITY", "latitude": 37.128899, "type": "B"},
        'suggest': '''{"hits": 2, "countryCode": "0925", "longitude": -0.12714, "label": "London, United Kingdom", "rank": 10.0, "suggestion": "London, United Kingdom", "destinationType": "CITY", "latitude": 51.506321, "type": "B"}''',
        # 'dest_city': '巴黎',
        'check_in': '20180118',
        # 'check_out': '20180120',
        'stay_nights': '2',
        'occ': '1',
        'tid': 'demo',
        'used_times': 0
        # 'room_count': '1'
    }

    spider = IhgListSpider(task)
    spider.crawl(required=['hotel'])
    print spider.code
    print json.dumps(spider.result, ensure_ascii=False)
    print spider.result['holiday_filter']
