#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年04月05日

@author: hourong
"""

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import ctrip_round_flight_lib
import re
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import urllib
from common_lib import process_ages, seat_type_to_queryparam


class CtripRoundFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripRoundFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
       'Flight': {'version': 'InsertRoundFlight2'},
    }

    # 对应多个老原爬虫
    old_spider_tag = {
       'ctripRoundFlight': {'required': ['Flight']}
    }

    def targets_request(self):
        dept_id, dest_id, dept_info, dest_info, dept_date, dest_date = ctrip_round_flight_lib.task_parser(
            self.task.content)

        homecity_name = dept_info['city_name']
        destcity_name = dest_info['city_name']
        seat_type = self.task.ticket_info.get('v_seat_type', 'E')
        query_cabin = seat_type_to_queryparam(seat_type)

        Search = 'http://flights.ctrip.com/international/round-%s-%s-%s-%s?%s&%s&%s' % (
            dept_id, dest_id, dept_id.lower(), dest_id.lower(), dept_date, dest_date, query_cabin)
        Search_1 = 'http://flights.ctrip.com/international/AjaxRequest/SearchFlights/AsyncSearchHandlerSOAII.ashx'
        Referer = 'http://flights.ctrip.com/international/'
        post_data_0 = {'FlightWay': 'D', 'homecity_name': homecity_name, 'destcity1_name': destcity_name,
                       'DDatePeriod1': dept_date, 'ADatePeriod1': dest_date, 'Quantity': '1', 'ChildQuantity': '0',
                       'InfantQuantity': '0', 'drpSubClass': query_cabin.upper(), 'IsFavFull': '', 'mkt_header': ''}

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def search_page_0():
            return {
                'req': {
                    'url': Search,
                    'headers': {
                        'Referer': Referer,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Connection': 'keep-alive',
                        #'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
                    },
                    'method': 'post',
                    'data': post_data_0
                },
                'user_handler': [
                    self.post_params_handler
                ],
                'data':
                    {
                        'content_type': 'text'
                    }
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_Flight)
        def search_page_1():
            pages = []
            pages.append({'req': {'url': Search_1,
                                  'headers': {'Referer': Search,
                                              'Content-Type': 'application/x-www-form-urlencoded',
                                              'Connection': 'keep-alive',
                                              },
                                  'method': 'post',
                                  'data': self.user_datas['post_params'],
                                  },
                          'user_extra': {'dept_date': dept_date, 'dest_date': dest_date},
                          'data': {'content_type': self.data_converter}
                          })
            self.user_datas['post_params'] = self.user_datas['post_params'].replace('SearchMode=Search', 'SearchMode=TokenSearch')
            pages.append({'req': {'url': Search_1,
                                  'headers': {'Referer': Search,
                                              'Content-Type': 'application/x-www-form-urlencoded',
                                              'Connection': 'keep-alive',
                                             },
                                  'method': 'post',
                                  'data': self.user_datas['post_params'].replace('SearchToken=1', 'SearchToken=2'),
                                  },
                          'user_extra': {'dept_date': dept_date, 'dest_date': dest_date},
                          'data': {'content_type': self.data_converter}
                          })
            pages.append({'req': {'url': Search_1,
                                  'headers': {'Referer': Search,
                                              'Content-Type': 'application/x-www-form-urlencoded',
                                              'Connection': 'keep-alive',
                                              },
                                  'method': 'post',
                                  'data': self.user_datas['post_params'].replace('SearchToken=2', 'SearchToken=3'),
                                  },
                          'user_extra': {'dept_date': dept_date, 'dest_date': dest_date},
                          'data': {'content_type': self.data_converter}
                          })
            return pages
        return [search_page_0, search_page_1]

    def cache_check(self, req, data):
        return False

    def post_params_handler(self, req, data):
        # self.user_datas['post_params'] = ctrip_round_flight_lib.get_post_data(data)
        if '对不起，您访问的太快了，休息一下吧。或者登录您的携程帐号继续访问' in data:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN,
                                                'ctripMultiFlight::代理被封')
        try:
            condition = self.process_post_data(data)
            params = 'SearchMode=Search&condition={0}&DisplayMode=RoundTripGroup&SearchToken=1'.format(urllib.quote(condition, safe='()'))
            self.user_datas['post_params'] = params
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID,
                                                'ctripMultiFlight::无法获取postdata')

    def process_post_data(self, data):
        ticket_info = self.task.ticket_info
        count = int(ticket_info.get('v_count', '1'))
        ages = ticket_info.get('v_age', '-1')
        adults, childs, infants = process_ages(count, ages)
        self.user_datas['adults, childs, infants'] = adults, childs, infants
        print adults, childs, infants
        condition = json.loads(ctrip_round_flight_lib.get_post_data(data))
        condition['Quantity'] = adults
        condition['ChildQuantity'] = childs
        condition['InfantQuantity'] = infants
        condition = json.dumps(condition)
        condition = condition.encode('utf-8')
        print condition
        return condition

    def data_converter(self, req, data):
        try:
            info = json.loads(data.decode('gbk').encode('utf8'))
        except:
            info = json.loads(data)

        if info is None:
            raise parser_except.ParserException(parser_except.DATA_NONE, 'ctripRound::未获取需要的 condition')

        return info

    def parse_Flight(self, req, data):
        # print data
        # result = ctrip_round_flight_lib.get_tickets(data, req['req']['user_extra']['dept_date'],
        #                                             req['req']['user_extra']['dest_date'])
        result = ctrip_round_flight_lib.get_tickets(data, req['user_extra']['dept_date'],
                                                    req['user_extra']['dest_date'],
                                                    self.user_datas['adults, childs, infants'])
        return result


if __name__ == '__main__':
    import mioji
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.get_proxy = simple_get_socks_proxy_new
    # from mioji.common.utils import simple_get_http_proxy, httpset_debug

    # httpset_debug()
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug, simple_get_socks_proxy_new
    spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    li = ['DLC&ORL&20180502&20180515', 'CSX&PUS&20180502&20170512', 'KMG&BUD&20180502&20170512']
    task.content = "PEK&CDG&20180330&20180402"  # 'XIY&KIX&20170905&20170912'
    task.source = 'ctripRoundFlight'

    spider = CtripRoundFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    print spider.result['Flight'][0]
