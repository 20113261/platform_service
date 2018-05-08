#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年04月05日

@author: dongkai
"""
import sys
sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import time
import cleartrip_multi_lib
from cleartrip_multi_lib import multitrip_base_params as create_params
from cleartrip_multi_lib import parse_content as page_parser

from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from utils import seat_type_to_queryparam

class ClearTripMultiFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cleartripMultiFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
        'Flight': {'version': 'InsertMultiFlight'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        'cleartripMultiFlight': {'required': ['Flight']}
    }

    def async_add_params(self, search_params):
        """
        """
        dept_id = search_params["from"]
        dest_id = search_params["to"]
        ret = {"nbs": 1,
               "fci": self.user_datas.get("call_in", int(time.time() * 1000)),
               "isIntl": True,
               "isRt": True,
               "isMetaSearch": False,
               "numLegs": 1,
               "fromTo1": "{0}_{1}".format(dept_id, dest_id),
               "fromTo2": "{1}_{0}".format(dept_id, dest_id),
               "psid": self.user_datas.get("psid"),
               "expiry": self.user_datas.get("expiry", True)}
        ret.update(search_params)
        return ret

    # def create_params(self):
    #     """
    #     生成往返请求参数的函数。返回 dict 格式。
    #     """
    #     # pull data 类型请求的判定
    #     base_params = cleartrip_multi_lib.multitrip_base_params(self.task_dict)
    #     psid = self.user_datas.get("psid")
    #     if psid:
    #         params = self.async_add_params(base_params)
    #     else:
    #         self.user_datas["sd"] = base_params["sd"]
    #         params = base_params
    #     return params

    def targets_request(self):
        # self.task_dict = cleartrip_multi_lib.content_parser(self.task)

        params = create_params(self.task)
        base_url = 'https://www.cleartrip.sa/flights/international/results?from1={from1}&to1={to1}&depart_date_1={depart_date_1}' +\
                '&multicity=true&from2={from2}&to2={to2}&depart_date_2={depart_date_2}&from3=&to3=&depart_date_3=&adults={adults}' +\
                   '&childs={childs}&infants={infants}&class={class}&intl=y&num_legs=2&sd={sd}'

        flight_url = base_url.format(**params)

        # @request(retry_count=3, proxy_type=PROXY_REQ)
        # def home_page():
        #     return {
        #         'req': {
        #             'url': flight_url,
        #         }
        #     }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Flight)
        def json_page():
            # referer = cleartrip_multi_lib.get_referer_url(self.task_dict)
            header = {'Accept': '*/*',
                      'Accept-Encoding': 'gzip, deflate, br',
                      'Accept-Language': 'zh-CN,zh;q=0.8',
                      #'Cache-Control': 'no-cache',
                      'Connection': 'keep-alive',
                      'Host': 'www.cleartrip.sa',
                      #'Pragma': 'no-cache',
                      'Referer': flight_url,
                      # 'utm_campaign': 'air_pg_fee',
                      'X-Requested-With': 'XMLHttpRequest'
                      }


            ret = {"req":
                       {"url": "https://www.cleartrip.sa/flights/results/mcairjson",
                        "params": params,
                        "headers": header},
                   "data": {"content_type": "json"}}
            return ret
            # while self.user_datas.get("expiredSupplier", True):
            #     yield ret

        # yield home_page
        yield json_page

    def cache_check(self, req, data):
        return False

    def parse_Flight(self, req, data):
        # page parse funcation need args
        adults = self.task.ticket_info.get('adults', 2)

        # self.user_datas["expiredSupplier"] = data["expiredSupplier"]
        # self.user_datas["psid"] = data["sid"]
        # self.user_datas["expiry"] = data["jsons"]["expiredSuppliers"]
        if all(map(lambda x: x in data, ['fare', 'content'])):
            try:
                return page_parser(data, adults)
            except Exception:
                parser_except.ParserException(
                    parser_except.PARSE_ERROR, 'cleartripMultiFlight::爬虫解析异常')
        else:
            raise parser_except.ParserException(
                parser_except.EMPTY_TICKET, 'cleartripMultiFlight::数据中无正常的机票信息')


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy

    mioji.common.spider.get_proxy = simple_get_socks_proxy

    #content = 'ORD&PEK&20170713|PEK&NYC&20170722'
    content = 'BJS&PAR&20170826|PAR&LON&20170830'
    task = Task('cleartrip::cleartrip', content)
    # task.ticket_info["flight_no"] = "LH723_LH2456&LH1167_LH720"

    spider = ClearTripMultiFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})

    for i,value in enumerate(spider.result['Flight']):
        print "数量：",i,":",value
