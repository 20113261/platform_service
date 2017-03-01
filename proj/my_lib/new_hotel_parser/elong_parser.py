#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf-8')

map_pat = re.compile(r'center=(.*?),(.*?)&', re.S)
num_pat = re.compile(r'\d+', re.S)
hotel_id_pat = re.compile(r'HotelId":(.*?),"HotelLowestPrice', re.S)
grade_pat = re.compile(r'(\d+)', re.S)


def elong_parser(content, url, other_info):
    hotel = Hotel()

    try:
        root = HTML.fromstring(content.decode('utf-8'))
    except Exception, e:
        print str(e)
        # return hotel

    # 解析酒店中英文名，如果没有中文名则置为英文名，如果都解析失败则退出
    try:
        temp_name = root.find_class('t24 yahei')[0].xpath('./text()')[0].strip().encode('utf-8')
        k = temp_name.find('(')
        j = temp_name.find(')')
        hotel.hotel_name = temp_name[:k]
        hotel.hotel_name_en = temp_name[k + 1:j]
    except Exception, e:
        print str(e)
        # return hotel_tuple

    print 'hotel.hotel_name'
    print hotel.hotel_name
    print 'hotel.hotil_name_en'
    print hotel.hotel_name_en

    print 'brand'
    print hotel.brand_name

    # 解析酒店地址
    try:
        hotel.address = root.find_class('mr5 left')[0].xpath('./text()')[0].strip().encode('utf-8')
    except:
        hotel.address = 'NULL'

    print 'hotel.address'
    print hotel.address

    try:
        map_infos = map_pat.findall(content)[0]
        hotel.map_info = map_infos[1] + ',' + map_infos[0]
    except Exception, e:
        hotel.map_info = 'NULL'

    print 'map_info'
    print hotel.map_info

    # 解析酒店星级

    try:
        star_temp = root.find_class('t24 yahei')[0].xpath('b/@class')[0].encode('utf-8')
        hotel.star = star_temp[-1]
        if hotel.star == ' ':
            hotel.star = -1
    except Exception, e:
        hotel.star = -1

    print 'star'
    print hotel.star
    # 解析酒店评分
    try:
        tp = root.xpath('//div[@class="pertxt_num"]/text()')[0].encode('utf-8')
        print tp
        t_grade = grade_pat.findall(tp)[0]
        print 't_grade', t_grade
        hotel.grade = float(t_grade) * 0.05
    except Exception, e:
        print 'no'
        print str(e)
        hotel.grade = 'NULL'
    print 'grade'
    print hotel.grade

    # 解析酒店评论数
    try:
        review_num_str = root.find_class('hrela_comt_total')[0]. \
            xpath('a/text()')[0].encode('utf-8').strip()
        print review_num_str
        hotel.review_num = int(review_num_str)
    except:
        hotel.review_num = -1

    print 'review'
    print hotel.review_num

    # 解析酒店简介
    try:
        desc_list = root.xpath('//div[@class="dview_info"]/dl[1]/dd')
        for each in desc_list:
            print each
        hotel.description = hotel.description[:-9]
    except:
        hotel.description = 'NULL'

    print 'description'
    print hotel.description

    # parse check_in time info , check out time info
    try:
        temp_time = root.xpath('//div[@id="iscrollNewAmenities"]/div/dl/dd/text()')[0]. \
            encode('utf-8').strip()
        print temp_time
        hotel.check_in_time = temp_time.split('，')[0]
        k = temp_time.find('离店时间：')
        if k != -1:
            hotel.check_out_time = temp_time[k + 16:]
    except:
        hotel.check_out_time = 'NULL'
    print 'check_in'
    print hotel.check_in_time

    print 'check_out'
    print hotel.check_out_time
    # parse all services at this hotel

    try:
        service = ''
        service_list = root.xpath('//*[@id="serverall"]/li/text()')
        for each in service_list:
            service += each.encode('utf-8').strip() + '|'
        hotel.service = service[:-1]
        if hotel.service == '':
            hotel.service = 'NULL'
    except Exception, e:
        hotel.service = 'NULL'
        print str(e)
    print 'hotel.service'
    print hotel.service

    if '免费自助停车设施' in hotel.service:
        hotel.is_parking_free = 'Yes'
        hotel.has_parking = 'Yes'
    if '收费自助停车设施' in hotel.service:
        hotel.has_parking = 'Yes'
        hotel.is_parking_free = 'No'
    if '免费 Wi-Fi' in hotel.service:
        hotel.has_wifi = 'Yes'
        hotel.is_wifi_free = 'Yes'

    print 'has_parking'
    print hotel.has_parking
    print 'is_parking_free'
    print hotel.is_parking_free
    print 'has_wifi'
    print hotel.has_wifi
    print 'has_free_wifi'
    print hotel.is_wifi_free
    print 'img_items'
    print hotel.img_items
    hotel.source = 'elong'
    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    # url = 'http://ihotel.elong.com/101703/'
    url = 'http://ihotel.elong.com/670847/'
    other_info = {u'source_id': u'670847', u'city_id': u'20236'}
    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = elong_parser(content, url, other_info)
    print 'Hello World'

    # try:
    #     session = DBSession()
    #     session.add(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
