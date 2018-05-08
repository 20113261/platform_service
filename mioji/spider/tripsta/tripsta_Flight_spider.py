#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年4月5日

@author: fanbowen
'''
import urllib
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Flight
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()
# 关闭神烦的warning
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import re
from lxml import html
import datetime
import time
from GetDaydiff import GetDaydiff, GetAirline

DATE_F = '%Y/%m/%d'
hd = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip,deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8,und;q=0.6',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'www.tripsta.cn',
    # 'Origin':'http://www.agoda.com',
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
}
class_code_dict = {'E': 'Y', 'B': 'C', 'F': 'F', 'P': 'W'}
seat_type_dict = {'1': 'ECO', '2': 'BUS', '3': 'FST', '5': 'PEC'}
seat_dict = {'Economy':'经济舱','Business':'商务舱','First':'头等舱','Economy Premium':'超级经济舱','Economy Standard':'标准经济舱'}
cabinzh={'Y':'经济舱','C':'商务舱'}
monda = {'一月':'01','二月':'02','三月':'03','四月':'04','五月':'05','六月':'06','七月':'07','八月':'08','九月':'09','十月':'10','十一月':'11','十二月':'12'}


class tripstaFlightSpider(Spider):
    source_type = 'tripstaFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'},
        'multi': {'bind': 'Flight'}
    }
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'tripstaFlight': {'required': ['Flight', 'multi']}
    }

    def targets_request(self):
        self.user_datas['tickets'] = []
        self.user_datas['ticket_info'] = self.task.ticket_info
        self.user_datas['taskcontent'] = self.task.content
        self.user_datas['ticket_no'] = self.task.ticket_info.get('flight_no', 'NULL')
        self.user_datas['seat_type'] = self.task.ticket_info.get('v_seat_type', 'E')
        self.user_datas['count'] = int(self.task.ticket_info.get('v_count', '2'))
        self.user_datas['age'] = self.task.ticket_info.get('v_age', '_'.join(['-1'] * self.user_datas['count']))
        self.user_datas['hold_seat'] = self.task.ticket_info.get('v_hold_seat', '_'.join(['1'] * self.user_datas['count']))
        self.user_datas['dept_id'], self.user_datas['dest_id'], self.user_datas['dept_day'] = self.task.content.split('&')
        self.user_datas['seat_num'] = int(self.user_datas['hold_seat'].count('1'))
        self.user_datas['dept_day'] = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', self.user_datas['dept_day'])
        self.user_datas['ages'] = [int(float(x)) for x in self.user_datas['age'].split('_')]
        self.user_datas['adult_nu'] = len([_ for _ in self.user_datas['ages'] if _ >= 12 or _ == -1])
        self.user_datas['child_nu'] = len([_ for _ in self.user_datas['ages'] if 2 < _ < 12])
        self.user_datas['infant_nu'] = len([_ for _ in self.user_datas['ages'] if 0 <= _ <= 2])
        self.user_datas['onlap'] = 'Y' if '0' in self.user_datas['hold_seat'] else 'N'
        self.user_datas['class_code'] = dict(E='Y', B='C', F='F', P='W')[self.user_datas['seat_type']]
        self.user_datas['old'] = '0'
        self.user_datas['tickets_list'] = []

        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_url_page():
            import datetime
            dp_day = datetime.datetime.strptime(self.user_datas['dept_day'], '%Y-%m-%d')
            ds_day = dp_day + datetime.timedelta(days=1)
            dp_day = str(dp_day.day)+'%2F'+str(dp_day.month)+'%2F'+str(dp_day.year)
            ds_day = str(ds_day.day)+'%2F'+str(ds_day.month)+'%2F'+str(ds_day.year)
            url = 'http://www.tripsta.cn/flights/results?dep=' + str(self.user_datas['dept_id']).lower() + '&arr=' + str(self.user_datas['dest_id']).lower() + '&isRoundtrip=0&obDate=' + dp_day + '&ibDate='+ ds_day +'&obTime=&ibTime=&extendedDates=0&resetStaticSearchResults=1&passengersAdult=' + str(self.user_datas['adult_nu']) + '&passengersChild=' + str(self.user_datas['child_nu']) + '&passengersInfant=' + str(self.user_datas['infant_nu']) + '&airlineCode=&class=' + str(self.user_datas['class_code']) + '&directFlightsOnly=0'
            url = urllib.unquote(url)
            self.user_datas['url'] = url
            return {
                'req': {'url': url, 'headers': hd},
                'user_handler': [self.get_page]
            }

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True, binding=[self.get_Flight])
        def get_all_page_first():
            return [{'req': {'url': flight, 'headers': hd}} for i, flight in enumerate(self.user_datas['get_url'])]
            #return [{'req': {'url': flight, 'headers': hd, 'page_number': i}} for i, flight in enumerate(self.user_datas['get_url'])]

        @request(retry_count=3, proxy_type=PROXY_REQ, binding=self.parse_multi, multi=True, async=True)
        def get_all_page_tic():
            temp = [{'req': {'url': flight, 'headers': hd},
                     # 'user_handler': [self.temp]
                  } for flight in self.user_datas['tickets_list'][0]['url']]
            return temp
            # return [{'req': {'url': flight, 'headers': hd, 'page_number': i},
            #          'user_handler': [self.temp]
            #          } for i, flight in enumerate(self.user_datas['tickets_list'][every]['url'])]


        yield get_url_page
        yield get_all_page_first
        # if self.user_datas['tickets_list']:
        #     yield get_all_page_tic
            # for every in range(len(self.user_datas['tickets_list'])):
            #     self.user_datas['every'] = every
            #     print '***' * 10
            #     self.user_datas['temp'] = []
            #     yield get_all_page_tic

    def parse_Flight(self, req, data):
        pass


    def parse_multi(self, req, data):
        return_rule = []
        for data_ in data:
            doma = html.fromstring(data_)
            try:
                return_rule += ['_'.join(doma.find_class('left')[0].xpath('./div/pre/text()')).strip()]
            except:
                pass
        rule = '|'.join(return_rule)
        flight_tuple = list(self.user_datas['tickets_list'][0]['flight_tuple'])
        print flight_tuple
        flight_tuple[-10] = flight_tuple[-11] = rule
        print [tuple(flight_tuple)]
        return [tuple(flight_tuple)]


    def get_page(self, req, data):
        content_start = data.rfind('<!DOCTYPE html>')
        content = data[content_start + 15:]
        content = content.decode('utf-8')
        signIn_pat = "To keep you safe from internet threats, please sign in to your company's security service."
        auth_pat = "Authentication Required"
        dom = html.fromstring(content)
        try:
            lenpage = dom.find_class('pagination')[0].xpath('./li/span/a/text()')[-3]
        except Exception as e:
            lenpage = 1
        self.user_datas['lenpage'] = lenpage
        self.user_datas['get_url'] = []
        for x in range(int(lenpage)):
            url1 = self.user_datas['url'] + '&page=' + str(x + 1)
            url1 = urllib.unquote(url1)
            self.user_datas['get_url'].append(url1)
        print self.user_datas['get_url']

    def get_Flight(self, req, data):
        return self.parse_page(self.user_datas['ticket_no'], (data, req['req']), self.user_datas['dept_day'], self.user_datas['seat_num'], self.user_datas['class_code'], self.user_datas['dept_id'], self.user_datas['dest_id'])

    def parse_page(self, ticket_no,content_origin, dept_day,seat_num, class_code, dept_id1, dest_id1):
        tickets = []
        pat2 = re.compile(r'(\d+)h (\d+)min')
        get_airline = GetAirline()
        get_daydiff = GetDaydiff()
        content = content_origin[0]
        K = content_origin[1]
        content_start = content.rfind('<!DOCTYPE html>')
        content = content[content_start + 15:]
        content = content.decode('utf-8')
        try:
            root = html.fromstring(content)
            ticketlist = root.xpath('//*[@class="fare-wrapper clearfix"]')
        except Exception, e:
            return []

        pat1 = re.compile(r'\((.*?)\)')
        for lenpage in range(len(ticketlist)):
            page = ticketlist[lenpage]
            try:
                segment = page.find_class('segment')
                price = page.find_class('amount')[0].xpath('./text()')[0].strip()
            except Exception, e:
                continue
            if ',' in price:
                price = price.replace(',', '')
            for lenseg in range(len(segment)):
                seg = segment[lenseg]
                dept_day1 = dept_day
                flight = Flight()
                flight_no, stop_time, plane_type, flight_corp, stop_id, seat_type, \
                real_class = [], [], [], [], [], [], []
                strseg = '|'.join(seg.find_class('quiet no-wrap')[0].xpath('./text()')).strip()
                dur = \
                pat2.findall(seg.find_class('duration quiet')[0].xpath('./span[1]/@title')[0].split(':')[-1].strip())[0]
                flight.dur = int(dur[0]) * 3600 + int(dur[1]) * 60
                segnext = seg.getnext()
                if '直达' in strseg:
                    dept_shi = seg.find_class('time depart')[0].xpath('./@data-timestamp')[0]
                    dept_time = self.get_yestoday(self.get_time(dept_shi), 0, -8)
                    dest_shi = seg.find_class('time arrive')[0].xpath('./@data-timestamp')[0]
                    dest_time = self.get_yestoday(self.get_time(dest_shi), 0, -8)
                    stop_time.append(dept_time + '_' + dest_time)
                    dept_id = seg.find_class('cursor_default')[0].xpath('./@title')[0].strip()
                    dest_id = seg.find_class('cursor_default')[1].xpath('./@title')[0].strip()
                    dept_id = pat1.findall(dept_id)[0]
                    dest_id = pat1.findall(dest_id)[0]
                    stop_id.append(dept_id + '_' + dest_id)
                    flight_no.append(
                        seg.find_class('first flight quiet')[0].xpath('./span/text()')[0].strip().replace(' ', ''))
                    seginfo = segnext.find_class('segment-details-sub')[0].xpath('./td[1]/strong/text()')
                    plane_type.append(seginfo[0])
                    # print seginfo
                    for tt in seginfo:
                        if 'Economy' in tt or 'Business' in tt:
                            seat_type.append(seat_dict[tt.split('(')[0].strip()])
                            break
                            # seat_type.append(seat_dict[seginfo[-2].split('(')[0].strip()])
                else:
                    seginfo = segnext.find_class('relative')[0].find_class('segment-details-main')
                    for info in seginfo:
                        dept_all = info.find_class('depart-city')[0].find_class('time')[0].xpath('./text()')[0]
                        dept_id = dept_all.split(' ')[0].strip()
                        dept_time = dept_day1 + 'T' + dept_all.split(' ')[1].strip() + ':00'

                        dest_all = info.xpath('./td[4]')[0].find_class('time')[0].xpath('./text()')[0]
                        dest_id = dest_all.split(' ')[0].strip()
                        in1 = info.xpath('./td[4]')[0].find_class('css-tooltip')
                        if in1 != []:
                            mon = in1[0].xpath('./img/@alt')[0].split(',')[-1].strip().split(' ')
                            if len(mon[0]) == 1:
                                mon[0] = '0' + mon[0]
                            try:
                                dept_day1 = mon[2] + '-' + monda[mon[1].encode('utf8')] + '-' + mon[0]
                            except KeyError:
                                dept_day1 = mon[2] + '-' + monda[mon[1].encode('raw-unicode-escape')] + '-' + mon[0]
                        dest_time = dept_day1 + 'T' + dest_all.split(' ')[-1].strip() + ':00'
                        stop_id.append(dept_id + '_' + dest_id)
                        stop_time.append(dept_time + '_' + dest_time)
                        infonext = info.getnext()
                        infoinfo = infonext.xpath('./td/strong/text()')
                        flight_no.append(infoinfo[0].replace(' ', ''))
                        if 'Economy' in infoinfo[1] or 'Business' in infoinfo[1]:
                            plane_type.append('NULL')
                            seat_type.append(seat_dict[infoinfo[1].split('(')[0].strip()])
                        else:
                            plane_type.append(infoinfo[1])
                            # print infoinfo
                            # print infoinfo[2].split('(')[0].strip()
                            # print infoinfo
                            seat_type.append(seat_dict[infoinfo[2].split('(')[0].strip()])
                flight.price = float(price) / seat_num
                flight.source = 'tripsta::tripsta'
                flight.currency = 'CNY'
                flight.flight_no = '_'.join(flight_no)
                flight.plane_type = '_'.join(plane_type)
                if 'Economy' in flight.plane_type or 'Business' in flight.plane_type:
                    flight.plane_type = '_'.join(['NULL'] * len(flight.plane_type.split('_')))
                flight.stop = len(plane_type) - 1
                flight.dept_time = stop_time[0].split('_')[0]
                flight.dept_day = flight.dept_time.split('T')[0]
                flight.dest_time = stop_time[-1].split('_')[-1]
                flight.stop_time = '|'.join(stop_time)
                flight.dept_id = stop_id[0].split('_')[0]
                flight.dest_id = stop_id[-1].split('_')[-1]
                flight.stop_id = '|'.join(stop_id)
                flight.seat_type = '_'.join(seat_type)
                flight.real_class = '_'.join(seat_type)
                flight.flight_corp = get_airline.GetAirline(flight.flight_no)
                flight.daydiff = get_daydiff.GetDaydiff(flight.stop_time)
                flight.tax = 0
                # if flight.flight_no == ticket_no:
                #     day = dept_day.split('-')
                #     dept_day3 = day[2] + '%2F' + day[1] + '%2F' + day[0]
                #     return_rule = {}
                #     return_rule['url'] = []
                #     for x in range(len(ticket_no.split('_'))):
                #         url1 = 'http://www.tripsta.cn/flight-results-terms?multiGdsResultID=' + str(lenpage + 10 * K) + '&legIndex=0&connectionIndex=' + str(lenseg) + '&segmentIndex=' + str(x) + '&bookingID=&dep=' + dept_id1 + '&arr=' + dest_id1 + '&passengersAdult=1&passengersChild=0&passengersInfant=0&class=&airlineCode=&directFlightsOnly=0&extendedDates=0&isRoundtrip=0&obDate=' + dept_day3 + '&obTime=&ibDate=&ibTime='
                #         return_rule['url'].append(url1)
                #     return_rule['flight_tuple'] = (flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id,
                #                 flight.dest_id, flight.dept_day, flight.dept_time, flight.dest_time, flight.dur,
                #                 flight.rest, flight.price, flight.tax, flight.surcharge, flight.promotion,
                #                 flight.currency,
                #                 flight.seat_type, flight.real_class, flight.package, flight.stop_id, flight.stop_time,
                #                 flight.daydiff, flight.source, flight.return_rule, flight.change_rule, flight.stop,
                #                 flight.share_flight, flight.stopby, flight.baggage, flight.transit_visa,
                #                 flight.reimbursement, flight.flight_meals, flight.ticket_type, flight.others_info)
                #     self.user_datas['tickets_list'].append(return_rule)
                # else:
                #     print flight.flight_no
                flight_tuple = (flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id,
                            flight.dest_id, flight.dept_day, flight.dept_time, flight.dest_time, flight.dur,
                            flight.rest, flight.price, flight.tax, flight.surcharge, flight.promotion,
                            flight.currency,
                            flight.seat_type, flight.real_class, flight.package, flight.stop_id, flight.stop_time,
                            flight.daydiff, flight.source, flight.return_rule, flight.change_rule, flight.stop,
                            flight.share_flight, flight.stopby, flight.baggage, flight.transit_visa,
                            flight.reimbursement, flight.flight_meals, flight.ticket_type, flight.others_info)
                tickets.append(flight_tuple)

        print self.user_datas['tickets_list']
        return tickets

    def get_yestoday(self, mytime, day, hour):
        myday = datetime.datetime(int(mytime[0:4]), int(mytime[5:7]), int(mytime[8:10]), int(mytime[11:13]),
                                  int(mytime[14:16]), int(mytime[17:19]))
        # now = datetime.datetime.now()
        delta = datetime.timedelta(days=day, hours=hour)
        my_yestoday = myday + delta
        my_yes_time = my_yestoday.strftime('%Y-%m-%dT%H:%M:%S')
        return my_yes_time

    def get_time(self, time1):
        time1 = float(time1)
        timeArray = time.localtime(time1)
        dept_time = time.strftime("%Y-%m-%dT%H:%M:%S", timeArray)
        return str(dept_time)







if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_http_proxy
    from mioji.common import spider

    spider.get_proxy = simple_get_http_proxy
    task = Task()
    #task.ticket_info = {'flight_no': 'OZ332_OZ1023'}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'PEK&CDG&20170909'
    spider = tripstaFlightSpider(task)
    print spider.source_type
    print spider.crawl()
    print spider.result
    spider.store()
    # print len(spider.tickets)
    # for item in spider.tickets:
    #     print item
