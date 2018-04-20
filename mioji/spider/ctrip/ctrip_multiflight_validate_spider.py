#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年03月29日

@author: hourong
"""
from mioji.common import parser_except
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import json
import ctrip_multi_flight_lib
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW


class CtripMultiFlightValidateSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'ctripMultiFlightValidate'

    targets = {
        'Validate': {},
    }
    # 对应多个老原爬虫
    old_spider_tag = {}

    def targets_request(self):
        task = self.task
        data = {
            'IsDepart': 'F',
            'FlightWay': 'S',
            'remarkParameter': task.content
        }

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_Validate)
        def validate_request():
            return {'req':
                {
                    'url': 'http://flights.ctrip.com/international/AjaxRequest/SearchFlights/SearchRemarkHandler.ashx',
                    'data': data,
                    'method': 'POST',
                    'headers': {
                        "Content-Type": "application/x-www-form-urlencoded",
                        'Referer': 'http://www.ctrip.com/'
                    }
                },
                'data': {
                    'content_type': self.data_converter
                },
            }

        return [validate_request]

    def data_converter(self, req, data):
        try:
            return json.loads(data.decode("GBK", "ignore"))
        except:
            raise parser_except.ParserException(parser_except.PROXY_INVALID, "ctrip_multi::代理错误，未抓回数据")

    def parse_Validate(self, req, data):
        # 可以通过request binding=[]指定解析方法
        dfs = []
        for dom in data['RebookNew'][0]['Data'][0]['Data']:
            dfs.append(
                '_'.join(dom).replace('<BR>', '').replace('<strong>', '').replace('</strong>', '').replace('&yen;', ''))
        return '|'.join(dfs)


if __name__ == '__main__':
    from mioji.common.task_info import Task

    remark = '%5b%7b%22OrderID%22%3a0%2c%22IsHaveTrain%22%3afalse%2c%22DateRange%22%3a%222017-6-5%3e2017-6-19%22%2c%22IsImmediate%22%3a%22F%22%2c%22Channel%22%3a%22GDS-WS%22%2c%22Carrier%22%3a%22HU%22%2c%22AgencyId%22%3a1305%2c%22IsPrivateFare%22%3afalse%2c%22PassengerType%22%3a1%2c%22FlightSegmentList%22%3a%5b%7b%22FcGroupID%22%3a1%2c%22FcSegmentSeqID%22%3a1%2c%22FlightNo%22%3a%22HU491%22%2c%22SegmentNo%22%3a0%7d%2c%7b%22FcGroupID%22%3a1%2c%22FcSegmentSeqID%22%3a2%2c%22FlightNo%22%3a%22SN2283%22%2c%22SegmentNo%22%3a0%7d%2c%7b%22FcGroupID%22%3a2%2c%22FcSegmentSeqID%22%3a1%2c%22FlightNo%22%3a%22SN3816%22%2c%22SegmentNo%22%3a0%7d%2c%7b%22FcGroupID%22%3a2%2c%22FcSegmentSeqID%22%3a1%2c%22FlightNo%22%3a%22HU492%22%2c%22SegmentNo%22%3a0%7d%5d%2c%22PenaltyKey%22%3a%22%7b%5c%22FareIdPairs%5c%22%3a%5c%22572347304%7c570157876%5c%22%2c%5c%22RateParis%5c%22%3a%5c%220%7c0%5c%22%2c%5c%22SegmentPairs%5c%22%3a%5c%222%7c2%5c%22%2c%5c%22AgentId%5c%22%3a1305%2c%5c%22TicketingAirline%5c%22%3a%5c%22HU%5c%22%2c%5c%22BeforeDeparture%5c%22%3a%5c%227D%5c%22%2c%5c%22Routing%5c%22%3a%5c%22BJS-HU-BRU-SN-OSL%7cLIS-SN-BRU-HU-BJS%5c%22%2c%5c%22MinStay%5c%22%3a%5c%220%5c%22%2c%5c%22MaxStay%5c%22%3a%5c%22183%5c%22%2c%5c%22OutboundFirstAddonID%5c%22%3a0%2c%5c%22OutboundLastAddonID%5c%22%3a0%2c%5c%22InboundFirstAddonID%5c%22%3a0%2c%5c%22InboundLastAddonID%5c%22%3a0%2c%5c%22FareSouces%5c%22%3a%5c%223%7c3%5c%22%2c%5c%22AllowDateRange%5c%22%3a%5c%222017-04-01%3e2017-06-30%5c%22%2c%5c%22TokenNumber%5c%22%3anull%2c%5c%22FCFareRemarkRemarkRequests%5c%22%3a%5b%7b%5c%22DepartCity%5c%22%3a%5c%22BJS%5c%22%2c%5c%22ArriveCity%5c%22%3a%5c%22OSL%5c%22%2c%5c%22Carrier%5c%22%3a%5c%22HU%5c%22%2c%5c%22FareBasis%5c%22%3a%5c%22EK6M1CNT%5c%22%2c%5c%22Eligibility%5c%22%3a%5c%22NOR%5c%22%2c%5c%22TravelDate%5c%22%3a%5c%222017-06-12T00%3a00%3a00%5c%22%2c%5c%22TariffNo%5c%22%3a%5c%22IPREUAS%5c%22%2c%5c%22RuleNo%5c%22%3a%5c%22CY01%5c%22%2c%5c%22SegmentCount%5c%22%3a0%2c%5c%22SalePrice%5c%22%3a1580.000%2c%5c%22Ptcmd%5c%22%3a%5c%22%5c%22%2c%5c%22PolicyNo%5c%22%3a%5c%22%5c%22%2c%5c%22TourCode%5c%22%3a%5c%22%5c%22%2c%5c%22MinPax%5c%22%3a1%2c%5c%22SeatGrade%5c%22%3a%5c%22Y%5c%22%7d%2c%7b%5c%22DepartCity%5c%22%3a%5c%22LIS%5c%22%2c%5c%22ArriveCity%5c%22%3a%5c%22BJS%5c%22%2c%5c%22Carrier%5c%22%3a%5c%22HU%5c%22%2c%5c%22FareBasis%5c%22%3a%5c%22EK6M1CNT%5c%22%2c%5c%22Eligibility%5c%22%3a%5c%22NOR%5c%22%2c%5c%22TravelDate%5c%22%3a%5c%222017-06-12T00%3a00%3a00%5c%22%2c%5c%22TariffNo%5c%22%3a%5c%22IPREUAS%5c%22%2c%5c%22RuleNo%5c%22%3a%5c%22CY01%5c%22%2c%5c%22SegmentCount%5c%22%3a0%2c%5c%22SalePrice%5c%22%3a1580.000%2c%5c%22Ptcmd%5c%22%3a%5c%22%5c%22%2c%5c%22PolicyNo%5c%22%3a%5c%22%5c%22%2c%5c%22TourCode%5c%22%3a%5c%22%5c%22%2c%5c%22MinPax%5c%22%3a1%2c%5c%22SeatGrade%5c%22%3a%5c%22Y%5c%22%7d%5d%2c%5c%22TaxFeeDetails%5c%22%3a%5b%7b%5c%22PassengerType%5c%22%3a%5c%22ADT%5c%22%2c%5c%22TaxFeeDetailPerPtc%5c%22%3a%7b%5c%22SalesLocation%5c%22%3a%5c%22SHA%5c%22%2c%5c%22SalesCurrency%5c%22%3a%5c%22CNY%5c%22%2c%5c%22TaxFeeDetail%5c%22%3a%5b%7b%5c%22TaxFeeType%5c%22%3a%5c%22YQI%5c%22%2c%5c%22TaxFeeValue%5c%22%3a756.0%7d%2c%7b%5c%22TaxFeeType%5c%22%3a%5c%22YRF%5c%22%2c%5c%22TaxFeeValue%5c%22%3a2400.0%7d%2c%7b%5c%22TaxFeeType%5c%22%3a%5c%22001CN%5c%22%2c%5c%22TaxFeeValue%5c%22%3a90.0%7d%2c%7b%5c%22TaxFeeType%5c%22%3a%5c%22001BE%5c%22%2c%5c%22TaxFeeValue%5c%22%3a339.0%7d%2c%7b%5c%22TaxFeeType%5c%22%3a%5c%22003YP%5c%22%2c%5c%22TaxFeeValue%5c%22%3a78.0%7d%2c%7b%5c%22TaxFeeType%5c%22%3a%5c%22001PT%5c%22%2c%5c%22TaxFeeValue%5c%22%3a30.0%7d%5d%7d%7d%5d%7d%22%2c%22IsReplaceCtripRule%22%3afalse%2c%22IsDouble%22%3afalse%2c%22IsMultiPUSpecialPrice%22%3afalse%7d%5d'

    task = Task('ctripmultiFlightValidate', remark)

    spider = CtripMultiFlightValidateSpider()
    spider.task = task
    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
