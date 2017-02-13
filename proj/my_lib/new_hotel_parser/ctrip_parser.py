#! /usr/bin/env python
# coding=UTF8

'''
    @author:fangwang
    @date:2014-05-13
    @desc: crawl and parse ctrip room data via API
'''

import sys
import traceback

import re
import requests
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf8')

URL = 'http://openapi.ctrip.com/Hotel/OTA_HotelDescriptiveInfo.asmx?wsdl'

TASK_ERROR = 12

PROXY_NONE = 21
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
DATA_NONE = 24

pat1 = re.compile(r'HotelName="(.*?)" AreaID=".*?" HotelId="(.*?)">', re.S)
pat2 = re.compile(r'Latitude="(.*?)" Longitude="(.*?)"', re.S)


def ctrip_parser(page, url, other_info):
    hotel = Hotel()
    try:
        root = HTML.fromstring(page.decode('utf-8'))
    except Exception, e:
        print str(e)
    print root
    try:
        hotel_name = root.xpath('//*[@class="name"]/text()')[0].encode('utf-8').strip()
        k = hotel_name.find('(')
        hotel.hotel_name_en = hotel_name[:k]
        hotel.hotel_name = hotel_name[k:].replace('(', '').replace(')', '').strip()
        if k == -1:
            hotel.hotel_name = hotel_name.strip()
            hotel.hotel_name_en = hotel_name.strip()
    except Exception, e:
        traceback.print_exc(e)

    print 'hotel_name'
    print hotel.hotel_name
    print 'hotel_name_en'
    print hotel.hotel_name_en

    try:
        map_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip()
        map = map_temp.split('|')
        print map
        hotel.map_info = map[1] + ',' + map[0]
    except Exception, e:
        print str(e)
        hotel.map_info = 'NULL'

    print 'hotel.map_info'
    print hotel.map_info
    try:
        grade = root.xpath('//*[@class="score_text"]/text()')[0]
        hotel.grade = grade.encode('utf-8').strip()
    except Exception, e:
        print str(e)

    print 'grade'
    print hotel.grade
    try:
        address = root.xpath('//div [@class="adress"]/span/text()')[0]
        hotel.address = address.encode('utf-8').strip()
    except Exception, e:
        print str(e)

    print 'address'
    print hotel.address

    try:
        review = root.xpath('//*[@id="commnet_score"]/span[3]/span/text()')[0]
        hotel.review_num = review.encode('utf-8').strip()
    except Exception, e:
        print str(e)

    print 'review_nums'
    print hotel.review_num

    try:
        desc = root.xpath('//div[@id="detail_content"]/span/div/div/text()')[0]
        hotel.description = desc.encode('utf-8').strip().rstrip()
    except Exception, e:
        print str(e)

    print 'desc'
    hotel.description = 'NULL'

    try:
        pic_list = root.xpath('//div[@id="picList"]/div/div/@_src')
        if pic_list != []:
            img_items = ''
            for each in pic_list:
                s = each.encode('utf-8').strip()
                img_items += s + '|'
            hotel.img_items = img_items[:-1]
    except Exception, e:
        traceback.print_exc(e)

    print 'hotel.img_items'
    print hotel.img_items

    try:
        p = root.xpath('//div[@id="detail_content"]/div')[2]
        q = HTML.tostring(p)
        print q
        # parser = HTMLParser()
        # print type(q)
        # print parser.unescape(q)
        checkin_pat = re.compile(
            r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;')
        check_in = checkin_pat.findall(q)
        print check_in
        if check_in == []:
            checkin_pat1 = re.compile(
                r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21518;')
            check_in_time = checkin_pat1.findall(q)[0].encode('utf-8') + '以后'
        else:
            check_in_str = check_in[0].encode('utf-8')
            time = check_in_str.split('</span>-<span class="text_bold">')
            check_in_time = time[0] + '-' + time[1]

        checkout_pat = re.compile(
            r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21069;')
        check_out = checkout_pat.findall(q)
        print '--------', check_out
        if check_out == []:
            checkout_pat1 = re.compile(
                r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span></td></tr>')
            check_out_str = checkout_pat1.findall(q)[0]
            print 'hehehhehehehhe', check_out_str
            time = check_out_str.split('</span>-<span class="text_bold">')
            check_out_time = time[0] + '-' + time[1]
        else:
            check_out_time = check_out[0].encode('utf-8') + '以前'

        hotel.check_in_time = check_in_time.encode('utf-8').strip()
        hotel.check_out_time = check_out_time.encode('utf-8').strip()
    except Exception, e:
        # print str(e)
        traceback.print_exc(e)

    print 'check_in'
    print hotel.check_in_time

    print 'check_out'
    print hotel.check_out_time

    try:
        card_pat = re.compile(r'<div class="card_cont_img">(.*?)</div></<div></td></tr>')
        search_card = card_pat.findall(page)[0]
        card_pat1 = re.compile(r'<img alt=(.*?) title=')
        card = card_pat1.findall(search_card)
        temp_name = ''
        for each in card:
            temp_name += each.encode('utf-8').strip()[1:-1] + '|'
        hotel.accepted_cards = temp_name[:-1]
    except Exception, e:
        print str(e)
    print 'hotel.accept_cards'
    print hotel.accepted_cards

    try:
        items = root.xpath('//*[@id="detail_content"]/div[2]/table/tbody/tr')
        if items != []:
            item_str = ''
            for each in items:
                item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
                item = each.xpath('./td/ul/li')
                temp = ''
                for each1 in item:
                    temp += each1.xpath('./text()')[0].encode('utf-8').strip() + '|'
                item_str += item_name + '::' + temp
            hotel.service = item_str[:-1]
    except Exception, e:
        print str(e)

    print 'hotel.service'
    print hotel.service

    try:
        if '停车场' in hotel.service:
            hotel.has_parking = 'Yes'
        if '免费停车场' in hotel.service:
            hotel.is_parking_free = 'Yes'
        if '收费停车场' in hotel.service:
            hotel.is_parking_free = 'No'
        if '无线上网' in hotel.service:
            hotel.has_wifi = 'Yes'
    except Exception, e:
        print str(e)

    print 'hotel.has_wifi'
    print hotel.has_wifi

    print 'hotel.is_wifi_free'
    print hotel.is_wifi_free

    print 'hotel.has_parking'
    print hotel.has_parking

    print 'hotel.is_parking_free'
    print hotel.is_parking_free

    hotel.hotel_url = url
    hotel.source = 'ctrip'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    url = 'http://hotels.ctrip.com/international/1039433.html'
    other_info = {
        'source_id': '1039433',
        'city_id': '10074'
    }
    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = ctrip_parser(content, url, other_info)

    try:
        session = DBSession()
        session.add(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
