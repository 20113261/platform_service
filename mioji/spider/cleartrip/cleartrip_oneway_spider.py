#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年04月05日

@author: dongkai
"""
import sys
import sys
sys.path.insert(0, '/Users/miojilx/Desktop/git/Spider/src/')
sys.path.insert(0, '/Users/miojilx/Desktop/git/slave_develop_new/workspace/spider/SpiderClient/bin')
sys.path.insert(0, '/Users/miojilx/Desktop/git/slave_develop_new/workspace/spider/SpiderClient/lib')
sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import cleartrip_oneway_lib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class ClearTripFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cleartripFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
        'Flight': {'version': 'InsertNewFlight'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        "cleartripFlight": {"required": ["Flight"]}
        # 'cleartripRoundFlight': {'required': ['Flight']}
    }

    def targets_request(self):
        task_dict = cleartrip_oneway_lib.content_parser(self.task)

        # @request(retry_count=3, proxy_type=PROXY_REQ)
        # def home_page():
        #     return {
        #         'req': {
        #             'url': 'http://www.cleartrip.sa',
        #         }
        #     }

        referer = cleartrip_oneway_lib.get_referer_url(task_dict)
        json_url, dest_city, dept_city = cleartrip_oneway_lib.get_json_url(task_dict)

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_Flight, ip_type="foreign")
        def json_page():
            return {
                'req': {
                    'url': json_url,
                },
                'data': {'content_type': 'json'}
            }

        # yield home_page   
        yield json_page

    def cache_check(self, req, data):
        return False

    def parse_Flight(self, req, data):
        if 'fare' in data and 'content' in data:
            try:
                return cleartrip_oneway_lib.page_parser(data)
            except Exception:
                parser_except.ParserException(parser_except.PARSE_ERROR, 'cleartripOneWayFlight::爬虫解析异常')
        else:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, 'cleartripOneWayFlight::数据中无正常的机票信息,被封禁')


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy_new
    from mioji.common import spider

    spider.slave_get_proxy = simple_get_socks_proxy_new
    content = 'SFO&CDG&20180123'
    task = Task('cleartrip::cleartrip', content)
    task.ticket_info["flight_no"] = "LH723_LH2456&LH1167_LH720"

    spider = ClearTripFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    for i,result in enumerate(spider.result['Flight']):
        print "数量：",i,":",result
