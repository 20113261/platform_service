#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年03月31日

@author: hourong
"""
import sys
sys.path.append("/Users/miojilx/Spider/src")
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import time
import cleartrip_round_lib
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ClearTripRoundFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'cleartripRoundFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
        'RoundFlight': {'version': 'InsertRoundFlight2'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        'cleartripRoundFlight': {'required': ['RoundFlight']}
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

    def create_params(self):
        """
        生成往返请求参数的函数。返回 dict 格式。
        """
        # task_dict = cleartrip_round_lib.content_parser(self.task.content, self.task.ticket_info)

        # pull data 类型请求的判定
        base_params = cleartrip_round_lib.roundtrip_base_params(self.task_dict)
        psid = self.user_datas.get("psid")
        if psid:
            params = self.async_add_params(base_params)
        else:
            self.user_datas["sd"] = base_params["sd"]
            params = base_params
            params["rhc"] = 1
        params["cc"] = self.user_datas.get("cc", 1)
        return params

    def targets_request(self):
        self.task_dict = cleartrip_round_lib.content_parser(self.task.content, self.task.ticket_info)
        self.user_datas['cc'] = 1
        # @request(retry_count=3, proxy_type=PROXY_REQ)
        # def home_page():
        #     return {
        #         'req': {
        #             'url': 'http://www.cleartrip.sa/flights',
        #         }
        #     }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_RoundFlight, user_retry=True, ip_type="foreign")
        def json_page():
            referer = cleartrip_round_lib.get_referer_url(self.task_dict)
            header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                      'Accept-Encoding': 'gzip, deflate, br',
                      'Accept-Language': 'zh-CN,zh;q=0.8',
                      'Cache-Control': 'no-cache',
                      'Connection': 'keep-alive',
                      'Host': 'www.cleartrip.sa',
                      'Pragma': 'no-cache',
                      'Referer': referer,
                      'utm_campaign': 'air_pg_fee',
                      'X-Requested-With': 'XMLHttpRequest'}
            return {"req": {
                            "url": "https://www.cleartrip.sa/flights/results/intlairjson",
                            "params": self.create_params(),
                            "headers": header},
                    "data": {"content_type": "json"}
            }
        yield json_page

    def user_retry_err_or_resp(self, err_or_resp, retry_count, request_template, is_exc):
        data = json.loads(err_or_resp.content)
        self.user_datas["expiredSupplier"] = data["expiredSupplier"]
        self.user_datas["psid"] = data["sid"]
        self.user_datas["expiry"] = data["jsons"]["expiredSuppliers"]
        if all(map(lambda x: x in data, ['fare', 'content'])):
            return True
        else:
            self.user_datas["call_in"] = data["jsons"]["call_in"]
            self.user_datas["cc"] += 1
            request_template["req"]["params"] = self.create_params()
            return False

    def cache_check(self, req, data):
        return False

    def parse_RoundFlight(self, req, data):
        if self.user_datas['cc'] > 10:
            parser_except.ParserException(
                parser_except.PROXY_INVALID, 'cleartripRoundFlight::爬虫代理被禁')
        else:
            try:
                return cleartrip_round_lib.page_parser(data, self.task_dict)
            except Exception:
                parser_except.ParserException(
                    parser_except.PARSE_ERROR, 'cleartripRoundFlight::爬虫解析异常')
                # import pdb;pdb.set_trace()
                # self.user_datas["expiredSupplier"] = data["expiredSupplier"]
                # self.user_datas["psid"] = data["sid"]
                # self.user_datas["expiry"] = data["jsons"]["expiredSuppliers"]
                # if all(map(lambda x: x in data, ['fare', 'content'])):
                #     try:
                #         return cleartrip_round_lib.page_parser(data, self.task_dict)
                #     except Exception:
                #         parser_except.ParserException(
                #             parser_except.PARSE_ERROR, 'cleartripRoundFlight::爬虫解析异常')
                # else:
                #     raise parser_except.ParserException(
                #         parser_except.PROXY_INVALID, 'cleartripRoundFlight::页面返回异常')


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_http_proxy, simple_get_socks_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_socks_proxy

    # li = ['PVG&HAM&20170616&20170626', 'TAO&FCO&20170605&20170615', 'TSN&CDG&20170611&20170625', 'XMN&BCN&20170916&20170930']
    li = ['BJS&LON&20170729&20170825']
    for l in li:
        content = l
        task = Task('cleartrip::cleartrip', content)
        # task.ticket_info["flight_no"] = "LH723_LH2456&LH1167_LH720"
        spider = ClearTripRoundFlightSpider()
        spider.task = task
        spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
        for i,result in enumerate(spider.result['RoundFlight']):
            print "数量：",i,":",result

