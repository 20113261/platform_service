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


class AirchinaFlightSpider(Spider):
    source_type = 'airchinaFlight'
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }
    old_spider_tag = {
        'airchinaFlight': {'required': ['Flight']}
    }

    @property
    def content_parser(self):
        content = self.task.content.split('&')
        timestamp = str(int(time.time()))
        org = content[0]
        dst = content[1]
        date = content[2]
        dept_date = "{}-{}-{}".format(date[:4], date[4:6], date[6:8])
        cabin = self.task.ticket_info['v_seat_type']
        occ = str(self.task.ticket_info['v_count'])
        acabin = Ecabins[cabin]
        return org, dst, timestamp, dept_date, occ, acabin

    def targets_request(self):
        org, dst, timestamp, dept_date, occ, acabin = self.content_parser

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Flight)
        def get_flight_data():
            url = "https://m.airchina.com.cn/en/c/invoke"
            params = 'a=3&p=1&rw=1&m=' + urllib.quote(
                '{"req":"{\\"backDate\\":\\"\\",\\"version\\":\\"2\\",\\"org\\":\\"%s\\",'
                '\\"dst\\":\\"%s\\",\\"timestamp\\":\\"%s\\",\\"flag\\":\\"1\\",'
                '\\"inf\\":\\"0\\",\\"geeflag\\":\\"qryFlights\\",\\"date\\":\\"%s\\",'
                '\\"adt\\":\\"%s\\",\\"cnn\\":\\"0\\",\\"cabin\\":\\"%s\\",\\"lang\\":\\"en_US\\"}",'
                '"token":"h5001","lang":"en_US",'
                '"geetest":"{\\"geetest_challenge\\":\\"c24ca4918df2e3a6566292dd2b8f105bbn\\",'
                '\\"geetest_validate\\":\\"086e8448d7298386c11cef5e6d08f18f\\",'
                '\\"geetest_seccode\\":\\"086e8448d7298386c11cef5e6d08f18f|jordan\\"}"}' % (org, dst, timestamp,
                                                                                            dept_date, occ, acabin)
            )
            return {
                'req': {
                    'url': url,
                    'method': 'post',
                    'params': params,
                }
            }
        yield get_flight_data

    def parse_Flight(self, req, resp):
        ticket = list()
        try:
            content = json.loads(resp)['goto']['flightInfomationList']
        except ValueError:
            raise parser_except.ParserException(22, '可能被封禁')

        for data in content:
            _tax = []
            mf = MFlight(MFlight.OD_ONE_WAY)
            for tax in json.loads(resp)['goto']['taxesFeesList']:
                _tax.append(int(tax['taxFeePrice']))
            mf.price = float(data['lowPrice']) + int(sum(_tax))
            mf.currency = 'CNY'
            mf.stopby = Ecabins[self.task.ticket_info['v_seat_type']]
            mf.source = 'airchina'
            ml = MFlightLeg()
            ml.rest = data['ticketNum'] if data['ticketNum'] != '' else -1
            for airline in data['flightSegmentList']:
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
            mf.append_leg(ml)
            ticket.append(mf.convert_to_mioji_flight().to_tuple())
        return ticket


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy_new

    # mioji.common.spider.slave_get_proxy = simple_get_socks_proxy_new
    task = Task()
    spider = AirchinaFlightSpider()
    task.content = "PEK&IAD&20180210"
    task.ticket_info = {'v_seat_type': 'E', "v_count": 1}
    spider.task = task
    result_code = spider.crawl()
    print(result_code, spider.result)
