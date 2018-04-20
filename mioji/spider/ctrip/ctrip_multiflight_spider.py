#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
import ctrip_multi_flight_lib
import ctrip_flight_lib
from collections import OrderedDict
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import urllib
from common_lib import process_ages, seat_type_to_queryparam

SEARCH_INDEX_URL = 'http://flights.ctrip.com/international/SearchIndex.aspx'
SEARCH_FLIGHTS_URL = 'http://flights.ctrip.com/international/AjaxRequest/SearchFlights/AsyncSearchHandlerSOAII.ashx'
header = {
    # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    "Content-Type": "application/x-www-form-urlencoded",
    'Referer': 'http://www.ctrip.com/international/',
    'Connection': 'keep-alive'
}

#  drpSubClass:C_F， 公务舱 drpSubClass:C
#  drpSubClass:F
#  Airline ALL


carbin_dict = {'E': 'Y_S', 'B': 'C', 'F': 'F', 'P': 'Y_S'}  # {'E':'Y_S', 'P': 'Y_S', 'F': 'C_F', 'B': 'C'}


class CtripMultiFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripMultiFlight'
    targets = {
        # 例行需指定数据版本：InsertMultiFlight
       'MultiFlight': {'version': 'InsertMultiFlight'},
    }

    old_spider_tag = {
        'ctripMultiFlight': {'required': ['MultiFlight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

        self.tickets = []
        self.tmp_ticket_storage = []
        self.tmp_storage = {}
        self.ticket_dict = OrderedDict()
        self.flight_no_part1 = None
        self.flight_no_part2 = None
        self.verify_cabin = None
        self.filter_func = lambda x: True
        self.max_count = 5

    def targets_request(self):
        # u can get task info from self.task
        task = self.task
        self.process_init_data()
        try:
            params = ctrip_multi_flight_lib.create_multi_search_params(task)
        except:
            raise parser_except.ParserException(12, '任务出错')
        params['drpSubClass'] = self.verify_cabin

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def search_index_request():
            ret = {'req':
                {
                    'url': SEARCH_INDEX_URL,
                    'method': 'post',
                    'data': params,
                    'headers': header,
                },
                'user_handler': [
                    self.index_condition_handler
                ]
            }
            return ret

        yield search_index_request

        @request(retry_count=2, proxy_type=PROXY_FLLOW, async=True)  # , binding=self.parse_MultiFlight
        def search_flights_request():
            pages = []
            header['Referer'] = SEARCH_INDEX_URL
            pages.append({
                'req': {'url': SEARCH_FLIGHTS_URL, 'data': self.user_datas['condition'][:-1] + str(1), 'method': 'post',
                        'headers': header},
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_slices]  # , self.sort_price]
            })
            self.user_datas['condition'] = self.user_datas['condition'].replace('SearchMode=Search', 'SearchMode=TokenSearch')
            pages.append({
                'req': {'url': SEARCH_FLIGHTS_URL, 'data': self.user_datas['condition'][:-1] + str(2), 'method': 'post',
                        'headers': header},
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_slices]
            })
            pages.append({
                'req': {'url': SEARCH_FLIGHTS_URL, 'data': self.user_datas['condition'][:-1] + str(3), 'method': 'post',
                        'headers': header},
                'data': {'content_type': 'json'},
                'user_handler': [self.parse_slices]
            })
            return pages

        yield search_flights_request

        @request(retry_count=2, proxy_type=PROXY_FLLOW, async=False, binding=self.parse_MultiFlight)
        def get_second_trip_requests():
            for ticket_key, ticket_info in self.ticket_dict.items():
                ret = {
                    'req':
                        {'url': SEARCH_FLIGHTS_URL,
                         'data': self.generate_second_part_postdata(ticket_info),
                         'method': 'post',
                         'headers': header
                         },
                    'data': {
                        'content_type': 'json'
                    },
                    'user_handler': [
                        self.parse_slices_second_part
                    ],
                    'useful_field': ticket_key
                }
                yield ret
        yield get_second_trip_requests

    def index_condition_handler(self, req, data):
        if '对不起，您访问的太快了，休息一下吧。或者登录您的携程帐号继续访问' in data:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN,
                                                'ctripMultiFlight::代理被封')
        try:
            # params = ctrip_flight_lib.get_postdata(data)
            # self.user_datas['condition'] = params
            condition = self.process_post_data(data)
            params = 'SearchMode=Search&condition={0}&SearchToken=1'.format(urllib.quote(condition, safe='()'))
            # print params
            self.user_datas['condition'] = params
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID,
                                                'ctripMultiFlight::无法获取postdata')
        # params = ctrip_flight_lib.get_postdata(data)

    # def sort_price(self, req, data):
    #     print('aaa')

    def process_init_data(self):
        ticket_info = self.task.ticket_info
        self.verify_cabin = ticket_info.get('v_seat_type', 'E').split('_')[0]  # seat_type_to_queryparam(ticket_info.get('v_seat_type', 'E').split('_')[0])  #
        if 'flight_no' in ticket_info:
            self.flight_no_part1, self.flight_no_part2 = self.task.ticket_info['flight_no'].split('&')
        else:
            self.max_count = 5

    def process_post_data(self, data):
        ticket_info = self.task.ticket_info
        count = int(ticket_info.get('v_count', '1'))
        ages = ticket_info.get('v_age', '-1')
        adults, childs, infants = process_ages(count, ages)
        self.user_datas['adults, childs, infants'] = adults, childs, infants
        condition = json.loads(ctrip_flight_lib.get_postdata(data))
        condition['Quantity'] = adults
        condition['ChildQuantity'] = childs
        condition['InfantQuantity'] = infants
        condition['drpSubClass'] = carbin_dict[self.verify_cabin]
        condition = json.dumps(condition)
        condition = condition.encode('utf-8')
        # print condition
        return condition

    def cache_check(self, req, data):
        return False

    def parse_slices(self, req, data):
        if data['ReturnCode'] != 0:
            return
        if self.flight_no_part1:
            self.filter_func = ctrip_multi_flight_lib.get_filter('flight_no', self.flight_no_part1)
        else:
            self.filter_func = ctrip_multi_flight_lib.get_filter('')
        val = ctrip_multi_flight_lib.parse_flight(data, self.user_datas['adults, childs, infants'], self.filter_func)
        print len(val)
        self.ticket_filter(val)
        for k in self.ticket_dict.keys():
            print k
        print len(self.ticket_dict)

    def parse_slices_second_part(self, req, data):
        if data['ReturnCode'] != 0:
            return
        ticket_key = req['useful_field']
        if self.flight_no_part2:
            self.filter_func = ctrip_multi_flight_lib.get_filter('flight_no', self.flight_no_part2)
        else:
            self.filter_func = ctrip_multi_flight_lib.get_filter('')
        result = ctrip_multi_flight_lib.parse_flight(data, self.user_datas['adults, childs, infants'], self.filter_func)
        self.tmp_storage[ticket_key] = result

    def combine_tickets(self, ticket_key):
        tickets = []
        ticket_info = self.ticket_dict[ticket_key]
        for tmp in self.tmp_storage[ticket_key]:
            para = []
            inde = [9, 10, 11, 12, 14, 21]
            for x in range(len(ticket_info) - 1):
                if x in inde:
                    para.append(tmp[x])
                else:
                    para.append(str(ticket_info[x]) + '&' + str(tmp[x]))
            tickets.append(tuple(para))
        self.tickets.extend(tickets)
        return tickets

    def ticket_filter(self, ticket_list):
        _ticket_dict = OrderedDict()
        for ticket in ticket_list:
            key = ticket[0] + '|' + ticket[13] + '|' + ticket[15] + '|' + str(ticket[10])
            if key not in self.ticket_dict:
                _ticket_dict[key] = ticket
            elif self.ticket_dict[key][10] > ticket[10]:
                _ticket_dict[key] = ticket

        # 拿页面前五个
        range_max = min(len(_ticket_dict), 5)
        for index in range(range_max):
            k,v = _ticket_dict.popitem(0)
            self.ticket_dict[k] = v

        # 拿除页面前五剩余的top 5低价
        result = sorted(_ticket_dict.items(),key=lambda x:x[1][10])
        for item in result[:5]:
            self.ticket_dict[item[0]] = item[1]

    def generate_second_part_postdata(self, sec):
        postdata = self.user_datas['condition'].replace(
            'SearchMode=TokenSearch', 'SearchMode=NextSegment&SegmentNo=2')
        postdata = postdata.replace('SearchToken=1', 'Parameter=' + sec[-1] +
                                    '&ABTString=M%3A63%2C160819_fli_ihtcp%3AC%3BM%3A92%2C161212_fli_fi' \
                                    '3xp%3AD%3BM%3A66%2C161107_fli_fispo%3AB%3BM%3A66%2C170120_fli_dho%3AA%3B')
        return postdata

    def parse_MultiFlight(self, req, data):
        return self.combine_tickets(req['useful_field'])

    # def response_callback(self, req, resp):u'UA889'
    #     print req


def save_resp_file(content, called_count=[0], endwith='josn'):
    file_name = "tmp%s.%s" % (called_count[0], endwith)
    with open(file_name, 'w') as fd:
        fd.write(json.dumps(content, ensure_ascii=False))
    called_count[0] += 1


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
    # httpset_debug()

    content = 'BJS&LON&20181117|MAN&BJS&20181124'
    task = Task('ctripmultiFlight', content)
    task.ticket_info = {'v_seat_type': 'F'}
    # task.ticket_info["flight_no"] = "LH723_LH2456&LH1167_LH720"
    # task.ticket_info["flight_no"] = "UA889&CA984"

    spider = CtripMultiFlightSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    # import json
    #
    print json.dumps(spider.result['MultiFlight'], ensure_ascii=False)
    # print spider.result
