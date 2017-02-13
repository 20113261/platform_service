#! /usr/bin/env python
# coding=utf-8

import json
import sys

import re
import requests
from common.logger import logger
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf-8')
map_pattern = re.compile(r'center=(.*?)')


def ebookers_parser(content, url, other_info):
    hotel = Hotel()

    try:
        html = HTML.fromstring(content.decode('utf-8'))
        html = HTML.make_links_absolute(html, base_url=url)
    except Exception, e:
        print str(e)

    try:
        root = html.find_class('hotelInformation')[0]
    except Exception, e:
        print str(e)

    name_en = 'NULL'

    try:
        # 匹配英文名
        eng_pattern = re.compile(r'([a-zA-Z].*[a-zA-Z]?)', re.S)
        name_all = root.find_class('page-header')[0].find_class('section-header-main')[0].text_content().strip()
        hotel_name_en = encode_unicode(eng_pattern.findall(name_all)[0])
        hotel_name = encode_unicode(name_all.split(name_en)[0])
        hotel.hotel_name = hotel_name
        hotel.hotel_name_en = hotel_name_en
    except Exception, e:
        print str(e)
    logger.info('begin parse the ebookers!!!')

    try:
        address = ''
        address_list = root.find_class('page-header')[0].find_class('address')[0]  # .xpath('span')[0]
        address += encode_unicode(address_list.find_class('street-address')[0].text_content().strip())
        address += ','
        address += encode_unicode(address_list.find_class('city')[0].text_content().strip())
        address += ','
        address += encode_unicode(address_list.find_class('province')[0].text_content().strip())
        address += ','
        address += encode_unicode(address_list.find_class('country')[0].text_content().strip())
        hotel.address = address
        postal_code = encode_unicode(address_list.find_class('postal-code')[0].text_content().strip())
        hotel.postal_code = postal_code
    except Exception, e:
        print str(e)

    try:
        grade = root.find_class('guest-rating')[0].find_class('rating-number')[0].text_content()
        hotel.grade = str(grade)
    except Exception, e:
        print str(e)

    try:
        star = root.find_class('star-rating-wrapper')[0].text_content().split('/')[0].strip()
        hotel.star = str(star)
    except:
        pass

    has_wifi = 'NULL'
    is_wifi_free = 'NULL'
    has_parking = 'NULL'
    is_parking_free = 'NULL'

    try:
        review_num = root.find_class('cols-nested')[0].xpath('a/span[@itemprop="reviewCount"]')[0].text_content()
        hotel.review_num = str(review_num)
    except Exception, e:
        print str(e)

    try:
        info_table = encode_unicode(
            root.find_class('tab-pane')[0].find_class('col')[0].xpath('section')[0].text_content())
        if '免费 Wi-Fi' in info_table:
            has_wifi = 'Yes'
            is_wifi_free = 'Yes'
        if '收费自助停车设施' in info_table:
            has_parking = 'Yes'
            is_parking_free = 'No'
        if '免费自助停车设施' in info_table:
            has_parking = 'Yes'
            is_parking_free = 'Yes'
        hotel.has_wifi = has_wifi
        hotel.is_wifi_free = is_wifi_free
        hotel.has_parking = has_parking
        hotel.is_parking_free = is_parking_free
    except Exception, e:
        print str(e)

    try:
        info_table = root.find_class('tab-pane')[0].find_class('col')[0].xpath('section')[0]
        category_num = len(info_table.xpath('h3'))
        service = ''
        try:
            general = info_table.xpath('div[@data-section="amenities-general"]')[0]
            service += '酒店设施：'
            info1 = ''
            for each in general.find_class('toggle-pane')[0].xpath('ul')[0].xpath('li'):
                info1 += each.text_content().rstrip(' ')
                info1 += ','
            service += encode_unicode(info1.rstrip(','))
            service += '|'
            hotel.service = service
        except Exception, e:
            print str(e)

        try:
            internet = info_table.xpath('div[@data-section="internet"]')[0]
            service += '互联网：'
            info2 = ''
            for each in general.find_class('toggle-pane')[0].xpath('ul')[0].xpath('li'):
                info2 += each.text_content().rstrip(' ')
                info2 += ','
            service += encode_unicode(info2.rstrip(','))
            service += '|'
            hotel.service = service
        except Exception, e:
            print str(e)

        try:
            parking = info_table.xpath('div[@data-section="internet"]')[0]
            service += '停车：'
            info3 = ''
            for each in general.find_class('toggle-pane')[0].xpath('ul')[0].xpath('li'):
                info3 += each.text_content().rstrip(' ')
                info3 += ','
            service += encode_unicode(info3.rstrip(','))
            service += '|'
            service = service.rstrip('|')
            hotel.service = service
        except Exception, e:
            print str(e)
    except Exception, e:
        print str(e)

    try:
        map_pattern = re.compile(r'var modelData =(.*?);')
        map_detail = map_pattern.findall(content)[0]
        map_json = json.loads(map_detail)
        map_temp = map_json['latLong'].encode('utf-8').split('|')
        map_info = map_temp[1] + ',' + map_temp[0]

        hotel.map_info = map_info
    except Exception, e:
        map_info = 'NULL'
        print str(e)

    print 'map_info', map_info
    try:
        img_list = root.find_class('jumbo-wrapper')[0].find_class('jumbo-hero')[0].xpath('img')
        img_url_set = set()
        for each in img_list:
            try:
                each_url = 'https:' + each.get('data-src')
            except:
                try:
                    each_url = 'https:' + each.get('src')
                except:
                    pass
            if each_url != 'https:':
                img_url_set.add(each_url)
        hotel.img_items = '|'.join(img_url_set)
    except Exception, e:
        print str(e)

    try:
        desc = encode_unicode(root.find_class('hotel-description')[0].find_class('visuallyhidden')[0].tail.strip())
        hotel.description = desc
    except Exception, e:
        print str(e)

    try:
        card_list = root.find_class('payment-logos')[0]
        accepted_card = ''
        for each in card_list:
            accepted_card += encode_unicode(each.get('alt'))
            accepted_card += '|'
        accepted_cards = accepted_card.rstrip('|')
        hotel.accepted_cards = accepted_cards
    except Exception, e:
        print str(e)

    try:
        policy_table = root.find_class('tab-pane')[0].find_class('col')[1].xpath('section')[0].getchildren()
        check_in_text = policy_table[2].xpath('p/text()')
        if '中午' in check_in_text:
            check_in_time = '中午'
        else:
            check_in_time = check_in_text.split('入住时间开始于')
        hotel.check_in_time = check_in_time
    except Exception, e:
        print str(e)

    try:
        policy_table = root.find_class('tab-pane')[0].find_class('col')[1].xpath('section')[0].getchildren()
        check_out_text = policy_table[4].xpath('p/text()')[0].encode('utf-8').strip()
        if '中午' in check_out_text:
            check_out_time = '中午'
        else:
            check_out_time = check_out_text.split('退房时间为 ')[1]
        hotel.check_out_time = check_out_time
    except Exception, e:
        print str(e)

    hotel.hotel_url = url
    hotel.source = 'ebookers'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


def encode_unicode(str):
    return str.replace('\u00', '\\x').decode('string-escape').encode('utf8')


if __name__ == '__main__':
    url = 'https://www.ebookers.com/Bruges-Woodlands-Hotels-Holiday-Park-Klein-Strand-Campground.h10000570.Hotel-Information?chkin=20%2F09%2F16&chkout=21%2F09%2F16&rm1=a3&hwrqCacheKey=935100a1-cb64-4bda-9c46-811850889621HWRQ1470785225733&c=03251cf4-f9ce-4d16-a4c8-e00d2f2ec790&'
    other_info = {
        'source_id': '10000570',
        'city_id': '10041'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = ebookers_parser(content, url, other_info)

    try:
        session = DBSession()
        session.merge(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
