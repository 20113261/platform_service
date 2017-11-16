#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:24
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_list_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import hotel_list_task

if __name__ == '__main__':
    # hotel_list_task('booking', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")
    # hotel_list_task('agoda', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")
    # hotel_list_task('ctrip', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")
    # hotel_list_task('expedia', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")
    # hotel_list_task('hotels', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")
    # hotel_list_task('elong', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")

    # source, city_id, country_id, check_in, part, is_new_type=False, suggest_type='1', suggest='',

    # hotel_list_task('expedia', '51211', '501', '20171102', 'test', task_name="list_hotel_test_test")

    # hotel_list_task(
    #     source='expedia',
    #     city_id='51211',
    #     country_id='501',
    #     check_in='20171102',
    #     part='test',
    #     is_new_type=True,
    #     suggest_type=1,
    #     suggest='https://www.expedia.com.hk/Hotel-Search?destination=%E7%93%A6%E5%8A%A0%E7%93%A6%E5%8A%A0%2C+%E6%96%B0%E5%8D%97%E5%A8%81%E7%88%BE%E6%96%AF%2C+%E6%BE%B3%E6%B4%B2&startDate=&endDate=&rooms=1&_xpid=11905%7C1&adults=2',
    #     task_name="list_hotel_test_test"
    # )
    pass

    # print(app.send_task(
    #     'proj.hotel_list_task.hotel_list_task',
    #     args=('booking', '51211', '501', '20171102', 'test'),
    #     kwargs=dict(task_name="list_hotel_booking_test", max_retry_times=10, retry_count=0),
    #     queue='hotel_list_task',
    #     routing_key='hotel_list_task'
    # ))

    # hotel_list_task('booking', '51211', '501', '20171102', 'test', True,
    #                 'https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ&sid=0ea0496158c9e121ffca9a093df19a8b&sb=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ%3Bsid%3D0ea0496158c9e121ffca9a093df19a8b%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF%2C+%E5%9F%83%E6%96%AF%E7%89%B9%E9%9B%B7%E9%A9%AC%E6%9D%9C%E6%8B%89%2C+%E8%A5%BF%E7%8F%AD%E7%89%99&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=1&group_adults=2&group_children=0&from_sf=1&ss_raw=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF&ac_position=0&ac_langcode=zh&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&search_pageview_id=01b6118bfa020346&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0')
    # print(app.send_task(
    #     'proj.hotel_list_task.hotel_list_task',
    #     args=('booking', '321321', '2333', '20171102', 'test', True,
    #           'https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ&sid=0ea0496158c9e121ffca9a093df19a8b&sb=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ%3Bsid%3D0ea0496158c9e121ffca9a093df19a8b%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF%2C+%E5%9F%83%E6%96%AF%E7%89%B9%E9%9B%B7%E9%A9%AC%E6%9D%9C%E6%8B%89%2C+%E8%A5%BF%E7%8F%AD%E7%89%99&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=1&group_adults=2&group_children=0&from_sf=1&ss_raw=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF&ac_position=0&ac_langcode=zh&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&search_pageview_id=01b6118bfa020346&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0'),
    #     kwargs=dict(task_name="list_hotel_booking_test", max_retry_times=10, retry_count=0),
    #     queue='hotel_list_task',
    #     routing_key='hotel_list_task'
    # ))

    # hotel_list_task(
    #     source='ctrip',
    #     city_id='TEST',
    #     country_id='TEST',
    #     check_in='20171125',
    #     part='test',
    #     is_new_type=True,
    #     suggest_type=1,
    #     suggest='http://hotels.ctrip.com/international/brianon22797',
    #     task_name="list_hotel_test_test",
    # )

    # hotel_list_task(
    #     source='ctrip',
    #     city_id='TEST',
    #     country_id='TEST',
    #     check_in='20171006',
    #     part='test',
    #     is_new_type=True,
    #     suggest_type=1,
    #     suggest='http://hotels.ctrip.com/international/brianon22797',
    #     task_name="list_hotel_test_test",
    #     retry_count=0,
    #     max_retry_times=6
    # )

    # hotel_list_task(
    #     source='hotels',
    #     city_id='NULL',
    #     country_id='205',
    #     check_in='20171228',
    #     part='20170929a',
    #     is_new_type=True,
    #     suggest_type=2,
    #     suggest='''{"caption": "\u96f7\u76ae\u4e9a, \u70ed\u90a3\u4e9a\uff08\u7701\uff09, \u610f\u5927\u5229 (<span class='highlighted'>Reppia</span>)", "destinationId": "10368135", "name": "\u96f7\u76ae\u4e9a", "latitude": 44.366699, "landmarkCityDestinationId": null, "type": "CITY", "redirectPage": "DEFAULT_PAGE", "longitude": 9.45, "geoId": "1000000000006360769"}''',
    #     task_name="list_hotel_test_test",
    #     retry_count=0,
    #     max_retry_times=6
    # )


    # print(hotel_list_task(
    #     source='hotels',
    #     city_id='NULL',
    #     country_id='238',
    #     check_in='20171128',
    #     part='20170929a',
    #     is_new_type=True,
    #     suggest_type=2,
    #     suggest='''{"caption": "\u7d22\u5c14\u5361, \u7f57\u9a6c\u5c3c\u4e9a (<span class='highlighted'>Solca</span>)", "destinationId": "10383790", "name": "\u7d22\u5c14\u5361", "latitude": 47.700001, "landmarkCityDestinationId": null, "type": "CITY", "redirectPage": "DEFAULT_PAGE", "longitude": 25.85, "geoId": "1000000000006374000"}''',
    #     task_name="list_hotel_test_test",
    #     retry_count=2,
    #     max_retry_times=6
    # ))

    '''
    
    '''
    # print(hotel_list_task(
    #     source='ctrip',
    #     city_id='NULL',
    #     country_id='238',
    #     check_in='20171218',
    #     part='20170929a',
    #     is_new_type=1,
    #     suggest_type=2,
    #     suggest='''SantAlbino|桑塔比诺，托斯卡纳大区，意大利|city|33376|santalbino|33376|santalbino|桑塔比诺|8|0||3600''',
    #     task_name="list_hotel_test_test",
    #     retry_count=2,
    #     max_retry_times=6,
    #     task_response=TaskResponse()
    # ))

    # print(hotel_list_task(
    #     source='booking',
    #     city_id='NULL',
    #     country_id='205',
    #     check_in='20171019',
    #     part='20170929a',
    #     is_new_type=1,
    #     suggest_type=2,
    #     suggest='''{"label_highlighted": "\u5a01\u5c3c\u65af, \u5a01\u5c3c\u6258\u5927\u533a, \u610f\u5927\u5229", "label_cjk": "<span class='search_hl_cjk'>\u5a01\u5c3c\u65af</span> <span class='search_hl_cjk'>\u5a01\u5c3c\u6258\u5927\u533a</span>, <span class='search_hl_cjk'>\u610f\u5927\u5229</span>", "__part": 0, "lc": "zh", "genius_hotels": "379", "rtl": 0, "hotels": "1953", "dest_id": "-132007", "cc1": "it", "label_multiline": "<span>\u5a01\u5c3c\u65af</span> \u5a01\u5c3c\u6258\u5927\u533a, \u610f\u5927\u5229", "nr_hotels_25": "3119", "_ef": [{"name": "ac_popular_badge", "value": 1}], "labels": [{"text": "\u5a01\u5c3c\u65af", "required": 1, "type": "city", "hl": 1}, {"text": "\u5a01\u5c3c\u6258\u5927\u533a", "required": 1, "type": "region", "hl": 1}, {"text": "\u610f\u5927\u5229", "required": 1, "type": "country", "hl": 1}], "__query_covered": 9, "flags": {"popular": 1}, "nr_hotels": "1953", "city_ufi": null, "label": "\u5a01\u5c3c\u65af, \u5a01\u5c3c\u6258\u5927\u533a, \u610f\u5927\u5229", "type": "ci", "dest_type": "city", "region_id": "914"}''',
    #     task_name="list_hotel_test_test",
    #     retry_count=2,
    #     max_retry_times=6
    # ))

    # print(hotel_list_task(
    #     source='booking',
    #     city_id='NULL',
    #     country_id='205',
    #     check_in='20171128',
    #     part='20170929a',
    #     is_new_type=1,
    #     suggest_type=1,
    #     suggest='''http://www.booking.com/searchresults.zh-cn.html?label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985:pl:ta:p1:p2:ac:ap1t1:neg:fi:tikwd-11455299683:lp9061505:li:dec:dm&sid=2fabc4030e6b847b9ef3b059e24c6b83&aid=376390&error_url=http://www.booking.com/index.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8ba5e9abe3eb9fcadf8e837d4d5a2464;sb_price_type=total&;&ss=Saint-Martial-de-Nabirat&ssne=Saint-Martial-de-Nabirat&ssne_untouched=Saint-Martial-de-Nabirat&dest_id=-1466961&dest_type=city&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=&group_adults=&group_children=0&from_sf=1ss=Saint-Martial-de-Nabirat&ssne=Saint-Martial-de-Nabirat&ssne_untouched=Saint-Martial-de-Nabirat&dest_id=-1466961&dest_type=city&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=&group_adults=&group_children=0&from_sf=1''',
    #     task_name="list_hotel_booking_20170929a",
    #     retry_count=2,
    #     max_retry_times=6
    # ))
    task = Task(_worker='', _task_id='demo', _source='booking', _type='hotel_list',
                _task_name='list_hotel_booking_20170929a',
                _used_times=0, max_retry_times=6,
                kwargs={'source': 'booking',
                        'city_id': 'NULL',
                        'country_id': '205',
                        'check_in': '20171128',
                        'part': '20170929a',
                        'is_new_type': 1,
                        'suggest_type': 1,
                        'suggest': '''https://www.booking.com/searchresults.zh-cn.html?label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985:pl:ta:p1:p2:ac:ap1t1:neg:fi:tikwd-11455299683:lp9061505:li:dec:dm&sid=2fabc4030e6b847b9ef3b059e24c6b83&aid=376390&error_url=http://www.booking.com/index.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8ba5e9abe3eb9fcadf8e837d4d5a2464;sb_price_type=total&;&ss=%E9%A9%AC%E8%90%A8%E5%A5%A5&ssne=%E9%A9%AC%E8%90%A8%E5%A5%A5&ssne_untouched=%E9%A9%AC%E8%90%A8%E5%A5%A5&dest_id=900048165&dest_type=city&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=&group_adults=&group_children=0&from_sf=1ss=%E9%A9%AC%E8%90%A8%E5%A5%A5&ssne=%E9%A9%AC%E8%90%A8%E5%A5%A5&ssne_untouched=%E9%A9%AC%E8%90%A8%E5%A5%A5&dest_id=900048165&dest_type=city&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=&group_adults=&group_children=0&from_sf=1''', })

    print(hotel_list_task(task=task))
