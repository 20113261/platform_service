#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
import re
import urllib
import json
from copy import deepcopy
from datetime import datetime
from mioji.common import parser_except
from mioji.common.logger import logger
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from ctrip_flight_lib import get_postdata, get_promotion, get_city_no
from common_lib import process_ages, seat_type_to_queryparam
from base_data import port_city
# # 关闭神烦的warning
# import requests
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# dicts
cabintask = {'E': 'Y', 'P': 'S', 'B': 'C', 'F': 'F'}

# url
search_url = 'http://flights.ctrip.com/international/AjaxRequest/SearchFlights/AsyncSearchHandlerSOAII.ashx'


class CtripFlightSpider(Spider):
    #注释，为国际版单程让路
    source_type = 'ctripFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
       'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
       'ctripFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

        # 任务信息
        self.adults = 1
        self.header = {
            # 'User-Agent': 不需要自己加，框架会帮你加一个随机生成的User-Agent并且会在本次任务过程中帮你传递
            # 'Host':'flights.ctrip.com',
            # 'Accept-Encoding': 'gzip, deflate',
        }
        self.task_info = {}
        self.postdata = ""
        self.tickets = []
        self.task_info = None
        self.start_get_url = 'http://flights.ctrip.com/international/'
        self.first_post_url = ''

        # url
        self.search_url = search_url

        if self.task is not None:
            self.process_task_info()

    def targets_request(self):
        # 处理这些信息
        if self.task_info is None:
            self.process_task_info()

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def first_page():
            '''
            data 如需要保存结果，指定data.key
            这个请求只需要访问主页
            '''
            self.first_post_url = 'http://flights.ctrip.com/international/{dept_city_en_name}-{dest_city_en_name}-{deptcity_code}-{destcity_code}?{dept_day}&{cabin}'.format(**self.task_info.__dict__)
            print self.first_post_url
            formdata = self.get_first_postdata()
            formdata_str = "FlightWay={FlightWay}&homecity_name={homecity_name}&HomeCityID={HomeCityID}&destcity1_name={destcity1_name}&destcityID={destcityID}&DDatePeriod1={DDatePeriod1}&Quantity={Quantity}&ChildQuantity={ChildQuantity}&InfantQuantity={InfantQuantity}&drpSubClass={drpSubClass}&IsFavFull=&mkt_header=".format(**formdata)
            self.header['Host'] = 'flights.ctrip.com'
            self.header['Content-Length'] = str(len(formdata_str))
            self.header['Origin'] = 'http://flights.ctrip.com'
            self.header['Referer'] = self.start_get_url
            self.header['Upgrade-Insecure-Requests'] = '1'
            self.header['Content-Type'] = 'application/x-www-form-urlencoded'
            self.header['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
            self.header['Accept-Encoding'] = 'gzip, deflate'
            self.header['Accept-Language'] = 'zh-CN,zh;q=0.9'

            return {
                'req': {'url': self.first_post_url, 'method': 'post', 'headers': self.header,'data':formdata_str},
                'user_handler': [self.process_post_data]
            }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_Flight, async=True)
        def get_flight_data():
            self.header = {}
            self.header['Accept-Encoding'] = 'gzip, deflate'
            self.header['Referer'] = self.first_post_url
            self.header['Origin'] = 'http://flights.ctrip.com'
            self.header['Cookie'] = self.cookie
            self.header['Content-Length'] = '0'
            header_1 = deepcopy(self.header)
            header_2 = deepcopy(self.header)
            header_3 = deepcopy(self.header)
            pages = []
            header_3['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            header_3['Content-Length'] = str(len(self.postdata))
            pages.append({
                'req': {'url': self.search_url, 'headers': header_3, 'method': 'post', 'data': self.postdata},
            })
            self.postdata = self.postdata.replace('SearchToken=1', 'SearchToken=2')
            self.postdata = self.postdata.replace('SearchMode=Search', 'SearchMode=TokenSearch')
            header_1['Content-Length'] = str(len(self.postdata))
            header_1['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            pages.append({
                'req': {'url': self.search_url, 'headers': header_1, 'method': 'post', 'data': self.postdata},
            })
            self.postdata = self.postdata.replace('SearchToken=2', 'SearchToken=3')
            header_2['Content-Length'] = str(len(self.postdata))
            header_2['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            pages.append({
                'req': {'url': self.search_url, 'headers': header_2, 'method': 'post', 'data': self.postdata},
            })

            return pages

        return [first_page, get_flight_data]

    def response_callback(self, req, resp):
        pass

    def check_list_result(self, list_result):
        result, all_except, all_ok, one_exception = list_result
        if result:
            return result, 0
        else:
            return result, 29

    def parse_Flight(self, req, payload):
        tickets = []
        try:
            data = json.loads(payload, encoding='gb2312')
        except Exception:
            raise parser_except.ParserException(parser_except.DATA_NONE,
                                                "ctrip::获得的爬虫数据不正确")
        if data['ReturnCode'] != 0:
            return tickets
        if 'FlightList' not in data:
            raise parser_except.ParserException(parser_except.EMPTY_TICKET,
                                                "ctrip::返回结构中无法获得机票信息")
        for flight in data['FlightList']:
            # print flight
            try:
                tickets += self.get_flight(flight)
            except Exception:
                raise parser_except.ParserException(parser_except.PARSE_ERROR,
                                                    "ctrip::解析错误")
        return tickets

    def get_flight(self, flight_info):
        tickets = []
        flight = Flight()
        flight.source = 'ctrip::ctrip'
        flight.currency = "CNY"
        flight.dur = int(flight_info["FlightTime"]) * 60
        flight.stop = len(flight_info['FlightDetail'])

        # 解出每个航班的信息
        flights_nos = []
        airlines = []
        plane_types = []
        dports = []
        aports = []
        dept_times = []
        arr_times = []
        day_diffs = []
        share_flight_no = []
        for detail in flight_info['FlightDetail']:
            flights_nos.append(detail['FlightNo'])
            share_flight_no.append(detail['FlightNo'])
            plane_types.append(detail['CraftType'])
            if 'AirlineName' in detail:
                airlines.append(detail['AirlineName'])
            else:
                airlines.append(detail['Carrier'])
            dports.append(detail['DPort'])
            aports.append(detail['APort'])
            time = datetime.strptime(detail['DepartTime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
            dept_times.append(time)
            time = datetime.strptime(detail['ArrivalTime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
            arr_times.append(time)
            day_diff = '1' if (detail['DepartTime'][0:10] != detail['ArrivalTime'][0:10]) else '0'
            day_diffs.append(day_diff)
            if 'CarrierFlightNo' in detail:
                share_flight_no.append(detail['CarrierFlightNo'])

        # 验证信息
        flight.flight_no = '_'.join(flights_nos)
        flight.plane_type = '_'.join(plane_types)
        flight.flight_corp = '_'.join(airlines)
        flight.dept_id, flight.dest_id, flight.stop_id = process_location(dports, aports)
        flight.daydiff = '_'.join(day_diffs)
        flight.dept_time, flight.dest_time, flight.dept_day, flight.stop_time = process_time(dept_times, arr_times)
        share_flight = '_'.join(share_flight_no)
        if share_flight != flight.flight_no:
            flight.share_flight = share_flight
        # 解出每张票的价格信息
        for fare in flight_info['FareList']:
            # total_price = fare['OverallPrice']
            surcharge = fare['OilFee']
            seat_types = []
            baggage_infos = []
            others_info = ''
            if 'ClassName' in fare:
                seat_types += [fare['ClassName']] * flight.stop  # 这里应该把 fare['ClassName'] 做成stop个数的
            elif 'ClassInfo' in fare:
                for segment in fare['ClassInfo']:
                    seat_types.append(segment['ClassName'])
            try:
                rest = re.compile(r'(\d+)', re.S).findall(fare['TicketLack'])[0]
            except:
                rest = -1
            if 'Declaration' in fare:
                for baggage_info in fare['Declaration']['Baggage']:
                    baggage_infos.append(baggage_info['Content'])

                if 'Note' in fare['Declaration']:
                    others_info = fare['Declaration']['Note'].replace('<br/>', '')
            flight.rest = rest
            try:
                flight.price = fare['AdultPrice']
                flight.tax = fare['AdultTax']
                if int(self.task_info.childs) or int(self.task_info.infants):
                    flight.others_info = self.generate_other_infos(fare)
            except:
                flight.price = fare['Price']
                flight.tax = fare['Tax']
            flight.surcharge = surcharge
            try:
                flight.promotion = get_promotion(fare['Tips'][0])
            except:
                flight.promotion = 'NULL'
            flight.seat_type = flight.real_class = '_'.join(seat_types)
            tickets.append(flight.to_tuple())
        self.tickets.extend(tickets)
        return tickets

    def generate_other_infos(self, fare):
        childs, infants = self.task_info.childs, self.task_info.infants
        results = 'Adult:(Price:%s, Tax:%s)' % (fare['AdultPrice'], fare['AdultTax'])
        if childs != '0':
            results += ', Child:(Price:%s, Tax:%s)' % (fare['ChildPrice'], fare['ChildTax'])
            if int(infants):
                results += ', Infant:(Price:%s, Tax:%s)' % (fare['InfPrice'], fare['InfTax'])
        else:
            results += ', Infant:(Price:%s, Tax:%s)' % (fare['ChildPrice'], fare['ChildTax'])
        return results

    def process_task_info(self):
        task = self.task

        ticket_info = task.ticket_info
        task_info = type('task_info', (), {})

        seat_type = ticket_info.get('v_seat_type', 'E')
        count = int(ticket_info.get('v_count', '1'))
        ages = ticket_info.get('v_age', '-1')
        try:
            dept_port, dest_port, dept_day = task.content.split('&')
            dept_id = port_city.get(dept_port, dept_port)
            dest_id = port_city.get(dest_port, dest_port)
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
            task_info.deptcity_no = str(val['city_id'])
            task_info.deptcity_code = str(val['code'])

            val = get_city_no(dest_id)
            task_info.destcity_name = urllib.quote(val['city_name'].decode('utf8').encode('gbk'))
            task_info.dest_city_en_name = val['city_en_name'].lower().replace('.', '').replace(' ', '')
            task_info.destcity_no = str(val['city_id'])
            task_info.destcity_code = str(val['code'])
        except:
            raise parser_except.ParserException(51,
                                                'ctripFlight::无法找到suggestion')
        self.task_info = task_info

    def get_first_postdata(self):
        task_info = self.task_info
        postdata = {}
        postdata['FlightWay'] = 'S'
        postdata['homecity_name'] = task_info.__dict__.get('deptcity_name')
        postdata['HomeCityID'] = task_info.__dict__.get('deptcity_no')
        postdata['destcity1_name'] = task_info.__dict__.get('destcity_name')
        postdata['destcityID'] = task_info.__dict__.get('destcity_no')
        postdata['DDatePeriod1'] = task_info.__dict__.get('dept_day')
        #postdata['ADatePeriod1'] = ''
        postdata['Quantity'] = '1'
        postdata['ChildQuantity'] = '0'
        postdata['InfantQuantity'] = '0'
        # postdata['Quantity'] = self.task_info.adults
        # postdata['ChildQuantity'] = self.task_info.childs
        # postdata['InfantQuantity'] = self.task_info.infants
        postdata['drpSubClass'] = task_info.cabin.upper()
        postdata['IsFavFull'] = ''
        postdata['mkt_header'] = ''
        return postdata

    def process_post_data(self, req, content):
        self.cookie = self.browser.br.cookies.items()[0][1]
        # self.cookie = self.browser.br.cookies.items()
        if '对不起，您访问的太快了，休息一下吧。或者登录您的携程帐号继续访问' in content:
            raise parser_except.ParserException(parser_except.PROXY_FORBIDDEN,
                                                'ctripFlight::代理被封')
        try:
            # self.postdata = get_postdata(content)
            condition = get_postdata(content)
            condition = json.loads(condition)
            # condition['Quantity'] = self.task_info.adults
            condition['Quantity'] = '1'
            # condition['ChildQuantity'] = self.task_info.childs
            # condition['InfantQuantity'] = self.task_info.infants
            condition['EngineFlightSwitch'] = '1'
            # condition['EngineScoreABTest'] = 'B'
            # condition['MaxSearchCount'] = '4'
            condition = json.dumps(condition)
            condition = condition.encode('utf-8')
            self.postdata = 'SearchMode=Search&condition={0}&SearchToken=1'.format(urllib.quote(condition, safe='()'))
        except:
            logger.exception('解析post_data出现问题')
            raise parser_except.ParserException(parser_except.PROXY_INVALID,
                                                'ctripFlight::无法获取postdata')


def inspect_task(adult, child, infant):
    if child and infant:
        return False
    if adult * 2 < child + infant:
        return False
    return True


def process_time(dept_times, arr_times):
    dept_time = dept_times[0]
    dept_day = dept_time.split('T')[0]
    arr_time = arr_times[-1]
    assert len(dept_times) == len(arr_times)
    stop_time = ''
    for i in range(len(dept_times)):
        stop_time += dept_times[i] + '_' + arr_times[i] + '|'

    return dept_time, arr_time, dept_day, stop_time[:-1]


def process_location(dports, aports):
    dept_id = dports[0]
    dest_id = aports[-1]
    assert len(dports) == len(aports)
    stop_id = ''
    for i in range(len(dports)):
        stop_id += dports[i] + '_' + aports[i] + '|'
    return dept_id, dest_id, stop_id[:-1]


def save_resp_file(content, called_count=[0], endwith='josn'):
    file_name = "tmp%s.%s" % (called_count[0], endwith)
    with open(file_name, 'w') as fd:
        fd.write(content)
    called_count[0] += 1


if __name__ == '__main__':
    from mioji.common.task_info import Task
    # import mioji.common.spider
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug, simple_get_socks_proxy_new

    # mioji.common.spider.get_proxy = simple_get_socks_proxy
    spider.slave_get_proxy = simple_get_socks_proxy_new
    # httpset_debug()

    # task_content_list = ['PVG&HKT&20180307','ZQN&PEK&20180306','HKT&PVG&20180312','SAN&LAX&20180429','CNS&MEL&20180803','BJS&BKK&20180803','INN&ZRH&20180420','VIE&SZG&20180418','HAJ&BJS&20180427','INN&ZRH&20180418','MIL&ZRH&20180418','MUC&FRA&20180421','FRA&LUX&20180422','NGO&OSA&20180212','TYO&NGO&20180209','LAS&SHA&20180217','VIE&LNZ&20180418','PRG&LEJ&20180421','TYO&BJS&20180609','GDL&MEX&20180225','PEK&CDG&20180206','PEK&MXP&20180304']
    # for content_temp in task_content_list:
    #     task = Task()
    #     task.content = content_temp
    #     task.ticket_info = {'v_seat_type': 'E'}
    #     spider = CtripFlightSpider()
    #     spider.task = task
    #     print spider.crawl()
    #     print spider.result
    task = Task()
    # task.content = 'CSX&JFK&20180520'
    # task.content = 'PRG&LEJ&20180421'
    task.content = 'BUD&BEG&20180309'
    # task.content = 'GDL&MEX&20180225'
    # task.content = 'PEK&CDG&20180206'
    # task.content = 'PEK&MXP&20180304'
    # task.content = 'LYS&DIJ&20180503'
    # task.content = 'DSM&SFO&20180218'
    # task.content = 'AKL&PEK&20180313'
    # task.content = 'PEK&ZQN&20180306'
    # task.content = 'PVG&HKT&20180307'
    # task.content = 'ZQN&PEK&20180306'
    # task.content = 'HKT&PVG&20180312'
    # task.content = 'CSX&JFK&20180520'
    # task.content = 'PAP&MBJ&20180402'
    # task.content = 'CKG&MIA&20180328'
    task.ticket_info = {'v_seat_type': 'E'}
    spider = CtripFlightSpider()
    spider.task = task
    print spider.crawl()
    print spider.result
    for i in spider.result:
        print len(spider.result[i])
        for temp in spider.result[i]:
            print temp
    # print len(spider.tickets)
    # for item in spider.tickets:
    #     print item
