#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年1月12日

@author: dujun
'''

import datetime
import re
from mioji.common.utils import setdefaultencoding_utf8
setdefaultencoding_utf8()

from mioji.common.spider import Spider, request, mioji_data, PROXY_FLLOW, PROXY_REQ

import agoda_parse

DATE_F = '%Y/%m/%d'


class agodaSpider(Spider):
    source_type = 'aogdaHotel'
    # 基础数据城市酒店列表 & 例行城市酒店
    targets = {
        'hotel': {},
        'room': {'version': 'InsertHotel_room3'}
    }
    # 设置上不上线 unable
    # unable = True
    # 关联原爬虫
    #   对应多个原爬虫
    old_spider_tag = {
        'agodaHotel': {'required': ['room']}
    }

    def process_content_info(self):
        cid = self.task.ticket_info.get('cid', None)
        taskcontent = self.task.content
        adult = self.task.ticket_info['room_info'][0].get('occ', 2)
        room_num = self.task.ticket_info['room_info'][0].get('num', 1)

        hotel_url, days, check_in_date = taskcontent.split('&')
        # 把http转为https，因为agoda统一转为HTTPS了，如果还是http会301导致cookie不可用。
        hotel_url_https = hotel_url.split(':')[0]
        if hotel_url_https[-1] == 'p':
            hotel_url_https += 's:'
            hotel_url = hotel_url_https + hotel_url.split(':')[1]
        check_in = str(check_in_date[:4]) + '-' + str(check_in_date[4:6]) + '-' + str(check_in_date[6:])
        check_out = str(datetime.datetime(int(check_in_date[:4]), int(check_in_date[4:6]),
                                          int(check_in_date[6:])) + datetime.timedelta(int(days)))[:10]
        self.user_datas['cid'] = cid
        self.user_datas['adult'] = adult
        self.user_datas['room_num'] = room_num
        self.user_datas['hotel_url'] = hotel_url
        self.user_datas['days'] = days
        self.user_datas['check_in_date'] = check_in_date
        self.user_datas['check_in'] = check_in
        self.user_datas['check_out'] = check_out
        search_url = hotel_url + '?checkin=' + check_in + '&los=' + days + '&adults=' + str(adult) + '&rooms=' + str(
            room_num) + '&cid=-1&currencyCode=CNY'  # &childs=0'
        return search_url
    def process_url_info(self):
        try:
            cid = self.task.ticket_info.get('cid', None)
            hotel_url = self.task.ticket_info.get('hotel_url', None)
            host_url, params_url = hotel_url.split('?')
            print host_url, params_url
            if self.task.ticket_info.get('checkin_date',None) and self.task.ticket_info.get('night',None):
                check_in_tmp = self.task.ticket_info['checkin_date']
                check_in = str(datetime.datetime(int(check_in_tmp[:4]),int(check_in_tmp[4:6]),int(check_in_tmp[6:])))[:10]
                days = self.task.ticket_info['night']
                check_out = str(datetime.datetime(int(check_in_tmp[:4]),int(check_in_tmp[4:6]),int(check_in_tmp[6:])) + datetime.timedelta(int(days)))[:10]
                adult = self.task.ticket_info.get('occ', '2')
                room_num = self.task.ticket_info.get('room_count', '1')
            else:
                params_list = params_url.split('&')
                for params in params_list:
                    if 'checkin' in params:
                        check_in = re.search(r'[\d]{4}-[\d]{2}-[\d]{2}', params).group(0)
                    elif 'los' in params:
                        days = re.search(r'[\d]+', params).group(0)
                    elif 'adults' in params:
                        adult = re.search(r'[\d]+', params).group(0)
                    elif 'rooms' in params:
                        room_num = re.search(r'[\d]+', params).group(0)
                check_out = str(
                    datetime.datetime(int(check_in[:4]), int(check_in[5:7]), int(check_in[8:])) + datetime.timedelta(
                        int(days)))[:10]
            self.user_datas['cid'] = cid
            self.user_datas['adult'] = adult
            self.user_datas['room_num'] = room_num
            self.user_datas['hotel_url'] = hotel_url
            self.user_datas['days'] = days
            self.user_datas['check_in_date'] = check_in
            self.user_datas['check_in'] = check_in
            self.user_datas['check_out'] = check_out
            search_url = host_url + '?checkin=' + check_in + '&los=' + days + '&adults=' + str(
                adult) + '&rooms=' + str(
                room_num) + '&cid=-1&currencyCode=CNY'  # &childs=0'
            return search_url
        except Exception as e:
            raise e

    def targets_request(self):
        self.hd = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip,deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8,und;q=0.6',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Content-Type':'application/x-www-form-urlencoded',
            'Host':'www.agoda.com',
            # 'Origin':'http://www.agoda.com',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
            'Cookie':'agoda.version.03=CookieId=41c7f3c1-b8c4-4bf8-a942-91f40ac73b9c&AllocId=9b27b0b9b51db16fa2f444202e6f8e2b1a5cc564355eb378db615fc6a8f04f85bc192cb176056b03049a0b93f0414c6e8228512f99abd9e347d2293f7d86a2687d6693ed175e214e55cf39aad64587264f18adf84641c7f3c1b8c4bf894291f40ac73b9c&DPN=1&DLang=zh-cn&CurLabel=CNY',
            'Upgrade-insecure-requests': '1',
        }
        print self.task.ticket_info
        if self.task.ticket_info.get('hotel_url', None):
            search_url = self.process_url_info()
        else:
            search_url = self.process_content_info()

        @request(retry_count=5, proxy_type=PROXY_REQ, binding=['room'])
        def get_city_page():
            url_get = search_url
            print url_get
            return {'req': {'url': url_get, 'headers': self.hd},
                    'data': {'content_type': 'string'},
                    }

        return [get_city_page]

    def parse_hotel(self, req, data):
        pass

    def parse_room(self, req, data):

        return agoda_parse.parse_page(data, self.user_datas['days'],
                                      self.user_datas['check_in'], self.user_datas['check_out'],
                                      self.user_datas['adult'], self.user_datas['cid'])


if __name__ == '__main__':
    from mioji.common.task_info import Task
    import json

    task = Task()
    task_list = [
        #'http://www.agoda.com/zh-cn/nala-individuellhotel/hotel/innsbruck-at.html&2&20171001',
        'https://www.agoda.com/zh-cn/best-western-plus-hotel-massena-nice/hotel/nice-fr.html&2&20180303',
    ]
    task.ticket_info= {
        'hotel_url':'https://www.agoda.com/zh-cn/royal-park-hotel-the-shiodome-tokyo/hotel/tokyo-jp.html?checkin=2017-08-21&los=1&adults=2&rooms=1&cid=-1&searchrequestid=3b462287-7643-4e86-b329-6f1734e0fe24',
        'night': '3',
        'checkin_date':'20171010',
        'cid':1
    }
    index = 0
    for t in task_list:
        print str(index) + '=' * 10
        index += 1
        task.content = t
        #task.ticket_info = {'cid': 1}
        import httplib
        httplib.HTTPConnection.debuglevel = 1
        httplib.HTTPSConnection.debuglevel = 1
    spider = agodaSpider()
    spider.task = task
    print spider.crawl()
    print spider.result
    # print spider.first_url()
