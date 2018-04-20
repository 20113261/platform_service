# -*- coding: utf-8 -*-

from mioji.common.class_common import Flight
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import json


map_cabin = {
    'ECONOMY': 'E',
    'BUSINESS': 'B',
    'FIRST': 'F',
    'PREMIUM-COACH': 'P',
}

CABIN_MAP = {
    'E': 'Economy',
    'B': 'Business',
    'F': 'First',
    'P': 'PremiumEconomy'
}


def get_cabin(x):
    for i in map_cabin:
        if i in x:
            return map_cabin[i]
    return 'E'


class CsairSpider(Spider):

    source_type = 'csairFlight'
    targets = {
        'flight': {'version': 'InsertNewFlight'},
    }
    old_spider_tag = {
        'csairFlight': {'required': ['flight']}
    }

    def __init__(self, task=None):
        super(CsairSpider, self).__init__(task=task)
        self.task = task
        self.task_info = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/63.0.3239.132 Safari/537.36",
        }

    def getdata(self):
        dep, arr, date = self.task.content.split("&")
        # date = date[:4]+"-"+date[4:6]+"-"+date[6:]
        data = {
            "language": "zh",
            "country": "cn",
            "m": 0,
            "flexible": "1",
            "adt": 1,
            "cnn": 0,
            "inf": 0,
            "dep": dep,
            "arr": arr,
            "date": date,
        }
        return data

    def targets_request(self):

        @request(retry_count=3, proxy_type=PROXY_REQ,)
        def get_md():
            return {
                'req': {
                    'method': 'post',
                    'url': 'http://b2c.csair.com/ita/intl/app',
                    'data': self.getdata(),
                    'headers': self.headers,
                },
                'user_handler': [self.parse_data]
            }

        yield get_md

        @request(retry_count=3, proxy_type=PROXY_FLLOW,)
        def get_cookie():
            return {
                'req':{
                    'method': 'get',
                    'url': 'http://b2c.csair.com/ita/intl/zh/shop/?execution={}'.format(self.md),
                    'headers': self.headers,
                },
                'user_handler': [self.parse_cookie]
            }

        yield get_cookie

        @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_flight)
        def get_flight():
            return {
                'req': {
                    'method': 'get',
                    'url': "http://b2c.csair.com/ita/rest/intl/shop/search?execution={}".format(self.md),
                    'headers': self.headers,
                },

            }
        yield get_flight

    def parse_data(self, req,resp):
        import re
        md = re.findall("execution=(.*?)\"", resp)[0]
        if len(md) == 32:
            self.md = md

    def parse_cookie(self, req, resp):
        try:
            czbook = self.browser.br.cookies.items()[1]
            JSESSIONID = self.browser.br.cookies.items()[6]
        except:
            raise parser_except.ParserException(22, "代理失效")
        self.headers = {
            "Cookie":"JSESSIONID={}; cz-book={};".format(JSESSIONID[1], czbook[1])
        }

    def parse_flight(self,req, resp):
        res = []
        body = json.loads(resp)

        dateflights = body["ita"]["sliceOptionsGrid"]["row"]
        src_format = '%Y-%m-%dT%H:%M'
        for f in dateflights:
            for p_index, _price in enumerate(f['cell']):
                m_flight = MFlight(MFlight.OD_ONE_WAY)
                m_flight.source = 'csair'
                try:
                    m_flight.price = float(_price['solution']["saleFareTotal"]["amount"])
                except KeyError:
                    continue
                m_flight.tax = float(_price["solution"]["saleTaxTotal"]["amount"])
                m_flight.currency = _price["solution"]["saleTaxTotal"]["currency"]
                m_flight.stopby = self.task.ticket_info.get('v_seat_type', 'E')
                m_leg = MFlightLeg()
                for seg_index, seg in enumerate(f["slice"]["segment"]):
                    m_seg = MFlightSegment()
                    _seat_type = get_cabin(_price["solution"]["slice"]["segment"][seg_index]["bookingInfo"][0]["cabin"])
                    # print _seat_type,_price["solution"]["slice"]["segment"][seg_index]["bookingInfo"][0]["cabin"]
                    m_seg.seat_type = CABIN_MAP.get(_seat_type, 'Economy')
                    m_seg.dept_id = seg["origin"]
                    m_seg.dest_id = seg["destination"]
                    dept_date = seg['leg'][0]["departure"].split("+")[0]
                    dest_date = seg["leg"][0]["arrival"].split("+")[0]
                    try:
                        m_seg.set_dept_date(dept_date, src_format)
                    except:
                        dept_date = seg['leg'][0]["departure"].split("-")[:-1]

                        m_seg.set_dept_date('-'.join(dept_date), src_format)
                    try:
                        m_seg.set_dest_date(dest_date, src_format)
                    except:
                        dest_date = seg["leg"][0]["arrival"].split("-")[:-1]
                        m_seg.set_dest_date('-'.join(dest_date), src_format)
                    m_seg.flight_no = seg["flight"]["carrier"]+str(seg["flight"]["number"])
                    m_seg.plane_type = seg["leg"][0]["aircraft"]["code"]
                    m_seg.real_class = m_seg.seat_type
                    try:
                        m_seg.share_flight = seg["leg"][0]["operationalFlight"]["carrier"]+\
                                             str(seg["leg"][0]["operationalFlight"]["number"])
                    except:
                        m_seg.share_flight = False

                    m_leg.append_seg(m_seg)
                m_flight.append_leg(m_leg)
                res.append(m_flight.convert_to_mioji_flight().to_tuple())
        res = list(set(res))
        return res


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    spider = CsairSpider()
    task = Task(source='csairFlight', content='PEK&AMS&20180303')
    spider.task = task
    print spider.crawl()
    print spider.result