#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Created on    : 18/1/8 下午6:08
# @Author  : zpy
# @Software: PyCharm

# Roundflight

import json
import urllib
from mioji.common import parser_except
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common.spider import Spider, request, PROXY_REQ

map_cabin = {
    'ECONOMY': 'E',
    'BUSINESS': 'B',
    'FIRST': 'F',
}


def get_cabin(x):
    for i in map_cabin:
        if i in x:
            return map_cabin[i]
    return 'E'


CABIN_MAP = {
    'E': 'Economy',
    'B': 'Business',
    'F': 'First',
    'P': 'PremiumEconomy'
}


class CsairRoundSpider(Spider):
    """ 南航单程爬虫
    多个接口
    使用direct 请求 北京到巴黎 ，将internation 设为0 。 返回无航线
    使用direct 请求 北京到巴黎 ，将internation 设为1 。 返回500错误
    使用interDirect 请求 北京到巴黎 ，将internation 设为0 。返回 routeQueryError
    使用interDirect 请求 北京到巴黎 ，将internation 设为1 。success

    """
    # source_type = 'csairRoundFlight'
    # targets = {
    #     'flight': {'version': 'InsertRoundFlight2'},
    # }
    # old_spider_tag = {
    #     'csairRoundFlight': {'required': ['flight']}
    # }

    def parse_task(self, task, data):
        """ 解析task 和data组合起来。
        往返的 PEK&CDG&20180225&20180227
        """
        try:
            dep, arr, dept, dest = task.content.split('&')
        except ValueError:
            raise parser_except.ParserException(12, 'check task')

        data['depcity'] = dep
        data['arrcity'] = arr
        data['flightdate'] = dept + dest
        data = 'json=' + urllib.quote(json.dumps(data))
        return data

    def targets_request(self):
        """ 国内的往返就是来回打了两次请求。。。使用的接口和之前的是相同的。"""

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_flight)
        def foreign_page():
            """请求国际的航线 """
            data = {"depcity": "PEK", "arrcity": "CDG", "flightdate": "2018012020180121",
                    "adultnum": "1", "childnum": "0", "infantnum": "0", "cabinorder": "0",
                    "airline": "1", "flytype": "0", "international": "1", "action": "0",
                    "segtype": "0", "cache": "0", "preUrl": ""}
            pdata = self.parse_task(self.task, data)
            return {
                'req': {
                    'url': 'https://b2c.csair.com/B2C40/query/jaxb/interReturn/query.ao',
                    'method': 'post',
                    'params': pdata,

                },
                'data': {'content_type': 'json'}
            }

        yield foreign_page

    def get_planetype_tax(self, planes, pcode, ktype='code'):
        """ 传入planes的列表，用code来寻找对应的飞机 获取plane_type ， tax"""
        plane_type, tax = 'NULL', 0
        for p in planes:
            if p[ktype] == pcode:
                ptype = ['enName', 'enplanename']
                for i in ptype:
                    if i in p:
                        plane_type = p[i]
                if 'airportTax' in p:
                    tax = float(p['airportTax'])
        return plane_type, tax

    def parse_flight(self, req, data):
        """ 获取国外航线的信息。 """
        if 'message' in data:  # 返回的字段中只有一个 错误信息
            raise parser_except.ParserException(29, "无该航线")
        res = []
        dateflights = data['dateflight']
        planes = data['planes']
        src_format = '%Y-%m-%dT%H:%M'
        for f in dateflights:
            # 航线
            for _price in f['prices']:
                # 航线不同价格
                m_flight = MFlight(MFlight.OD_ROUND)
                m_flight.source = 'csair'
                seg_index = 0
                flights_for_tax = []
                for _seg in f['segment']:
                    # 程
                    m_leg = MFlightLeg()
                    for _flight in _seg['flight']:
                        # 每程经停
                        m_seg = MFlightSegment()
                        m_seg.dept_id = _flight['depport']
                        m_seg.dest_id = _flight['arrport']
                        m_seg.set_dept_date(_flight['deptime'], src_format)
                        m_seg.set_dest_date(_flight['arrtime'], src_format)
                        m_seg.flight_no = _flight['flightNo']
                        m_seg.plane_type = _flight['plane']
                        m_seg.share_flight = True if _flight['codeshare'] == 'true' else False
                        _seat_type = get_cabin(_price['adultcabins'][seg_index]['type'])
                        m_seg.seat_type = CABIN_MAP.get(_seat_type)
                        m_seg.real_class = m_seg.seat_type
                        m_leg.append_seg(m_seg)
                        flights_for_tax.append(_flight['plane'])
                        seg_index += 1
                    m_flight.append_leg(m_leg)
                m_flight.stopby = get_cabin(_price['cabintype1'])  # 往返暂时取去程的等级，待议
                m_flight.price = float(_price['adultprice'])
                m_flight.currency = _price['adultcurrency']
                # m_flight.tax = [self.get_planetype_tax(planes, i, 'planetype')[1]
                #                 for i in flights_for_tax][0]
                adultcn = float(_price['adultcn'])
                adultxt = float(_price['adultxt'])
                adultyq = float(_price['adultyq'])
                m_flight.tax = float(adultcn + adultxt + adultyq)
                # if self.check_seat(m_flight):
                #     res.append(m_flight.convert_to_mioji_flight().to_tuple())
                res.append(m_flight.convert_to_mioji_flight().to_tuple())

        return res

    # def check_seat(self, flight):
    #     for leg in flight.legs:
    #         for seg in leg.segments:
    #             _ticket_seat = self.task.ticket_info.get('v_seat_type', 'E')
    #             seat_type = CABIN_MAP.get(_ticket_seat)
    #             if seg.seat_type != seat_type:
    #                 return False
    #     return True


if __name__ == '__main__':
    from mioji.common.task_info import Task

    spider = CsairRoundSpider()
    task = Task(source='csairRoundFlight', content='SHA&PAR&20180311&20180319')
    spider.task = task
    print spider.crawl()
    print spider.result
