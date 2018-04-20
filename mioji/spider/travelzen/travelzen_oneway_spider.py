#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import json
from TravelzenFlightParser import Handler
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER
from mioji.common import parser_except
from mioji.common.check_book.check_book_ratio import use_record_qid
from mioji.common.mioji_struct import MFlight, MFlightLeg, MFlightSegment
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'


class TravelzenFlightSpider(Spider):
    source_type = 'travelzen'
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }
    old_spider_tag = {
        'travelzenFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        # 任务信息
        self.api = None
        self.mode = 'OW'
        self._itinerary_count = 0
        # 验证的票
        self.verify_ticket = None

    def format_data_str(self, date):
        return date[:4] + '-' + date[4:6] + '-' + date[6:]

    def check_auth(self, auth):
        """ 检查认证信息是否为空 """
        check_auth = ('api', 'account', 'passwd')
        for i in check_auth:
            if i not in auth or auth[i] == '':
                raise parser_except.ParserException(121, u"却少认证信息")

    def process_task(self):
        # Auth
        task = self.task
        auth = json.loads(self.task.ticket_info['auth'])
        self.check_auth(auth)
        self.api = Handler(task, **auth)
        dept_code, arr_code, date = task.content.split('&')
        section = [(dept_code, self.format_data_str(date), arr_code)]
        return section

    def targets_request(self):
        section = self.process_task()
        req = self.api.get_post_parameters(self.mode, section, self.task.ticket_info)

        @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['Flight'])
        def do_request():
            return {
                'req': req,
                'user_handler': [self.assert_resp],
                'data': {'content_type': 'json'},
                'extra': {
                    'method': 'search',
                    'section': section,
                    'ticket_info': self.task.ticket_info
                }
            }

        # @request(retry_count=1, proxy_type=PROXY_NEVER, binding=['Flight'])
        # def req_rule():
        #     for ticket in self.verify_ticket:
        #         ticket[-1] = json.loads(ticket[-1])
        #         freight_rule_query_id = ticket[-1]['payInfo']['LimitQueryID']
        #         yield {
        #             'req': api_handler.get_change_rule_params(freight_rule_query_id),
        #             'data': {'content_type': 'json'},
        #             'extra': {
        #                 'method': 'req_rule',
        #                 'ticket': ticket,
        #             }
        #         }

        use_record_qid(unionKey='travelzen', api_name="FlightSearchRequest", task=self.task, record_tuple=[1, 0, 0])
        return [do_request]
        # if self.verify_ticket:
        #     yield req_rule

    def assert_resp(self, req, resp):
        if 'responseMetaInfo' not in resp or 'resultCode' not in resp['responseMetaInfo']:
            raise parser_except.ParserException(parser_except.API_NOT_ALLOWED, '返回格式错误:responseMetaInfo')
        elif resp['responseMetaInfo']['resultCode'] == "9008": # 对方返回 9008 是认证错误，转为122
            raise parser_except.ParserException(122, resp['responseMetaInfo']['reason'])
        elif resp['responseMetaInfo']['resultCode'] != "0":
            if '查询结果为空' in resp['responseMetaInfo']['reason']:
                raise parser_except.ParserException(parser_except.EMPTY_TICKET, 'API 提示无票')
            raise parser_except.ParserException(parser_except.API_NOT_ALLOWED,
                                                '返回出错:%s' % resp['responseMetaInfo']['reason'])

    def parse_Flight(self, req, resp):
        # if req['extra']['method'] == 'req_rule':
        #     t = req['extra']['ticket']
        #     t[-10] += '<br/>' + resp['EndorsementQueryResponse']['freightRuleLimitInfo'][0]['ruleTitle'] +'<br/>' +
        # resp['EndorsementQueryResponse']['freightRuleLimitInfo'][0]['ruleLimitContent']
        #     t[-11] += '<br/>' + resp['EndorsementQueryResponse']['freightRuleLimitInfo'][0]['ruleTitle'] +'<br/>' +
        # resp['EndorsementQueryResponse']['freightRuleLimitInfo'][0]['ruleLimitContent']
        #     others_info = t[-1]
        #     others_info['dev_change_rule'] = resp
        #     t[-1] = json.dumps(others_info)
        #     return [t]
        ret_dict = resp
        all_ticket = []
        for i in ret_dict['FlightSearchResponse']['flightSegmentResult']:
            mflight = MFlight(MFlight.OD_ONE_WAY)
            mflight.currency = 'CNY'
            for pr in i['policyReturnPoint']:
                if pr.get('passengerType', None) == 'ADU':
                    mflight.price = pr['facePrice']
                    mflight.tax = pr['tax']
                    mflight.source = 'travelzen'
                    mflight.surcharge = 0
            mflightleg = MFlightLeg()
            mflightleg.rest = i['segmentList'][0]['flightScheduled'][0]['remainSeatCount']
            mflightleg.return_rule = mflightleg.change_rule = '重要提示：请线下咨询客服！实际退改费用请以线下沟通结果为准。'
            mflightleg.others_info = json.dumps({
                'paykey': {'redis_key': self.task.redis_key, 'id': self._itinerary_count},
                'payInfo': {'dept_city': [i['segmentList'][0]['fromCity']],
                            'dest_city': [i['segmentList'][-1]['toCity']],
                            'policyID': i['policyReturnPoint'][0]['policyId'],
                            'LimitQueryID': i['freightRuleQueryID'],
                            'is_special_price': i.get('specialPrice', False),
                            'is_taken_seat': i.get('takenSeat', False),
                            'child_face_price': i.get('childFacePrice', 0),
                            'airline_company': i['airlineCompany'],
                            'is_share_flight': [x['flightScheduled'][0]['shareFlightNo'] for x in i['segmentList']]},
                'type': 'flight_one_way'
            })
            for seg in i['segmentList']:
                mfseg = MFlightSegment()
                seg_info = seg['flightScheduled'][0]
                mfseg.flight_no = seg_info['flightNo']
                mfseg.dept_id = seg_info['fromAirport']
                mfseg.dest_id = seg_info['toAirport']
                mfseg.plane_type = seg_info['planeModel']
                mfseg.flight_corp = i['airlineCompany']
                ddate = seg_info['fromDate'].replace(' ', 'T') + ':00'
                adate = seg_info['toDate'].replace(' ', 'T') + ':00'
                mfseg.set_dept_date(ddate, FOR_FLIGHT_DATE)
                mfseg.set_dest_date(adate, FOR_FLIGHT_DATE)
                mfseg.seat_type = seg.get('cabinRank', '')
                mfseg.real_class = seg.get('cabinCode', '')
                mflightleg.append_seg(mfseg)
            mflight.append_leg(mflightleg)
            all_ticket.append(mflight.convert_to_mioji_flight().to_tuple())
            self._itinerary_count += 1
        res_all = []
        for i in all_ticket:
            i = list(i)
            i[25] = i[30] = 'NULL'
            i = tuple(i)
            res_all.append(i)
        return res_all


if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    # auth =  {
    #     'api': 'http://apis.travelzen.com/service/flight/international',
    #     'account': '594a45163db1ee2040b8b51e',
    #     'passwd': '0j9dfzt3'
    # }
    auth = {"api":"http://api.test.travelzen.com/tops-openapi-for-customers/service/flight/international","account":"5941e779f47ba45ac43f84a2","passwd":"g0e9ax1h"}
    task.ticket_info = {
        'v_seat_type': 'E',
        # 'flight_no': 'MU9158_MU595',
        'auth': json.dumps(auth)
    }
    task.other_info = {}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'BJS&MFM&20180427'
    task.redis_key = 'default_redis_key'
    spider = TravelzenFlightSpider()
    spider.task = task
    print spider.source_type
    print spider.crawl()
    import time
    time.sleep(2)
    print json.dumps(spider.result, ensure_ascii=False)
