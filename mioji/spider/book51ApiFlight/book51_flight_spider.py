#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
www.51book.com
Created on 2017年11月25日
author: lw
"""

import re
import json
import time
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ

from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'ECONOMY','B':'BUSINESS','F':'FIRST','P':'PREMIUM_ECONOMY'}
# url
search_url = "http://interws.51book.com/"

query_cabin_dict = {'E': 'y_s', 'B': 'c', 'F': 'f', 'P': 'y_s'}


def seat_type_to_queryparam(seat_type):
    return query_cabin_dict.get(seat_type, 'Y_S')


def process_ages(passenger_count, age_info=None):
    # 处理乘客信息
    # 返回 adult_count, child_count, infant
    if age_info is None:
        return passenger_count, 0, 0
    age_info_dict = {
        'adult': 0,
        'child_count': 0,
        'infant_count': 0,
    }
    ages = age_info.split('_')
    if len(ages) == 1 and ages[0] == '-1':
        return passenger_count, 0, 0
    for age in ages:
        judge_age(age, age_info_dict)

    test_count = age_info_dict['adult'] + age_info_dict['child_count'] + age_info_dict['infant_count']
    assert passenger_count == test_count
    return age_info_dict['adult'], age_info_dict['child_count'], age_info_dict['infant_count']


def judge_age(age, age_info_dict):
    # 成人  1人 儿童(2-12岁) 1人 婴儿(14天-2岁) 1人
    if age == '-1':
        age_info_dict['adult'] += 1
        return
    age_int = int(age)
    if age_int < 12:
        # 需要判定是否有婴儿
        if 0 < age_int <= 2:
            age_info_dict['infant_count'] += 1
        else:
            age_info_dict['child_count'] += 1
    elif 12 <= age_int:
        age_info_dict['adult'] += 1


def test_(age_info, count):
    result = {'Quantity': process_ages(count, age_info)[0], 'ChildQuantity': process_ages(count, age_info)[1],
              'InfantQuantity': process_ages(count, age_info)[2]}
    print result


class BookFlightSpider(Spider):
    source_type = "51bookApiFlight"

    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        '51bookFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.verify_ticket = False
        self.index = 0


    def set_value(self):
        auth = json.loads(self.task.ticket_info["auth"])
        # 任务信息
        self.header = {
            "USERNAME": auth['agencyCode']
        }
        self.header2 = {
            "USERNAME": auth['agencyCode']
        }
        self.task_info = {}
        self.postdata = ""
        self.postdata2 = ''
        self.tickets = []

        # 时间戳
        current_milli_time = lambda: int(round(time.time() * 1000))
        timeStamp = current_milli_time()

        # postdata passengerNumberVo、segmentList/ECONOMY 需要自己解析task
        # self.postdata["RQData"]["passengerNumberVo"].append()
        tmp_seat = self.task.ticket_info['v_seat_type']
        passengerNumber = self.task.ticket_info['v_count']
        tmp_flight_no = self.task.ticket_info.get('flight_no',"")
        self.user_datas['flight_no'] = tmp_flight_no
        lenFN = tmp_flight_no.split("_")
        if len(lenFN) == 1:
            TF = True
        else:
            TF = False
        departureAirport, arrivalAirport, departureTime = self.task.content.split("&")

        try:

            agencyCode = auth['agencyCode']

            if agencyCode and self.header['USERNAME']:
                self.postdata = {"agencyCode": agencyCode,
                                 "timeStamp": timeStamp,
                                 "RQData":
                                     {"cabinClass": cabin[tmp_seat],
                                      "directFlight": TF,
                                      "routeType": "OW",  # 单程
                                      "passengerNumberVo": [
                                          {"passengerType": "ADT", "passengerNumber": passengerNumber}],
                                      "segmentList": [
                                          {"departureAirport": departureAirport, "arrivalAirport": arrivalAirport,
                                           "departureTime": departureTime}]
                                      }
                                 }
                self.postdata2 = {"agencyCode": agencyCode,
                                 "timeStamp": timeStamp,
                                 "RQData":
                                     {
                                         "itineraryId" : self.user_datas['itineraryId'],
                                         'fareId' : self.user_datas['fare_id']
                                      }
                                 }
                self.search_url = auth['host'] + agencyCode + "/search/searchFlight"
                self.queryRule_url = auth['host']+agencyCode+"/query/queryRule"

        except:
            raise parser_except.ParserException(121, '认证信息有误')

        from hashlib import md5
        auth = json.loads(self.task.ticket_info['auth'])
        safe_code = auth['safe_code']
        str_data2 = json.dumps(self.postdata2)
        prior_param2 = str_data2 + safe_code
        sign2 = md5()
        sign2.update(prior_param2)
        # 加密之后的数据
        req_param2 = sign2.hexdigest()
        self.header2["SIGN"] = req_param2

        if self.task is not None:
            self.process_task_info()
    # 调用函数，对数据进行操作

    def targets_request(self):
        # 处理这些信息
        self.set_value()
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')

        if self.task_info is None:
            self.process_task_info()
        from hashlib import md5
        auth = json.loads(self.task.ticket_info['auth'])
        safe_code = auth['safe_code']
        str_data = json.dumps(self.postdata)
        prior_param = str_data + safe_code
        sign = md5()
        sign.update(prior_param)
        # 加密之后的数据
        req_param = sign.hexdigest()
        self.header["SIGN"] = req_param
        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_Flight)
        def first_page():
            return {
                # header 需要两个字段
                'req': {'url': self.search_url, 'method': 'post', 'headers': self.header,"json":self.postdata},
                'methods':'req'

            }
        # return [first_page]
        @request(retry_count=1,proxy_type=PROXY_REQ,binding=self.parse_Flight)
        def req_rule():
            self.set_value()
            return { 'req':{'url':self.queryRule_url,'method':'post','headers':self.header2,'json':self.postdata2},
                     'methods':'req_rule',
                    }

        yield first_page
        if self.verify_ticket:
             yield req_rule

    def response_error(self,req, resp, error):
        resp = json.loads(resp)
        if resp['rsCode'] == 990001:
            raise parser_except.ParserException(122, '认证信息错误')

    def process_task_info(self):
        task = self.task

        ticket_info = task.ticket_info
        task_info = type('task_info', (), {})
        self.task.ticket_info['v_seat_type'] = ticket_info.get('v_seat_type', 'E')
        seat_type = ticket_info.get('v_seat_type', 'E')
        try:
            dept_id, dest_id, dept_day = task.content.split('&')

        except:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'Content Error:{0}'.format(self.task.content))

        task_info.dept_id = dept_id.lower()
        task_info.dest_id = dest_id.lower()
        task_info.dept_day = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', dept_day)

        task_info.cabin = seat_type_to_queryparam(seat_type)

        self.task_info = task_info

    def parse_Flight(self, req, data):
        if req['methods']=='req_rule':
            response = json.loads(data)
            tickets = self.user_datas['tickets']
            temp_tickets = []
            for i in tickets:
                if i[0] == self.user_datas['flight_no']:
                    i = list(i)
                    import re
                    pepi = re.compile('\'text-indent: 2em\'>(.*)')
                    rule_string = "改签：" + pepi.findall(response['RSData']['adtRule'][0].split('</p>')[2])[0] + "退票:" + \
                                  pepi.findall(response['RSData']['adtRule'][0].split('</p>')[3])[0]  # 退票

                    # i[-10] = pepi.findall(response['RSData']['adtRule'][0].split('</p>')[2])[0] #改签
                    # i[-11] = pepi.findall(response['RSData']['adtRule'][0].split('</p>')[3])[0] #退票
                    i[-10] = i[-11] = rule_string
                    i = tuple(i)
                temp_tickets.append(i)
            return temp_tickets
        tickets = []
        if req['methods'] == 'req':
            try:
                response = json.loads(data)
                 #存票
                for flight in response["RSData"]["avFlightList"]:
                    mflight = MFlight(MFlight.OD_ONE_WAY) #单程
                    mflight.currency = "CNY"
                    # mflight.price = flight["fareList"][0]["adultPrice"]["ticketPrice"]  #票价
                    # mflight.tax = flight["fareList"][0]["adultPrice"]['tax']  #税
                    if len(flight["fareList"]) == 1 and  flight["fareList"][0]['productType'] == 2:
                        continue
                    for fare in flight["fareList"]:
                        if int(fare['productType']) == 1:
                            fare_id = fare['fareId']
                            mflight.price = fare["adultPrice"]["ticketPrice"]  # 票价
                            mflight.tax = fare["adultPrice"]['tax']

                    mflight.source = "51book"
                    mflight.surcharge = 0
                    mflightleg = MFlightLeg()
                    mflightleg.others_info = {}
                    mflightleg.others_info = json.dumps({"paykey":{"redis_key":self.task.redis_key,'id':self.index,'itineraryId':flight['itineraryID'],
                                                        "fareId":fare_id}}, ensure_ascii=False)
                    self.index += 1
                    for seg in flight['odlist'][0]["flightDetail"]: # list[]
                        mfseg = MFlightSegment()
                        mfseg.flight_no = seg["flightNo"]
                        mfseg.dept_id = seg["departureAirport"] # 出发
                        mfseg.dest_id = seg["arriveAirport"] # 到达
                        mfseg.flight_corp = seg["airCarrierAline"] #承运航司
                        dep_date = seg["departureTime"].replace(" ","T")
                        des_date = seg["arriveTime"].replace(" ","T")
                        mfseg.set_dept_date(dep_date, FOR_FLIGHT_DATE)
                        mfseg.set_dest_date(des_date, FOR_FLIGHT_DATE)
                        mfseg.seat_type = cabin[self.task.ticket_info['v_seat_type']]
                        mfseg.real_class = self.task.ticket_info['v_seat_type']

                        mflightleg.append_seg(mfseg)
                    mflight.append_leg(mflightleg)
                    tickets.append(mflight.convert_to_mioji_flight().to_tuple())


                    for ticket in tickets:
                        if self.user_datas['flight_no'] == ticket[0]:
                            self.user_datas["itineraryId"] = flight["itineraryID"]
                            self.verify_ticket = True
                            self.user_datas['fare_id'] = fare_id
                self.user_datas['tickets'] = tickets
                if self.verify_ticket == False:
                    return tickets
            except Exception as e:
                print e

if __name__=="__main__":
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy

    mioji.common.spider.get_proxy = simple_get_socks_proxy

    task = Task()
    task.content = "PEK&HKG&20180206"
    task.redis_key = "123"
    task.ticket_info = {"flight_no":"CA6533","v_count":2,"v_seat_type": "E","auth":'{"agencyCode":"MIAOJI","safe_code":"a3bQQ7s^","host":"http://interws.51book.com/"}'}
    spider = BookFlightSpider()
    spider.task = task
    print spider.crawl()
    print "-"*80
    print spider.result
