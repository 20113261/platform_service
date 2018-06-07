#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mioji.common.spider import Spider,request,PROXY_REQ
from mioji.common.task_info import Task
from lxml import etree
import urllib

class HotelSpider(Spider):

    source_type = 'bestWestern'
    targets = {
        'Hotel':{'version':'InsertNewHotel'}
    }
    old_spider_tag = {
        'bestWesternHotel':{'required':['Hotel']}
    }

    def __init__(self,task=None):
        Spider.__init__(self,task=None)
        # self.task = task
        self.task_info = {} # 任务字典
        self.start_url = "https://www.bestwestern.net.cn/booking-path/searchhotel"
        self.city_id = None
        self.host_list = []



    def targets_request(self):
        # 解析任务
        if self.task is not None:
            self.process_task()
        @request(retry_count=4, proxy_type=PROXY_REQ, binding=self.parse_Hotel)
        def get_hotel_list():
            return {'req':{
                'url':self.start_url,
                'method':'get',
                'headers':{
                    'Cookie':'search_numberOfRooms={search_numberOfRooms};search_checkInDate={search_checkInDate}; search_checkOutDate={search_checkOutDate};search_numAdults={search_numAdults}; search_numChild={search_numChild};search_destination={search_destination};search_locationLat={search_locationLat}; search_locationLng={search_locationLng};'
                    .format(**self.task_info),
                    # 'Cookie':'search_numberOfRooms=1;search_checkInDate=2018-03-22;search_checkOutDate=2018-03-23;search_numAdults=1%2C1%2C1;search_numChild=0%2C0%2C0;search_destination=Berlin%2c+%e5%be%b7%e5%9b%bd;search_locationLat=52.5200066;search_locationLng=13.404954;'

                }
            }}

        return [get_hotel_list]

    # 解析任务
    def process_task(self):
        # 原始任务信息
        taskInfo = self.task.content+'&1&0&1'
        # 任务信息列表
        task_list = taskInfo.split("&") #['110'，柏林', '20180317', '2', '1', '0', '1']
        # 房间数
        search_numberOfRooms = task_list[6]
        # 入住日期
        search_checkInDate = task_list[2][:4]+"-"+task_list[2][4:6]+"-"+task_list[2][6:]
        # 退房日期
        search_checkOutDate = self.__get_checkOutDate(task_list[2],int(task_list[3]))
        # 成人数
        search_numAdults = self.__get_num_str(task_list[4])
        # 儿童数
        search_numChild = self.__get_num_str(task_list[5])
        # 地区
        search_destination = urllib.quote(task_list[1])
        # 纬度，经度
        search_locationLat,search_locationLng = self.__get_location(self.task.ticket_info)
        # city_id
        self.city_id = task_list[0]

        self.task_info = dict(
            search_numberOfRooms = search_numberOfRooms,
            search_checkInDate = search_checkInDate,
            search_checkOutDate = search_checkOutDate,
            search_numAdults = search_numAdults,
            search_numChild = search_numChild,
            search_destination = search_destination,
            search_locationLat = search_locationLat,
            search_locationLng = search_locationLng
        )


    # 解析酒店列表
    def parse_Hotel(self,req,resp):
        with open('1.html','w') as f:
            f.write(resp)
        # 酒店源
        source = 'bestwestern'

        html = etree.HTML(resp)
        root = html.xpath('//div[contains(@class,"searchResultsCard")]//div[@class="searchResultsCaption"]')

        for node in root:

            # 酒店所属来源
            hotelTypeDescription = node.xpath('./p[@class="hotelTypeDescription"]/a/text()')[0]
            # print hotelTypeDescription
            # 酒店所属地区
            hotelCityType = node.xpath('./p[@class="hotelTypeDescription"]/text()')[0]
            # print hotelCityType
            # 酒店名称
            hostName = node.xpath('./div[@class="hotelName"]/a/text()')[0]
            # print hostName
            # 酒店详情url
            hostURL = node.xpath('./div[@class="hotelName"]/a/@href')[0].encode('utf8')
            # print hostURL
            # 酒店id
            hostId = self.__getHostId(hostURL)
            # print hostId

            # 酒店信息
            host_info = tuple([
                source,
                hostId,
                self.city_id,
                hostURL
            ])

            self.host_list.append(host_info)
        print self.host_list

        return self.host_list

    # 获取退房日期
    # 参数：startDate 入住日期
    #      day 入住天数
    def __get_checkOutDate(self,startDate,day):
        # 入住年份
        checkInYear = startDate[:4]
        # 入住月份
        checkInMonth = startDate[4:6]
        # 入住日期
        checkInDate = startDate[6:]
        # 天数为31天的月份
        if checkInMonth in ['01','03','05','07','08','10','12']:
            if 31<int(checkInDate)+day<61:

                checkOutMonth = int(checkInMonth)+1
                if checkOutMonth>12:
                    # 退房年份
                    checkOutYear = str(int(checkInYear)+1)
                    checkOutMonth -= 12

                if checkOutMonth<10:
                    # 退房月份
                    checkOutMonth = '0'+str(checkOutMonth)
                else:
                    # 退房月份
                    checkOutMonth = str(checkOutMonth)

                checkOutDate = int(checkInDate+day-31)
                if checkOutDate<10:
                    # 退房日期
                    checkOutDate = '0'+str(checkOutDate)
                else:
                    # 退房日期
                    checkOutDate = str(checkOutDate)
            elif int(checkInDate)+day<31:
                checkOutYear = checkInYear
                checkOutMonth = checkInMonth
                checkOutDate = int(checkInDate)+day
                if checkOutDate<10:
                    checkOutDate = '0'+str(checkOutDate)
                else:
                    checkOutDate = str(checkOutDate)
        else:
            if 30 < int(checkInDate) + day < 61:

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
            elif int(checkInDate) + day < 30:
                checkOutYear = checkInYear
                checkOutMonth = checkInMonth
                checkOutDate = int(checkInDate) + day
                if checkOutDate < 10:
                    checkOutDate = '0' + str(checkOutDate)
                else:
                    checkOutDate = str(checkOutDate)
        checkOut = "-".join([checkOutYear,checkOutMonth,checkOutDate])

        return checkOut

    # 获取纬度，经度
    def __get_location(self,info):
        # db = WorkDB()
        # result = db.get_city_country()
        # # 经度，纬度
        # locationLng, locationLat = result.get(destination,"")[-1].split(",")
        # return locationLng,locationLat
        search_locationLng = info.get('locationLng')
        search_locationLat = info.get('locationLat')
        return search_locationLat,search_locationLng

    # 获得成人数（格式化后）
    def __get_num_str(self,num):
        a = ",".join(num * 3)  # a = '1,1,1'
        b = urllib.quote(a)   # b = '1%2C1%2C1'
        return b

    # 获取酒店id
    def __getHostId(self,url):
        hostId = url.split('/')[-1]
        return hostId


if __name__ == '__main__':
    task = Task()
    task.content = "110&Berlin, 德国&20180520&2"
    task.ticket_info = {'locationLng':13.404954,'locationLat':52.5200066}
    hotel_spider = HotelSpider()
    hotel_spider.task = task
    hotel_spider.crawl()