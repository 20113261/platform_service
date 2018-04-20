# coding:utf-8

from mioji.common.spider import Spider
from mioji.common.spider import request
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common import parser_except

import time
import re
import datetime

num_pat = re.compile(r'(\d+)')
price_pat = re.compile(r'[0-9.,]+')
zh_pat = re.compile(ur'[\u4e00-\u9fa5]+')
en_pat = re.compile(r'[a-zA-Z ]+')
currency_pat = re.compile('[a-zA-Z]+')
pnum_pat = re.compile(r'(\d+)')
others_info_pat = re.compile(ur'（(.+)）')
city_pat = re.compile(r'cn/(.+)-Hotels')
sourceid_pat = re.compile('h(\d+)\.Hotel')
name_pat = re.compile(r'Hotels-(.*?)\.h')


class ExpediaTax(Spider):
    source_type = 'expedia_tax'
    targets = {

        'expedia_tax': {}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联  原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        # 'Tax': {'required': ['room']}
    }

    def setting(self):
        content = self.task.content
        task_list = content.split('&')
        self.task_list = task_list
        self.urltmp = task_list[0]
        self.source_id = sourceid_pat.findall(self.urltmp)[0]
        # self.city = city_pat.findall(self.urltmp)[0].replace('-', ' ')
        # self.hotel_name = name_pat.findall(self.urltmp)[0].replace('-', ' ')
        # print 2
        self.dur = int(task_list[1])
        self.date1 = datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:]))

        self.check_in = str(datetime.datetime(int(task_list[2][:4]), int(task_list[2][4:6]), int(task_list[2][6:])))[
                        :10]
        self.check_in_new = self.check_in[0:4] + "%2F" + self.check_in[5:7] + '%2F' + self.check_in[8:10]
        self.check_out = str(self.date1 + datetime.timedelta(self.dur))[0:10]
        self.check_out_new = self.check_out[0:4] + "%2F" + self.check_out[5:7] + '%2F' + self.check_out[8:10]
        self.children = 0
        self.room_info = self.task.ticket_info.get('room_info', [])
        self.occ = self.task.ticket_info.get('occ', 2)
        self.room_count = self.task.ticket_info.get('room_count', 1)
        self.json_url = 'https://www.expedia.com.hk/api/infosite/{0}/getOffers?token={1}&brandId={2}&isVip=false&chid=&chkin={3}&chkout={4}&ts={5}'
        self.cid = self.task.ticket_info.get('cid', None)

    def targets_request(self):
        self.setting()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            print self.urltmp
            return {
                'req': {'url': self.urltmp},
                'user_handler': [self.process_paging_url]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_expedia_tax)
        def get_tickets_page():
            return {
                'req': {'url': self.json_url},
                'data': {'content_type': 'json'},
            }

        return [first_page, get_tickets_page]

    def process_paging_url(self, req, data):
        html_page = data
        self.html_page = data
        token = re.findall(r"infosite.token = '(.+?)'", html_page)[0]

        brandid = re.findall(r"infosite.hotelBrandId = '(\d+)'", html_page)[0]
        # guid = re.findall(r'GUID: "(.*?)"', html_page)[0]
        ts = str(int(time.time() * 10 ** 3))
        url_json = self.json_url.format(self.source_id, token, brandid, self.check_in_new, self.check_out_new, ts)
        temp_str = '&adults=' + str(self.occ) + '&children=' + str(self.children)
        for i in xrange(self.room_count):
            url_json += temp_str
        self.json_url = url_json

    def parse_expedia_tax(self, req, data):
        offers = data.get('offers', [])
        if not offers:
            return []

        try:
            price = offers[0]['price']['price']
            tax = offers[0]['taxesAndFeesNotIncludedInPrice']['double']
            rate = tax / price
            return [{'price': price, 'tax': tax, 'rate': rate}]
        except:
            return []


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    hotel_url = "http://www.expedia.com.hk/cn/Hotels-Hotel-Romance-Malesherbes-By-Patrick-Hayat.h1753932.Hotel-Information?chkin=2017%2F5%2F20&chkout=2017%2F5%2F21&rm1=a2&regionId=0&hwrqCacheKey=95ac5f10-6c82-4163-9959-901ddc9c674aHWRQ1493094040336&vip=false&c=1993f64d-88df-4719-a274-c3cf51ad721f&&exp_dp=885.37&exp_ts=1493094041525&exp_curr=HKD&exp_pg=HSR"
    task.content = hotel_url.split('?')[0] + "?&1&20171210"
    print task.content
    spider = ExpediaTax()
    spider.task = task

    print spider.crawl()
    print spider.result
