#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月19日

@author: dujun
'''

import datetime
from mioji.common.spider import Spider, request, PROXY_REQ

FORMAT_URL = 'http://www.booking.com/{0}.zh-cn.html?checkin={1};checkout={2};selected_currency=CNY;{3}'


class BookingHotelDetailSpider(Spider):
    
    __type = 'hotelDetail'
    # 基础数据城市酒店列表 & 例行城市酒店
    __targets_version = {
        'hotelDetail_room':{'version':'InsertHotel_room4'}
        }
    __targets = __targets_version.keys()
    # 关联原爬虫
    #   对应多个原爬虫
    __old_spider_tag = {
        'booking':{'required':['hotelDetail_room']}
        }
    
    def old_spider_tag(self):
        return BookingHotelDetailSpider.__old_spider_tag
    
    def crawl_type(self):
        return BookingHotelDetailSpider.__type
    
    def targets_parser(self):
        return BookingHotelDetailSpider.__targets
    
    def parser_targets_version(self):
        return BookingHotelDetailSpider.__targets_version
        
    def targets_request(self):
        taskcontent = '1301473&hotel/us/sweetwater-inn&1&20170102'
        info_list = taskcontent.split('&')
        
        _, name, nights, check_in_temp = info_list[0], info_list[1], info_list[2], info_list[3]

        check_in = check_in_temp[:4] + '-' + check_in_temp[4:6] + '-' + check_in_temp[6:]
        check_out_temp = datetime.datetime(int(check_in_temp[:4]), int(check_in_temp[4:6]), int(check_in_temp[6:]))
        check_out = str(check_out_temp + datetime.timedelta(days=int(nights)))[:10]
        
        peoples = 2
        room_num = 1
        info = 'req_adults={0};no_rooms={1}'.format(peoples, room_num)
#         if len(info_list) > 4:
#             info = get_info(info_list[4:])
        url = FORMAT_URL.format(name, check_in, check_out, info)
        
        @request(retry_count=3, proxy_type=PROXY_REQ)
        def detail():
            return {
                    'req':
                        {'method':'GET',
                        'url':url,
                        'params':None
                        },
                    'data':{'key':'page:0', 'remove':'auto', 'content_type':'html'},
                    'parser_bind':[self.parse_hotelDetail_room ]
                    } 
            
        return [detail]
    
    def parse_hotelDetail_room(self, req, data):
        print 'parse', data
        return ['test_room']


if __name__ == '__main__':
    class T(object):
        def __init__(self):
            self.source = 'booking'
            
    spider = BookingHotelDetailSpider(T())
    spider.crawl()