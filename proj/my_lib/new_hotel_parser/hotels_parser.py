#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
from lxml import html as HTML

from data_obj import Hotel, DBSession

star_pat = re.compile(r'在此页面中显示为 (.*) 星')
num_pat = re.compile(r'\d+')
map_pat = re.compile(r'center=(.*?)&zoom', re.S)

check_in = re.compile(r'入住时间开始于(.*?)</li>')
check_out = re.compile(r'退房时间(.*?)</li>')

reload(sys)
sys.setdefaultencoding('utf-8')


def hotels_parser(content, url, other_info):
    hotel = Hotel()
    content = content.decode('utf-8')
    root = HTML.fromstring(content)
    try:
        name_temp = root.xpath('//*[@class="vcard"]/h1/text()')[0].encode('utf-8')
        print name_temp
    except Exception, e:
        print str(e)

    try:
        hotel.hotel_name = name_temp.split('(')[0].strip().encode('utf-8')
        print 'hotel_name'
        print hotel.hotel_name
        try:
            hotel.hotel_name_en = name_temp.split('(')[1].replace(')', '').strip().encode('utf-8')
        except:
            hotel.hotel_name_en = 'NULL'
        # hotel.source_id = root.xpath('//*[@id="roomdesc_mainContainerSize1"]/input[1]/@value')[0]
        print 'hotel_name_en'
        print hotel.hotel_name_en
    except Exception, e:
        print str(e)
        # return hotel_tuple
    print 'hotel.hotel_name_en'
    print hotel.hotel_name_en
    try:
        hotel.address = root.find_class('postal-addr')[0].text_content() \
            .encode('utf-8').strip().replace('\n', '').replace('  ', '')
    except:
        hotel.address = 'NULL'
    print 'address'
    print hotel.address
    try:
        temp = root.find_class('visible-on-small map-widget-wrapper')[0].xpath('div/@style')[0].encode('utf-8').strip()
        map_info = map_pat.findall(temp)[0]
        hotel.map_info = map_info.split(',')[1] + ',' + map_info.split(',')[0]
    except Exception, e:
        print str(e)
        hotel.map_info = 'NULL'
    print 'map_info'
    print hotel.map_info
    try:
        hotel.postal_code = root.find_class('postal-code')[0].text.strip() \
            .encode('utf-8').replace(',', '')
    except:
        hotel.postal_code = 'NULL'

    print 'postal_code'
    print hotel.postal_code
    star_nums = 0
    try:
        temp_star = root.xpath('//div [@class="vcard"]/span/span')
        print 'dasdsadsafdfd'
        print temp_star
        for i in temp_star:
            if i.xpath('./@class')[0] == 'icon icon-star':
                star_nums += 1
            if i.xpath('./@class')[0] == 'icon icon-star icon-star-scale icon-star-half-parent':
                star_nums += 0.5

        hotel.star = float(star_nums)
    except:
        hotel.star = -1.0
    print 'star'
    print hotel.star
    try:
        hotel.grade = root.find_class('rating')[0].xpath('strong/text()')[0]
        hotel.grade = float(hotel.grade)
    except Exception, e:
        print str(e)
        hotel.grade = -1.0

    print 'hotel.grade'
    print hotel.grade
    try:
        review_num_temp = root.find_class('total-reviews')[0].text
        review_num = num_pat.findall(review_num_temp)[0]
        hotel.review_num = int(review_num)
    except:
        hotel.review_num = -1

    print 'review_num_temp'
    print hotel.review_num

    try:
        image_list = root.find_class('carousel-thumbnails')[0].xpath('ol/li')
        hotel.img_items = ''
        image_name = ''
        hotel.img_items = ''
        for each_image_ele in image_list:
            image_url = each_image_ele.xpath('a/@href')[0]
            hotel.img_items += image_url + '|'
        hotel.img_items = hotel.img_items[:-1]
    except:
        hotel.img_items = 'NULL'

    print 'hotel_img_items'
    print hotel.img_items

    try:
        description_temp = root.get_element_by_id('overview').xpath('b/text()')[0] \
            .encode('utf-8').strip()
        hotel.description = description_temp.encode('utf-8')
    except Exception, e:
        print str(e)
        hotel.description = 'NULL'

    print 'description'
    print hotel.description

    try:
        service = ''
        service_list = root.find_class('main-amenities two-columned')[0].xpath('ul/li')
        for each in service_list:
            service += each.text_content().encode('utf-8').strip() + '|'
    except Exception, e:
        print str(e)
        hotel.service = 'NULL'
    hotel.service = service[:-1]
    print 'service'
    print hotel.service

    try:
        temp = root.find_class('col-6-24 travelling-container resp-module')[0]
        wifi_text = HTML.tostring(temp).encode('utf-8').strip()
        if 'WiFi' in wifi_text:
            hotel.has_wifi = 'Yes'
        else:
            hotel.has_wifi = 'NULL'
    except Exception, e:
        print str(e)
        hotel.has_wifi = 'NULL'

    print 'has_wifi'
    print hotel.has_wifi

    try:
        temp = root.find_class('col-6-24 transport-container last resp-module')[0]
        car_text = HTML.tostring(temp).encode('utf-8').strip()
        if car_text.find('免费自助停车'):
            hotel.has_parking = 'Yes'
            hotel.is_parking_free = 'Yes'
        if car_text.find('停车场'):
            hotel.has_parking = 'Yes'
    except Exception, e:
        print str(e)
        hotel.has_parking = 'NULL'
        hotel.is_parking_free = 'NULL'
    print 'has_park'
    print hotel.has_parking

    print 'is_parking_free'
    print hotel.is_parking_free

    try:
        temp = root.xpath('//*[@id="at-a-glance"]/div/div[1]/div[2]/div/ul[2]')[0]
        check_in_time = temp.xpath('./li[1]/text()')[0]
        check_out_time = temp.xpath('./li[2]/text()')[0]
    except Exception, e:
        print str(e)
        check_in_time = 'NULL'
        check_out_time = 'NULL'

    hotel.check_in_time = check_in_time.encode('utf-8')
    hotel.check_out_time = check_out_time.encode('utf-8')
    print 'hotelcheck_in_time'
    print hotel.check_in_time
    print 'hotel_check_out_time'
    print hotel.check_out_time
    hotel.source = 'hotels'

    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    url = 'http://www.hotels.cn/hotel/details.html?WOE=2&q-localised-check-out=2015-11-10&WOD=1&q-room-0-children=0&pa=252&tab=description&q-localised-check-in=2015-11-09&hotel-id=119538&q-room-0-adults=2&YGF=14&MGT=1&ZSX=0&SYE=3'
    other_info = {
        'source_id': '119538',
        'city_id': '10001'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = hotels_parser(content, url, other_info)

    try:
        session = DBSession()
        session.add(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
