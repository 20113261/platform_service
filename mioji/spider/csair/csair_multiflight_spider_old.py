# coding:utf-8

"""CSAIR-Multi-Flight-Spider

Brief-Intro：
    Step1:同步顺序获取每一程的信息，并按程stash->stations；
    Step2:根据stations中的每程信息进行笛卡尔乘组合整个Flight航班；
    Step3:异步请求每个组合的价格信息，并对每个组合的价格信息进行解析；
    Step4:只要有一个价格信息正常解析即表示验证可用，否则，无可用航班信息。
"""

import json
import re
import urllib
import copy
import itertools
from mioji.common import parser_except
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW

SEAT_MAP = {
    'E': ['Y', 'B', 'K', 'H', 'L', 'M', 'Q', 'X', 'E'],
    'B': ['J', 'C', 'Z', 'O', 'W'],
    'F': ['P', 'F'],
    'P': ['Y']
}

CABIN_MAP = {
    'E': 'Economy',
    'B': 'Business',
    'F': 'First',
    'P': 'PremiumEconomy'
}

class CsairMultiSpider(Spider):
    # source_type = 'csairMultiFlight'
    # targets = {'flight': {'version': 'InsertMultiFlight'}}
    # old_spider_tag = {'csairMultiFlight': {'required': ['flight']}}

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.price_task = []
        self.stations = []
        self.leg_group = []
        self.m_flighs = []
        self.is_first_leg = True
        self.parsed_task = []
        self.seat_type = 'Y'

    def targets_request(self):

        @request(retry_count=3, async=False, proxy_type=PROXY_REQ)
        def flight_page():
            """请求国际的航线"""
            data = {"depcity": "", "arrcity": "", "flightdate": "", "adultnum": "1",
                    "childnum": "0", "infantnum": "0", "cabinorder": "0", "airline": "1",
                    "flytype": "1", "international": "1", "action": "0", "segtype": "1",
                    "cache": "0", "preUrl": ""}

            parse_result = self.parse_task(self.task, data)
            pages = []
            for one_data in parse_result:
                pages.append({
                    'req': {
                        'url': 'https://b2c.csair.com/B2C40/query/jaxb/interMore/query.ao',
                        'method': 'post',
                        'params': one_data,

                    },
                    'data': {'content_type': 'json'},
                    'user_handler': [self.stash_leg]
                })
            return pages

        @request(retry_count=3, async=True, proxy_type=PROXY_FLLOW, binding=self.parse_flight)
        def price_page():
            """用取到的航线进行组合。构造一个请求，获取该组合的费用信息"""

            self.group_leg(self.stations)
            parse_result, plane_list = self.parse_price_task(self.leg_group)
            pages = []
            for index, one_data in enumerate(parse_result):
                pages.append({
                    'req': {
                        'url': 'https://b2c.csair.com/B2C40/query/jaxb/interPrice/query.ao',
                        'method': 'post',
                        'params': one_data,
                        # 异步并发会造成顺序错乱，
                        # 在这里向后续解析传递plane信息，
                        # 以便信息解析不依赖请求的顺序。
                        # 注意：此trick会造成warming
                        'plane_codes': plane_list[index]
                    },
                    'data': {'content_type': 'json'}
                })
            return pages

        yield flight_page
        yield price_page

    def parse_price_task(self, leg_group):
        """ 解析获取价格的任务"""
        post_data = {"isChangePassenger": "false", "adultnum": "1", "childnum": "0",
                     "infantnum": "0", "preUrl": "", "bestbuy": "true", "segments": []}
        segment = {"segtype": "M", "depcity": "", "arrcity": "", "depdateTime": "",
                   "arrdateTime": "", "flights": []}
        flight = {"isSliceBegin": 0, "carrier": "", "flightno": "", "depport": "", "arrport": "",
                  "deptime": "", "arrtime": "", "cabin": "Y", "bookingClassAvails": ""}
        parse_result = []
        plane_list = []
        for one_plan in leg_group:
            _post_data = copy.deepcopy(post_data)
            _segment = copy.deepcopy(segment)
            _segment['depdateTime'] = one_plan[0]['flights'][0]['deptime']
            _segment['arrdateTime'] = one_plan[-1]['flights'][-1]['arrtime']
            one_leg_plane = []
            for leg in one_plan:
                for seg_index, seg in enumerate(leg['flights']):
                    _flight = copy.deepcopy(flight)
                    _flight['carrier'], _flight['flightno'] = re.findall('(\w+?)(\d+)', seg['flightno'])[0]
                    _flight['depport'] = seg['depport']
                    _flight['arrport'] = seg['arrport']
                    _flight['deptime'] = seg['deptime']
                    _flight['arrtime'] = seg['arrtime']
                    if seg_index == 0:
                        _flight['isSliceBegin'] = 1
                    _flight['bookingClassAvails'] = ",".join([i['name'] + ':' + i['info'] for i in seg['cabins']])
                    _flight['cabin'] = self.seat_type[0]
                    one_leg_plane.append(seg['plane'])
                    _segment['flights'].append(_flight)
            _post_data['segments'].append(_segment)
            quote_text = 'json=' + urllib.quote(json.dumps(_post_data))
            parse_result.append(quote_text)
            plane_list.append(one_leg_plane)

        return parse_result, plane_list

    def parse_task(self, task, data):
        tasks = task.content.split('|')
        _seat_type = self.task.ticket_info.get('v_seat_type', 'E')
        self.seat_type = SEAT_MAP[_seat_type]
        parse_result = []
        for _task in tasks:
            try:
                dep, arr, date = _task.split('&')
                self.parsed_task.append({'dep': dep, 'arr': arr, 'date': date})
                item = copy.deepcopy(data)
                item['depcity'] = dep
                item['arrcity'] = arr
                item['flightdate'] = date
                quote_text = 'json=' + urllib.quote(json.dumps(item))
                parse_result.append(quote_text)
            except ValueError:
                raise parser_except.ParserException(12, 'check task')
        return parse_result

    def group_leg(self, stations):
        """接口信息没有明确的程间限制，多程进行笛卡尔乘组合航班，待后续请求验证"""
        d_p_result = reduce(lambda x, y: list(itertools.product(x, y)), stations)
        flat = lambda l: sum(map(flat, l), ()) if isinstance(l, tuple) else (l,)
        for item in d_p_result:
            self.leg_group.append(flat(item))

    def stash_leg(self, res, data):
        """ 暂存单程信息"""
        try:
            self.stations.append(data['segment']['dateFlight'])
        except Exception:
            raise parser_except.ParserException(29, "可用航线")

    def parse_flight(self, req, data):
        """ 解析组合航班总的费用信息，生成航班信息的最终结果"""
        if not data:
            return []
        src_format = '%Y-%m-%dT%H:%M'
        plane_codes = req['req']["plane_codes"]
        m_flight = MFlight(MFlight.OD_MULTI)
        m_flight.source = 'csair'
        leg_index = 0
        price_info = data['pricedItinerary'][0]['fareBreakDowns'][0]
        segments = data['pricedItinerary'][0]['flightSegments']
        for seg_index, _seg in enumerate(segments):
            m_seg = MFlightSegment()
            m_seg.dept_id = _seg['departureLocation']
            if len(self.parsed_task) > leg_index:
                if self.parsed_task[leg_index]['dep'] == m_seg.dept_id:
                    leg_index += 1
                    m_flight.append_leg(MFlightLeg())
            m_seg.dest_id = _seg['arrivalLocation']
            m_seg.set_dept_date(_seg['departureDateTime'], src_format)
            m_seg.set_dest_date(_seg['arrivalDateTime'], src_format)
            m_seg.flight_no = _seg['marketingCarrier'] + _seg['flightNumber']
            m_seg.plane_type = plane_codes[seg_index]
            _seat_type = self.task.ticket_info.get('v_seat_type', 'E')
            m_seg.seat_type = CABIN_MAP.get(_seat_type, 'Economy')
            print m_seg.seat_type
            m_seg.real_class = m_seg.seat_type
            m_flight.legs[-1].append_seg(m_seg)
        m_flight.price = float(price_info['totalFareCurrencyCode'])
        m_flight.currency = price_info['baseFareCurrencyCode']
        m_flight.tax = m_flight.price - float(price_info['baseFareAmount'])
        return [m_flight.convert_to_mioji_flight().to_tuple()]


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task(source='csair', content='PEK&TPE&20180321|TPE&SEL&20180328')
    task.ticket_info = {'v_seat_type': 'E'}
    spider = CsairMultiSpider(task)
    print spider.crawl()
    print spider.result
