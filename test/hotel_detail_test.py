#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/22 下午6:39
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_detail_test.py
# @Software: PyCharm
from proj.hotel_tasks import hotel_base_data

if __name__ == '__main__':
    # hotel_base_data(source='booking',
    #                 url='http://www.booking.com/hotel/ma/assilah-marina-golf-assilah12.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ;sid=050b6a05c88840f3fd54bb8b9bf8cb62;checkin=2017-09-22;checkout=2017-09-23;ucfs=1;soh=1;srpvid=0f7c3351e00606b6;srepoch=1506064675;highlighted_blocks=;all_sr_blocks=;room1=A%2CA;soldout=0%2C0;hpos=12;hapos=72;dest_type=city;dest_id=-24680;srfid=15119f6b66615aadc25111e98e76dc3ad45ae212X72;from=searchresults;highlight_room=#no_availability_msg',
    #                 part='detail_hotel_booking_20170919a', other_info={
    #         'source_id': '2531377', 'city_id': '51511'
    #     }, country_id='NULL', task_name='detail_hotel_booking_20170919a', retry_count=0, max_retry_times=10)

    # hotel_base_data(source='hotels',
    #                 url='http://zh.hotels.com/ho381063/?pa=8&q-check-out=2017-12-16&tab=description&q-room-0-adults=2&YGF=14&q-check-in=2017-12-15&MGT=1&WOE=6&WOD=5&ZSX=0&SYE=3&q-room-0-children=0',
    #                 part='detail_hotel_hotels_20170925d', other_info={
    #         'source_id': '381063', 'city_id': 'NULL'
    #     },
    #                 country_id='NULL',
    #                 task_name='detail_hotel_hotels_20170925d',
    #                 retry_count=0,
    #                 max_retry_times=10)

    # hotel_base_data(source='hotels',
    #                 url='https://zh.hotels.com/ho677996/',
    #                 part='detail_hotel_hotels_20170925d', other_info={
    #         'source_id': '677996', 'city_id': 'NULL'
    #     },
    #                 country_id='NULL',
    #                 task_name='detail_hotel_hotels_20170925d',
    #                 retry_count=0,
    #                 max_retry_times=10)

    hotel_base_data(source='hotels',
                    url='http://zh.hotels.com/ho463739/?pa=1&q-check-out=2017-12-06&tab=description&q-room-0-adults=2&YGF=14&q-check-in=2017-12-05&MGT=1&WOE=3&WOD=2&ZSX=0&SYE=3&q-room-0-children=0',
                    part='detail_hotel_hotels_20170925d', other_info={
            'source_id': '463739', 'city_id': 'NULL'
        },
                    country_id='NULL',
                    task_name='detail_hotel_hotels_20170925d',
                    retry_count=0,
                    max_retry_times=10)
