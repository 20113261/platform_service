#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mioji.common.utils import setdefaultencoding_utf8
import unicodedata

setdefaultencoding_utf8()
import re
import json
import urllib
import datetime
import math
from lxml import html as HTML
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ, PROXY_NONE
from mioji.common.parser_except import PARSE_ERROR
from mioji.common.class_common import Room  
from mioji.common.logger import logger

url_template = 'https://secure3.hilton.com/zh_CN/hi/reservation/book.htm?ctyhocn={0}&inputModule=HOTEL_SEARCH&arrivalDay={1}&arrivalMonth={2}&arrivalYear={3}&departureDay={4}&departureMonth={5}&departureYear={6}'


class hiltonHotelSpider(Spider):
    """希尔顿酒店短时间内一个ip最多同时查询30次报价, 否则要换ip和cookies"""

    source_type = 'hiltonHotel'
    targets = { 
        # 例行需指定数据版本：InsertHotel_room4
        'room': {'version': 'InsertHotel_room3'},
            } 
    old_spider_tag = {
        'hiltonHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.ceil = False
        self.room_maps = dict()
        self.url_maps = dict()
        self.path = 0
        super(hiltonHotelSpider, self).__init__(task=task)

    def mk_info(self, task):
        # 处理这些信息
        task = task
        try:
            self.occ = int(task.ticket_info['room_info'][0]['occ'])
        except:
            self.occ = 2
        lis = task.content.split('&')
        checkin = lis[-1]
        self.night = int(lis[-2])
        checkin = datetime.datetime.strptime(checkin, "%Y%m%d")
        checkout = checkin + datetime.timedelta(days=self.night)
        self.check_out = checkout.strftime("%Y-%m-%d")
        self.check_in = checkin.strftime("%Y-%m-%d")
        self.source = 'hilton'
        # task.content = "NULL&NULL&SINHITW&3&20171201"
        self.city = lis[1]
        self.ctyhocn = lis[2]
        self.arrivalDay = checkin.day
        self.arrivalMonth = checkin.month
        self.arrivalYear = checkin.year
        self.check_out_day = checkout.day
        self.check_out_month = checkout.month
        self.check_out_year = checkout.year
        self.request_url = url_template.format(self.ctyhocn,self.arrivalDay, self.arrivalMonth, self.arrivalYear, self.check_out_day, self.check_out_month, self.check_out_year) 
        #self.request_url = 'https://secure3.hilton.com/zh_CN/hi/reservation/book.htm?execution=e1s2'
        # 爬取的某些参数
        self.ids = None
        self.verify_flights = []  # 这个是验证时保存的flight
        self.tickets = []
        self.verify_tickets = []  # 这个是验证结果出来保存的票

    def targets_request(self):
        task = self.task
        self.mk_info(task)
        self.hd = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Cache-Control':'max-age=0',
                # 'Connection':'keep-alive',
                # 'Cookie':'bm_sv=56F9245A9FAC4D502F93C2E16E33DF3E~+vEmaC4BAXmWtvNA72Tuz4ImNCZTHJ5IeB9XmAqOeQg7ArWAMj4aj/q76e77KTFIkWfHm9t515q28JY74DlAZUNaIbMIvhcjSz1+r3SlhIRaceFxI5iFCE6FePGDUDMecunc0mmyinDLe1QDp6IF95RV5sJWpQx3Zj2/FWZDerc=;',
                'Host':'secure3.hilton.com',
                # 'Referer':'https://secure3.hilton.com/zh_CN/hi/reservation/book.htm?execution=e1s1',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
                }

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def first_page():
            return {
                    'req' :{'url': self.request_url, 'headers':self.hd},
                    'user_handler': [self.parse_base]
            }
        yield first_page

        @request(retry_count=5, proxy_type=PROXY_REQ)
        def other_page():
            return {
                'req': {'url': self.request_url, 'headers': self.hd, 'cookies': {}},
                'user_handler': [self.parse_base2]
            }

        len(self.url_maps)
        dispatchers = math.ceil(len(self.url_maps) / 30.0)
        logger.info(u'第二次请求数量为{}, 需要进行{}次请求'.format(len(self.url_maps), dispatchers))
        pages = []
        for room in self.room_maps:
            pages.append({'req': {'url': 'https://secure3.hilton.com' + self.room_maps[room][0]}})
        res_list = self.list_of_groups(pages, 30)

        first_heap, other_heap = res_list[0], res_list[1:]
        for pro_list in [first_heap[:15], first_heap[15:]]:
            if self.ceil:
                yield other_page
                @request(retry_count=0, proxy_type=PROXY_FLLOW, binding=[self.parse_room], async=True)
                def detail():
                    return pro_list
                yield detail
                self.ceil = False
                continue

            @request(retry_count=0, proxy_type=PROXY_FLLOW, binding=[self.parse_room], async=True)
            def detail():
                return pro_list
            yield detail

        logger.info(u'换个ip继续请求')
        if int(dispatchers) > 1:
            for heap in other_heap:
                self.browser.br.cookies.clear_session_cookies()
                self.ceil = False
                yield other_page
                for pro_list in [heap[:15], heap[15:]]:
                    if self.ceil:
                        yield other_page
                        @request(retry_count=0, proxy_type=PROXY_FLLOW, binding=[self.parse_room], async=True)
                        def detail():
                            return pro_list
                        yield detail
                        self.ceil = False
                        continue
                        # @request(retry_count=1, proxy_type=PROXY_FLLOW, binding=[self.parse_room], async=True)
                        # def single_page():
                        #     return page
                        # yield single_page
                    @request(retry_count=0, proxy_type=PROXY_FLLOW, binding=[self.parse_room], async=True)
                    def detail():
                        return pro_list
                    yield detail

    def list_of_groups(self, lia, lena):
        list_of_groups = zip(*(iter(lia),) * lena)
        end_list = [list(i) for i in list_of_groups]
        count = len(lia) % lena
        end_list.append(lia[-count:]) if count != 0 else end_list
        return end_list

    def parse_room(self, req, resp):
        room_tuple = []
        try:
            tree = HTML.fromstring(resp)
            url = req['req']['url']
            room = self.url_maps[url][0]
            room.room_type = tree.xpath(u'//b[text()="客房"]/parent::span/parent::h3')[0].text_content()[3:]
            room.bed_type = ''
            room.has_breakfast = ''
            hotel_url = ''
            room.price = float(
                tree.xpath(u'//td[text()="住宿费用总计"]/following-sibling::td[1]')[0].text.strip().replace(',', ''))
            price_real = float(tree.xpath(u'//td[text()="房费小计"]/following-sibling::td[1]')[0].text.strip().replace(',', ''))
            room.tax = get_tax(tree) or room.price - price_real
            policy = get_all_policy(tree)
            others_info = {}
            others_info[u'policy'] = policy
            room.others_info = json.dumps(others_info)
            room.return_rule = policy.get(u'取消政策', '')
            room_tuple = (str(room.hotel_name), str(room.city), str(room.source),str(room.source_hotelid),
                    str(room.source_roomid),str(room.real_source), str(room.room_type), int(room.occupancy),
                    str(room.bed_type), float(room.size), int(room.floor), str(room.check_in),
                    str(room.check_out), int(room.rest), float(room.price), float(room.tax),
                    str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free),
                    str(room.has_breakfast), str(room.is_breakfast_free),
                    str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule),
                    str(room.change_rule),
                    str(room.room_desc), str(room.others_info), str(room.guest_info))
            self.url_maps[url][1] = 1
        except Exception as e:
            print resp
            if u'很抱歉！由于无操作状态超过 15 分钟，您的会话已过期' in resp:
                logger.info(u'已经到达请求次数的上线')
                self.ceil = True
            else:
                logger.info(u'解析错误')

            return None
        return [room_tuple]

    def parse_base2(self, a, b):
        try:
            root = HTML.fromstring(b)
            name = root.xpath('//h1[@class="hotelNameNoLink"]/span[1]')[0].text_content()
            hotel_name = name if name else root.xpath('//h1[@class="hotelNameNoLink"]')[0].text_content()
        except:
            # 框架的bug，当多次请求中，遇到超时错误或者其他错误，会返回上一次请求的时候的 resp
            self.ceil = True
            return
        self.ceil = False

