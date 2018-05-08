#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mioji.common.spider import Spider,request,PROXY_REQ,PROXY_FLLOW
from mioji.common.class_common import Room
from mioji.common.task_info import Task
from mioji.common import parser_except
from lxml import etree
import re
import json
import urllib

class RoomSpider(Spider):
    source_type = 'bestwesternHotel'
    targets = {
        'Room': {'version': 'InsertNewRoom'}
    }
    old_spider_tag = {
        'bestwesternHotel':{'required': 'Room'}
    }

    def __init__(self,task=None):
        Spider.__init__(self,task=None)
        self.task = task
        # 酒店-房间详情url
        self.hotel_room_url = "https://www.bestwestern.net.cn/booking-path/hotel-rooms/"
        # 目标房间支付页面url
        self.room_pay_url = "https://www.bestwestern.net.cn/booking-path/checkout"
        # 任务信息
        self.task_info = {}
        # 每个房间基础信息集合
        self.base_room_info_list = []
        # 请求支付页面需要的参数
        self.check_info_list = []
        self.cookies = {}


        # 解析任务
        if task is not None:
            self.process_task()

    def targets_request(self):

        # 请求真正的酒店-房间详情url
        @request(retry_count=2, proxy_type=PROXY_REQ)
        def first_request():
            true_hotel_room_url = self.true_hotel_room_url

            return {
                'req':{
                    'url': true_hotel_room_url,
                    'method':'get',
                    'headers':{
                        'Cookie':"search_numAdults={search_numAdults};search_checkInDate={search_checkInDate};search_checkOutDate={search_checkOutDate};search_numberOfRooms={search_numberOfRooms}".format(**self.task_info)
                    }
                },
                'user_handler':[self.process_first_request]
            }

        # 请求房间支付详情
        @request(retry_count=2,proxy_type=PROXY_FLLOW,binding=self.parse_Room)
        def room_pay_detail_request():
            all_list = []
            for data in self.check_info_list:
                all_list.append({
                    'req':{
                        'url':self.room_pay_url,
                        'method':'post',
                        # 'data':'task={task}&roomTypeCodeSelect1={roomTypeCodeSelect1}&ratePlanCodeSelect1={ratePlanCodeSelect1}&ratePlanTypeSelect1={ratePlanTypeSelect1}&corporateIdSelect1={corporateIdSelect1}&promoCodeSelect1={promoCodeSelect1}&sign1={sign1}&a6f2551eee1c47d71e08748910549a68={a6f2551eee1c47d71e08748910549a68}'.format(**data),
                        'data':data,
                        'headers':{
                            # 'cookies':self.cookies
                            'Cookie': "CURRENCY-track={CURRENCY-track};"
                                      "search_checkOutDate={search_checkOutDate};"
                                      "search_locationLng={search_locationLng};"
                                      "search_locationLat={search_locationLat};"
                                      "search_distanceUnit={search_distanceUnit};"
                                      "search_numberOfRooms={search_numberOfRooms};"
                                      "search_destination_country={search_destination_country};"
                                      "search_numChild={search_numChild};"
                                      "search_destination={search_destination};"
                                      "search_checkInDate={search_checkInDate};"
                                      "d3dfb4735e1c338c57890b655b56b722={d3dfb4735e1c338c57890b655b56b722};"
                                      "search_distance={search_distance};search_numAdults={search_numAdults}".format(**self.cookies),
                            # 'Cookie':'CURRENCY-track=EUR;search_checkOutDate=2018-04-02;search_locationLng=1.257505;search_locationLat=45.825205;search_distanceUnit=mi;search_numberOfRooms=1;search_destination_country=FR;search_numChild=0;search_destination=Limoges%2C+%E6%B3%95%E5%9B%BD;search_checkInDate=2018-04-01;d3dfb4735e1c338c57890b655b56b722=ucqlk5ctjg7rn6g4bppvmocici;search_distance=50;search_numAdults=2',
                            'Referer':self.true_hotel_room_url,
                            'Content-Type': "application/x-www-form-urlencoded"
                        }
                    }
                })
            return all_list


        yield first_request
        yield room_pay_detail_request

    # 处理请求 真正的酒店-房间详情url 返回的数据
    def process_first_request(self,req,resp):
        with open("3.html","w") as f:
            f.write(resp)
        html = etree.HTML(resp)

        result = re.search('房间已售空，请更改搜索'.decode('utf8'),resp)
        # 如果没有匹配结果，证明有房间
        if type(result) == type(None):

            self.cookies = {c.name:c.value for c in req['resp'].cookies}
            # self.cookies = req['resp'].cookies
            list = zip(self.cookies.keys(),self.cookies.values())
            L = []
            for l in list:
                a = "{}={}".format(*l)
                L.append(a)
            self.check_cookie = ";".join(L)
            print self.check_cookie
            # print self.cookies

            # 处理有房间时的数据
            self.__process_room(req,resp)
        else:
            print "房间已售空"
            # 否则房间已售空
            raise parser_except.ParserException(29,"无房间")

    # 解析房间
    def parse_Room(self,req,resp):

        html = etree.HTML(resp)

        data = req['req']['data']
        print data
        data_list = data.split("&")
        import re
        for data in data_list:
            list = data.split("=")
            if re.search(r'roomTypeCodeSelect',list[0]):
                source_roomid = list[1]

        for r in self.base_room_info_list:
            if r['source_roomid'] == source_roomid:
                base_info = r['base_info']

                room = Room()

                # 酒店名
                room.hotel_name = base_info['hotel_name']
                # 城市名
                room.city = base_info['city']
                # 源名
                room.source = base_info['source']
                # 酒店id
                room.source_hotelid = base_info['source_hotelid']
                # 房间id
                room.source_roomid = r['source_roomid']
                # 房间类型
                room.room_type = html.xpath('//div[@class="paymentSummaryFixedWrapper"]//p[contains(@class,"bedsAdultChildrenLabel")]/text()')[0].split(",")[0].strip()
                # 真实购买源
                room.real_source = base_info['real_source']
                # 房间人数
                room.occupancy = base_info['occupancy']
                # 床型
                room.bed_type = 'NULL'
                # 大小
                room.size = -1.0
                # 楼层
                room.floor = -1
                # 入住时间,退房时间
                room.check_in, room.check_out = self.__get_date(html)
                # 房间剩余量
                room.rest = 1
                # 总价格（含税）
                room.price = html.xpath('//p[@class="amount"]/span[@id="total-room-amount"]/text()')[0]
                # 税
                room.tax = 0
                # 货币类型
                room.currency = base_info['currency']
                # 房间描述
                room.room_desc = base_info['room_desc'].strip() + "," + html.xpath('//div[contains(@class,"roomDetailsContentContainer")]//div[contains(@class,"paddingContainer")][1]/text()')[0].strip()
                # 酒店url
                room.hotel_url = self.true_hotel_room_url

                room_info = tuple([
                    room.hotel_name,
                    room.city,
                    room.source,
                    room.source_hotelid,
                    room.source_roomid,
                    room.real_source,
                    room.room_type,
                    room.occupancy,
                    room.bed_type,
                    room.size,
                    room.floor,
                    room.check_in,
                    room.check_out,
                    room.rest,
                    room.price,
                    room.tax,
                    room.currency,
                    room.pay_method,
                    room.is_extrabed,
                    room.is_extrabed_free,
                    room.has_breakfast,
                    room.is_breakfast_free,
                    room.is_cancel_free,
                    room.extrabed_rule,
                    room.return_rule,
                    room.room_desc,
                    "NULL",
                    "NULL"
                ])
                return room_info

    # 解析任务
    def process_task(self):
        infos = self.task.content.split('&')
        # 真正的酒店-房间详情url
        self.true_hotel_room_url = self.hotel_room_url + infos[0]

        # 入住天数
        day = infos[1]
        # 入住日期
        check_in_date = infos[2]
        # 每间房入住人数
        occ = self.task.ticket_info['room_info'][0]['occ']
        # 房间数
        room_count = self.task.ticket_info['room_info'][0]['room_count']

        self.task_info = dict(
            search_numAdults=self.__get_num_str(occ),
            search_checkInDate = "-".join([check_in_date[:4],check_in_date[4:6],check_in_date[6:]]),
            search_checkOutDate = self.__get_checkOutDate(check_in_date,day),
            search_numberOfRooms = room_count
        )

    # 得到房间人数字符串
    def __get_num_str(self,occ):
        a = ",".join(occ * 3)  # a = '1,1,1'
        b = urllib.quote(a)  # b = '1%2C1%2C1'
        return b

    # 获取退房日期
    # 参数：startDate 入住日期
    #      day 入住天数
    def __get_checkOutDate(self, startDate, day):
        # 入住年份
        checkInYear = startDate[:4]
        # 入住月份
        checkInMonth = startDate[4:6]
        # 入住日期
        checkInDate = startDate[6:]
        # 天数为31天的月份
        if checkInMonth in ['01', '03', '05', '07', '08', '10', '12']:
            if 31 < int(checkInDate) + int(day) < 61:

                checkOutMonth = int(checkInMonth) + 1
                if checkOutMonth > 12:
                    # 退房年份
                    checkOutYear = str(int(checkInYear) + 1)
                    checkOutMonth -= 12

                if checkOutMonth < 10:
                    # 退房月份
                    checkOutMonth = '0' + str(checkOutMonth)
                else:
                    # 退房月份
                    checkOutMonth = str(checkOutMonth)

                checkOutDate = int(checkInDate + day - 31)
                if checkOutDate < 10:
                    # 退房日期
                    checkOutDate = '0' + str(checkOutDate)
                else:
                    # 退房日期
                    checkOutDate = str(checkOutDate)
            elif int(checkInDate) + int(day) < 31:
                checkOutYear = checkInYear
                checkOutMonth = checkInMonth
                checkOutDate = int(checkInDate) + int(day)
                if checkOutDate < 10:
                    checkOutDate = '0' + str(checkOutDate)
                else:
                    checkOutDate = str(checkOutDate)
        else:
            if 30 < int(checkInDate) + int(day) < 61:

                checkOutMonth = int(checkInMonth) + 1
                if checkOutMonth > 12:
                    # 退房年份
                    checkOutYear = str(int(checkInYear) + 1)
                    checkOutMonth -= 12

                if checkOutMonth < 10:
                    # 退房月份
                    checkOutMonth = '0' + str(checkOutMonth)
                else:
                    # 退房月份
                    checkOutMonth = str(checkOutMonth)

                checkOutDate = int(checkInDate + day - 30)
                if checkOutDate < 10:
                    # 退房日期
                    checkOutDate = '0' + str(checkOutDate)
                else:
                    # 退房日期
                    checkOutDate = str(checkOutDate)
            elif int(checkInDate) + int(day) < 30:
                checkOutYear = checkInYear
                checkOutMonth = checkInMonth
                checkOutDate = int(checkInDate) + int(day)
                if checkOutDate < 10:
                    checkOutDate = '0' + str(checkOutDate)
                else:
                    checkOutDate = str(checkOutDate)
        checkOut = "-".join([checkOutYear, checkOutMonth, checkOutDate])

        return checkOut

    # 处理有房间时的数据
    def __process_room(self,req,resp):
        print "有房间"

        html = etree.HTML(resp)
        rooms = html.xpath('//div[contains(@class,"group-room")]')
        for room in rooms:

            room_id = room.xpath('./@id')[0]
            m = re.search(r'\d+',room_id)
            # 房间基本信息
            base_room_info = dict(
                # 房间id
                source_roomid=m.group(),
                # 基础信息
                base_info = dict(
                    # 城市名
                    city=html.xpath(
                        '//div[contains(@class,"addressContainer")]/span[@id="address-1-city-state-zip"]/text()')[
                        0].split(",")[0],
                    # 源名
                    source = 'bestwestern',
                    # 酒店id
                    source_hotelid = self.task.content.split("&")[0],
                    # 货币类型
                    currency = html.xpath('//div[@class="phoneNumbers"]/div[2]/div[2]/p[2]/text()')[0].split("(")[1][:-1],
                    # 酒店名
                    hotel_name = html.xpath('//div[@class="hotelSummary"]//h1[@id="hotel-name"]/a/text()')[0],
                    # 真实购买源
                    real_source = 'bestwestern',
                    # 房间描述
                    room_desc = room.xpath('.//div[@class="roomDetailsIcons"]/span/text()')[0],
                    # 可入住人数
                    occupancy = self.__get_occ(resp)
                )
            )
            self.base_room_info_list.append(base_room_info)

        select_rooms = html.xpath('//div[@class="selectRateButtonContainer"]/button/@onclick')
        for select_room in select_rooms:
            list = select_room.split(",")
            # 请求支付页面需要的参数
            check_info  = self.__get_post_data(list)
            self.check_info_list.append(check_info)

        with open('room_info.json','w') as f:
            f.write(json.dumps(self.base_room_info_list,ensure_ascii=False))

    # 获取可入住人数
    def __get_occ(self,resp):
        p = "最高入住率".decode('utf8') + r": (\d+)"
        m = re.search(p, resp)
        num = m.group(1)
        if int(num) >= int(self.task.ticket_info['room_info'][0]['occ']):
            return num
        else:
            raise parser_except.ParserException(29, "无房间")


    # 获取入住退房时间
    def __get_date(self,html):
        list = html.xpath('//div[@class="dateInfo"]//p[@class="date"]/text()')
        date0 = list[0].split('/')
        check_in_date = "-".join(date0[::-1])
        date1 = list[1].split('/')
        check_out_date = "-".join(date1[::-1])
        return check_in_date,check_out_date

    # 获取post请求支付页面的参数
    def __get_post_data(self,list):
        room_count = int(self.task.ticket_info['room_info'][0]['room_count'])
        data = {}
        data['task'] = "initBookingRooms"
        for i in range(1,room_count+1):
            data["roomTypeCodeSelect"+str(i)] = list[4].replace("'", "")
            data["ratePlanCodeSelect"+str(i)] = list[5].replace("'", "")
            data["ratePlanTypeSelect"+str(i)] = list[6].replace("'", "")
            data["corporateIdSelect"+str(i)] = ""
            data["promoCodeSelect"+str(i)] = ""
            data["sign"+str(i)] = 1
        data["a6f2551eee1c47d71e08748910549a68"] = ""
        data_list = ["{}={}".format(*li) for li in zip(data.keys(), data.values())]
        post_data = "&".join(data_list)
        return post_data


if __name__ == '__main__':
    task = Task()
    # task.content = "best-western-plus-richelieu-limoges-93563&1&20180401"
    task.content = "best-western-hotel-am-spittelmarkt-berlin-95382&1&20180401"
    task.ticket_info = {
        'room_info': [{
            # 成年人数
            'occ': '2',
            # 房间数
            'room_count': 2,
        }]
    }
    spider = RoomSpider(task)
    spider.crawl()