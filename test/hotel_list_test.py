#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 下午2:24
# @Author  : Hou Rong
# @Site    : 
# @File    : hotel_list_test.py
# @Software: PyCharm
from proj.celery import app

from proj.hotel_list_task import hotel_list_task

if __name__ == '__main__':
    # hotel_list_task('booking', '10001', '501', '20171102', 'test', task_name="list_hotel_booking_test")

    # print(app.send_task(
    #     'proj.hotel_list_task.hotel_list_task',
    #     args=('booking', '51211', '501', '20171102', 'test'),
    #     kwargs=dict(task_name="list_hotel_booking_test", max_retry_times=10, retry_count=0),
    #     queue='hotel_list_task',
    #     routing_key='hotel_list_task'
    # ))

    # hotel_list_task('booking', '51211', '501', '20171102', 'test', True,
    #                 'https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ&sid=0ea0496158c9e121ffca9a093df19a8b&sb=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ%3Bsid%3D0ea0496158c9e121ffca9a093df19a8b%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF%2C+%E5%9F%83%E6%96%AF%E7%89%B9%E9%9B%B7%E9%A9%AC%E6%9D%9C%E6%8B%89%2C+%E8%A5%BF%E7%8F%AD%E7%89%99&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=1&group_adults=2&group_children=0&from_sf=1&ss_raw=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF&ac_position=0&ac_langcode=zh&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&search_pageview_id=01b6118bfa020346&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0')
    print(app.send_task(
        'proj.hotel_list_task.hotel_list_task',
        args=('booking', '321321', '2333', '20171102', 'test', True,
              'https://www.booking.com/searchresults.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ&sid=0ea0496158c9e121ffca9a093df19a8b&sb=1&src=index&src_elem=sb&error_url=https%3A%2F%2Fwww.booking.com%2Findex.zh-cn.html%3Flabel%3Dgen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ%3Bsid%3D0ea0496158c9e121ffca9a093df19a8b%3Bsb_price_type%3Dtotal%26%3B&ss=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF%2C+%E5%9F%83%E6%96%AF%E7%89%B9%E9%9B%B7%E9%A9%AC%E6%9D%9C%E6%8B%89%2C+%E8%A5%BF%E7%8F%AD%E7%89%99&checkin_year=&checkin_month=&checkin_monthday=&checkout_year=&checkout_month=&checkout_monthday=&no_rooms=1&group_adults=2&group_children=0&from_sf=1&ss_raw=%E5%B7%B4%E8%BE%BE%E9%9C%8D%E6%96%AF&ac_position=0&ac_langcode=zh&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&dest_id=-372124&dest_type=city&search_pageview_id=01b6118bfa020346&search_selected=true&search_pageview_id=01b6118bfa020346&ac_suggestion_list_length=5&ac_suggestion_theme_list_length=0'),
        kwargs=dict(task_name="list_hotel_booking_test", max_retry_times=10, retry_count=0),
        queue='hotel_list_task',
        routing_key='hotel_list_task'
    ))
