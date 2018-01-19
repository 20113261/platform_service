#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/22 下午6:39
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_detail_test.py
# @Software: PyCharm
import sys

sys.path.append('/data/lib')
from proj.my_lib.Common.Task import Task
from proj.total_tasks import hotel_detail_task
from MongoTaskInsert import TaskType

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

    # task = Task(_worker='', _task_id='demo', _source='booking', _type='hotel',
    #             _task_name='detail_hotel_hotels_20170925d',
    #             _used_times=0, max_retry_times=10,
    #             kwargs={'source': 'hotels',
    #                     'url': 'https://zh.hotels.com/ho635577984/',
    #                     'part': 'detail_hotel_hotels_20170925d',
    #                     'source_id': '635577984',
    #                     'city_id': 'NULL',
    #                     'country_id': 'NULL'})

    # task = Task(_worker='', _queue='hotel_detail', _routine_key='hotel_detail', _task_id='demo', _source='hotels',
    #             _type='hotel',
    #             _task_name='detail_hotel_hotels_20170928d',
    #             _used_times=0, max_retry_times=10,
    #             # kwargs={
    #             #     'source': 'hotels',
    #             #     'url': 'http://zh.hotels.com/ho691218/?pa=6&tab=description&ZSX=0&SYE=3&q-room-0-children=0&q-room-0-adults=2',
    #             #     'part': 'detail_hotel_hotels_20170928d',
    #             #     'source_id': '691218',
    #             #     'city_id': 'NULL',
    #             #     'country_id': 'NULL'
    #             # },
    #             kwargs={
    #                 "url": "http://www.booking.com\n/hotel/ph/tg-hometel.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=3b827f3aa2e3fca0a95ec0d56605f64a;checkin=2018-01-08;checkout=2018-01-11;ucfs=1;soh=1;srpvid=511e686ec99000f9;srepoch=1511448670;highlighted_blocks=;all_sr_blocks=;room1=A%2CA;soldout=0%2C0;hpos=10;hapos=520;dest_type=region;dest_id=5374;srfid=0a39626563bec2b30fbbedccb1438d4e5f55493fX520;from=searchresults;soldout_clicked=1\n;highlight_room=#no_availability_msg",
    #                 "country_id": "NULL", "source": "booking", "part": "detail_hotel_booking_20171122a",
    #                 "city_id": "NULL", "source_id": "1878253"},
    #             task_type=TaskType.NORMAL, list_task_token=None)
    #
    # print(hotel_detail_task(task=task))

    # task = Task(_worker='', _queue='hotel_detail', _routine_key='hotel_detail', _task_id='demo', _source='hotels',
    #             _type='hotel',
    #             _task_name='detail_hotel_holiday_20171226a',
    #             _used_times=0, max_retry_times=10,
    #             kwargs={
    #                 # "url": "http://www.booking.com\n/hotel/ph/tg-hometel.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=3b827f3aa2e3fca0a95ec0d56605f64a;checkin=2018-01-08;checkout=2018-01-11;ucfs=1;soh=1;srpvid=511e686ec99000f9;srepoch=1511448670;highlighted_blocks=;all_sr_blocks=;room1=A%2CA;soldout=0%2C0;hpos=10;hapos=520;dest_type=region;dest_id=5374;srfid=0a39626563bec2b30fbbedccb1438d4e5f55493fX520;from=searchresults;soldout_clicked=1\n;highlight_room=#no_availability_msg",
    #                 "url": "https://www.ihg.com/holidayinnexpress/hotels/cn/zh/teluk/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/TELUK/details",
    #                 "country_id": "NULL",
    #                 "source": "holiday",
    #                 "part": "detail_hotel_holiday_20171226a",
    #                 "city_id": "NULL",
    #                 "source_id": "ABYSY"
    #             },
    #             task_type=TaskType.NORMAL, list_task_token=None)
    #
    # print(hotel_detail_task(task=task))

    task = Task(_worker='', _queue='hotel_detail', _routine_key='hotel_detail', _task_id='demo', _source='holiday',
                _type='hotel',
                _task_name='detail_hotel_ctrip_20171127a',
                _used_times=0, max_retry_times=10,
                kwargs={
                    # "url": "http://www.booking.com\n/hotel/ph/tg-hometel.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBA-gBAZICAXmoAgQ;sid=3b827f3aa2e3fca0a95ec0d56605f64a;checkin=2018-01-08;checkout=2018-01-11;ucfs=1;soh=1;srpvid=511e686ec99000f9;srepoch=1511448670;highlighted_blocks=;all_sr_blocks=;room1=A%2CA;soldout=0%2C0;hpos=10;hapos=520;dest_type=region;dest_id=5374;srfid=0a39626563bec2b30fbbedccb1438d4e5f55493fX520;from=searchresults;soldout_clicked=1\n;highlight_room=#no_availability_msg",
                    # "url": "https://www.ihg.com/holidayinnexpress/hotels/cn/zh/teluk/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/TELUK/details",
                    # "url": "https://www.expedia.com.hk/Bhimtal-Hotels-Emerald-Trail.h4474316.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=6139790&sort=recommended&hwrqCacheKey=b07edfbf-68f1-472b-b58d-d153dc82d7feHWRQ1511794413272&vip=false&c=c8d5ec02-71e2-496b-aa9f-5988e64b7931&",
                    # "url": "https://www.booking.com/hotel/us/new-lakefront-home-4br-47-2b-in-katy-west-houston.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=760b4b8ac503b49f5d89e67ec36a2fa9;aer=1;dest_id=20126498;dest_type=city;dist=0;hapos=90;hpos=15;room1=A%2CA;sb_price_type=total;spdest=ci%2F20126498;spdist=41.0;srepoch=1511794977;srfid=75643f0d9b7ac3fe31b60ecc58ba9f10b377fd16X90;srpvid=fdcc69d0f9a606d5;type=total;ucfs=1&#hotelTmpl",
                    # "url": "https://www.expedia.com.hk/Hotels-Beautiful.h19200665.Hotel-Information",
                    "url": "https://www.ihg.com/holidayinnexpress/hotels/cn/zh/dalpw/hoteldetail#####https://apis.ihg.com/hotels/v1/profiles/DALPW/details",
                    "country_id": "NULL",
                    "source": "holiday",
                    "part": "detail_hotel_marriott_20170109a",
                    "city_id": "10011",
                    "source_id": "BMGCY"
                },
                task_type=TaskType.NORMAL, list_task_token=None)

    print(hotel_detail_task(task=task))
