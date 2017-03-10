#! /usr/bin/env python
# coding=utf-8

import sys

# import db_add
import re
import requests
# from common.logger import logger
from lxml import etree
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf-8')

map_pat = re.compile('center=(.*)&zoom')


def hoteltravel_parser(page, url, other_info):
    hotel = Hotel()

    page = page.decode('utf-8')
    root = HTML.fromstring(page)

    try:
        detail = root.get_element_by_id('hotel-detail')
        hotel_name = detail[0].text_content()
        hotel.hotel_name = hotel_name.replace('\'', '').encode('utf-8')
    except:
        print 'into'
        try:
            hotel.hotel_name = root.find_class('hotel_text_address')[0].xpath('h1/text()')[0].encode('utf-8').strip()
        except Exception, e:
            print str(e)
    hotel.hotel_name_en = hotel.hotel_name

    print 'hotel_name=>%s' % hotel.hotel_name
    print 'hotel_name_en=>%s' % hotel.hotel_name_en

    try:
        map = root.xpath('//div [@id="topmap"]/a/img/@src')[0].encode('utf-8').strip()
        t_map = map_pat.findall(map)[0]
        hotel.map_info = t_map.split(',')[1] + ',' + t_map.split(',')[0]
    except Exception, e:
        print str(e)

    print 'map_info=>%s' % hotel.map_info

    try:
        detail = root.find_class('clearfix hidden-sm hidden-md hidden-lg nomarginbottom')[0]
        addr_str = etree.tostring(detail)

        pattern = re.compile('/>([^<>]*?)</p')
        match = pattern.findall(addr_str)
        hotel.address = match[0].strip().replace('\'', '')
    except:
        try:
            detail = root.get_element_by_id('hotel-detail')
            # print detail
            hotel.address = detail.xpath('address/text()')[0].encode('utf-8').strip().replace('\'', '')
        except:
            # pass
            hotel.address = 'NULL'

    print 'address=>%s' % hotel.address

    pattern = re.compile('rating-stars star_(.?)')
    match = pattern.findall(page)

    try:
        hotel.star = str(float(match[0]))
    except Exception, e:
        # logger.info("%s" % str(e))
        # pass
        hotel.star = -1
    print 'star=>%s' % hotel.star

    try:
        pattern = re.compile('rating-point">(.*?)/5</span>')
        match = pattern.findall(page)
        hotel.grade = str(match[0])
    except:
        try:
            temp_grade = root.find_class('col-xs-4 col-sm-6 col-md-6 nopadding')[0].xpath('span/text()')[0]
            hotel.grade = temp_grade.split('/')[0]
        except Exception, e:
            print str(e)
            hotel.grade = -1

    print 'grade=>%s' % hotel.grade

    try:
        pattern = re.compile('<span class="badge">\[(\d*?)\]</span>')
        match = pattern.findall(page)
        hotel.review_num = str(int(match[0]))
    except:
        try:
            # detail = root.find_class('clearfix hidden-sm hidden-md hidden-lg nomarginbottom')[0]
            # review_str = etree.tostring(detail)
            # pattern = re.compile('<a href="#reviews" onclick="trpReview\(\);">\(([0-9,]+)')
            # match = pattern.findall(review_str)
            # num = match[0].replace(',', '')
            num = root.xpath('//span[@itemprop="votes"]/text()')[0]
            hotel.review_num = int(num)
        except:
            try:
                detail = root.find_class('col-xs-4 col-sm-6 col-md-6 nopadding')[0]
                review_str = etree.tostring(detail)
                pattern = re.compile('<a href="#reviews" onclick="trpReview\(\);">\(([0-9,]+)')
                match = pattern.findall(review_str)
                num = match[0].replace(',', '')
                hotel.review_num = int(num)
            except Exception, e:
                print str(e)
                hotel.review_num = -1

    print 'review=>%s' % hotel.review_num

    match = re.findall(u'Internet', page)
    if len(match) != 0:
        hotel.has_wifi = 'Yes'

    match = re.findall(u'Wi-Fi', page)
    if len(match) != 0:
        hotel.has_wifi = 'Yes'

    match = re.findall(u'internet', page)
    if len(match) != 0:
        hotel.has_wifi = 'Yes'

    print 'has_wifi=>%s' % hotel.has_wifi

    match = re.findall(u'parking', page)
    if len(match) != 0:
        hotel.has_parking = 'Yes'

    match = re.findall(u'Parking', page)

    if len(match) != 0:
        hotel.has_parking = 'Yes'
    print 'has_parking=>%s' % hotel.has_parking

    try:
        detail = root.get_element_by_id('collapseFour')
    except Exception, e:
        print str(e)

    try:
        service = ''
        nav_list = detail.xpath('./div/nav')
        for nav in nav_list:
            title = nav.xpath('./h6/text()')[0].strip().encode('utf-8')
            if ':' not in title:
                title += ':'
            li_list = nav.xpath('./ul/li/text()')
            service += title
            service += ','.join(li_list)
            # for li in li_list:
            #     service += li.strip().encode('utf-8') + ','
            service = service[:-1] + '|'

        hotel.service = service[:-1]
        # for nav in detail[0][1:]:
        #     for ul in nav[1]:
        #         service += ul.text_content().strip() + '|'
        # hotel.service = service[:-1].replace('\'', '').encode('utf-8')
    except Exception, e:
        # logger.info("%s" % str(e))
        print e
        hotel.service = "NULL"

    print 'service=>%s' % hotel.service

    # img_items = []
    try:
        img_items = ''
        img_list = root.xpath('//ul[@class="hotel-slider"]/li/img[@class="lazy"]/@data-original')
        img_items += '|'.join(img_list)
        hotel.img_items = img_items[:-1]
        # ul = root.get_element_by_id('bx-pager')
        # for li in ul:
        #     attributes = li[0].attrib
        #     url = attributes['src'].strip().encode('utf8')
        #     img_items.append(url)
        # hotel.img_items = '|'.join(img_items)
    except Exception, e:
        # logger.info("%s" % str(e))
        print str(e)

    print 'img_items=>%s' % hotel.img_items

    try:
        description = root.get_element_by_id('hotelComment').text_content().replace('\'', '').encode('utf-8')
        hotel.description = description.replace('"', '')
    except Exception, e:
        print str(e)
        hotel.description = 'NULL'
    print 'description=>%s' % hotel.description

    hotel.source = 'hoteltravel'
    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    url = 'http://www.hoteltravel.com/canada/banff/bandff_voyager.htm#reviews'
    other_info = {
        'source_id': 'canada/banff/bandff_voyager.htm',
        'city_id': '50846'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    # for _ in xrange(100):
    result = hoteltravel_parser(content, url, other_info)

    # try:
    #     session = DBSession()
    #     session.add(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
