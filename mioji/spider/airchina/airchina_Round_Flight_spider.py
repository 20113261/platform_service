#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import json
import time
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_REQ
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight
FOR_FLIGHT_DATE = '%Y-%m-%d' + 'T%H:%M:%S'
Ecabins = {'E': 'Economy', 'P': 'Economy', 'B': 'First', 'F': 'First'}
Ccabins = {'E': '经济舱', 'P': '经济舱', 'B': '头等舱/商务舱', 'F': '头等舱/商务舱'}


class AirchinaRoundFlightSpider(Spider):
    source_type = 'airchinaRoundFlight'
    targets = {
        'Flight': {'version': 'InsertRoundFlight2'}
    }
    old_spider_tag = {
        'airchinaRoundFlight': {'required': ['Flight']}
    }

    @property
    def content_parser(self):
        content = self.task.content.split('&')
        timestamp = str(int(time.time()))
        org = content[0]
        dst = content[1]
        go_date = content[2]
        back_date = content[3]
        dept_date = "{}-{}-{}".format(go_date[:4], go_date[4:6], go_date[6:8])
        dest_date = "{}-{}-{}".format(back_date[:4], back_date[4:6], back_date[6:8])
        cabin = self.task.ticket_info['v_seat_type']
        occ = str(self.task.ticket_info['v_count'])
        acabin = Ecabins[cabin]
        return dest_date, org, dst, timestamp, dept_date, occ, acabin

    def targets_request(self):
        dest_date, org, dst, timestamp, dept_date, occ, acabin = self.content_parser

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Flight)
        def get_flight_data():
            url = "https://m.airchina.com.cn/en/c/invoke"
            params = 'a=3&p=1&rw=1&m=' + urllib.quote(
                '{"req":"{\\"backDate\\":\\"%s\\",\\"version\\":\\"2\\",\\"org\\":\\"%s\\",'
                '\\"dst\\":\\"%s\\",\\"timestamp\\":\\"%s\\",\\"flag\\":\\"1\\",\\"inf\\":\\"0\\",'
                '\\"geeflag\\":\\"qryFlights\\",\\"date\\":\\"%s\\",\\"adt\\":\\"%s\\",\\"cnn\\":\\"0\\",'
                '\\"cabin\\":\\"%s\\",\\"lang\\":\\"en_US\\"}","token":"h5001","lang":"en_US",'
                '"geetest":"{\\"geetest_challenge\\":\\"52f39bb3faa7bbda6fc1f16424a1821b41\\",'
                '\\"geetest_validate\\":\\"43fa9d742fd49be44a1475b903378528\\",'
                '\\"geetest_seccode\\":\\"43fa9d742fd49be44a1475b903378528|jordan\\"}"}' % (dest_date, org, dst,
                                                                                            timestamp, dept_date,
                                                                                            occ, acabin)
            )
            return {
                'req': {
                    'url': url,
                    'method': 'post',
                    'params': params
                }
            }
        yield get_flight_data

    def parse_legs(self, resp, content):
        _single = []
        for con in content:
            mf = MFlight(MFlight.OD_ROUND)
            mf.price = float(con['lowPrice'])
            ml = MFlightLeg()
            ml.rest = con['ticketNum'] if con['ticketNum'] != '' else -1
            ml.rest = con['ticketNum'] if con['ticketNum'] != '' else -1
            for airline in con['flightSegmentList']:
                ms = MFlightSegment()
                ms.flight_no = airline['flightNo']
                ms.flight_corp = airline['flightCompany']
                ms.plane_type = airline['flightModel']
                ms.seat_type = Ccabins[self.task.ticket_info['v_seat_type']]
                ms.real_class = Ccabins[self.task.ticket_info['v_seat_type']]
                ms.dept_id = airline['flightDep']
                ms.dest_id = airline['flightArr']
                dept_date = airline['flightDepdatePlan'] + 'T' + airline['flightDeptimePlan'][:8]
                dest_date = airline['flightArrdatePlan'] + 'T' + airline['flightArrtimePlan'][:8]
                ms.set_dept_date(dept_date, FOR_FLIGHT_DATE)
                ms.set_dest_date(dest_date, FOR_FLIGHT_DATE)
                ml.append_seg(ms)
            _single.append([mf.price, ml])
        return _single

    def parse_Flight(self, req, resp):

        _b = []
        _c = []
        ticket = list()
        try:
            content_goto = json.loads(resp)['goto']['flightInfomationList']
            content_back = json.loads(resp)['back']['flightInfomationList']
            for g in content_goto:
                _b.append(g)
            for b in content_back:
                _c.append(b)
        except ValueError:
            raise parser_except.ParserException(22, '可能被封禁')
        tax_list = json.loads(resp)['goto']['taxesFeesList']
        taxs = []
        for tax in tax_list:
            taxs.append(int(tax['taxFeePrice']))
        tax_pay = int(sum(taxs))

        goto = self.parse_legs(resp, _b)
        back = self.parse_legs(resp, _c)
        for go in goto:
            for ba in back:
                mf = MFlight(MFlight.OD_ROUND)
                mf.price = go[0] + ba[0] + tax_pay
                mf.currency = 'CNY'
                mf.stopby = Ecabins[self.task.ticket_info['v_seat_type']]
                mf.source = 'airchina'
                mf.legs.extend([go[1], ba[1]])
                ticket.append(mf.convert_to_mioji_flight().to_tuple())
        return ticket


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    # mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = AirchinaRoundFlightSpider()
    task.content = "PEK&CDG&20180202&20180204"
    task.ticket_info = {'v_seat_type': 'E', "v_count": 1}
    spider.task = task
    result_code = spider.crawl()
    print(result_code, spider.result)
