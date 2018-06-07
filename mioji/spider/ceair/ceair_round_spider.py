# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
# import re
# import urllib
import json
import random
# import socket
# import traceback
# from datetime import datetime
# from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_miojilight
# from mioji.common.class_common import Flight
# from mioji.common.phone_user_agent_list import moblie_user_agent
from mioji.common import parser_except


# cabintask = {'E': 0, 'P': 4, 'B': 2, 'F': 3}


class CeairRoundFlightSpider(Spider):
    source_type = 'ceairRoundFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertRoundFlight2'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ceairRoundFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        super(CeairRoundFlightSpider, self).__init__(task=task)
        self.task_info = {}
        self.tickets = []
        self.task_info = None
        self.flight_numbers = []
        self.flight_operating_no = []
        self.mflight = None
        self.already = set()
        self.first_request_success = 0

    def targets_request(self):
        dep, arr, dept_date, dept_date2 = self.task.content.split('&')
        year, month, day = dept_date[:4], dept_date[4:6], dept_date[6:]
        dept_date = '-'.join([year, month, day])
        year, month, day = dept_date2[:4], dept_date2[4:6], dept_date2[6:]
        dept_date2 = '-'.join([year, month, day])
        data = 'searchCond={"tripType":"RT","adtCount":1,"chdCount":0,"infCount":0,"currency":"CNY","sortType":"a","segmentList":[{"deptCd":"%s","arrCd":"%s","deptDt":"%s"},{"deptCd":"%s","arrCd":"%s","deptDt":"%s"}],"sortExec":"a","page":"0"}' %(dep, arr, dept_date, arr, dep, dept_date2)
        # data = 'searchCond={"tripType":"RT","adtCount":1,"chdCount":0,"infCount":0,"currency":"CNY","sortType":"a","segmentList":[{"deptCd":"PVG","arrCd":"HND","deptDt":"2017-12-30","deptAirport":"","arrAirport":"","deptCdTxt":"上海","arrCdTxt":"东京","deptCityCode":"SHA","arrCityCode":"TYO"},{"deptCd":"HND","arrCd":"PVG","deptDt":"2018-01-01","deptAirport":"","arrAirport":"","deptCdTxt":"东京","arrCdTxt":"上海","deptCityCode":"TYO","arrCityCode":"SHA"}],"sortExec":"a","page":"0"}'
        rand = (str(random.random()) + str(random.random()).replace('.', ''))[:14]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cache-Control': 'max-age=0'
        }

        @request(retry_count=4, proxy_type=PROXY_REQ, binding=self.parse_Flight)
        def get_flight_data():
            return {
                'req': {
                    'method': 'post',
                    'url': 'http://www.ceair.com/otabooking/flight-search!doFlightSearch.shtml?' + rand,
                    'headers': headers,
                    'data': data,
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }

        yield get_flight_data
        import math
        page_num = int(math.ceil(int(self.flight_num) / 50.0))
        # 抓取第二页
        if page_num > 1:
            @request(retry_count=4, proxy_type=PROXY_REQ, binding=self.parse_Flight, async=True)
            def get_next_page():
                pages = []
                for i in range(1, page_num):
                    pages.append({
                        'req': {
                            'method': 'post',
                            'url': 'http://www.ceair.com/otabooking/flight-search!doFlightSearch.shtml?=' + rand,
                            'headers': headers,
                            'data': data % (dep, arr, dept_date, 'p' + str(i)),
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                    })
                return pages

            yield get_next_page

    def respon_callback(self, req, resp):
        print req, resp

    def parse_Flight(self, req, resp):
        resp = json.loads(resp.encode('latin-1'))
        if u'您选择的航线没有航班计划，请参考价格日历，重新选择出发日期' in resp.get('resultMsg', ''):
            raise parser_except.ParserException(29, '当日无票')

        if not hasattr(self, 'flight_num'):
            self.flight_num = resp['shopLandFlightResultNum']

        try:
            product = resp['airResultDto']['productUnits']
        except TypeError as e:
            logger.error(str(e), exc_info=True)
            return
        all_tickets, result = {}, []
        for i in product:
            r = all_tickets.setdefault(i['flightNoGroup'], [])
            i['fareInfoView'][0]['flights'] = [i['oriDestOption'][0]['flights']] + [i['oriDestOption'][1]['flights']]
            i['fareInfoView'][0]['cabinInfo'] = i['cabinInfo']
            r.append(i['fareInfoView'][0])
        for leg, tickets in all_tickets.items():
            for ticket in tickets:
                m_flight = MFlight(MFlight.OD_ROUND)
                m_flight.price = float_deal_none(ticket.get('fare', {}).get('salePrice', 0))
                m_flight.tax = float_deal_none((ticket.get('fare', {}).get('referenceTax', 0)))
                m_flight.currency = ticket[u'fare'].get(u'currencyCode', 'CNY')
                m_flight.source = 'ceair'
                m_flight.stopby = self.task.ticket_info.get('v_seat_type', 'E')
                # 改退签政策只抓取了原始数据，详细内容请基础数据去处理~么么哒
                for flights in ticket['flights']:
                    m_leg = MFlightLeg()
                    m_leg.return_rule = ticket['ruleInfo'].get('changeRuleJsonStr')
                    m_leg.change_rule = ticket['ruleInfo'].get('refundRuleJsonStr')
                    for flight in flights:
                        m_seg = MFlightSegment()
                        m_seg.flight_no = flight['flightNumber']
                        m_seg.dept_id = flight[u'departureAirport']['code']
                        m_seg.dest_id = flight[u'arrivalAirport']['code']
                        dept_date = flight[u'departureDateTime']
                        dest_date = flight[u'arrivalDateTime']
                        m_seg.set_dept_date(dept_date, '%Y-%m-%d %H:%M')
                        m_seg.set_dest_date(dest_date, '%Y-%m-%d %H:%M')
                        m_seg.seat_type = ticket['cabinInfo']['baseCabinCode']
                        if '/' in m_seg.seat_type or '%' in m_seg.seat_type or '-' in m_seg.seat_type:
                            m_seg.seat_type = get_flight_seat(m_seg.seat_type, flight, flights, ticket['flights'])
                        m_seg.plane_type = flight.get(u'equipment', {}).get(u'airEquipType', '')
                        m_seg.flight_corp = flight.get(u'marketingAirline', {}).get(u'code', '')
                        m_seg.real_class = flight[u'bookingClassAvail'].get(u'cabinCode', '')
                        if m_seg.seat_type == 'more' and m_seg.real_class == 'C':
                            m_seg.seat_type = 'economy'
                        m_seg.share_flight = flight.get(u'operatingAirline', {}).get(u'flightNumber', '')
                        m_leg.append_seg(m_seg)
                    m_flight.append_leg(m_leg)
                r_f = m_flight.convert_to_mioji_flight().to_tuple()
                if r_f in self.already:
                    continue
                result.append(r_f)
                self.already.add(r_f)
        # result = filter_result(self, result)
        return result


def float_deal_none(string):
    if not string:
        return .0
    return float(string)


def get_flight_seat(seat_type, flight, flights, all_flights):
    seat_type = seat_type.split('%')[0] if '%' in seat_type else seat_type
    seat_type = seat_type.split('/')[all_flights.index(flights)] if '/' in seat_type else seat_type
    seat_type = seat_type.split('-')[flights.index(flight)] if '-' in seat_type else seat_type
    return seat_type


def filter_result(self, result):
    flight_no = self.task.ticket_info.get('flight_no', '')
    if flight_no:
        new_result = [r for r in result if flight_no in r[23].split('_') + r[11].split('_') and check_seat(self, r)]
    else:
        new_result = [r for r in result if check_seat(self, r)]
    return new_result


def check_seat(self, r):
    seat = self.task.ticket_info.get('v_seat_type', 'E')
    map_seat = {
        'F': 'first',  # 头等舱
        'E': 'economy',  # 经济舱
        'B': 'business'  # 公务舱
    }
    seat = map_seat[seat]
    all_seats = r[17].split('_') + r[29].split('_')
    for s in all_seats:
        if s == seat:
            return True
    return False


if __name__ == '__main__':

    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy
    # mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()
    task.content = 'HKG&SIN&20180228&20180301'
    task.ticket_info = {'v_seat_type': 'F', 'flight_no': 'MU8729'}

    spider = CeairRoundFlightSpider()
    spider.task = task
    code = spider.crawl()
    print code
    print spider.result