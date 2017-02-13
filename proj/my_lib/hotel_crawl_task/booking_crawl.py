#! /usr/bin/env python
# coding=utf-8
from __future__ import absolute_import

import urllib
from datetime import *

import re
import requests
from common.common import get_proxy
from lxml import html as HTML
from util.UserAgent import GetUserAgent

from .data_obj import Task, HotelCrawl, DBSession

reload(sys)
sys.setdefaultencoding('utf-8')

hotelcount_pat = re.compile(r'\d+')


def is_alp(a):
    if 'a' <= a <= 'z':
        return True
    elif 'A' <= a <= 'Z':
        return True
    else:
        return False


def get_time():
    date1 = date.today()
    s_day = date1 + timedelta(days=2)
    s_nian = s_day.year
    s_yue = s_day.month
    s_ri = s_day.day
    e_day = s_day + timedelta(days=3)
    e_nian = e_day.year
    e_yue = e_day.month
    e_ri = e_day.day

    return s_nian, s_yue, s_ri, e_nian, e_yue, e_ri


def booking_list_crawl(task):
    # 将任务进行拆分，拆分成该源上的城市中文名和城市id
    # eg :黄石国家公园西门&6406&region , 大雾山国家公园&255516&landmark
    # eg: 福森&-1773182
    # 任务类型, city, region, landmark
    city_name_zh, source_city_id, search_type = task.content.encode('utf8').split('&')

    # 对城市中文名进行编码
    city_name_zh = urllib.quote(city_name_zh)

    check_in_year = task.check_in[0:7]
    check_in_day = task.check_in[8:]
    check_out_year = task.check_out[0:7]
    check_out_day = task.check_out[8:]

    # 对首页url进行拼接
    # url = get_search_url(check_in, check_out, source_city_id, city_name_zh, 1)
    # 注意！！！！！！大部分抓的dest_type都是city，黄石国家公园西门是region, 大雾山国家公园大峡谷国家公园都是landmark

    Id = source_city_id
    dest_type = search_type
    destination = city_name_zh

    if is_alp(Id[0]):
        url = 'http://www.booking.com/searchresults.zh-cn.html?aid=397647;label=bai408jc-index-XX-XX-XX-unspec-cn-com-L%3Azh-O%3Aabn-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo;sid=4cb8e58619e9a15fe212e5b9fbec271b;dcid=12;checkin_monthday=' + check_in_day + ';checkin_year_month=' + check_in_year + ';checkout_monthday=' + check_out_day + ';checkout_year_month=' + check_out_year + ';class_interval=1;dest_id=' + Id + ';dest_type=' + dest_type + ';dtdisc=0;group_adults=2;group_children=0;hlrd=0;hyb_red=0;inac=0;label_click=undef;nha_red=0;no_rooms=1;offset=0;postcard=0;qrhpp=9f9582988e3752a8d34a7f85874afc39-city-0;redirected_from_city=0;redirected_from_landmark=0;redirected_from_region=0;review_score_group=empty;room1=A%2CA;sb_price_type=total;score_min=0;src=index;src_elem=sb;ss=' + destination + ';ss_all=0;ss_raw=' + destination + ';ssb=empty;sshis=0;origin=search;srpos=1&place_id=' + Id
    else:
        url = 'http://www.booking.com/searchresults.zh-cn.html?aid=397647;label=bai408jc-index-XX-XX-XX-unspec-cn-com-L%3Azh-O%3Aabn-B%3Achrome-N%3Ayes-S%3Abo-U%3Asalo;sid=4cb8e58619e9a15fe212e5b9fbec271b;dcid=12;checkin_monthday=' + check_in_day + ';checkin_year_month=' + check_in_year + ';checkout_monthday=' + check_out_day + ';checkout_year_month=' + check_out_year + ';class_interval=1;dest_id=' + Id + ';dest_type=' + dest_type + ';dtdisc=0;group_adults=2;group_children=0;hlrd=0;hyb_red=0;inac=0;label_click=undef;nha_red=0;no_rooms=1;offset=0;postcard=0;qrhpp=9f9582988e3752a8d34a7f85874afc39-city-0;redirected_from_city=0;redirected_from_landmark=0;redirected_from_region=0;review_score_group=empty;room1=A%2CA;sb_price_type=total;score_min=0;src=index;src_elem=sb;ss=' + destination + ';ss_all=0;ss_raw=' + destination + ';ssb=empty;sshis=0;origin=search;srpos=1'

    print url, '================='
    PROXY = get_proxy(source="Platform")
    headers = {
        'User-agent': GetUserAgent()
    }
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    page = requests.get(url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    content = page.text
    root = HTML.fromstring(content)
    hotel = root.xpath('//*[@class="sr_header "]/h1/text()')[0].encode('utf-8').replace(',', '').strip()
    # print hotel
    # 获取酒店数，获取的当前时间内有空房的酒店数
    # 有两个数时取后面的数
    temp_count = hotelcount_pat.findall(hotel)
    hotel_count = temp_count[-1]
    crawl_page = int(hotel_count) / 15 + 1
    # todo data crawl
    # 对首页进行数据爬取
    # parse_each_page(page, city_id, continent)

    result = list()
    result.append(url)
    # 开始进行翻页
    for page_index in range(1, crawl_page):
        offset = 14 + (page_index - 1) * 15
        each_page_url = get_search_url(task.check_in, task.check_out, source_city_id, city_name_zh, offset, search_type)
        result.append(each_page_url)

    return result


def booking_detail_crawl(url, task):
    PROXY = get_proxy(source="Platform")
    headers = {
        'User-agent': GetUserAgent()
    }
    proxies = {
        'http': 'socks5://' + PROXY,
        'https': 'socks5://' + PROXY
    }
    page = requests.get(url, proxies=proxies, headers=headers)
    page.encoding = 'utf8'
    content = page.text
    root = HTML.fromstring(content)
    session = DBSession()
    hotel_element_list = root.get_element_by_id('hotellist_inner').xpath('div')
    for hotel in hotel_element_list:
        try:
            hotel_crawl = HotelCrawl()
            hotel_crawl.source_id = hotel.xpath('@data-hotelid')[0]
            hotel_crawl.source = 'booking'
            hotel_url = hotel.find_class('hotel_name_link')[0].xpath('@href')[0]
            hotel_crawl.hotel_url = 'http://www.booking.com' + hotel_url.split('?sid')[0]
            hotel_crawl.city_id = task.city_id
            hotel_crawl.flag = task.flag
            session.merge(hotel_crawl)
        except Exception, e:
            print str(e)
    session.commit()
    session.close()


def get_search_url(check_in, check_out, source_city_id, city_name_zh, offset, search_type):
    # 获取翻页的链接
    check_in_yearmonth = check_in[:7]
    check_in_day = check_in[-2:]

    check_out_yearmonth = check_out[:7]
    check_out_day = check_out[-2:]

    offset = str(offset)
    city_name_zh = urllib.quote(city_name_zh)

    search_url = 'http://www.booking.com/searchresults.zh-cn.html?;dcid=1' + \
                 ';checkin_monthday=' + check_in_day + \
                 ';checkin_year_month=' + check_in_yearmonth + \
                 ';checkout_monthday=' + check_out_day + \
                 ';checkout_year_month=' + check_out_yearmonth + \
                 ';' + search_type + '=' + source_city_id + \
                 ';class_interval=1;csflt={};' + \
                 ';no_rooms=1;' + \
                 'review_score_group=empty;score_min=0;si=ai,' + \
                 'co,ci,re,di;src=searchresults;ssb=empty' + \
                 ';ssne_untouched=' + city_name_zh + \
                 ';origin=disamb_sr' + \
                 ';rows=15;offset=' + offset

    return search_url


# @shared_task()
# def send_task(it, callback):
#     callback = subtask(callback)
#     return group(callback.clone([arg, ]) for arg in it)()
#
#
# @shared_task()
# def echo(it):
#     print it
#
#
# def booking_crawl_chain(task):
#     # chain = (fetch_get_url.s(url) | parse_total.s() | send_task.s(fetch_get_url.s()))
#     chain = (booking_list_crawl.s(task=task) | send_task.s(echo.s()))
#     chain()


if __name__ == '__main__':
    task = Task()
    task.city_id = '10001'
    task.content = '巴黎&-1456928&city'
    # task.content = '敦刻尔克&-1424668&city'
    # task.content = '多维尔&-1423684&city'
    # task.content = '尤拉拉&ChIJPz2rao9AIysRAIUkKqgXAgQ&city'
    task.check_in = '2015-10-16'
    task.check_out = '2015-10-18'
    task.flag = 'test_booking'
    booking_list_crawl.delay(task=task)
    # booking_crawl_chain(task=task)
    # booking_list_crawl(task=task)
    # target_url = 'http://www.booking.com/searchresults.zh-cn.html?;dcid=1;checkin_monthday=16;checkin_year_month=2015-10;checkout_monthday=18;checkout_year_month=2015-10;city=-1456928;class_interval=1;csflt={};;no_rooms=1;review_score_group=empty;score_min=0;si=ai,co,ci,re,di;src=searchresults;ssb=empty;ssne_untouched=%25E5%25B7%25B4%25E9%25BB%258E;origin=disamb_sr;rows=15;offset=14'
    # booking_detail_crawl(target_url, task=task)
