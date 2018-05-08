# -*- coding: utf-8 -*-
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import json
import random
# from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_miojilight
from mioji.common import parser_except



class CeairFlightSpider(Spider):
    source_type = 'ceairFlight'
    targets = {'Flight': {'version': 'InsertNewFlight'}}
    old_spider_tag = {'ceairFlight': {'required': ['Flight']}}

    def __init__(self, task=None):
        super(CeairFlightSpider, self).__init__(task)
        self.already = set()

    def targets_request(self):
        dep, arr, dept_date = self.task.content.split('&')
        year, month, day = dept_date[:4], dept_date[4:6], dept_date[6:]
        dept_date = '-'.join([year, month, day])
        data = 'searchCond={"tripType":"OW","adtCount":1,"chdCount":0,"infCount":0,"currency":' \
                '"CNY","sortType":"a","segmentList":[' \
                '{"deptCd":"%s","arrCd":"%s","deptDt":"%s"}],' \
                '"sortExec":"a","page":"%s"}' \

        data2 = data % (dep, arr, dept_date, '0')


        rand = (str(random.random()) + str(random.random()).replace('.', ''))[:17]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'http://www.ceair.com/flight2014/nay-pvg-171227_CNY.html',
            'Cache-Control': 'max-age=0'
        }

        @request(retry_count=4, proxy_type=PROXY_REQ, binding=self.parse_Flight, async=True)
        def get_flight_data():
            return {'req': {
                    'method': 'post',
                    'url': 'http://www.ceair.com/otabooking/flight-search!doFlightSearch.shtml?=' + rand,
                    'headers': headers,
                    'data': data2,
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest'
                },
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
            i['fareInfoView'][0]['flights'] = i['oriDestOption'][0]['flights']
            i['fareInfoView'][0]['cabinInfo'] = i['cabinInfo']
            r.append(i['fareInfoView'][0])
        for leg, tickets in all_tickets.items():
            for ticket in tickets:
                m_flight = MFlight(MFlight.OD_ONE_WAY)
                m_flight.price = float_deal_none(ticket.get('fare', {}).get('salePrice', 0))
                m_flight.tax = float_deal_none((ticket.get('fare', {}).get('referenceTax', 0)))
                m_flight.currency = ticket[u'fare'].get(u'currencyCode', 'CNY')
                m_flight.source = 'ceair'
                m_flight.stopby = self.task.ticket_info.get('v_seat_type', 'E')
                m_leg = MFlightLeg()
                # 改退签政策只抓取了原始数据，详细内容请基础数据去处理~么么哒
                m_leg.return_rule = ticket['ruleInfo'].get('changeRuleJsonStr')
                m_leg.change_rule = ticket['ruleInfo'].get('refundRuleJsonStr')
                for flight in ticket['flights']:
                    m_seg = MFlightSegment()
                    m_seg.flight_no = flight['flightNumber']
                    m_seg.dept_id = flight[u'departureAirport']['code']
                    m_seg.dest_id = flight[u'arrivalAirport']['code']
                    dept_date = flight[u'departureDateTime']
                    dest_date = flight[u'arrivalDateTime']
                    m_seg.set_dept_date(dept_date, '%Y-%m-%d %H:%M')
                    m_seg.set_dest_date(dest_date, '%Y-%m-%d %H:%M')
                    m_seg.plane_type = flight.get(u'equipment', {}).get(u'airEquipType', '')
                    m_seg.flight_corp = flight.get(u'marketingAirline', {}).get(u'code', '')
                    m_seg.seat_type = get_flight_seat(ticket['cabinInfo']['baseCabinCode'], flight, ticket['flights'])
                    m_seg.real_class = flight[u'bookingClassAvail'].get(u'cabinCode', '')
                    m_seg.share_flight = flight.get(u'operatingAirline', {}).get(u'flightNumber', '')
                    m_leg.append_seg(m_seg)
                m_flight.append_leg(m_leg)
                flight_object = m_flight.convert_to_mioji_flight()
                if 'more' in flight_object.seat_type and 'C' in flight_object.real_class:
                    flight_object.seat_type.replace('more', 'business')
                print flight_object.seat_type, flight_object.real_class
                f_r = flight_object.to_tuple()
                if f_r in self.already:
                    continue
                self.already.add(f_r)
                result.append(f_r)
        # result = filter_result(self, result)
        return result


def float_deal_none(string):
    if not string:
        return .0
    return float(string)


def get_flight_seat(seat_type, flight, flights):
    seat_type = seat_type.split('%')[0] if '%' in seat_type else seat_type
    seat_type = seat_type.split('-')[flights.index(flight)] if '-' in seat_type else seat_type
    return seat_type


def filter_result(self, result):
    flight_no = self.task.ticket_info.get('flight_no', '')
    if flight_no:
        new_result = [r for r in result if flight_no in r[0].split('_') and check_seat(self, r)]
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
    all_seats = r[15].split('_')
    for s in all_seats:
        if s == seat:
            return True
    return False


if __name__ == "__main__":
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy
    # mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task()
    task.content = 'TSN&ICN&20180131'
    task.ticket_info = {'v_seat_type': 'E', 'flight_no': 'MU8729'}

    spider = CeairFlightSpider()
    spider.task = task
    code = spider.crawl()
    print code
    print spider.result