# -*- coding: utf-8 -*-

from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.logger import logger
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight
import json


class CeairMultiFlightspider(Spider):

    source_type = 'ceairMultiFlight'

    targets = {
        # 例行需指定数据版本：InsertMultiFlight
        'MultiFlight': {'version': 'InsertMultiFlight'},
    }
    old_spider_tag = {
        'ceairMultiFlight': {'required': ['MultiFlight']}
    }

    def __init__(self, task=None):
        super(CeairMultiFlightspider, self).__init__(task=task)
        self.task = task
        self.task_info = {}
        self.tickets = []
        self.already = set()

    @staticmethod
    def float_deal_none(string):
        if not string:
            return .0
        return float(string)

    @staticmethod
    def get_flight_seat(type):
        seat_lists = []
        seat_type = type.split("%")[0]
        seat_list = seat_type.split("/")
        for seat in seat_list:
            seat_lists +=seat.split("-")
        return seat_lists

    def get_param(self,page):
        content = self.task.content
        one, two = content.split("|")
        one_deptCd, one_arrCd, one_deptDt = one.split("&")
        two_deptCd, two_arrCd, two_deptDt = two.split("&")
        search = json.dumps({
            "adtCount": 1, "chdCount": 0, "infCount": 0, "currency": "CNY", "tripType": "RT", "recommend": False,
            "page": str(page), "sortType": "a", "sortExec": "a",
            "segmentList": [
                {"deptCd": one_deptCd, "arrCd": one_arrCd, "deptDt": self.get_time(one_deptDt)},
                {"deptCd": two_deptCd, "arrCd": two_arrCd, "deptDt": self.get_time(two_deptDt)}
            ]
        })
        data = {
            "searchCond":search
        }
        return data

    def get_time(self,deotDt):
        year, month, day = deotDt[:4], deotDt[4:6], deotDt[6:]
        dept_date = '-'.join([year, month, day])
        return dept_date

    def targets_request(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:51.0) Gecko/20100101 Firefox/51.0',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cache-Control': 'max-age=0'
        }

        @request(retry_count=4, binding=self.parse_MultiFlight)
        def get_multiflight_data():
            return {
                'req': {
                    'method': 'post',
                    'url': 'http://www.ceair.com/otabooking/flight-search!doFlightSearch.shtml',
                    'headers': headers,
                    'data': self.get_param(0),
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }
        yield get_multiflight_data
        import math
        page_num = int(math.ceil(int(self.flight_num) / 50.0))
        if page_num > 1:
            @request(retry_count=4, proxy_type=PROXY_REQ, binding=self.parse_MultiFlight, async=True)
            def get_next_page():
                pages = []
                for i in range(1, page_num):
                    pages.append({
                                'req': {
                                        'method': 'post',
                                        'url': 'http://www.ceair.com/otabooking/flight-search!doFlightSearch.shtml',
                                        'headers': headers,
                                        'data': self.get_param(i),
                                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                                        'X-Requested-With': 'XMLHttpRequest'
                                        }
                                    })
                return pages
            yield get_next_page

    def parse_MultiFlight(self,req, resp):
        body = json.loads(resp.encode('latin-1'))
        if not hasattr(self, 'flight_num'):
            self.flight_num = body['shopLandFlightResultNum']
        try:
            productlist = body['airResultDto']['productUnits']
        except Exception as e:
            logger.error(str(e), exc_info=True)
            return
        result = []
        for product in productlist:
            m_flight = MFlight(MFlight.OD_ONE_WAY)
            m_flight.stopby = self.task.ticket_info.get('v_seat_type', 'E')
            m_flight.price = product["fareInfoView"][0].get("fare", {}).get('salePrice', 0)
            m_flight.tax = product["fareInfoView"][0].get("fare", {}).get('referenceTax', 0)
            m_flight.currency = product["fareInfoView"][0].get("fare", {}).get('currencyCode', "CNY")
            m_flight.source = 'ceair'
            for multi_index, oriDestOp in enumerate(product["oriDestOption"]):
                m_leg = MFlightLeg()
                m_leg.segments = []
                for flight_index,flight in enumerate(oriDestOp["flights"]):
                    m_seg = MFlightSegment()
                    m_seg.flight_no = flight["flightNumber"]
                    m_seg.dept_id = flight["departureAirport"]["code"]
                    m_seg.dest_id = flight["arrivalAirport"]["code"]
                    m_seg.set_dept_date(flight["departureDateTime"], '%Y-%m-%d %H:%M')
                    m_seg.set_dest_date(flight["arrivalDateTime"], '%Y-%m-%d %H:%M')
                    code = product["cabinInfo"]["baseCabinCode"]
                    try:
                        m_seg.seat_type = self.get_flight_seat(code)[multi_index+flight_index]
                    except:
                        m_seg.seat_type = self.get_flight_seat(code)[-1]
                    m_seg.real_class = flight[u'bookingClassAvail'].get(u'cabinCode', '')
                    if m_seg.seat_type == 'more' and m_seg.real_class == 'C':
                        m_seg.seat_type = 'economy'

                    m_seg.share_flight = flight.get(u'operatingAirline', {}).get(u'flightNumber', '')
                    m_seg.share_flight = flight.get(u'operatingAirline', {}).get(u'flightNumber', '')
                    m_leg.append_seg(m_seg)
                m_flight.append_leg(m_leg)
            r_f = m_flight.convert_to_mioji_flight().to_tuple()
            if r_f in self.already:
                continue
            result.append(r_f)
            self.already.add(r_f)
        return result


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug
    # mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
    # httpset_debug()

    content = 'HND&PEK&20180317|SHA&HND&20180325'
    task = Task('ceairmultiFlight', content)
    task.ticket_info = {'v_seat_type': 'F'}
    spider = CeairMultiFlightspider()
    spider.task = task
    code = spider.crawl()
    print spider.result


