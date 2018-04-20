# -*- coding: utf-8 -*-

import json
from mioji.common import parser_except
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
import re

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


class CsairMultiSpider(Spider):
    source_type = 'csairMultiFlight'
    targets = {'flight': {'version': 'InsertMultiFlight'}}
    old_spider_tag = {'csairMultiFlight': {'required': ['flight']}}

    def __init__(self, task=None):
        super(CsairMultiSpider, self).__init__(task=task)
        self.task = task
        self.task_info = {}
        self.id_list = []
        self.result_row = {}
        self.count = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/63.0.3239.132 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.id_url = re.compile("next/.*?/.*?/(.*?)/1?")

    def getdata(self):
        task1, task2 = self.task.content.split('|')
        dep1, arr1, date1 = task1.split("&")
        dep2, arr2, date2 = task2.split("&")
        data = "language=zh&country=cn&m=2&adt=1&cnn=0&inf=0&dep={}&depName={}&arr={}&arrName={}&date={}" \
               "&dep={}&depName={}&arr={}&arrName={}&date={}&flexible=1".format(dep1, dep1, arr1, arr1, date1,
                                                                                dep2, dep2, arr2, arr2, date2,
                                                                                )
        return data

    def targets_request(self):
        @request(retry_count=3, proxy_type=PROXY_REQ,new_session=True)
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

        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def get_cookie():
            return {
                'req': {
                    'method': 'get',
                    'url': 'http://b2c.csair.com/ita/intl/zh/shop/?execution={}'.format(self.md),
                    'headers': self.headers,
                },
                'user_handler': [self.parse_cookie]
            }

        yield get_cookie

        @request(retry_count=1, proxy_type=PROXY_FLLOW)
        def get_row():
            return {
                'req': {
                    'method': 'get',
                    'url': "http://b2c.csair.com/ita/rest/intl/shop/search?execution={}".format(self.md),
                    'headers': self.headers,
                },
                'user_handler': [self.parse_go]
            }

        yield get_row

        @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=self.parse_flight,async=True)
        def get_flight():
            multi_Fligh = []
            for id_ in self.id_list:
                req = {
                    'req': {
                        'method': 'get',
                        'url': "http://b2c.csair.com/ita/rest/intl/shop/next/{}/{}/{}/1?execution={}".format(self.session,
                                                                                                             self.solutionSet,
                                                                                                             id_,
                                                                                                             self.md),
                    }
                }
                if len(multi_Fligh) < 8:
                    self.count += 1
                    multi_Fligh.append(req)
                else:
                    break
            return multi_Fligh
        yield get_flight
        while True:
            if self.count < len(self.id_list):
                self.headers.pop("Cookie")
                yield get_md
                yield get_cookie
                yield get_row
                self.id_list = self.id_list[self.count:]
                yield get_flight
            else:
                break

    def parse_data(self,req, resp):
        import re
        md = re.findall("execution=(.*?)\"", resp)[0]
        if len(md) == 32:
            self.md = md

    def parse_cookie(self,req,resp):
        try:
            czbook = self.browser.br.cookies.items()[1]
            JSESSIONID = self.browser.br.cookies.items()[6]
        except:
            raise parser_except.ParserException(22, "代理失效")
        self.headers["Cookie"] = "JSESSIONID={}; cz-book={};".format(JSESSIONID[1], czbook[1])

    def parse_go(self,req,resp):
        body = json.loads(resp)
        try:
            self.row_one = body["ita"]["sliceOptionsGrid"]["row"]
        except:
            raise parser_except.ParserException(22, "代理失效")
        self.id_list = []
        for item in body["ita"]["sliceOptionsGrid"]["row"]:
            for i in item["cell"]:
                try:
                    self.id_list.append(i["solution"]["id"])
                    self.result_row[i["solution"]["id"]] = (i, item["slice"])
                except:
                    continue

        self.session = body["ita"]["session"]
        self.solutionSet = body["ita"]["solutionSet"]

    def parse_flight(self,req, resp):

        body = json.loads(resp)
        req_url = req["req"]["url"]
        res = []
        id_ = self.id_url.findall(req_url)[0]
        # Flight = []
        src_format = '%Y-%m-%dT%H:%M'
        result_row = self.result_row[id_]
        try:
            ita = body["ita"]["sliceOptionsGrid"]["row"]
        except:
            print body
            return
        for round_row in body["ita"]["sliceOptionsGrid"]["row"]:
            for round_cell in round_row["cell"]:
                m_flight = MFlight(MFlight.OD_MULTI)
                try:
                    m_flight.price = float(round_cell['solution']["saleFareTotal"]["amount"])
                except:
                    continue
                m_flight.tax = float(round_cell["solution"]["saleTaxTotal"]["amount"])
                m_flight.currency = round_cell["solution"]["saleTaxTotal"]["currency"]
                m_flight.stopby = self.task.ticket_info.get('v_seat_type', 'E')
                m_flight.source = 'csair'
                Flight = [result_row, [round_cell,round_row["slice"]]]
                for leg_item in Flight:
                    m_leg = MFlightLeg()
                    for seg_index, seg_item in enumerate(leg_item[1]["segment"]):
                        m_seg = MFlightSegment()
                        _seat_type = get_cabin(leg_item[0]["solution"]["slice"]["segment"][seg_index]["bookingInfo"][0]["cabin"])
                        m_seg.seat_type = CABIN_MAP.get(_seat_type, 'Economy')
                        m_seg.dept_id = seg_item["origin"]
                        m_seg.dest_id = seg_item["destination"]
                        dept_date = seg_item['leg'][0]["departure"].split("+")[0]
                        dest_date = seg_item["leg"][0]["arrival"].split("+")[0]
                        try:
                            m_seg.set_dept_date(dept_date, src_format)
                        except:
                            dept_date = seg_item['leg'][0]["departure"].split("-")[:-1]

                            m_seg.set_dept_date('-'.join(dept_date), src_format)
                        try:
                            m_seg.set_dest_date(dest_date, src_format)
                        except:
                            dest_date = seg_item["leg"][0]["arrival"].split("-")[:-1]
                            m_seg.set_dest_date('-'.join(dest_date), src_format)
                        m_seg.flight_no = seg_item["flight"]["carrier"] + str(seg_item["flight"]["number"])
                        m_seg.plane_type = seg_item["leg"][0]["aircraft"]["code"]
                        try:
                            m_seg.share_flight = seg_item["leg"][0]["operationalFlight"]["carrier"]+\
                                                 str(seg_item["leg"][0]["operationalFlight"]["number"])
                        except:
                            m_seg.share_flight = False
                        m_seg.real_class = m_seg.seat_type
                        m_leg.append_seg(m_seg)
                    m_flight.append_leg(m_leg)
                res.append(m_flight.convert_to_mioji_flight().to_tuple())
        return res


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new

    task = Task(source='csair', content='DLC&LAX&20180310|YVR&CAN&20180313')
    task.ticket_info = {'v_seat_type': 'E'}
    spider = CsairMultiSpider(task)
    print spider.crawl()
    print spider.result