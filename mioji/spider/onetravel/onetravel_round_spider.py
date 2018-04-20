# coding=UTF-8
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

import time
import datetime
import math
import re
import json
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from mioji.common.task_info import Task
from mioji.common.class_common import RoundFlight
from mioji.common.logger import logger
from mioji.common.template.GetAirline import GetAirline
from mioji.common.template.GetDayDiff import GetDaydiff
from lxml import html as HTML
# 关闭神烦的warning
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

M_dict = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
          'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
class_code_dict = {'E': '1', 'B': '2', 'F': '3', 'P': '5'}
seat_type_dict = {'1': '经济舱', '2': '商业舱', '3': '头等舱', '5': '超级经济舱'}



class OnetravelRoundFlightSpider(Spider):
    
    source_type = "ontravelRoundFlight"

    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }

    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'ontravelRoundFlight': {'required': ['Flight']}
    }

    def __init__(self, task=None):
        super(OnetravelRoundFlightSpider, self).__init__(task)

        # 初始化任务
        self.task = task

    def pare_para(self):
        taskcontent = self.task.content.encode('utf-8')
        try:
            task_list = taskcontent.split('&')
            self.task_list_len = len(task_list)
            self.dept_id, self.dest_id, dept_day, dest_day = task_list[0], task_list[1], task_list[2], task_list[3]
            self.dept_day = dept_day[0:4] + '-' + dept_day[4:6] + '-' + dept_day[6:8]
            self.dest_day = dest_day[0:4] + '-' + dest_day[4:6] + '-' + dest_day[6:8]

            if len(task_list) != 4:
                person_age_list = task_list[6].split('_')
                person_nu = int(task_list[4])
                adult_nu, senior_nu, child_nu, infant_lap, infant_seat, class_code, child_age_s \
                    = (0, 0, 0, 0, 0, '1', '')

                childAge_list = []
                try:
                    self.class_code = class_code_dict[task_list[5]]
                except:
                    pass
                try:
                    for i in range(person_nu):
                        if (float(person_age_list[i]) < 2) and (float(person_age_list[i]) > -1):
                            pass
                        elif (float(person_age_list[i]) < 12) and (float(person_age_list[i]) > -1):
                            child_nu += 1
                            childAge_list.append(person_age_list[i])
                        elif float(person_age_list[i]) < 65:
                            adult_nu += 1
                        else:
                            senior_nu += 1
                except Exception, e:
                    logger.error('adult_nu, child_nu  .etc获取have errors %s' % e)
                for i in range(int(child_nu)):
                    child_age_s += 'c' + str(i) + '-' + str(childAge_list[i])
            else:
                adult_nu, senior_nu, child_nu, infant_lap, infant_seat, class_code, child_age_s \
                    = (1, 0, 0, 0, 0, '1', '')
            self.adult_nu, self.senior_nu, self.child_nu, self.infant_lap, self.infant_seat, self.class_code, self.child_age_s = adult_nu, senior_nu, child_nu, infant_lap, infant_seat, class_code, child_age_s
        except Exception, e:
            import traceback
            raise parser_except.ParserException(parser_except.TASK_ERROR, msg=traceback.format_exc(e))

        # url

        if self.task_list_len == 4:
            self.url0 = 'http://www.onetravel.com/default.aspx?tabid=3582&from=' + self.dept_id + '&to=' + self.dest_id + '&dst=&rst=&daan=&raan=&fromDt=' + self.dept_day + '&fromTm=1100&toDt=' + self.dest_day + '&toTm=1100&rt=true&ad=1&se=0&ch=0&infl=0&infs=0&class=1&airpref=&preftyp=1&searchflxdt=false&IsNS=false&searchflxarpt=false&childAge='
        else:
            self.url0 = 'http://www.onetravel.com/default.aspx?tabid=3582&from=' + self.dept_id + '&to=' + self.dest_id + '&dst=&rst=&daan=&raan=&fromDt=' + self.dept_day + '&fromTm=1100&toDt=' + self.dest_day + '&toTm=1100&rt=true&ad=' + str(
                self.adult_nu) + '&se=' + str(self.senior_nu) + '&ch=' + str(child_nu) + '&infl=0&infs=0&class=' + str(
                self.class_code) + '&airpref=&preftyp=1&searchflxdt=false&IsNS=false&searchflxarpt=false&childAge=' + str(
                self.child_age_s) + ''

    def targets_request(self):
        self.pare_para()
        url0 = self.url0
        referer0 = 'http://www.onetravel.com/'

        url1 = 'http://www.onetravel.com/FPNext/Air/Listing/s/1'
        hd = {'Referer':url0}
        @request(retry_count = 3, proxy_type = PROXY_REQ)
        def first_url():
            return {
                'req':{
                    'url':url0,
                    'headers':hd
                }
            }
        @request(retry_count = 3, proxy_type = PROXY_REQ, binding=['Flight'])
        def Sec_url():
            return {
                'req':{
                    'url':url0,
                    'headers':hd
                },
                'user_handler':[self.has_next_page]
            }

        @request(retry_count = 3, proxy_type = PROXY_REQ, binding=['Flight'])
        def Third_url():
            
            pages = []
            page_num = self.user_datas.get('page_num', 1)
            for ind in xrange(page_num):
                url4 = url0.replace('Listing', 'NextPage') + '?ID=' + str(ind + 2) + '&_=' + str(
                    int(time.time() * 1000))
                pages.append(
                   {
                    'req':{
                        'url':url4,
                        'headers':hd
                    }
                 }
                )
                
            return pages

        
        yield first_url
        url0 = self.user_datas['response_url']
        url1 = url0.replace('Listing', 'LoadListingOnSearchCompleted') + '?_=' + str(int(time.time() * 1000))
        hd['Referer'] = url0

        yield Sec_url

        if self.user_datas['has_next_page']:
            yield Third_url

    def solve(self, year, from_time, from_mon):
        noon = from_time[-2:]
        hour = from_time[:-2].split(':')
        min = hour[1]
        hour = hour[0]
        mon = from_mon.split(',')[0].strip().split(' ')
        time_day = mon[1].strip()
        time_mon = M_dict[mon[0].strip()]
        t1 = year + '-' + time_mon + '-' + time_day + ' ' + hour + ':' + min + ':00' + ' ' + noon
        t1 = time.strptime(t1, '%Y-%m-%d %I:%M:%S %p')
        datetime = time.strftime('%Y-%m-%dT%H:%M:%S', t1)
        return datetime

    def has_next_page(self, req, data):
        if data.find('not find flights') !=  -1:
            self.user_datas['has_next_page'] = False
        else:
            try:
                dom = HTML.fromstring(data)
                tree = dom.find_class('pdbt10 hidden')
                len_page = tree[0].xpath('./b[2]/text()')[0]
                print len_page, '&'*100
                if int(len_page) > 1:
                    self.user_datas['page_num'] = int(len_page)
                    self.user_datas['has_next_page'] = True
                else:
                    #如果只需要翻一页就不用继续往下翻了
                    self.user_datas['has_next_page'] = False
            except Exception, e:
                self.user_datas['has_next_page'] = False

    def response_callback(self,req,resp):
        print req['req']['url'], '='*100
        if req['req']['url'] == self.url0:
            
            self.user_datas['response_url'] = resp.url 
    
    def parse_Flight(self, req, data):
        # print data
        tickets = []
        dom = HTML.fromstring(data)
        flight_info = dom.find_class('contract-block')
        print len(flight_info), '-'*100
        for each in flight_info:
            flight = RoundFlight()
            stop_id_A, stop_id_B, stop_time_A, stop_time_B = [], [], [], [],
            airline_A, airline_B, flight_no_A, flight_no_B, plane_no_A, plane_no_B = [], [], [], [], [], []
            seat_type_A, seat_type_B, real_class_A, real_class_B = [], [], [], []
            price_info = each.find_class('fare__amount is--total')[0]
            price = price_info.xpath('./span[1]/@title')[0]
            tax = 0
            child_info = each.find_class('fare__amount is--child')
            other_info_A = each.find_class('segment__single')[0]

            flight_num_pat = re.compile(r'\d+')
            flight_code_pat = re.compile(r"air/ai/(.*?).gif")

            for i in range(len(other_info_A.find_class("segment__itinerary col-xs-12"))):
                figure = \
                    other_info_A.find_class("segment__itinerary col-xs-12")[i].find_class(
                        'itinerary__airline col-xs-4')[
                        0].xpath('./figure/img/@src')[0]
                code = flight_code_pat.findall(figure)[0]
                f = \
                    other_info_A.find_class("segment__itinerary col-xs-12")[i].find_class(
                        'itinerary__airline col-xs-4')[
                        0].find_class('airline__info')[0].find_class('flight__num')[0].xpath('text()')[0]
                num = flight_num_pat.findall(f)[0]
                real_flight = code + str(num)
                flight_no_A.append(real_flight)

            # 获取航空公司和航班号
            for (aA, fA) in zip(other_info_A.find_class('airline__title'), other_info_A.find_class('flight__num')):
                airline_A += aA.xpath('./text()')
                real_class_A += ['NULL']
                seat_type_A.append(seat_type_dict[self.class_code])
            airline_A = '_'.join(airline_A)
            flight_no_A = '_'.join(flight_no_A)
            for A in other_info_A.find_class('flight__aircraft undertxt tooltip-link'):
                plane_no_A += A.xpath('./text()')
            plane_no_A = '_'.join(plane_no_A)
            time_id_info_A = other_info_A.find_class('segment__itinerary col-xs-12')
            stop_A = str(len(time_id_info_A) - 1)
            Year = self.dept_day.split('-')[0]
            for tii in time_id_info_A:
                from_time_mon_A = tii.find_class('airport__info is--from')[0]
                from_time_A = from_time_mon_A.find_class('airport__time')[0].xpath('./text()')[0].strip()
                from_mon_A = from_time_mon_A.xpath('./li[1]/span/text()')[0]
                from_time_A = self.solve(Year, from_time_A, from_mon_A)
                from_id_A = from_time_mon_A.xpath('./@title')[0].split(')')[0].split('(')[1]
                to_time_mon_A = tii.find_class('airport__info is--to')[0]
                to_time_A = to_time_mon_A.xpath('./li[1]/time/text()')[0].strip()
                to_mon_A = to_time_mon_A.xpath('./li[1]/span/text()')[0]
                to_time_A = self.solve(Year, to_time_A, to_mon_A)
                to_id_A = to_time_mon_A.xpath('./@title')[0].split(')')[0].split('(')[1]
                stop_time_A.append(from_time_A + '_' + to_time_A)
                stop_id_A.append(from_id_A + '_' + to_id_A)
            dur_A = '-1'
            if each.find_class('is--total-trip') != []:
                time_dur_A = each.find_class('is--total-trip')[0].xpath('./text()')[0].split(' ')
                dur_hour_A = time_dur_A[0][:-1]
                dur_min_A = time_dur_A[1][:-1]
                dur_A = str(int(dur_hour_A) * 3600 + int(dur_min_A) * 60)
            dept_id_A = stop_id_A[0].split('_')[0]
            dest_id_A = stop_id_A[-1].split('_')[1]
            dept_time_A = stop_time_A[0].split('_')[0]
            dest_time_A = stop_time_A[-1].split('_')[1]
            stop_time_A = '|'.join(stop_time_A)
            stop_time_A = stop_time_A.replace(' ', 'T')
            stop_id_A = '|'.join(stop_id_A)
            other_info_B = each.find_class('segment__single')[1]

            for i in range(len(other_info_B.find_class("segment__itinerary col-xs-12"))):
                figure = \
                    other_info_B.find_class("segment__itinerary col-xs-12")[i].find_class(
                        'itinerary__airline col-xs-4')[
                        0].xpath('./figure/img/@src')[0]
                code = flight_code_pat.findall(figure)[0]
                f = \
                    other_info_B.find_class("segment__itinerary col-xs-12")[i].find_class(
                        'itinerary__airline col-xs-4')[
                        0].find_class('airline__info')[0].find_class('flight__num')[0].xpath('text()')[0]
                num = flight_num_pat.findall(f)[0]
                real_flight = code + str(num)
                flight_no_B.append(real_flight)
            # 获取航空公司和航班号
            for (aB, fB) in zip(other_info_B.find_class('airline__title'), other_info_B.find_class('flight__num')):
                airline_B += aB.xpath('./text()')
                real_class_B += ['NULL']
                seat_type_B.append(seat_type_dict[self.class_code])
            airline_B = '_'.join(airline_B)
            flight_no_B = '_'.join(flight_no_B)

            for B in other_info_B.find_class('flight__aircraft undertxt tooltip-link'):
                plane_no_B += B.xpath('./text()')
            plane_no_B = '_'.join(plane_no_B)
            time_id_info_B = other_info_B.find_class('segment__itinerary col-xs-12')
            stop_B = str(len(time_id_info_B) - 1)
            Year = self.dept_day.split('-')[0]
            for tii in time_id_info_B:
                from_time_mon_B = tii.find_class('airport__info is--from')[0]
                from_time_B = from_time_mon_B.find_class('airport__time')[0].xpath('./text()')[0].strip()
                from_mon_B = from_time_mon_B.xpath('./li[1]/span/text()')[0]
                from_time_B = self.solve(Year, from_time_B, from_mon_B)
                from_id_B = from_time_mon_B.xpath('./@title')[0].split(')')[0].split('(')[1]
                to_time_mon_B = tii.find_class('airport__info is--to')[0]
                to_time_B = to_time_mon_B.xpath('./li[1]/time/text()')[0].strip()
                to_mon_B = to_time_mon_B.xpath('./li[1]/span/text()')[0]
                to_time_B = self.solve(Year, to_time_B, to_mon_B)
                to_id_B = to_time_mon_B.xpath('./@title')[0].split(')')[0].split('(')[1]

                stop_time_B.append(from_time_B + '_' + to_time_B)
                stop_id_B.append(from_id_B + '_' + to_id_B)
            dur_B = '-1'
            if each.find_class('is--total-trip') != []:
                time_dur_B = each.find_class('is--total-trip')[0].xpath('./text()')[0].split(' ')
                dur_hour_B = time_dur_B[0][:-1]
                dur_min_B = time_dur_B[1][:-1]
                dur_B = str(int(dur_hour_B) * 3600 + int(dur_min_B) * 60)

            dept_time_B = stop_time_B[0].split('_')[0]
            dest_time_B = stop_time_B[-1].split('_')[1]
            stop_time_B = '|'.join(stop_time_B)
            stop_time_B = stop_time_B.replace(' ', 'T')
            stop_id_B = '|'.join(stop_id_B)
            real_class_A = '_'.join(real_class_A)
            real_class_B = '_'.join(real_class_B)
            seat_type_A = '_'.join(seat_type_A)
            seat_type_B = '_'.join(seat_type_B)
            flight.source = 'onetravel::onetravel'
            flight.currency = 'USD'
            flight.seat_type_B = seat_type_B
            flight.real_class_B = real_class_B
            flight.dept_time_B = dept_time_B.replace(' ', 'T')
            flight.dest_time_B = dest_time_B.replace(' ', 'T')
            flight.plane_no_B = plane_no_B
            flight.flight_no_B = flight_no_B
            flight.airline_B = airline_B
            flight.stop_B = stop_B
            flight.dur_B = int(dur_B)
            flight.stop_id_B = stop_id_B
            flight.stop_time_B = stop_time_B

            flight.seat_type_A = seat_type_A
            flight.real_class_A = real_class_A
            flight.dept_id = dept_id_A
            flight.dest_id = dest_id_A
            flight.dept_time_A = dept_time_A.replace(' ', 'T')
            flight.dest_time_A = dest_time_A.replace(' ', 'T')
            flight.dept_day = dept_time_A[:10]
            flight.dest_day = dept_time_B[:10]
            flight.plane_no_A = plane_no_A
            flight.flight_no_A = flight_no_A
            flight.airline_A = airline_A
            flight.price = price
            flight.tax = tax
            flight.stop_A = stop_A
            flight.dur_A = int(dur_A)
            flight.stop_id_A = stop_id_A
            flight.stop_time_A = stop_time_A

            # 计算daydiff
            gdd = GetDaydiff()
            flight.daydiff_A = gdd.GetDaydiff(flight.stop_time_A)
            flight.daydiff_B = gdd.GetDaydiff(flight.stop_time_B)

            flight_tuple = flight.to_tuple()
            tickets.append(flight_tuple)
            if child_info != []:
                ticket_type = '儿童票'
                flight.price = child_info[0].xpath('./span[1]/@title')[0]
                tax = -1
                flight.tax = tax
                flight.ticket_type = ticket_type
                flight_tuple = flight.to_tuple()
                tickets.append(flight_tuple)
        return tickets

if __name__ == '__main__':
    task = Task()

    task.content = 'CAN&ADL&20170630&20170712'
    task.source = 'onetravelRoundFlight'
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    s = OnetravelRoundFlightSpider()
    s.task = task
    print s.crawl(cache_config={'lifetime_sec': 10 * 24 * 60 * 60, 'enable': True})