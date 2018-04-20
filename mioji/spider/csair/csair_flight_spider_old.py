#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Created on    : 18/1/4 上午9:46
# @Author  : zpy
# @Software: PyCharm

from mioji.common.class_common import Flight
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import json
import urllib

map_cabin = {
    'ECONOMY': 'E',
    'BUSINESS': 'B',
    'FIRST': 'F',
}


# get_cabin = lambda x: [x[i] for i in map_cabin if i in x][0]
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


class CsairSpider(Spider):
    """ 南航单程爬虫
    多个接口
    使用direct 请求 北京到巴黎 ，将internation 设为0 。 返回无航线
    使用direct 请求 北京到巴黎 ，将internation 设为1 。 返回500错误
    使用interDirect 请求 北京到巴黎 ，将internation 设为0 。返回 routeQueryError
    使用interDirect 请求 北京到巴黎 ，将internation 设为1 。success

    """
    #
    # source_type = 'csairFlight'
    # targets = {
    #     'flight': {'version': 'InsertNewFlight'},
    # }
    # old_spider_tag = {
    #     'csairFlight': {'required': ['flight']}
    # }

    def targets_request(self):

        # @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_flight_inter)
        # def json_page():
        #     """请求国内的航线 """
        #     data = {"depcity": '', "arrcity": '', "flightdate": '', "adultnum": "1", "childnum": "0",
        #             "infantnum": "0", "cabinorder": "0", "airline": "1", "flytype": "0", "international": "0",
        #             "action": "0", "segtype": "1", "cache": "0", "preUrl": ""}
        #     pdata = self.parse_task(self.task, data)
        #
        #     return {
        #         'req': {
        #             'url': 'https://b2c.csair.com/B2C40/query/jaxb/direct/query.ao',
        #             'method': 'post',
        #             'params': pdata
        #
        #         },
        #         'data': {'content_type': 'json'}
        #     }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_flight)
        def other_page():
            """请求国际的航线"""
            data = {"depcity": 'PEK', "arrcity": 'CDG', "flightdate": '20180302',
                    "adultnum": "1", "childnum": "0", "infantnum": "0", "cabinorder": "0",
                    "airline": "1", "flytype": "0", "international": "1", "action": "0",
                    "segtype": "1", "cache": "0", "preUrl": ""}

            pdata = self.parse_task(self.task, data)

            return {
                'req': {
                    'url': 'https://b2c.csair.com/B2C40/query/jaxb/interDirect/query.ao',
                    'method': 'post',
                    'params': pdata

                },
                'data': {'content_type': 'json'}
            }

        # yield json_page # 暂无国内的航线。 直接打国外的。
        # if self.next_page:
        yield other_page

    def parse_task(self, task, data):
        try:
            dep, arr, date = task.content.split('&')
        except ValueError:
            raise parser_except.ParserException(12, 'check task')
        data['depcity'] = dep
        data['arrcity'] = arr
        data['flightdate'] = date
        data = 'json=' + urllib.quote(json.dumps(data))
        return data

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

    def convert_time(self, d):
        """(20180301, 0905) --> 2018-01-05T12:13"""
        return self.convert_date(d[0]) + 'T' + d[1][:2] + ':' + d[1][2:] + ':00'

    def convert_date(self, d):
        """ 20180101 --> 2018-01-01"""
        return '-'.join([d[:4], d[4:6], d[6:8]])

    def parse_flight_inter(self, req, data):
        """ 获取国内航线的信息"""
        if 'message' in data:  # 返回的字段中只有一个 错误信息
            self.next_page = True
            return
        res = []
        flight_nos = data['segment']['dateflight']['flight']
        planes = data['planes']
        flight = Flight()
        flight.dept_id = data['airports'][-1]['code']  # 起点站 direct和interdirect不同。。。
        flight.dest_id = data['airports'][0]['code']  # 终点站
        if len(data['airports']) > 2:  # 不准确。。
            flight.dept_id, flight.dest_id = flight.dest_id, flight.dept_id

        for f in flight_nos:
            flight.dept_day = f['deptime'][:10]  # 出发时间
            flight.flight_no = f['flightno']  # 航班号
            pcode = f['plane']

            dep = (f['depdate'], f['deptime'])
            arr = (f['arrdate'], f['arrtime'])
            flight.dept_time = self.convert_time(dep)
            flight.dest_time = self.convert_time(arr)

            for p in f['cabin']:
                flight.price = float(p['adultprice'])  # 价格
                flight.plane_type, flight.tax = self.get_planetype_tax(planes, pcode, 'planetype')  # 飞机机型， 税费
                res.append(flight.to_tuple())
        return res

    def parse_flight(self, req, data):
        """ 获取国外航线的信息。 """
        if 'message' in data:  # 返回的字段中只有一个 错误信息
            raise parser_except.ParserException(29, "无该航线")
        res = []
        dateflights = data['segment'][0]['dateflight']
        planes = data['planes']
        src_format = '%Y-%m-%dT%H:%M'
        for f in dateflights:
            for p_index, _price in enumerate(f['prices']):
                m_flight = MFlight(MFlight.OD_ONE_WAY)
                m_flight.source = 'csair'
                m_leg = MFlightLeg()
                for f_index, _flight in enumerate(f['flight']):
                    _seat_type = get_cabin(_price['adultcabins'][f_index]['type'])
                    if _seat_type != self.task.ticket_info.get('v_seat_type', 'E'):
                        m_leg.segments = []
                        break
                    m_seg = MFlightSegment()
                    m_seg.seat_type = CABIN_MAP.get(_seat_type)
                    m_seg.dept_id = _flight['depport']
                    m_seg.dest_id = _flight['arrport']
                    m_seg.set_dept_date(_flight['deptime'], src_format)
                    m_seg.set_dest_date(_flight['arrtime'], src_format)
                    m_seg.flight_no = _flight['flightNo']
                    m_seg.plane_type = _flight['plane']
                    m_seg.share_flight = True if _flight['codeshare'] == 'true' else False
                    m_seg.real_class = m_seg.seat_type
                    m_leg.append_seg(m_seg)
                if not m_leg.segments:
                    break
                m_flight.stopby = get_cabin(_price['cabintype'])
                m_flight.price = float(_price['adultprice'])
                m_flight.currency = _price['adultcurrency']
                # m_flight.tax = [self.get_planetype_tax(planes, i['plane'], 'planetype')[1]
                #                 for i in f['flight']][0]
                adultcn = float(_price['adultcn'])
                adultxt = float(_price['adultxt'])
                adultyq = float(_price['adultyq'])
                m_flight.tax = float(adultcn + adultxt + adultyq)
                m_flight.append_leg(m_leg)
                res.append(m_flight.convert_to_mioji_flight().to_tuple())

        return res


if __name__ == '__main__':
    from mioji.common.task_info import Task

    spider = CsairSpider()
    task = Task(source='csairFlight', content='PEK&CDG&20180320')
    spider.task = task
    print spider.crawl()
    print spider.result
