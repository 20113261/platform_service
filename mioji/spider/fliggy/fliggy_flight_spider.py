#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json
import random
import time
import re
from mioji.common.utils import setdefaultencoding_utf8
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.logger import logger
import mioji.common.spider
from fliggy_flight_parse import Fliggy_flight_parse

setdefaultencoding_utf8()


class FliggyFlightSpider(Spider):
    source_type = 'fliggyFlight'
    targets = {'Flight': {'version': 'InsertNewFlight'}}
    old_spider_tag = {'fliggyFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.task_info = {}
        self.tickets = []
        self.task_info = None
        self.flag = False
        self.retry = 4
        self.search_index = "https://www.fliggy.com/ijipiao"
        self.search_result = ('https://sijipiao.fliggy.com/ie/flight_search_result.htm?'
                              'searchBy=1278'
                              '&tripType=1'
                              '&depCity={dep_city}'
                              '&arrCity={arr_city}'
                              '&depDate={dep_date}')

    def targets_request(self):
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')
        self.dep_city = self.task.content[:3]
        self.arr_city = self.task.content[4:7]
        self.dep_date = (self.task.content[8:12] + '-' + self.task.content[12:14] +
                    '-' + self.task.content[14:])

        @request(retry_count=3, proxy_type=PROXY_REQ, async=False,
                 new_session=True)
        def visit_search_index():
            """访问航班搜索页面"""
            search_entrance = [
                "https://www.baidu.com/s?ie=utf-8&wd=%E9%A3%9E%E7%8C%AA",
                "https://www.sogou.com/web?query=%E9%A3%9E%E7%8C%AA",
                "https://www.so.com/s?ie=utf-8&fr=so.com&src=home_so.com&q=%E9%A3%9E%E7%8C%AA"
            ]
            page = {
                "req": {
                    "url": self.search_index,
                    "method": "get",
                    "headers": {
                        "referer": random.choice(search_entrance)
                    }
                },
            }
            return [page]
        def get_result_url():
            return self.search_result.format(dep_city=self.dep_city, arr_city=self.arr_city,
                                             dep_date=self.dep_date)
        _referer = get_result_url()

        @request(retry_count=4, proxy_type=PROXY_REQ, async=False,
                 binding=self.parse_Flight, new_session=False)
        def get_flight_data():
            """获取搜索结果"""

            # searchCabinType : 0: 全部    1：经济     2：商务/头等
            cabin = self.task.ticket_info.get('v_seat_type', 0)
            if cabin == 'E': cabin = 1
            elif cabin == 'F' or cabin == 'B': cabin = 2
            query_url = 'https://sijipiao.fliggy.com/ie/flight_search_result_poller.do?src=filter&supportMultiTrip=true&searchBy=1281&searchJourney=%5b%7b%22arrCityCode%22%3a%22{}%22%2c%22depCityCode%22%3a%22{}%22%2c%22depDate%22%3a%22{}%22%7d%5d&tripType=0&searchCabinType={}&agentId=-1&searchMode=0&b2g=0&formNo=-1&cardId=&needMemberPrice=true'.format(self.arr_city, self.dep_city, self.dep_date, cabin)
            page = {
                'req': {'url': query_url,
                        'method': 'get',
                        'headers': {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
                                    'referer': _referer
                                    },
                        }}
            return page
        yield get_flight_data
        while self.flag and self.retry > 0:
            logger.error('被封禁，剩余重试次数' + str(self.retry))
            yield get_flight_data
            self.retry -= 1
        if self.retry == 0 and self.flag:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN, '代理被封禁')


    def parse_Flight(self, req, resp):
        resp = resp.decode('unicode_escape')
        resp = resp.replace('{0:', '{"0":', 1000)
        cabin = self.task.ticket_info['v_seat_type']
        # resp = re.compile('\((.*)\)').search(resp).group(1)
        try:
            resp = json.loads(resp)
        except:
            self.flag = True
            return
        if 'url' in resp:
            # 被封禁了
            self.flag = True
            return
        parser = Fliggy_flight_parse()
        self.flag = False
        return parser.parse_one_way(resp, cabin)


"""
jsonp2578({"rgv587_flag":"sm","url":"https://sec.taobao.com/query.htm?action=QueryAction&event_submit_do_css=ok&smApp=iespro&smPolicy=iespro-result_poller-anti_Spider-checklogin&smCharset=GBK&smTag=MTE5LjEyMy4zNC40NywsNTAyMGM0NmYxNWFkNGExMTllOWI0Mzc1MDVkMzExMzE%3D&smReturn=https%3A%2F%2Fsijipiao.fliggy.com%2Fie%2Fflight_search_result_poller.do%3Fsrc%3Dfilter%26_ksTS%3D151676140466_2577%26callback%3Djsonp2578%26supportMultiTrip%3Dtrue%26searchBy%3D1280%26searchJourney%3D%255B%257B%2522arrCityCode%2522%253A%2522TYO%2522%252C%2522depCityCode%2522%253A%2522BJS%2522%252C%2522depDate%2522%253A%25222018-01-31%2522%252C%2522selectedFlights%2522%253A%255B%255D%257D%252C%257B%2522arrCityCode%2522%253A%2522BJS%2522%252C%2522depCityCode%2522%253A%2522TYO%2522%252C%2522depDate%2522%253A%25222018-02-03%2522%257D%255D%26tripType%3D1%26searchCabinType%3D2%26agentId%3D-1%26searchMode%3D0%26b2g%3D0%26formNo%3D-1%26cardId%3D%26needMemberPrice%3D&smSign=CytxfnyHcbK6LwgundPEcg%3D%3D"})
"""

if __name__ == '__main__':
    # 测试
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new
    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new
    fliggy_list = ['BUD&SJJ&20180424']

    result_count = 0
    for _task in fliggy_list:
        task = Task()
        task.content = _task
        task.ticket_info = {'v_seat_type': 'E', 'flight_no': 'UA078'}
        spider = FliggyFlightSpider()
        spider.task = task
        result_code = spider.crawl()
        if result_code == 0:
            result_count += 1
        print spider.result
        print spider.code

    print '总共成功次数：', result_count

