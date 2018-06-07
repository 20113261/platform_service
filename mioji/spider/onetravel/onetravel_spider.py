#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
onetravel
'''
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from lxml import html as Html
import time
from mioji.common.class_common import Flight
from mioji.common.airline_common import Airline
from mioji.common.logger import logger

HOST = 'http://www.onetravel.com'
FIRST_URL = HOST + '/default.aspx?tabid=3582&dst=&rst=&daan=&raan=&fromTm=1100&rt=false&airpref=&preftyp=1&searchflxdt=false&IsNS=false&searchflxarpt=false'

M_dict = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'}
class_code_dict = {'E': '1', 'B': '2', 'F': '3', 'P': '5'}
seat_type_dict = {'1': '经济舱', '2': '商务舱', '3': '头等舱', '5': '超级经济舱'}

hd = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,und;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'www.onetravel.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
}


class OneTravel(Spider):
    source_type = 'onetravelFlight'  # 抓取目标
    # 数据目标
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }
    # 对应多个老爬虫
    old_spider_tag = {
        'onetravelFlight': {'required': ['Flight']}
    }

    def targets_request(self):
        taskcontent = self.task.content
        dept_id, dest_id, dept_day = taskcontent.split('&')

        ticket_info = self.task.ticket_info
        seat_type = ticket_info.get('v_seat_type', 'E')
        count = int(ticket_info.get('v_count', '2'))
        age = ticket_info.get('v_age', '_'.join(['-1'] * count))
        hold_seat = ticket_info.get('v_hold_seat', '_'.join(['1'] * count))

        dept_day_url = re.sub('(\d{4})(\d\d)(\d\d)', r'\2/\3/\1', dept_day)
        ages = [int(float(x)) for x in age.split('_')]
        seats = [int(x) for x in hold_seat.split('_')]
        adult_nu = len([_ for _ in ages if 12 <= _ < 65 or _ == -1])
        senior_nu = len([_ for _ in ages if _ >= 65])
        child_nu = len([_ for _ in ages if 0 <= _ < 12])
        infant_nu = 0  # len([age for age, seat in zip(ages, seats) if 0 <= age < 12 and not seat])
        infant_seat = 0  # len([age for age, seat in zip(ages, seats) if 0 <= age < 12 and seat])
        class_code = class_code_dict[seat_type]
        airline = get_airline(ticket_info.get('flight_no', None))
        child_age_s = ''.join(
            'c%s-%s%s' %
            (i, age, '' if seat else 'L') for i, (age, seat) in enumerate(
                [
                    (age, seat) for age, seat in zip(
                    ages, seats) if 0 <= age < 12]))
        person_num = int(count)
        dept_day = re.sub('(\d{4})(\d\d)(\d\d)', r'\1-\2-\3', dept_day)
        # 拼接出来第一个请求url
        url0 = 'http://www.onetravel.com/default.aspx?tabid=3582&from=' + dept_id + '&to=' + dest_id + '&dst=&rst=&daan=&raan=&fromDt=' + dept_day_url + '&fromTm=1100&rt=false&ad=' + str(
            adult_nu) + '&se=' + str(senior_nu) + '&ch=' + str(child_nu) + '&infl=' + str(
            infant_nu) + '&infs=0&class=' + str(
            class_code) + '&airpref=' + airline + '&preftyp=1&searchflxdt=false&IsNS=false&searchflxarpt=false&childAge=' + str(
            child_age_s) + ''
        referer0 = 'http://www.onetravel.com/'
        self.user_datas['page_1'] = ''
        self.user_datas['lenp'] = self.user_datas['len_page'] = 1
        self.user_datas['dept_id'] = dept_id
        self.user_datas['dest_id'] = dest_id
        self.user_datas['dept_day'] = dept_day
        self.user_datas['person_num'] = person_num
        self.user_datas['class_code'] = class_code
        self.user_datas['res'] = []

        @request(retry_count=8, proxy_type=PROXY_REQ)
        def token_request():
            hd['Referer'] = 'http://www.onetravel.com/'
            self.user_datas['first_resp_url'] = url0
            return {'req': {'url': url0,
                            'headers': hd},
                    'data': {'content_type': 'html'},
                    }

        @request(retry_count=5, proxy_type=PROXY_FLLOW, async=True)
        def page_count_request():
            url1 = self.user_datas['first_resp_url']
            url2 = url1.replace('Listing', 'LoadListingOnSearchCompleted') + '?_=1439034293446'
            hd['Referer'] = url1

            page1 = [{
                         'req': {'url': url2,
                                 'headers': hd,
                                 'method': 'get'},
                         'user_handler': [self.handler]
                     } for i in range(2)]
            return page1

        @request(retry_count=5, proxy_type=PROXY_FLLOW, async=True, binding=[self.parse_Flight])
        def page_request():
            return [{'req': {
                'url': str(self.user_datas['first_resp_url']).replace('Listing', 'NextPage') + '?ID=' + str(
                    ind + 1) + '&_=' + str(1439034548868 + ind * 50),
                'headers': hd,
                'method': 'get'},
                     } for ind in xrange(self.user_datas['lenp'])]

        yield token_request
        yield page_count_request
        yield page_request

    def handler(self, req, data):
        page1 = data
        dom = Html.fromstring(data)
        tree = dom.find_class('pdbt10 hidden')
        len_page = int(tree[0].xpath('./b[2]/text()')[0])
        if len(page1) > len(self.user_datas['page_1']):
            self.user_datas['page_1'] = page1
            self.user_datas['lenp'] = len_page if len_page < 3 else 3
            logger.info('页面总数 %s', self.user_datas['lenp'])

    def response_callback(self, req, resp):
        if req['req']['url'] == FIRST_URL:
            self.user_datas['first_resp_url'] = resp.url

    def parse_Flight(self, req, data):
        return self.parse_page(data, self.user_datas['dept_day'], self.user_datas['person_num'],
                               self.user_datas['class_code'])

    def parse_page(self, page, dept_day, person_num, class_code):
        tickets = []

        i = 0
        content = page
        i += 1
        try:
            dom = Html.fromstring(content)
        except:
            return tickets
        try:
            flight_info = dom.find_class("contract-block")
        except:
            flight_info = 'NULL'

        for each in flight_info:
            flight = Flight()
            real_class, day_diff, seat_type, flight_no, plane_type, corp, stop_id, stop_time, = [
                                                                                                ], [], [], [], [], [], [], []

            price_info = each.find_class('fare__amount is--total')[0]
            price = price_info.xpath('./span[1]/@title')[0]
            tax = 0
            child_info = each.find_class('fare__amount is--child')
            corp_list = each.find_class('itinerary__airline col-xs-4')
            patone = re.compile(r'//c.fareportal.com/n/common/air/ai/(.*?).gif')

            for cor in corp_list:
                if cor.xpath('./figure/img/@src') != []:
                    corp += patone.findall(cor.xpath('./figure/img/@src')[0])

            plane_list = each.find_class('flight__aircraft undertxt tooltip-link')

            for pla in plane_list:
                if pla is None:
                    pass
                plane_type += pla.xpath('./text()')
            plane_type = '_'.join(plane_type)

            flight_no_list = each.find_class('info__flight')
            for no in flight_no_list:
                flight_no += no.xpath('./span[1]/text()')

            len_corp = len(corp)
            count = 0
            for no in range(len(corp)):
                f_no = flight_no[count].split(' ')[-1].strip()
                if f_no.isdigit():
                    flight_no[no] = corp[no] + f_no
                    count += 1
                else:
                    count += 1
                    f_no = flight_no[count].split(' ')[1].strip()
                    flight_no[no] = corp[no] + f_no
                    count += 1
            seat_type = [seat_type_dict[class_code]] * len_corp
            real_class = ['NULL'] * len_corp
            flight_no = '_'.join(flight_no[:len_corp])
            seat_type = '_'.join(seat_type)
            flight.real_class = '_'.join(real_class)
            for cor in range(len(corp)):
                if corp[cor] in Airline:
                    corp[cor] = Airline[corp[cor]]
                else:
                    corp[cor] = 'NULL'
            corp = '_'.join(corp)

            time_id_info = each.find_class('itinerary__airport')
            stop = str(len(time_id_info) - 1)
            Year = dept_day.split('-')[0]
            broken_flag = True
            for tii in time_id_info:
                try:
                    from_time_mon = tii.find_class('airport__info is--from')[0]
                except:
                    broken_flag = False
                    break
                from_time = from_time_mon.find_class('airport__time')[
                    0].xpath('./text()')[0].strip()
                from_mon = from_time_mon.xpath('./li[1]/span[contains(@class, "hidden-xs")]/text()')[0]
                from_time = self.solve(Year, from_time, from_mon)
                from_id = from_time_mon.xpath(
                    './@title')[0].split(')')[0].split('(')[1]
                to_time_mon = tii.find_class('airport__info is--to')[0]
                to_time = to_time_mon.xpath('./li[1]/time/text()')[0].strip()
                to_mon = to_time_mon.xpath('./li[1]/span[contains(@class, "hidden-xs")]/text()')[0]
                to_time = self.solve(Year, to_time, to_mon)
                to_id = to_time_mon.xpath(
                    './@title')[0].split(')')[0].split('(')[1]
                stop_time.append(from_time + '_' + to_time)
                stop_id.append(from_id + '_' + to_id)
                if from_mon == to_mon:
                    day_diff.append('0')
                else:
                    day_diff.append('1')

            if not broken_flag:
                continue
            dur = 'NULL'
            dur_hour, dur_min = '0', '0'
            if each.find_class('is--total-trip') != []:
                time_dur = each.find_class(
                    'is--total-trip')[0].xpath('./text()')[0].split(' ')
                if len(time_dur) == 2:
                    dur_hour = time_dur[0][:-1]
                    dur_min = time_dur[1][:-1]
                else:
                    dur_min = time_dur[0][:-1]
            dur = str(int(dur_hour) * 3600 + int(dur_min) * 60)

            dept_id = stop_id[0].split('_')[0]
            dest_id = stop_id[-1].split('_')[1]
            day_diff = '_'.join(day_diff)
            dept_time = stop_time[0].split('_')[0].replace(' ', 'T')
            dest_time = stop_time[-1].split('_')[1].replace(' ', 'T')
            stop_time = '|'.join(stop_time)
            stop_time = stop_time.replace(' ', 'T')
            stop_id = '|'.join(stop_id)
            if dept_time.split('T')[0] != dept_day:
                continue
            flight.seat_type = seat_type
            flight.plane_type = plane_type
            flight.flight_no = flight_no
            flight.flight_corp = corp
            flight.currency = 'USD'
            flight.dept_time = dept_time
            flight.dest_time = dest_time
            flight.dept_day = dept_day
            flight.daydiff = day_diff
            flight.stop_time = stop_time.strip()
            flight.dest_id = dest_id.strip()
            flight.dept_id = dept_id
            flight.stop_id = stop_id
            flight.stop = stop
            flight.source = 'onetravel::onetravel'
            flight.dur = dur
            flight.tax = tax
            flight.price = price
            flight.source = 'onetravel::onetravel'
            flight.dur = dur
            flight.tax = tax
            flight.price = price
            if flight.to_tuple() not in self.user_datas['res']:
                tickets.append(flight.to_tuple())
                self.user_datas['res'].append(flight.to_tuple())
            if child_info != []:
                flight.price = child_info[0].xpath('./span[1]/@title')[0]
                flight.ticket_type = '儿童票'
                flight.tax = -1

                if flight.to_tuple() not in self.user_datas['res']:
                    tickets.append(flight.to_tuple())
                    self.user_datas['res'].append(flight.to_tuple())
        tickets = list(set(tickets))

        return tickets

    def solve(self, year, from_time, from_mon):
        t = time.strptime(from_time, '%I:%M%p')
        hour_min_sec = time.strftime('%H:%M:%S', t)
        mon = from_mon.split(',')[0].strip().split(' ')

        time_day = mon[1].strip()
        time_mon = M_dict[mon[0].strip()]
        datatime = year + '-' + time_mon + '-' + time_day + ' ' + hour_min_sec
        return datatime


def get_airline(flight_no):
    if flight_no:
        return flight_no[:2]
    return 'ALL'

def get_proxies(source):
    return "10.19.66.70:30000"


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import mioji.common.spider
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    mioji.common.spider.get_proxy = get_proxies  # simple_get_socks_proxy
    task = Task()
    # task.ticket_info = {'flight_no': 'FM9312_MU8308_KE2115'}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'PEK&ORD&20170630'  # &3&E&24_-1_0.5&1_1_0'
    spider = OneTravel(task)
    spider.crawl()
    print spider.result
    # spider.store()
