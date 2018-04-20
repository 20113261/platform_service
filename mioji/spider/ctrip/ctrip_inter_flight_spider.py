#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on 2017年10月17日
author: fu
"""

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import re
import time
import urllib
import json
from datetime import datetime
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from ctrip_flight_lib import get_postdata, get_promotion, get_city_no
from common_lib import process_ages, seat_type_to_queryparam

from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_miojilight
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'经济舱','B':'商务舱','F':'头等舱','P':'超级经济舱'}

# # 关闭神烦的warning
# import requests
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
#
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ?curr=USD&language=EN&  英语 ?curr=JPY&language=JP&  日语 ?curr=HKD&language=HK&  香港繁体 ?curr=HKD&language=EN&  香港英语
# ?curr=KRW&language=KR&  韩语 ?curr=SGD&language=EN&  新加坡 ?curr=EUR&language=DE&  德语 ?curr=EUR&language=FR&  法语
# ?curr=EUR&language=ES&  西班牙语 ?curr=RUB&language=RU&  俄语 ?curr=IDR&language=ID&  印度尼西亚 ?curr=THB&language=TH&  泰语 ?curr=MYR&language=MY&  马来西亚
# dicts
cabintask = {'E': 'Y', 'B': 'C', 'F': 'F'}
weekday = {'0': 'mon', '1': 'tue', '2': 'wed', '3': 'thur', '4': 'fri', '5': 'sat', '6': 'sun'}
# url
search_url = 'https://english.ctrip.com/flights/Ajax/First'


class CtripFlightSpider(Spider):

    source_type = 'ctripFlightRoutine'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ctripFlightRoutine': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

        # 任务信息
        self.adults = 1
        self.header = {
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authority': 'english.ctrip.com'
        }
        self.task_info = {}
        self.postdata = ""
        self.tickets = []
        self.task_info = None

        # url
        self.search_url = search_url

        if self.task is not None:
            self.process_task_info()

    def targets_request(self):
        # 处理这些信息
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')
        if self.task_info is None:
            self.process_task_info()
        import datetime
        b = datetime.datetime.now()
        c = str(b)
        a = 'https://english.ctrip.com/flights/{dept_city_en_name}-to-{dest_city_en_name}/tickets-{dept_id}-{dest_id}/?' \
            'flighttype=s&dcity={dept_id}&acity={dest_id}&' \
            'relddate=reld1&startdate={dept_day}&startday=star1&relweek=rel1&searchboxArg=t'.format(
            **self.task_info.__dict__)
        dt = datetime.datetime(int(self.task.content[8:12]), int(self.task.content[12:14]),
                               int(self.task.content[14:]))
        relddate = (dt - b).days
        relweek = relddate // 7
        startday = weekday[str(dt.weekday())]
        a = a.replace('reld1', str(relddate))
        a = a.replace('star1', str(startday))
        self.a = a.replace('rel1', str(relweek))

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            return {
                'req': {'url': self.a, 'method': 'get', 'headers': self.header},
                'user_handler': [self.process_post_data]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_Flight, async=True)
        def get_flight_data():
            self.header = {}
            self.header['Referer'] = self.a
            self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.header['Authority'] = 'english.ctrip.com'
            pages = []
            pages.append({
                'req': {'url': self.search_url, 'headers': self.header, 'method': 'post', 'data': self.postdata},
            })
            self.postdata = self.postdata.replace('PartitionSearchToken=0', 'PartitionSearchToken=1')

            pages.append({
                'req': {'url': self.search_url, 'headers': self.header, 'method': 'post', 'data': self.postdata},
            })
            return pages

        return [first_page, get_flight_data]

    def respon_callback(self, req, resp):
        print req, resp

    def parse_flight_no(self,flight):
        # 去0操作
        if '_' in flight:
            a = flight.split('_')[0]
            b = flight.split('_')[1]
            pipre = re.compile('[0]*')
            len1 = len(pipre.match(a[2:]).group())
            fl_fir = a[:2] + a[2+len1:]
            len2 = len(pipre.match(b[2:]).group())
            fl_end = b[:2] + b[2+len2:]
            return fl_fir + '_' + fl_end
        else:
            pipre = re.compile('[0]*')
            len3 = len(pipre.match(flight[2:]).group())
            return flight[:2] + flight[2+len3:]

    def parse_Flight(self, req, data):
        try:
            resp = json.loads(data)
            if resp['resultCount'] == 0:
                return []
            all_ticket = []
            for flight in resp['FlightIntlAjaxResults']:
                mflight = MFlight(MFlight.OD_ONE_WAY)
                mflight.currency = flight['currency']
                priceinfo = flight['flightIntlPolicys'][0]['PriceInfos'][0]
                mflight.price = priceinfo['TotalPrice']
                mflight.tax = priceinfo['Tax']
                mflight.source = 'ctrip::ctrip'
                mflight.surcharge = 0
                mflightleg = MFlightLeg()
                for seg in flight['flightIntlDetails']:
                    mfseg = MFlightSegment()
                    mfseg.flight_no = self.parse_flight_no(seg['flightNo'])
                    mfseg.dept_id = seg['dPort']
                    mfseg.dest_id = seg['aPort']
                    mfseg.plane_type = seg['category']
                    mfseg.flight_corp = seg['departureAirportName']
                    d = time.localtime(float(seg['departureTime'][6:16]))
                    ddate = str(d[0])+'-'+str(d[1])+'-'+str(d[2])+'T'+str(d[3])+':'+str(d[4])+':'+'00'
                    a = time.localtime(float(seg['arrivalTime'][6:16]))
                    adate = str(a[0])+'-'+str(a[1])+'-'+str(a[2])+'T'+str(a[3])+':'+str(a[4])+':'+'00'
                    mfseg.set_dept_date(ddate, FOR_FLIGHT_DATE)
                    mfseg.set_dest_date(adate, FOR_FLIGHT_DATE)
                    mfseg.seat_type = cabin[self.task.ticket_info['v_seat_type']]
                    mfseg.real_class = cabin[self.task.ticket_info['v_seat_type']]
                    mflightleg.append_seg(mfseg)
                mflight.append_leg(mflightleg)
                all_ticket.append(mflight.convert_to_mioji_flight().to_tuple())
            return all_ticket
        except Exception as e:
            print e

    def process_task_info(self):
        task = self.task

        ticket_info = task.ticket_info
        task_info = type('task_info', (), {})
        self.task.ticket_info['v_seat_type'] = ticket_info.get('v_seat_type', 'E')
        seat_type = ticket_info.get('v_seat_type', 'E')
        count = int(ticket_info.get('v_count', '1'))
        ages = ticket_info.get('v_age', '-1')
        try:
            dept_id, dest_id, dept_day = task.content.split('&')
            adults, childs, infants = process_ages(count, ages)
        except:
            raise parser_except.ParserException(parser_except.TASK_ERROR,
                                                'Content Error:{0}'.format(self.task.content))

        task_info.dept_id = dept_id.lower()
        task_info.dest_id = dest_id.lower()
        task_info.dept_day = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', dept_day)
        # infants = 0
        # childs = 0
        # adults = count

        task_info.infants, task_info.childs, task_info.adults = str(infants), str(childs), str(adults)
        task_info.cabin = seat_type_to_queryparam(seat_type)

        try:
            val = get_city_no(dept_id)
            task_info.deptcity_name = urllib.quote(val['city_name'].decode('utf8').encode('gbk'))
            task_info.dept_city_en_name = val['city_en_name'].lower().replace('.', '').replace(' ', '')
            task_info.deptcity_no = val['city_id']

            val = get_city_no(dest_id)
            task_info.destcity_name = urllib.quote(val['city_name'].decode('utf8').encode('gbk'))
            task_info.dest_city_en_name = val['city_en_name'].lower().replace('.', '').replace(' ', '')
            task_info.destcity_no = val['city_id']
        except:
            raise parser_except.ParserException(51,
                                                'ctripFlight::无法找到suggestion')
        self.task_info = task_info

    def process_post_data(self, req, content):
        # self.time_no = self.browser._br.cookies.items()[1][1].split('=')[1]
        self.time_no = self.browser.br.cookies._cookies['.ctrip.com']['/']['_combined'].value.split('=')[1]
        seattype = cabintask[self.task.ticket_info['v_seat_type']]
        self.postdata ='MultDcity0=dcity0&' \
                       'MultAcity0=acity0&' \
                       'MultDDate0=ddate&' \
                       'MultDcity1=&' \
                       'MultAcity1=&' \
                       'MultDDate1=&' \
                       'MultDcity2=&' \
                       'MultAcity2=&' \
                       'MultDDate2=&' \
                       'MultDcity3=&' \
                       'MultAcity3=&' \
                       'MultDDate3=&' \
                       'MultDcity4=&' \
                       'MultAcity4=&' \
                       'MultDDate4=&' \
                       'MultDcity5=&' \
                       'MultAcity5=&' \
                       'MultDDate5=&' \
                       'Search_FlightKey=&' \
                       'FlightWay=OW&' \
                       'DSeatClass=seatype&' \
                       'DSeatSelect=seatype&' \
                       'ChildType=ADT&' \
                       'Quantity=1&' \
                       'ChildQty=0&' \
                       'BabyQty=0&' \
                       'AirlineChoice=&' \
                       'HomePortCode=&' \
                       'Dest1PortCode=&' \
                       'CurrentSeqNO=1&' \
                       'DCity=dcity0&' \
                       'ACity=acity0&' \
                       'DDatePeriod1=ddate&' \
                       'ADatePeriod1=&' \
                       'filter_ddate=%40&' \
                       'filter_adate=%40&' \
                       'ptype=ADT&' \
                       'Transfer_Type=-1&' \
                       'PartitionSearchToken=0&' \
                       'NonstopOnly=&' \
                       'TransNo=time_no&' \
                       'RouteToken=&' \
                       'ABTesting=&' \
                       'SubChannel=0&' \
                       'ABTestingTracker=&' \
                       'channel_data_list=%7B%22' \
                       'TrackingID%22%3Anull%2C%22' \
                       'ShoppingId%22%3Anull%2C%22' \
                       'BatchID%22%3A0%2C%22' \
                       'AllianceID%22%3Anull%2C%22' \
                       'CampaignCode%22%3Anull%2C%22' \
                       'Currency%22%3Anull%2C%22' \
                       'Amount%22%3Anull%2C%22' \
                       'Language%22%3Anull%2C%22' \
                       'SID%22%3Anull%2C%22' \
                       'DepartureCity%22%3A%22dcity0%2C%22%2C%22' \
                       'ArrivalCity%22%3A%22acity0%2C%22%2C%22' \
                       'DepartureDate%22%3Anull%2C%22' \
                       'TurnaroundDate%22%3Anull%2C%22' \
                       'CabinCode%22%3Anull%2C%22' \
                       'TripType%22%3Anull%2C%22' \
                       'Channel%22%3Anull%2C%22' \
                       'OuID%22%3Anull%7D&' \
                       'SearchType=Sync'
        ddate = self.task.content[8:12] + '-' + self.task.content[12:14] + '-' + self.task.content[14:]
        self.postdata = self.postdata.replace("dcity0", self.task.content[0:3])
        self.postdata = self.postdata.replace("acity0", self.task.content[4:7])
        self.postdata = self.postdata.replace("seatype", seattype)
        self.postdata = self.postdata.replace("ddate", ddate)
        self.postdata = self.postdata.replace("time_no", self.time_no)


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    # mioji.common.spider.get_proxy = simple_get_socks_proxy
    # httpset_debug()


    list = ['PAR&BJS&20171013',
 'ZRH&PAR&20171209',
 'ZRH&BJS&20171114',
 'MRY&LAX&20171103',
 'LAX&SHA&20171107',
 'NCE&BJS&20171113',
 'ZRH&BJS&20171113',
 'BJS&PAR&20171230',
 'MRY&SFO&20171102',
 'ZRH&NCE&20171110',
 'PAR&NCE&20171203',
 'OSA&SHA&20171202',]
    for i in range(1):
        task = Task()
        task.content = 'PAR&BJS&20180305'
        task.ticket_info = {'v_seat_type': 'E'}
        spider = CtripFlightSpider()
        spider.task = task
        print spider.crawl()
        print spider.result

    # print len(spider.tickets)
    # for item in spider.tickets:
    #     print item
