#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年4月5日

@author: fanbowen
'''


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
from common.airline_common import Airline
from common.airport_common import Airport




seat_dic = {
        'M': '经济舱',
        'W': '经济舱',
        'C': '商务舱'
        }


DATE_F = '%Y/%m/%d'
hd = {
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip,deflate, sdch',
    'Accept-Language':'zh-CN,zh;q=0.8,und;q=0.6',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Content-Type':'application/x-www-form-urlencoded',
    'Host':'www.britishairways.com',
    # 'Origin':'http://www.agoda.com',
    #'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
}
class_code_dict = {'E': 'Y', 'B': 'C', 'F': 'F', 'P': 'W'}
seat_type_dict = {'1': 'ECO', '2': 'BUS', '3': 'FST', '5': 'PEC'}
seat_dict = {'Economy':'经济舱','Business':'商务舱','First':'头等舱','Economy Premium':'超级经济舱','Economy Standard':'标准经济舱'}
cabinzh={'Y':'经济舱','C':'商务舱'}
monda = {'一月':'01','二月':'02','三月':'03','四月':'04','五月':'05','六月':'06','七月':'07','八月':'08','九月':'09','十月':'10','十一月':'11','十二月':'12'}


class tripstaFlightSpider(Spider):
    source_type = 'britishairFlight'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'Flight': {'version': 'InsertNewFlight'}
    }
    # Enable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'britishairFlight': {'required': ['Flight']}
    }

    def targets_request(self):
        taskcontent = self.task.content
        check_valid = self.task.ticket_info.get('flight_no', '')
        # 获取任务信息
        info = self.get_info(taskcontent)
        post_data = self.get_post(info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7])
        self.user_datas['check_valid'] = check_valid
        self.user_datas['info'] = info
        self.user_datas['flightDirect'] = []
        self.user_datas['flightConnect'] = []
        self.user_datas['ticket'] = []

        # 第一次请求，获得cookie
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def get_url0():
            url0 = 'http://www.britishairways.com/travel/home/public/zh_cn'
            self.user_datas['url0'] = url0
            return {
                'req': {'url': url0, 'headers': hd},
            }

        # 第二次请求，获得cookie， 并在set_time中完成下一次对url的拼接
        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def get_url1():
            hd['Content-Type'] = "application/x-www-form-urlencoded"
            hd['Referer'] = self.user_datas['url0']
            url1 = 'http://www.britishairways.com/travel/fx/public/zh_cn'
            self.user_datas['url1'] = url1
            return {
                'req': {'method': 'post', 'url': url1, 'headers': hd, 'data': post_data},
                'user_handler': [self.set_time]
            }

        # 第三次请求，获得一部分不用return_rule的航班信息
        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=[self.set_Flight])
        def get_url2():
            hd['Referer'] = self.user_datas['url1']
            url2 = self.user_datas['url2']
            return {
                'req': {'url': url2, 'headers': hd},
            }

        # 第四次请求，获得cookie
        @request(retry_count=3, proxy_type=PROXY_FLLOW)
        def get_url3():
            print self.user_datas['ticket'][self.user_datas['count']]['inf']
            outbound, hla, hbo = self.user_datas['ticket'][self.user_datas['count']]['inf'][0], self.user_datas['ticket'][self.user_datas['count']]['inf'][1], self.user_datas['ticket'][self.user_datas['count']]['inf'][2]
            cabin = outbound.split('-')[0]
            num = outbound.split('-')[-1]
            postData = 'eId=111075&eIdSortBy=&outboundCabin=' + cabin + '&outbound=' + num + '&selectedHboFare=' + hbo + '&isHBOPage=' + hbo + '&outboundHLAFlag=' + hla + '&smeToggleDisplay=DISCOUNT&outbound=' + outbound + '&continue=%E7%BB%A7%E7%BB%AD'
            url3 = 'https://www.britishairways.com/travel/fx/public/zh_cn?source=continue'
            self.user_datas['url3'] = url3
            return {
                'req': {'method': 'post', 'url': url3, 'headers': hd, 'data': postData},
            }

        # 第五次请求， 再parse_flight中完成解析并返回
        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=[self.parse_Flight])
        def get_url4():
            hd['Referer'] = self.user_datas['url3']
            time_tuple = datetime.datetime.now().timetuple()
            timestamp = time.mktime(time_tuple)
            ts = str(int(timestamp))
            url4 = 'https://www.britishairways.com/travel/fx/public/zh_cn?eId=111011&timestamp=' + ts + '&source=continue&source=continue'
            return {
                'req': {'method': 'get', 'url': url4, 'headers': hd},
            }

        yield get_url0
        yield get_url1
        yield get_url2
        print '############'
        # 如果有需要的
        for i in range(len(self.user_datas['ticket'])):
            self.user_datas['count'] = i
            yield get_url3
            yield get_url4

    def parse_Flight(self, req, data):
        info = self.return_parser(data)
        print 'info is {0}'.format(info)
        tuple_ = self.user_datas['ticket'][self.user_datas['count']]['tuple']
        tuple_ = list(tuple_)
        tuple_[-11] = info[0]
        tuple_[-6] = info[1]
        tuple_ = tuple(tuple_)
        print 'tuple_ is {0}'.format(tuple_)
        return [tuple_]



    def set_time(self, req, data):
        time_tuple = datetime.datetime.now().timetuple()
        timestamp = time.mktime(time_tuple)
        ts = str(int(timestamp))
        url2 = 'http://www.britishairways.com/travel/fx/public/zh_cn?eId=111011&timestamp=' + ts
        self.user_datas['url2'] = url2

    def set_Flight(self, req, data):
        print '*' * 100
        res = self.britishair_parser(data, self.user_datas['info'][2], self.user_datas['check_valid'], self.user_datas['url2'])
        return res


    def change_return_rule(self, req, data):
        doma = html.fromstring(data)
        print data
        try:
            req['req']['return_rule'] += ['_'.join(doma.find_class('left')[0].xpath('./div/pre/text()')).strip()]
            print 'req is {0}'.format(['_'.join(doma.find_class('left')[0].xpath('./div/pre/text()')).strip()])
        except:
            pass
        self.user_datas[str(req['req']['num'])]['return_rule'] = req['req']['return_rule']


    def return_parser(self, page):
        try:
            dom = html.fromstring(page.decode('utf-8'))
            root = dom.find_class('pageContent')[0]
        except Exception, e:
            return None
        return_info = ''
        try:
            info = root.find_class('aboutYourFlightsTable')[0]
            for tr in info.xpath('./tbody/tr'):
                return_info += (tr.find_class('conditions')[0].text_content().strip())
                return_info += '|'
            return_info = return_info.rstrip('|')
        except Exception, e:
            try:
                info = root.get_element_by_id('FareRulesOutbound')
                for ul in info.xpath('./ul'):
                    for li in ul.xpath('./li'):
                        return_info += li.text_content()
                    return_info += '|'
                return_info = return_info.rstrip('|')
            except Exception, e:
                pat = re.compile(r"var myString = '(.*)';")
                tmp_info = pat.findall(page)
                if len(tmp_info) > 0:
                    for tmp in tmp_info:
                        if len(tmp) > 200:
                            return_info = tmp
                            break
                else:
                    return_info = 'NULL'
                if len(return_info) < 200:
                    return_info = 'NULL'
        baggage_info = ''
        try:
            info = root.find_class('baggageContent')[0]
        except Exception, e:
            try:
                info = root.get_element_by_id('baggageContents')
            except Exception, e:
                baggage_info = 'NULL'
                return (return_info, baggage_info)
        try:
            for td in info.xpath('./tbody/tr/td'):
                baggage_info += td.text_content().strip()
        except Exception, e:
            baggage_info = 'NULL'
        return (return_info, baggage_info)



    def get_info(self, task_content):
        task = task_content.split('&')
        dept = task[0]
        dest = task[1]
        dept_day = task[2]
        dept_day = dept_day[:4] + '-' + dept_day[4:6] + '-' + dept_day[6:]
        try:
            cabin = task[4]
            if cabin == 'E':
                cabin = 'M'
            elif cabin == 'B':
                cabin = 'C'
            elif cabin == 'P':
                cabin = 'W'
            else:
                cabin = 'M'
            people = task[5]
            age_l = people.split('_')
            ad = 0
            ya = 0
            ch = 0
            inf = 0
            for age in age_l:
                if int(age) == -1 or int(age) > 16:
                    ad += 1
                elif int(age) >= 12 and int(age) <= 15:
                    ya += 1
                elif int(age) >= 2 and int(age) <= 11:
                    ch += 1
                else:
                    inf += 1
        except Exception, e:
            return (dept, dest, dept_day, 'M', '1', '0', '0', '0')
        return (dept, dest, dept_day, cabin, str(ad), str(ya), str(ch), str(inf))

    def get_post(self, dept, dest, dept_day, cabin, ad, ya, ch, inf):
        date = dept_day.split('-')
        depDate = date[2] + '%2F' + date[1] + '%2F' + date[0][2:]
        try:
            country_code = Airport[dept]['country_code']
        except Exception, e:
            country_code = ''
        postData = 'eId=111002&saleOption=FO&depCountry=' + country_code + '&from=' + dept + '&journeyType=OWFLT&to=' + dest + '&depDate=' + depDate + '&cabin=' + cabin + '&restrictionType=LOWEST&ad=' + ad + '&ya=' + ya + '&ch=' + ch + '&inf=' + inf + '&getFlights=%E6%9F%A5%E6%89%BE%E8%88%AA%E7%8F%AD'
        return postData

    def return_validation(self, obj, ref, outbound, hla, hbo):
        obj.add_referer(ref)
        url0 = 'https://www.britishairways.com/travel/fx/public/zh_cn?source=continue'
        try:
            cabin = outbound.split('-')[0]
            num = outbound.split('-')[-1]
        except Exception, e:
            return None
        postData = 'eId=111075&eIdSortBy=&outboundCabin=' + cabin + '&outbound=' + num + '&selectedHboFare=' + hbo + '&isHBOPage=' + hbo + '&outboundHLAFlag=' + hla + '&smeToggleDisplay=DISCOUNT&outbound=' + outbound + '&continue=%E7%BB%A7%E7%BB%AD'
        try:
            page0, _ = obj.req('post', url0, postData, paras_type=2, html_flag=True)
        except Exception, e:
            return None
        obj.add_referer(url0)
        time_tuple = datetime.datetime.now().timetuple()
        timestamp = time.mktime(time_tuple)
        ts = str(int(timestamp))
        url1 = 'https://www.britishairways.com/travel/fx/public/zh_cn?eId=111011&timestamp=' + ts + '&source=continue&source=continue'
        try:
            page1, _ = obj.req('get', url1, html_flag=True)
        except Exception, e:
            return None
        if page1 == None or len(page1) < 50:
            return None
        # open('valid.html', 'w').write(page1)
        info = self.return_info(page1)
        return info

    def return_info(self, page):
        try:
            dom = html.fromstring(page.decode('utf-8'))
            root = dom.find_class('pageContent')[0]
        except Exception, e:
            return None
        return_info = ''
        try:
            info = root.find_class('aboutYourFlightsTable')[0]
            for tr in info.xpath('./tbody/tr'):
                return_info += (tr.find_class('conditions')[0].text_content().strip())
                return_info += '|'
            return_info = return_info.rstrip('|')
        except Exception, e:
            try:
                info = root.get_element_by_id('FareRulesOutbound')
                for ul in info.xpath('./ul'):
                    for li in ul.xpath('./li'):
                        return_info += li.text_content()
                    return_info += '|'
                return_info = return_info.rstrip('|')
            except Exception, e:
                pat = re.compile(r"var myString = '(.*)';")
                tmp_info = pat.findall(page)
                if len(tmp_info) > 0:
                    for tmp in tmp_info:
                        if len(tmp) > 200:
                            return_info = tmp
                            break
                else:
                    return_info = 'NULL'
                if len(return_info) < 200:
                    return_info = 'NULL'
        baggage_info = ''
        try:
            info = root.find_class('baggageContent')[0]
        except Exception, e:
            try:
                info = root.get_element_by_id('baggageContents')
            except Exception, e:
                baggage_info = 'NULL'
                return (return_info, baggage_info)
        try:
            for td in info.xpath('./tbody/tr/td'):
                baggage_info += td.text_content().strip()
        except Exception, e:
            baggage_info = 'NULL'
        return (return_info, baggage_info)

    def britishair_parser(self, page, dept_date, check_valid, ref):
        result = []
        if page == None or len(page) < 50:
            pass
        if page.find('我们可能没有飞往您所选目的地的航班') != -1:
            pass
        try:
            dom = html.fromstring(page.decode('utf8'))
        except Exception, e:
            pass
        try:
            root = dom.get_element_by_id('outBoundFlightList')
        except Exception, e:
            return []
        flightDirect = []
        flightConnect = []
        try:
            flightDirect.append(root.find_class('flightList directFlight')[0])
        except Exception, e:
            pass
        try:
            flightDirect.append(root.find_class('flightList directFlightsTable connectflights')[0])
        except Exception, e:
            pass
        try:
            flightConnect.append(root.find_class('flightList connectFlightsTable connectflights')[0])
        except Exception, e:
            pass

        cur_pat = re.compile(r"tagManTrackingInfo.currency_code = '(.*?)';")
        try:
            currency = cur_pat.findall(page)[0]
        except Exception, e:
            currency = 'NULL'
        try:
            tax_info = dom.find_class('lowestPriceNotice')[0].text_content().strip().replace(' ', '')
        except Exception, e:
            tax = -1
        if '不含' in tax_info or '不包含' in tax_info:
            tax = -1
        elif '包含' in tax_info:
            tax = 0
        else:
            tax = -1
        if not flightDirect and not flightConnect:
            return []

        # 直飞
        for f_tmp in flightDirect:
            try:
                f_list = f_tmp.get_element_by_id('outboundDates')
            except Exception, e:
                continue
            tr = f_list.xpath('./tr')
            if len(tr) == 0:
                tr = f_list.xpath("./tr[@class='compact']")
            for f_l in tr:
                flight = Flight()
                flight.dept_day = dept_date
                flight.source = 'britishair::britishair'
                try:
                    base = f_l.find_class('outBorder')[0].xpath('./table/tbody/tr')[0]
                except Exception, e:
                    base = f_l
                try:
                    dept_info = base.find_class('departure')[0]
                    dest_info = base.find_class('arrival')[0]
                    operator_info = base.find_class('operator')[0]
                    price_info = base.find_class('priceselecter')
                except Exception, e:
                    continue
                try:
                    dept_time = dept_info.find_class('time')[0].text_content().strip()
                    flight.dept_time = dept_date + 'T' + dept_time + ':00'
                except Exception, e:
                    flight.dept_time = 'NULL'
                try:
                    flight.dept_id = dept_info.find_class('airportCode')[0].text_content().strip()
                except Exception, e:
                    try:
                        flight.dept_id = operator_info.find_class('FlightData')[0].find_class('from')[
                            0].text_content().strip()
                    except Exception, e:
                        flight.dept_id = 'NULL'
                try:
                    dest_time = dest_info.find_class('time')[0].text_content().strip()
                    dest_date = dest_info.find_class('date')[0].text_content().strip().replace(' ', '')
                    date_pat = re.compile(r'(\d+).*?(\d+).*?')
                    date_tmp = date_pat.findall(dest_date)[0]
                    if len(date_tmp[0]) < 2:
                        month = '0' + date_tmp[0]
                    else:
                        month = date_tmp[0]
                    if len(date_tmp[1]) < 2:
                        day = '0' + date_tmp[1]
                    else:
                        day = date_tmp[1]
                    if int(month) < int(dept_date[5:7]):
                        dest_year = int(dept_date[:4]) + 1
                    else:
                        dest_year = int(dept_date[:4])
                    flight.dest_time = str(dest_year) + '-' + month + '-' + day + 'T' + dest_time + ':00'
                except Exception, e:
                    flight.dest_time = 'NULL'
                try:
                    flight.dest_id = dest_info.find_class('airportCode')[0].text_content().strip()
                except Exception, e:
                    try:
                        flight.dest_id = operator_info.find_class('FlightData')[0].find_class('to')[
                            0].text_content().strip()
                    except Exception, e:
                        flight.dest_id = 'NULL'
                flight.stop_id = flight.dept_id + '_' + flight.dest_id
                flight.stop_time = flight.dept_time + '_' + flight.dest_time
                try:
                    if flight.dept_time[8:10] != flight.dest_time[8:10]:
                        flight.daydiff = 1
                    else:
                        flight.daydiff = 0
                except Exception, e:
                    pass
                try:
                    flight_corp = operator_info.find_class('FlightData')[0].find_class('Carrier')[
                        0].text_content().strip()
                    flight.flight_corp = Airline[flight_corp]
                except Exception, e:
                    flight.flight_corp = 'NULL'
                try:
                    flight.flight_no = flight_corp + \
                                       operator_info.find_class('FlightData')[0].find_class('FlightNumber')[
                                           0].text_content()
                except Exception, e:
                    flight.flight_no = 'NULL'
                for price_seg in price_info:
                    try:
                        price_raw = price_seg.find_class('priceSelectionContainer')[0].text_content()
                        price_pat = re.compile(r'.*?(\d+)$')
                        flight.price = float(price_pat.findall(price_raw)[0])
                        flight.tax = tax
                        flight.currency = currency
                    except Exception, e:
                        continue
                    try:
                        seat_rest = price_seg.find_class('threelimitedSeatAvailMessage')[0].text_content()
                        rest_pat = re.compile(r'.*?(\d+).*?')
                        flight.rest = rest_pat.findall(seat_rest)[0]
                    except Exception, e:
                        pass
                    try:
                        type_info = price_seg.xpath('./@class')[0]
                        type_pat = re.compile(r'.*?price-(\w).*?')
                        t = type_pat.findall(type_info)[0]
                        flight.seat_type = seat_dic[t]
                    except Exception, e:
                        pass
                    try:
                        if flight.flight_no == check_valid:
                            outbound = price_seg.find_class('outBoundPriceInput')[0].xpath('./@value')[0].strip()
                            other_info = price_seg.find_class('outBoundPriceInput')[0].xpath('./@class')[0].strip()
                            if 'HLAAvailable' in other_info:
                                hla = 'true'
                            else:
                                hla = 'false'
                            if 'HBOPriceInput' in other_info:
                                hbo = 'true'
                            else:
                                hbo = 'false'
                            temp = {}
                            temp['inf'] = (outbound, hla, hbo)
                            temp['tuple'] = (
                                flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id,
                                flight.dest_id,
                                flight.dept_day, flight.dept_time, flight.dest_time, flight.dur, flight.rest,
                                flight.price,
                                flight.tax, flight.surcharge, flight.promotion, flight.currency, flight.seat_type,
                                flight.real_class, flight.package, flight.stop_id, flight.stop_time, flight.daydiff,
                                flight.source, flight.return_rule, flight.change_rule, flight.stop,
                                flight.share_flight,
                                flight.stopby, flight.baggage, flight.transit_visa, flight.reimbursement,
                                flight.flight_meals,
                                flight.ticket_type, flight.others_info)
                            self.user_datas['ticket'].append(temp)
                        else:
                            flight_tuple = (
                                flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id, flight.dest_id,
                                flight.dept_day, flight.dept_time, flight.dest_time, flight.dur, flight.rest,
                                flight.price,
                                flight.tax, flight.surcharge, flight.promotion, flight.currency, flight.seat_type,
                                flight.real_class, flight.package, flight.stop_id, flight.stop_time, flight.daydiff,
                                flight.source,
                                flight.return_rule, flight.change_rule, flight.stop, flight.share_flight, flight.stopby,
                                flight.baggage, flight.transit_visa, flight.reimbursement, flight.flight_meals,
                                flight.ticket_type,
                                flight.others_info)
                            result.append(flight_tuple)
                    except Exception, e:
                        print e


        # 中转
        for f_tmp in flightConnect:
            try:
                f_list = f_tmp.get_element_by_id('outboundDates')
            except Exception, e:
                continue
            tr = f_list.xpath("./tr[@class='expand expanded']")
            if len(tr) == 0:
                tr = f_list.xpath("./tr[@class='compact']")
            for f_l in tr:
                try:
                    all_info = f_l.find_class('outBorder')[0].xpath('./table/tbody/tr')
                except Exception, e:
                    continue
                if len(all_info) == 0:
                    continue
                elif len(all_info) == 1:
                    base = all_info[:]
                else:
                    base = all_info[:-1]
                flight = Flight()
                flight.dept_day = dept_date
                flight.source = 'britishair::britishair'
                flight_no = []
                plane_type = []
                flight_corp = []
                stop_id = []
                stop_time = []
                daydiff = []
                real_class = []
                stop = 0
                for seg in base:
                    try:
                        dept_info = seg.find_class('departuretrue')[0]
                        dest_info = seg.find_class('arrivaltrue')[0]
                        operator_info = seg.find_class('operatortrue')[0]
                    except Exception, e:
                        continue
                    stop += 1
                    try:
                        dept_time = dept_info.find_class('departtime')[0].text_content().strip()
                        dept_date_tmp = dept_info.find_class('departdate')[0].text_content().strip()
                        date_pat = re.compile(r'(\d+).*?(\d+).*?')
                        date_tmp = date_pat.findall(dept_date_tmp)[0]
                        if dept_date_tmp[-1] == '月':
                            date_tmp = (date_tmp[1], date_tmp[0])
                        if len(date_tmp[0]) < 2:
                            month = '0' + date_tmp[0]
                        else:
                            month = date_tmp[0]
                        if len(date_tmp[1]) < 2:
                            day = '0' + date_tmp[1]
                        else:
                            day = date_tmp[1]
                        if int(month) < int(dept_date[5:7]):
                            dept_year = int(dept_date[:4]) + 1
                        else:
                            dept_year = int(dept_date[:4])
                        dept_time = str(dept_year) + '-' + month + '-' + day + 'T' + dept_time + ':00'
                        # print dept_time
                    except Exception, e:
                        dept_time = 'NULL'
                    try:
                        dest_time = dest_info.find_class('arrivaltime')[0].text_content().strip()
                        dest_date = dest_info.find_class('arrivaldate')[0].text_content().strip()
                        date_tmp = date_pat.findall(dest_date)[0]
                        if len(date_tmp[0]) < 2:
                            month = '0' + date_tmp[0]
                        else:
                            month = date_tmp[0]
                        if len(date_tmp[1]) < 2:
                            day = '0' + date_tmp[1]
                        else:
                            day = date_tmp[1]
                        if int(month) < int(dept_date[5:7]):
                            dest_year = int(dept_date[:4]) + 1
                        else:
                            dest_year = int(dept_date[:4])
                        dest_time = str(dest_year) + '-' + month + '-' + day + 'T' + dest_time + ':00'
                    except Exception, e:
                        dest_time = 'NULL'
                    stop_time.append(dept_time + '_' + dest_time)

                    try:
                        if dept_time[8:10] != dest_time[8:10]:
                            daydiff.append('1')
                        else:
                            daydiff.append('0')
                    except Exception, e:
                        daydiff.append('-1')
                    real_class.append('NULL')
                    plane_type.append('NULL')
                    try:
                        corp = operator_info.find_class('FlightData')[0].find_class('Carrier')[0].text_content().strip()
                        corp_t = Airline[corp]
                    except Exception, e:
                        corp_t = 'NULL'
                    flight_corp.append(corp_t)
                    try:
                        no = corp + operator_info.find_class('FlightData')[0].find_class('FlightNumber')[
                            0].text_content()
                    except Exception, e:
                        no = 'NULL'
                    flight_no.append(no)
                    try:
                        dept_id = operator_info.find_class('FlightData')[0].find_class('from')[0].text_content()
                    except Exception, e:
                        dept_id = 'NULL'
                    try:
                        dest_id = operator_info.find_class('FlightData')[0].find_class('to')[0].text_content()
                    except Exception, e:
                        dest_id = 'NULL'
                    stop_id.append(dept_id + '_' + dest_id)

                    if len(all_info) > 1:
                        summary = all_info[-1]
                        try:
                            stop_info = summary.find_class('connections')[0].text_content().strip()
                            flight.stop = stop_info
                        except Exception, e:
                            pass
                        try:
                            dur_info = summary.find_class('journeyTime')[0].text_content().strip()
                            dur_pat = re.compile(r'(\d+).*?(\d+).*?')
                            dur = dur_pat.findall(dur_info)[0]
                            flight.dur = int(dur[0]) * 3600 + int(dur[1]) * 60
                        except Exception, e:
                            pass
                try:
                    flight.dept_id = stop_id[0].split('_')[0]
                    flight.dest_id = stop_id[-1].split('_')[-1]
                    flight.dept_time = stop_time[0].split('_')[0]
                    flight.dest_time = stop_time[-1].split('_')[-1]
                except Exception, e:
                    continue
                flight.flight_no = '_'.join(flight_no)
                flight.flight_corp = '_'.join(flight_corp)
                flight.stop_id = '|'.join(stop_id)
                flight.stop_time = '|'.join(stop_time)
                flight.daydiff = '_'.join(daydiff)
                flight.real_class = '_'.join(real_class)
                flight.plane_type = '_'.join(plane_type)
                price_info = base[0].find_class('priceselecter')

                if len(price_info) > 0:
                    for price_seg in price_info:
                        try:
                            price_raw = price_seg.find_class('priceSelectionContainer')[0].text_content()
                            price_pat = re.compile(r'.*?(\d+)$')
                            flight.price = float(price_pat.findall(price_raw)[0])
                            flight.tax = tax
                            flight.currency = currency
                        except Exception, e:
                            continue
                        try:
                            seat_rest = price_seg.find_class('threelimitedSeatAvailMessage')[0].text_content()
                            rest_pat = re.compile(r'.*?(\d+).*?')
                            flight.rest = rest_pat.findall(seat_rest)[0]
                        except Exception, e:
                            pass
                        try:
                            type_info = price_seg.xpath('./@class')[0]
                            type_pat = re.compile(r'.*?price-(\w).*?')
                            t = type_pat.findall(type_info)[0]
                            seat_type = [seat_dic[t]] * stop
                            flight.seat_type = '_'.join(seat_type)
                        except Exception, e:
                            seat_type = ['NULL'] * stop
                            flight.seat_type = '_'.join(seat_type)
                        try:
                            if flight.flight_no == check_valid:
                                outbound = price_seg.find_class('outBoundPriceInput')[0].xpath('./@value')[0].strip()
                                other_info = price_seg.find_class('outBoundPriceInput')[0].xpath('./@class')[0].strip()
                                if 'HLAAvailable' in other_info:
                                    hla = 'true'
                                else:
                                    hla = 'false'
                                if 'HBOPriceInput' in other_info:
                                    hbo = 'true'
                                else:
                                    hbo = 'false'
                                temp = {}
                                temp['inf'] = (outbound, hla, hbo)
                                temp['tuple'] = (
                                    flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id,
                                    flight.dest_id,
                                    flight.dept_day, flight.dept_time, flight.dest_time, flight.dur, flight.rest,
                                    flight.price,
                                    flight.tax, flight.surcharge, flight.promotion, flight.currency, flight.seat_type,
                                    flight.real_class, flight.package, flight.stop_id, flight.stop_time, flight.daydiff,
                                    flight.source, flight.return_rule, flight.change_rule, flight.stop,
                                    flight.share_flight,
                                    flight.stopby, flight.baggage, flight.transit_visa, flight.reimbursement,
                                    flight.flight_meals,
                                    flight.ticket_type, flight.others_info)
                                self.user_datas['ticket'].append(temp)



                            else:
                                flight_tuple = (
                                    flight.flight_no, flight.plane_type, flight.flight_corp, flight.dept_id,
                                    flight.dest_id,
                                    flight.dept_day, flight.dept_time, flight.dest_time, flight.dur, flight.rest,
                                    flight.price,
                                    flight.tax, flight.surcharge, flight.promotion, flight.currency, flight.seat_type,
                                    flight.real_class, flight.package, flight.stop_id, flight.stop_time, flight.daydiff,
                                    flight.source, flight.return_rule, flight.change_rule, flight.stop,
                                    flight.share_flight,
                                    flight.stopby, flight.baggage, flight.transit_visa, flight.reimbursement,
                                    flight.flight_meals,
                                    flight.ticket_type, flight.others_info)

                                result.append(flight_tuple)
                        except Exception, e:
                            pass

        print 'result is {0}'.format(result)
        return result


if __name__ == '__main__':
    from mioji.common.task_info import Task
    task = Task()
    task.ticket_info = {'flight_no': 'BA1594'}
    # task.content = 'PEK&ORD&20170919'
    task.content = 'JFK&LON&20170513'#&3&E&24_-1_0.5&1_1_0'
    spider = tripstaFlightSpider(task)
    print spider.source_type
    print spider.crawl()
    spider.store()
    # print len(spider.tickets)
    # for item in spider.tickets:
    #     print item
