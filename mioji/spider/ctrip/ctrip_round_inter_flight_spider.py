#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年10月16日
author fu
"""

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import json
import time
import re
import ctrip_round_flight_lib
from mioji.common import parser_except
from collections import OrderedDict
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight

# dicts
cabintask = {'E': 'Y', 'B': 'C', 'F': 'F', 'P': 'S',}
weekday = {'0': 'mon', '1': 'tue', '2': 'wed', '3': 'thur', '4': 'fri', '5': 'sat', '6': 'sun'}
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'经济舱','B':'商务舱','F':'头等舱','P':'超级经济舱'}
# url
search_url = 'https://english.ctrip.com/flights/Ajax/First'

class CtripRoundFlightSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    # source_type = 'ctripRoundFlight'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    # targets = {
        # 例行需指定数据版本：InsertMultiFlight
        # 'Flight': {'version': 'InsertRoundFlight2'},
    # }

    # 对应多个老原爬虫
    # old_spider_tag = {
    #     'ctripRoundFlight': {'required': ['Flight']}
    # }
    def __init__(self, task=None):
        Spider.__init__(self, task=task)

        self.tickets = []
        self.tmp_ticket_storage = []
        self.tmp_storage = {}
        self.ticket_dict = OrderedDict()
        self.flight_no_part1 = None
        self.flight_no_part2 = None
        self.verify_cabin = None
        self.filter_func = lambda x: True
        self.max_count = 3
        self.third_data = []

    def targets_request(self):
        if self.task.content:
            content = self.task.content.split('&')
            if content[0] == content[1]:
                raise parser_except.ParserException(12, '任务出错')
        if self.task.ticket_info.get('flight_no',None):
            self.flight_no_part1 = self.task.ticket_info['flight_no']
        dept_id, dest_id, dept_info, dest_info, dept_date, dest_date = ctrip_round_flight_lib.task_parser(
            self.task.content)
        self.seat_type = self.task.ticket_info.get('v_seat_type', 'E')
        dept_en_name = dept_info['city_en_name'].lower()
        dest_en_name = dest_info['city_en_name'].lower()
        dept_id = dept_id.lower()
        dest_id = dest_id.lower()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def search_page_0():
            # flighttype  s 单程  d 往返  m 联程
            import datetime
            b = datetime.datetime.now()
            c = str(b)
            a = 'https://english.ctrip.com/flights/{0}-to-{1}/tickets-{2}-{3}/?' \
                'flighttype=d&dcity={4}&acity={5}&' \
                'relddate=reld1&relrdate=relr1&startdate={6}&returndate={7}&startday=star1&returnday=retu1' \
                '&relweek=rel1&searchboxArg=t'.format(dept_en_name,dest_en_name,dept_id,dest_id,
                                                      dept_id,dest_id,dept_date,dest_date)

            dstart = datetime.datetime(int(self.task.content[8:12]), int(self.task.content[12:14]),
                                       int(self.task.content[14:16]))
            dreturn = datetime.datetime(int(self.task.content[17:21]), int(self.task.content[21:23]),
                                        int(self.task.content[23:]))
            relddate = (dstart - b).days + 1
            relrdate = (dreturn - b).days + 1
            relweek = relddate // 7
            startday = weekday[str(dstart.weekday())]
            returnday = weekday[str(dreturn.weekday())]
            a = a.replace('reld1', str(relddate))
            a = a.replace('relr1', str(relrdate))
            a = a.replace('star1', str(startday))
            a = a.replace('retu1', str(returnday))
            self.a = a.replace('rel1', str(relweek))
            self.header = {
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate, br',
                'Authority': 'english.ctrip.com'
            }
            return {
                'req': {'url': self.a, 'method': 'get', 'headers': self.header},
                'user_handler': [self.process_post_data]
            }

        @request(retry_count=1, proxy_type=PROXY_FLLOW, async=True)
        def search_page_1():
            self.header = {}
            self.header['Referer'] = self.a
            self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.header['Authority'] = 'english.ctrip.com'
            self.search_url = search_url
            pages = []
            pages.append({
                'req': {'url': self.search_url, 'headers': self.header, 'method': 'post', 'data': self.postdata},
                'user_handler': [self.parse_slices]
            })
            self.postdata = self.postdata.replace('PartitionSearchToken=0', 'PartitionSearchToken=1')

            pages.append({
                'req': {'url': self.search_url, 'headers': self.header, 'method': 'post', 'data': self.postdata},
                'user_handler': [self.parse_slices]
            })
            return pages

        @request(retry_count=2, proxy_type=PROXY_FLLOW, binding=self.parse_Flight, async=False)
        def search_page_2():
            self.header = {}
            self.header['Referer'] = 'https://english.ctrip.com/flights/ShowFareNext'
            self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            self.header['Authority'] = 'english.ctrip.com'
            self.search_url_0 = 'https://english.ctrip.com/flights/Ajax/Next'
            pages = []
            for i in self.third_data:
                count = self.third_data.index(i)
                pages.append({
                    'req': {'url': self.search_url_0,
                            'headers': self.header,
                            'method': 'post',
                            'data': self.process_post_data_t(i, self.flight_list[count])},
                })
            return pages
        yield search_page_0
        yield search_page_1
        if self.third_data != []:
            yield search_page_2

    def process_post_data(self, req, content):
        # self.time_no = self.browser._br.cookies.items()[1][1].split('=')[1]
        self.time_no = self.browser.br.cookies._cookies['.ctrip.com']['/']['_combined'].value.split('=')[1]
        seattype = cabintask[self.seat_type]
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
                       'FlightWay=RT&' \
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
                       'ADatePeriod1=adate&' \
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
        self.postdata = self.postdata.replace("dcity0", self.task.content[0:3])
        self.postdata = self.postdata.replace("acity0", self.task.content[4:7])
        self.postdata = self.postdata.replace("seatype", seattype)
        ddate = self.task.content[8:12]+'-'+self.task.content[12:14]+'-'+self.task.content[14:16]
        adate = self.task.content[17:21]+'-'+self.task.content[21:23]+'-'+self.task.content[23:]
        self.postdata = self.postdata.replace("ddate", ddate)
        self.postdata = self.postdata.replace("adate", adate)
        self.postdata = self.postdata.replace("time_no", self.time_no)

    def process_post_data_t(self, post_data, flight_n):
        self.postdata = self.postdata.replace('CurrentSeqNO=1','CurrentSeqNO=2')
        flight_n = flight_n.replace('_', '%7c')
        search_flight = 'Search_FlightKey=' + flight_n
        self.postdata = self.postdata.replace('Search_FlightKey=', search_flight)
        ab = 'ABTestingTracker=M:98,160325_enf_aruii:D;M:6,170106_kof_citys:B;'
        self.postdata = self.postdata.replace('ABTestingTracker=', ab)
        data = 'RouteToken=' + post_data
        self.postdata = self.postdata.replace('RouteToken=', data)

        return self.postdata

    def parse_slices(self, req, data):
        if self.flight_no_part1:
            self.parse_one_Flight(data, self.flight_no_part1)
        else:
            self.parse_one_Flight(data, None)

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

    def parse_one_Flight(self, data, flight_no):
        try:
            resp = json.loads(data)
        except Exception as e:
            raise e
        if resp['resultCount'] == 0:
            return []
        self.all_flights = []
        self.third_data = []
        self.flight_list = []
        if flight_no:
            for flights in resp['FlightIntlAjaxResults']:
                f_list =[]
                for legs in flights['flightIntlDetails']:
                    f_list.append(legs['flightNo'])
                v_no = '_'.join(f_list)
                res_flight = self.parse_flight_no(v_no)
                if res_flight == flight_no:
                    self.flight_list.append(v_no)
                    self.third_data.append(flights['flightIntlPolicys'][0]['shoppingInfoID'])
                    self.all_flights.append(flights)
            if self.all_flights == []:
                raise parser_except.ParserException(parser_except.EMPTY_TICKET, '无此航班')
        else:
            count = 0
            for flights in resp['FlightIntlAjaxResults']:
                count += 1
                if count in [3]:
                    f_list = []
                    for legs in flights['flightIntlDetails']:
                        f_list.append(legs['flightNo'])
                    v_no = '_'.join(f_list)
                    self.flight_list.append(v_no)
                    self.third_data.append(flights['flightIntlPolicys'][0]['shoppingInfoID'])
                    self.all_flights.append(flights)

    def parse_Flight(self, req, data):
        try:
            resp = json.loads(data)
        except Exception as e:
            raise e
        if resp['resultCount'] == 0:
            return []
        tickets = []
        for flight in resp['FlightIntlAjaxResults']:
            mflight = MFlight(MFlight.OD_ROUND)
            price_info = flight['flightIntlPolicys'][0]['PriceInfos'][0]
            mflight.currency = self.all_flights[0]['currency']
            mflight.price = price_info['Price']
            mflight.tax = price_info['Tax']
            mflight.source = 'ctrip'
            mflight.surcharge = 0
            for leg in range(2):
                if leg == 0:
                    mflightleg = MFlightLeg()
                    for seg in self.all_flights[0]['flightIntlDetails']:
                        mfseg = MFlightSegment()
                        mfseg.flight_no = self.parse_flight_no(seg['flightNo'])
                        mfseg.dept_id = seg['dPort']
                        mfseg.dest_id = seg['aPort']
                        mfseg.plane_type = seg['category']
                        mfseg.flight_corp = seg['airlineCode']
                        d = time.localtime(float(seg['departureTime'][6:16]))
                        ddate = str(d[0]) + '-' + str(d[1]) + '-' + str(d[2]) + 'T' + str(d[3]) + ':' + str(
                            d[4]) + ':' + '00'
                        a = time.localtime(float(seg['arrivalTime'][6:16]))
                        adate = str(a[0]) + '-' + str(a[1]) + '-' + str(a[2]) + 'T' + str(a[3]) + ':' + str(
                            a[4]) + ':' + '00'
                        mfseg.set_dept_date(ddate, FOR_FLIGHT_DATE)
                        mfseg.set_dest_date(adate, FOR_FLIGHT_DATE)
                        mfseg.seat_type = cabin[self.seat_type]
                        mfseg.real_class = cabin[self.seat_type]
                        mflightleg.append_seg(mfseg)
                    mflight.append_leg(mflightleg)
                else:
                    mflightleg = MFlightLeg()
                    for seg in flight['flightIntlDetails']:
                        mfseg = MFlightSegment()
                        mfseg.flight_no = self.parse_flight_no(seg['flightNo'])
                        mfseg.dept_id = seg['dPort']
                        mfseg.dest_id = seg['aPort']
                        mfseg.plane_type = seg['category']
                        mfseg.flight_corp = seg['airlineCode']
                        d = time.localtime(float(seg['departureTime'][6:16]))
                        ddate = str(d[0]) + '-' + str(d[1]) + '-' + str(d[2]) + 'T' + str(d[3]) + ':' + str(
                            d[4]) + ':' + '00'
                        a = time.localtime(float(seg['arrivalTime'][6:16]))
                        adate = str(a[0]) + '-' + str(a[1]) + '-' + str(a[2]) + 'T' + str(a[3]) + ':' + str(
                            a[4]) + ':' + '00'
                        mfseg.set_dept_date(ddate, FOR_FLIGHT_DATE)
                        mfseg.set_dest_date(adate, FOR_FLIGHT_DATE)
                        mfseg.seat_type = cabin[self.seat_type]
                        mfseg.real_class = cabin[self.seat_type]
                        mflightleg.append_seg(mfseg)
                    mflight.append_leg(mflightleg)
            tickets.append(mflight.convert_to_mioji_flight().to_tuple())
        return tickets


if __name__ == '__main__':
    import mioji
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_http_proxy

    # mioji.common.spider.get_proxy = simple_get_http_proxy
    # from mioji.common.utils import simple_get_http_proxy, httpset_debug

    # httpset_debug()

    task = Task()
    li = ['BJS&LON&20171117&20171121', 'CSX&PUS&20170502&20170512', 'KMG&BUD&20170502&20170512']
    # 城市三字码
    task.content = 'BJS&WLG&20180302&20180320'
    task.source = 'ctripRoundFlight'
    task.ticket_info = {'v_seat_type':"B"}
    spider = CtripRoundFlightSpider()
    spider.task = task

    print spider.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': False})
    print spider.result


