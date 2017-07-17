#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/13 下午11:11
# @Author  : Hou Rong
# @Site    : 
# @File    : tripadvisor_parser.py
# @Software: PyCharm
import sys
import re
import requests
import pyquery
import json
from data_obj import Hotel
from proj.my_lib.decode_raw_site import decode_raw_site

reload(sys)
sys.setdefaultencoding('utf-8')


def tripadvisor_parser(content, url, other_info):
    hotel = Hotel()
    doc = pyquery.PyQuery(content)

    hotel.hotel_name = hotel.hotel_name_en = doc('#HEADING').text()
    print 'hotel.hotel_name', hotel.hotel_name
    print 'hotel.hotel_name_en', hotel.hotel_name_en

    hotel.address = doc('.address').text()
    print 'hotel.address', hotel.address

    # tripadvisor 由于为请求过的页面不加载 meta 以下处理 map_info 完全失效
    # meta_location = doc('meta[name="location"]').attr('content')
    # map_info_temp = re.findall('\=(\d+\.\d+,\d+\.\d+)', meta_location)
    # if map_info_temp:
    #     hotel.map_info = map_info_temp[0]

    map_info_temp = re.findall("taStore\.store\(\'typeahead.recentHistoryList\',([\s\S]+?)\);", content)[0].strip()
    map_info_json = json.loads(map_info_temp)
    hotel.map_info = ','.join(map_info_json[0]['coords'].split(',')[::-1])
    print 'hotel.map_info', hotel.map_info

    # star 需要强制处理成 int ，即 floor 。
    star_temp = doc('.ui_star_rating').attr('class') or ''
    star_temp_list = re.findall('star_(\d+)', star_temp)
    if star_temp_list:
        hotel.star = int(star_temp_list[-1])
    else:
        hotel.star = -1

    # 对 tripadvisor 中出现的 star 大于 5 进行特殊处理
    if hotel.star > 5:
        if hotel.star % 5 == 0:
            hotel.star = int(hotel.star / 10)
        else:
            hotel.star = -1

    print 'hotel.star', hotel.star

    # grade float 值
    try:
        hotel.grade = float(doc('.overallRating').text())
    except Exception:
        hotel.grade = -1
    print 'hotel.grade', hotel.grade

    # 评论数 int 值
    review_temp = doc('.pagination-details').text().replace(',', '').replace('，', '')
    review_temp_list = re.findall('(\d+)', review_temp)
    if review_temp_list:
        hotel.review_num = int(review_temp_list[-1])
    else:
        hotel.review_num = -1
    print 'hotel.review_num', hotel.review_num

    #  酒店服务解析
    hotel.service = '|'.join(
        map(lambda x: x.text(), doc('.ui_columns.section_content .item:not([class*="title"])').items()))
    if not hotel.service:
        hotel.service = 'NULL'
    print 'hotel.service', hotel.service

    # 酒店图片采用 POI 部分抓取此处不处理
    hotel.img_items = 'NULL'
    print 'hotel.img_items', hotel.img_items

    # 由于简介暂时没有存内容，暂存 website_url
    raw_encode_website_str = doc('.blEntry.website').attr('data-ahref')
    if raw_encode_website_str:
        raw_tripadvisor_url = decode_raw_site(raw_encode_website_str)
        hotel.description = raw_tripadvisor_url
    else:
        hotel.description = 'NULL'

    print 'hotel.description', hotel.description

    hotel.source = 'tripadvisor'

    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    other_info = {
        'source_id': '119538',
        'city_id': '10001'
    }
    # url = 'https://www.tripadvisor.cn/Hotel_Review-g143034-d282791-Reviews-Volcano_House-Hawaii_Volcanoes_National_Park_Island_of_Hawaii_Hawaii.html'
    # url = 'https://www.tripadvisor.cn/Hotel_Review-g187147-d265476-Reviews-Hotel_de_Londres_Eiffel-Paris_Ile_de_France.html'
    # url = 'https://www.tripadvisor.cn/Hotel_Review-g187147-d7182695-Reviews-Maison_Souquet-Paris_Ile_de_France.html'
    # url = 'https://www.tripadvisor.cn/Hotel_Review-g293974-d7053739-Reviews-Business_Life_Boutique_Hotel-Istanbul.html'
    url = 'https://cn.tripadvisor.com/Hotel_Review-g187147-d6882422-Reviews-Hotel_du_Mont_Louis-Paris_Ile_de_France.html'
    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = tripadvisor_parser(content, url, other_info)