#14:33:00,445
    def parse_base(self, req, resp):
        room = Room()
        # rooms =[]
        root = HTML.fromstring(resp)

        policy = root.xpath(u'//div[@class="rate-desc-wrapper"]/div/strong/a')
        print policy


        room.source = self.source
        room.real_source = self.source
        room.check_in = self.check_in
        date_info = root.xpath('//span[@class="sumSectionDatesDesktop"]/span[@class="sumDates"]')[0].text_content()
        room.check_out = self.check_out
        try:
            name = root.xpath('//h1[@class="hotelNameNoLink"]/span[1]')[0].text_content()
            room.hotel_name = name if name else root.xpath('//h1[@class="hotelNameNoLink"]')[0].text_content()
        except:
            room.hotel_name = root.xpath('//h1[@class="hotelNameNoLink"]')[0].text_content()
        room.city = self.city
        room.source_hotelid=self.ctyhocn
        choice_data = root.xpath('//ul[@class="group"]/li')
        try:
            currency = root.xpath('//select[@id="changeCurrency"]/@onchange')[0]
            room.currency = re.findall('\'(...)\'',currency)[0]
            print room.currency
        except Exception as e:
            raise parser_except.ParserException(parser_except.EMPTY_TICKET,
                                            'get currency error')

        for data in choice_data:
            cu = data.xpath('div[@class="optionItems"]/h6/span[@class="priceHeader"]')[0].text_content()
            # try:
            #     #room.tax = float(re.findall(u'([\d\.]*\%)',cu)[0][:-1])/100
            #     room.tax = -1
            #     #print 'tax--->',room.tax
            # except:
            room.tax = -1
            desc = data.xpath('div[@class="itemTitleAndDesc"]/span')[0].text_content().replace('\n','').replace(' ','').replace('\t','')
            more_list = data.xpath('div[@class="optionItems"]//li')
            for more in more_list:
                source_roomid_href = more.xpath('div[@class="rate-desc-wrapper"]/div/strong/a')[0].get('href')
                source_roomid = re.findall('&srpId=(.*?)&roomCode=(.*?)&',source_roomid_href)[0]
                room.source_roomid = source_roomid[0]+','+source_roomid[1]
                more = more.text_content().replace('\n','').replace(' ','').replace('\t','')
                #print 'more--->',more
                _more = more.split('。')
                room.room_type = _more[0].replace('详情','').replace('房价类型','')

                s_price = re.findall(u'每晚([\d,]*)',more)[-1].replace(',','')
                room.price = float(s_price) * self.night # 修改，通过列表页面的价格计算总计价格。 不考虑税率 服务费。

                #print re.findall(u'每晚([\d,]*)',more)
                room.rest = -1
                room.floor = -1
                room.occupancy = self.occ
                room.pay_method = '在线支付'
                room.is_extrabed ='Null'
                room.is_extrabed_free ='Null'
                room.has_breakfast = 'Null'
                room.is_breakfast_free ='Null'
                room.is_cancel_free = 'Null'
                room.extrabed_rule = 'Null'
                room.return_rule = 'Null'
                room.change_rule = 'Null'
                room.others_info = 'Null'
                room.room_desc = desc + _more[1]
                #print 'desc---->>->>',room.room_desc
                #print room.room_type
                #print 'price----->>>>>',room.price
                #print re.findall(u'每晚([\d,]*)',_more[-2])[0].replace(',','')
                # room_tuple = (str(room.hotel_name), str(room.city), str(room.source),str(room.source_hotelid),
                #         str(room.source_roomid),str(room.real_source), str(room.room_type), int(room.occupancy),
                #         str(room.bed_type), float(room.size), int(room.floor), str(room.check_in),
                #         str(room.check_out), int(room.rest), float(room.price), float(room.tax),
                #         str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free),
                #         str(room.has_breakfast), str(room.is_breakfast_free),
                #         str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule),
                #         str(room.change_rule),
                #         str(room.room_desc), str(room.others_info), str(room.guest_info))
                # rooms.append(room_tuple)
                self.room_maps[room.source_roomid] = [source_roomid_href, room]
                self.url_maps['https://secure3.hilton.com' + source_roomid_href] = [room, 0]
            # return rooms


