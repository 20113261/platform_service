#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
www.51book.com
Created on 2017年11月25日
author: lw
"""

import re
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ

from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'ECONOMY','B':'BUSINESS','F':'FIRST','P':'PREMIUM_ECONOMY'}
# url
search_url = "http://interws.51book.com/MIAOJI/search/searchFlight"

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


class BookMultiFlightSpider(Spider):
    source_type = "51bookFlight"

    targets = {
        'MultiFlight': {'version': 'InsertMultiFlight'}}

    old_spider_tag = {
        '51bookMultiFlight': {'required': ['MultiFlight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)
        self.verify_ticket = False
        self.index = 0

    def set_value(self):
        # 任务信息
        auth = json.loads(self.task.ticket_info["auth"])
        self.header = {
            "USERNAME": auth["agencyCode"]
        }
        self.header2 = {
            "USERNAME": auth["agencyCode"]
        }
        self.task_info = {}
        self.postdata = ""
        self.postdata2 = ""
        self.tickets = []
        self.task_info = None
        # 时间戳
        import time
        current_milli_time = lambda: int(round(time.time() * 1000))
        timeStamp = current_milli_time()
        auth = json.loads(self.task.ticket_info['auth'])
        agencyCode = auth['agencyCode']
        self.header["USERNAME"] = agencyCode
        tmp_cabin = self.task.ticket_info['v_seat_type']
        passengerNumber = self.task.ticket_info['v_count']
        content1, content2 = self.task.content.split("|")
        a = content1.split("&")  # [PAR,ROM,20180926]
        b = content2.split("&")  # [ROM,FLR,20180928]
        fli_no_1 = ((self.task.ticket_info['flight_no']).split("&"))[0]
        fli_no_2 = ((self.task.ticket_info['flight_no']).split("&"))[1]
        self.user_datas['flight_no'] = self.task.ticket_info['flight_no']
        f1 = fli_no_1.split("_")
        f2 = fli_no_2.split("_")
        if len(f1) == 1 and len(f2) == 1:
            TF = True
        else:
            TF = False

        try:
            if agencyCode and self.header['USERNAME']:
                self.postdata = {"agencyCode": agencyCode,
                                 "timeStamp": timeStamp,
                                 "RQData":
                                     {"cabinClass": cabin[tmp_cabin],
                                      "directFlight": TF,
                                      "routeType": "MS",
                                      "passengerNumberVo": [
                                          {"passengerType": "ADT", "passengerNumber": passengerNumber}],
                                      "segmentList": [
                                          {"departureAirport": a[0], "arrivalAirport": a[1], "departureTime": a[2]},
                                          {"departureAirport": b[0], "arrivalAirport": b[1], "departureTime": b[2]}
                                      ]
                                      }
                                 }
                self.postdata2 = {"agencyCode": agencyCode,
                                                   "timeStamp": timeStamp,
                                                   "RQData":
                                                       {
                                                           "itineraryId": self.user_datas['itineraryId'],
                                                           'fareId': self.user_datas['fare_id']
                                                       }
                                                   }

                # url
                self.search_url = str(auth['host']) + str(agencyCode) + "/search/searchFlight"
                self.queryRule_url = auth['host'] + agencyCode + "/query/queryRule"
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

    def targets_request(self):
        self.set_value()
        # 处理这些信息
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')

        if self.task_info is None:
            self.process_task_info()
        from hashlib import md5
        # safe_code = "a3bQQ7s^"
        auth = json.loads(self.task.ticket_info['auth'])
        safe_code = auth["safe_code"]
        str_data = json.dumps(self.postdata)
        prior_param = str_data + safe_code
        sign = md5()
        sign.update(prior_param)
        # 加密之后的数据
        req_param = sign.hexdigest()

        self.header["SIGN"] = req_param
        print "header:",self.header
        print "-"*80
        print "postdata",self.postdata
        self.header['USERNAME'] = auth["agencyCode"]

        @request(retry_count=3, proxy_type=PROXY_REQ,binding=self.parse_MultiFlight)
        def first_page():
            return {
                # header 需要两个字段
                'req': {'url': self.search_url, 'method': 'post', 'headers': self.header,"json":self.postdata},
                'methods': 'req',
            }
        # return [first_page]
        @request(retry_count=1, proxy_type=PROXY_REQ, binding=self.parse_MultiFlight)
        def req_rule():
            self.set_value()
            return {
                'req': {'url': self.queryRule_url, 'method': 'post', 'headers': self.header2, 'json': self.postdata2},
                'methods': 'req_rule',
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
        content_0 = (task.content.split('|'))[0]
        content_1 = (task.content.split('|'))[1]
        for i in (content_0,content_1):
            try:
                dept_id, dest_id, dept_day = i.split('&') #出发城市，到达城市，出发时间，返回时间
            except:
                raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                    'Content Error:{0}'.format(self.task.content))

        task_info.dept_id = dept_id.lower()
        task_info.dest_id = dest_id.lower()
        task_info.dept_day = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', dept_day)
        task_info.cabin = seat_type_to_queryparam(seat_type)
        self.task_info = task_info

    def parse_MultiFlight(self, req, data):
        if req['methods']=='req_rule':
            response = json.loads(data)
            tickets = self.user_datas['tickets']
            temp_tickets = []
            for i in tickets:
                if i[0] == self.user_datas['flight_no']:
                    i = list(i)
                    i[-1] = i[-1].split('&')[1]
                    pepi = re.compile('\'text-indent: 2em\'>(.*)')
                    rule_string ="改签："+ pepi.findall(response['RSData']['adtRule'][0].split('</p>')[2])[0]+"退票:"+pepi.findall(response['RSData']['adtRule'][0].split('</p>')[3])[0] #退票
                    # i[-10] = pepi.findall(response['RSData']['adtRule'][0].split('</p>')[2])[0] #改签
                    # i[-11] = pepi.findall(response['RSData']['adtRule'][0].split('</p>')[3])[0] #退票
                    i[22] = i[23] = rule_string
                    i = tuple(i)
                temp_tickets.append(i)
            return temp_tickets
        tickets = []
        if req['methods'] == 'req':
            try:
                response = json.loads(data)
                for flight in response["RSData"]["avFlightList"]:
                    mflight = MFlight(MFlight.OD_MULTI) # 往返
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
                    count = 0
                    self.index += 1
                    for leg in flight['odlist']:
                        mflightleg = MFlightLeg()
                        mflightleg.others_info = {}
                        if count == 0:
                            mflightleg.others_info["paykey"] = ""
                            count += 1
                        else:
                            mflightleg.others_info = json.dumps({"paykey":{"redis_key":self.task.redis_key,"id": self.index-1,"itineraryId": flight["itineraryID"],
                                                                "fareId":fare_id}}, ensure_ascii=False)
                        for seg in leg['flightDetail']:
                            mfseg = MFlightSegment()
                            mfseg.flight_no = seg["flightNo"].replace('/','_')
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
                        if ticket[0] == self.user_datas['flight_no']:
                            self.user_datas["itineraryId"] = flight["itineraryID"]
                            self.user_datas['fare_id'] = fare_id
                            self.verify_ticket = True

                self.user_datas["tickets"] = tickets
                if self.verify_ticket==False:
                    return tickets
            except Exception as e:
                print e



if __name__=="__main__":
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy

    mioji.common.spider.get_proxy = simple_get_socks_proxy

    task = Task()
    task.redis_key = "123"
    task.content = "HKG&ICN&20180217|ICN&SIN&20180221"
    task.ticket_info = {"flight_no":'OZ722&OZ751',"v_count":2,'v_seat_type': 'E',"auth":'{"agencyCode":"MIAOJI","safe_code":"a3bQQ7s^","host":"http://interws.51book.com/"}'}
    # task = {"task_data": "", "crawl_day": None, "master_info": {"spider_mq_port": "5672", "spider_mq_routerKey": "scv101", "spider_mq_exchangeType": "direct", "spider_mq_queue": "spider_callback_data", "spider_mq_user": "writer", "spider_mq_vhost": "test", "spider_mq_exchange": "spiderToVerify", "redis_db": 0, "spider_mq_passwd": "miaoji1109", "master_addr": "10.10.135.140:92", "spider_mq_host": "10.19.131.242", "redis_passwd": "MiojiRedisOrzSpiderVerify", "redis_addr": "10.10.55.126:6379"}, "create_time": 1512443927.881395, "id": 0, "other_info": {"request_begin_time": "1512443927771", "adults": 2, "qid": "1512443926438", "norm_flight_information": {"flight_type": "flightmulti", "appointed_source_list": "", "adults": 2, "section": [{"dest_iata_id": "SIN", "from_city_tri_code": "HKG", "flight_no": "CX739", "seat_type_id_str": "1", "to_cid": "20087", "stop_cid": "20043_20087", "router_src": "", "to_city_tri_code": "SIN", "dest_time": "20180209_15:30", "dept_iata_id": "HKG", "dept_day": "20180209", "stop_id": "HKG_SIN", "stop_time": "20180209_11:35#20180209_15:30", "dept_time": "20180209_11:35", "seat_type_str": "E", "from_cid": "20043"}, {"dest_iata_id": "SEA", "from_city_tri_code": "SIN", "flight_no": "DL166_DL166", "seat_type_id_str": "1_1", "to_cid": "50019", "stop_cid": "20087_20071|20071_50019", "router_src": "", "to_city_tri_code": "SEA", "dest_time": "20180212_09:55", "dept_iata_id": "SIN", "dept_day": "20180212", "stop_id": "SIN_NRT|NRT_SEA", "stop_time": "20180212_06:45#20180212_14:35|20180212_17:30#20180212_09:55", "dept_time": "20180212_06:45", "seat_type_str": "E_E", "from_cid": "20087"}]}, "journey_redis_key": "journey_1512443926438_664f065c76f08339e72ce281bc8734b6_1512443927771", "ticket_index": 0, "uid": "0c7y1bpt5a20b10506cb4wxlid19xg6i", "redis_key": "flightmulti|HKG_SIN_20180209|SIN_SEA_20180212|51book|E|10.10.95.29:8090|1512443926438|104f894a784c6f6cd3d2c326b4c2d63f|0", "all_cache_key": "all_flightmulti|20043|20087|20180209|20087|50019|20180212|E", "ticket_redis_key": "traffic_1512443926438_104f894a784c6f6cd3d2c326b4c2d63f", "journey_md5": "664f065c76f08339e72ce281bc8734b6", "source": "51bookMultiFlight", "ticket_info": {"uid": "0c7y1bpt5a20b10506cb4wxlid19xg6i", "flight_no": "CX739&DL166_DL166", "seat_type": "E", "v_count": 2, "auth": "{\"acc_mj_uid\":\"51book_001\",\"agencyCode\":\"MIAOJI\",\"host\":\"http://interws.51book.com/\",\"safe_code\":\"a3bQQ7s^\"}", "env_name": "test", "qid": "1512443926438", "dest_time": "20180209_11:35", "v_seat_type": "E", "verify_type": "verify", "csuid": "17ukjpya5a0da7d0bdbd2ttv6111c5x4", "tid": "lm73q1pt5a20eac69e652fpoid12bgqc", "dept_time": "20180209_11:35", "ptid": "ulwy", "md5": "104f894a784c6f6cd3d2c326b4c2d63f"}, "csuid": "17ukjpya5a0da7d0bdbd2ttv6111c5x4", "ptid": "ulwy", "content": "HKG&SIN&20180209|SIN&SEA&20180212", "callback_type": "scv101", "req_type": "b107", "tid": "lm73q1pt5a20eac69e652fpoid12bgqc", "ticket_redis_lock_key": "traffic_1512443926438_104f894a784c6f6cd3d2c326b4c2d63f_lock", "productId": "interline|20043|20087|20180209|20180209|CX739|20087|50019|20180212|20180212|DL166_DL166", "data_type": "flightmulti", "api_acc": 1, "spd_src": "51book_E", "src": "51book", "machine_ip": "10.10.95.29", "journey_redis_lock_key": "journey_1512443926438_664f065c76f08339e72ce281bc8734b6_1512443927771_lock", "cache_key": "flightmulti|HKG|SIN|20180209|SIN|SEA|20180212|CX739|DL166_DL166|51book|E", "ticket_md5": "104f894a784c6f6cd3d2c326b4c2d63f", "machine_port": 8090}, "proxy_info": {}, "redis_key": "flightmulti|HKG_SIN_20180209|SIN_SEA_20180212|51book|E|10.10.95.29:8090|1512443926438|104f894a784c6f6cd3d2c326b4c2d63f|0", "content": "HKG&SIN&20180209|SIN&SEA&20180212", "task_type": 3, "callback_type": "scv101", "ticket_info": {"uid": "0c7y1bpt5a20b10506cb4wxlid19xg6i", "flight_no": "CX739&DL166_DL166", "seat_type": "E", "v_count": 2, "auth": "{\"acc_mj_uid\":\"51book_001\",\"agencyCode\":\"MIAOJI\",\"host\":\"http://interws.51book.com/\",\"safe_code\":\"a3bQQ7s^\"}", "env_name": "test", "qid": "1512443926438", "dest_time": "20180209_11:35", "v_seat_type": "E", "verify_type": "verify", "csuid": "17ukjpya5a0da7d0bdbd2ttv6111c5x4", "tid": "lm73q1pt5a20eac69e652fpoid12bgqc", "dept_time": "20180209_11:35", "ptid": "ulwy", "md5": "104f894a784c6f6cd3d2c326b4c2d63f"}, "verify": {"type": "pre", "set_type": "E"}, "priority": 0, "source": "51bookMultiFlight", "redis_db": 0, "update_time": None, "success_times": 0, "new_task_id": "022543b2-d96b-11e7-83f1-5254000eda2c", "redis_port": "6379", "req_qid": "1512443926438", "host": "10.10.135.140:92", "req_uid": "0c7y1bpt5a20b10506cb4wxlid19xg6i", "crawl_hour": 0, "req_qid_md5": "1512443926438-104f894a784c6f6cd3d2c326b4c2d63f", "redis_passwd": "MiojiRedisOrzSpiderVerify", "update_times": 0, "redis_host": "10.10.55.126", "req_md5": "104f894a784c6f6cd3d2c326b4c2d63f", "timeslot": -1}
    spider = BookMultiFlightSpider()
    spider.task = task
    print spider.crawl()
    print "-"*80
    print spider.result
