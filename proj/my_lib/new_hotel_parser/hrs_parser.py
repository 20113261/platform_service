#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf-8')

star_pattern = re.compile(r'(\d+)')


def hrs_parser(content, url, other_info):
    hotel = Hotel()

    try:
        content = content.decode('utf-8')
        root = HTML.fromstring(content)
    except Exception, e:
        print str(e)

    # 解析酒店中英文名，如果没有中文名则置为英文名，如果都解析失败则退出

    try:
        hotel_name = root.xpath('//div[@id="detailsHead"]/h2/span/text()')[0].encode('utf-8'). \
            strip('')
        hotel_name_en = hotel_name
        hotel.hotel_name = hotel_name
        hotel.hotel_name_en = hotel_name_en
    except Exception, e:
        print str(e)

    try:
        address = root.xpath('//div[@id="detailsHead"]')[0].find_class('hotelAdress')[0]. \
            text_content().encode('utf-8').strip('')
        hotel.address = address
    except Exception, e:
        print str(e)

    try:
        star_text = root.xpath('//div[@id="detailsHead"]')[0].find_class('starContainer')[0]. \
            xpath('./span/@class')[0].encode('utf-8')
        print star_text
        star = star_pattern.findall(star_text)[0]
        hotel.star = str(star)
    except Exception, e:
        print str(e)

    try:
        grade = \
            root.find_class('titleWrap hideOnScroll')[0].find_class('rating ratingSmall rating8')[0].xpath(
                './a/text()')[
                0].encode('utf-8').strip('\n')
        hotel.grade = str(grade)
    except Exception, e:
        print str(e)

    try:
        lon_pattern = re.compile(r'lon=(.*?);window.hdSinglePageMapInstance=true')
        lat_pattern = re.compile(r'lat=(.*?),lon=')

        tmp_lon = lon_pattern.findall(page)[0]
        tmp_lat = lat_pattern.findall(page)[0]
        lon = float(tmp_lon.split('/')[0]) / float(tmp_lon.split('/')[1])
        lat = float(tmp_lat.split('/')[0]) / float(tmp_lat.split('/')[1])
        map_info = str(lon) + ',' + str(lat)
        hotel.map_info = map_info
    except Exception, e:
        print str(e)

    try:
        review_nums_text = root.find_class('titleWrap hideOnScroll')[0].find_class \
            ('rating ratingSmall rating8')[0].xpath('./a[2]/text()')[1]. \
            encode('utf-8').strip('\n')
        review_nums = str(star_pattern.findall(review_nums_text)[0].encode('utf-8'))
        hotel.review_num = review_nums
    except Exception, e:
        hotel.review_num = '-1'
        print str(e)

    try:
        tmp_service = root.find_class('jsAmenities equipement col33')[0].xpath('./ul')
        service = ''
        for each_service in tmp_service:
            item_list = each_service.xpath('./li')
            for each_item in item_list:
                service += each_item.text_content().encode('utf-8').strip('') + '|'
        service = service[:-1]
        hotel.service = service
    except Exception, e:
        print str(e)

    try:
        if 'WLAN' in hotel.service:
            hotel.has_wifi = 'Yes'
            if '0 EUR/hour' in hotel.service:
                hotel.is_wifi_free = 'Yes'
        if 'car park' in hotel.service:
            hotel.has_parking = 'Yes'
    except Exception, e:
        print str(e)

    try:
        pay_card = ''
        pays = root.find_class('payment')[0].xpath('./ul')
        for pay in pays:
            for each in pay.xpath('./li'):
                pay_card += each.text_content().encode('utf-8').strip() + '|'
        pay_card = pay_card[:-1]
        hotel.accepted_cards = pay_card
    except Exception, e:
        print str(e)
    print hotel.accepted_cards

    try:
        check_in_pattern = re.compile(r'Earliest check-in</strong><br/>(.*?)</p>')
        check_in = check_in_pattern.findall(content.replace('\n', '').replace('\t', ''))[0]
        check_in = str(check_in)
    except Exception, e:
        print str(e)
        check_in = 'NULL'
    hotel.check_in_time = check_in
    print hotel.check_in_time
    try:
        check_out_pattern = re.compile(r'Latest check-out</strong><br/>(.*?)</p>')
        check_out = check_out_pattern.findall(content.replace('\n', '').replace('\t', ''))[0]
        check_out = str(check_out)
    except Exception, e:
        print str(e)
        check_out = 'NULL'
    hotel.check_out_time = check_out
    print hotel.check_out_time

    hotel.source = 'hrs'
    hotel.hotel_url = url.encode('utf-8')
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    url = 'http://www.hrs.com/web3/hotelData.do?activity=photo&singleRooms=0&doubleRooms=1&adults=2&children=0&availability=true&hotelnumber=100'
    other_info = {
        'source_id': '100',
        'city_id': '10013'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = hrs_parser(content, url, other_info)

    try:
        session = DBSession()
        session.add(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