def get_all_policy(tree):
    all_policy = tree.xpath(u'//h2[@class="section-title"]/following-sibling::*')
    all_policy = [i if not i.getchildren() else i.getchildren() for i in all_policy]
    new = []
    for i in all_policy:
        if isinstance(i, list):
            new += i
        else:
            new.append(i)
    policy, j = {}, u''
    for i in new:
        if i.tag == u'h3':
            j = i.text.strip() if i.text else u''
            j = u'税费' if j == u'税费：' else j
            policy.setdefault(j, u'')
        else:
            try:
                if i.text and i is not None:
                    policy[j] = policy[j] + i.text.strip()
            except Exception as e:
                print(str(e))
                return policy
    return policy


def get_tax(tree):
    tax_fee = tree.xpath(u'//td[text()="税费："]/following-sibling::td')
    tax_fee = [i.text.strip().replace(u',', u'') for i in tax_fee if i.text]
    tax = ''
    for i in tax_fee:
        try:
            tax = float(i)
        except:
            pass
    return tax


if __name__ == '__main__':
    import mioji

    from mioji.common.utils import simple_get_socks_proxy

    mioji.common.spider.slave_get_proxy = simple_get_socks_proxy
    from mioji.common.task_info import Task
    task = Task()
    task.content = "NULL&50012&NANSIDI&2&20180521"
    spider = hiltonHotelSpider(task)
    task.ticket_info = {
        "room_info": [{"occ": 2, "num": 1}, ],
    }
    print spider.crawl()
    print spider.result
    # print len(spider.result['room'])
    '''
    f=open('hilton_hotels','w')
    for i in spider.result['room']:
        for ii in i:
            f.write(str(ii))
            f.write(';')
        f.write('\n')
    '''
    # print spider.verify_tickets
