#! /usr/bin/env python
# coding=utf-8

import json
import sys

import re
import requests
# from common.logger import logger
from lxml import html as HTML

from data_obj import Hotel  # DBSession

reload(sys)
sys.setdefaultencoding('utf-8')
map_pattern = re.compile(r'center=(.*?)')


def expedia_parser(content, url, other_info):
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
        # eng_pattern = re.compile(r'([a-zA-Z].*[a-zA-Z]?)', re.S)
        name_all = root.find_class('page-header')[0].find_class('section-header-main')[0].text_content().strip()
        hotel_name_en = name_all
        hotel_name = name_all

        # 爬虫中彻底去除酒店名称处理逻辑
        # 处理酒店名称
        # if len(re.findall(u'([\u4e00-\u9fff]+)', unicode(hotel_name))) > 0:
        #     if hotel_name.endswith(hotel_name_en):
        #         hotel_name = hotel_name.replace(hotel_name_en, '').strip()
        #         if hotel_name == '':
        #             hotel_name = hotel_name_en
        #
        # if hotel_name_en == hotel_name:
        #     all_res = re.findall(u'([\u4e00-\u9fff]+)', unicode(hotel_name))
        #     if len(all_res) != 0:
        #         hotel_name_en = hotel_name.split(all_res[0].encode())[-1]
        #         hotel_name = hotel_name.replace(hotel_name_en, '')

        hotel.hotel_name = hotel_name
        hotel.hotel_name_en = hotel_name_en
        hotel.brand_name = 'NULL'
    except Exception, e:
        print str(e)
    print 'hotel_brand_name=>%s' % hotel.brand_name
    print 'hotel_name=>%s' % hotel.hotel_name
    print 'hotel_name_en=>%s' % hotel.hotel_name_en
    try:
        address = ''
        full_address = root.xpath('//div[@class="full-address"]//span/text()')
        add_temp = full_address[:-1]
        address = ','.join(add_temp)
        hotel.postal_code = full_address[-1].strip().encode('utf-8')
        hotel.address = address
        # address_list = root.find_class('page-header')[0].find_class('address')[0]  # .xpath('span')[0]
        # address += encode_unicode(address_list.find_class('street-address')[0].text_content().strip())
        # address += ','
        # address += encode_unicode(address_list.find_class('city')[0].text_content().strip())
        # address += ','
        # address += encode_unicode(address_list.find_class('province')[0].text_content().strip())
        # address += ','
        # address += encode_unicode(address_list.find_class('country')[0].text_content().strip())
        # hotel.address = address
        # postal_code = encode_unicode(address_list.find_class('postal-code')[0].text_content().strip())
        # hotel.postal_code = postal_code
    except Exception, e:
        print str(e)
        hotel.address = 'NULL'
    print 'postal_code=>%s' % hotel.postal_code
    print 'address=>%s' % hotel.address
    try:
        grade = root.find_class('guest-rating')[0].find_class('rating-number')[0].text_content()
        hotel.grade = float(grade)
    except Exception, e:
        print str(e)

    print 'grade=>%s' % hotel.grade
    try:
        star = root.find_class('star-rating-wrapper')[0].text_content().split('/')[0].strip()
        hotel.star = str(int(star))
    except:
        hotel.star = -1
    print 'star=>%s' % hotel.star

    try:
        review_num = re.findall(r'\"totalReviews\":(\d+),', content)
        hotel.review_num = review_num[0].strip().encode('utf-8')
        # review_num = root.find_class('cols-nested')[0].xpath('a/span[@itemprop="reviewCount"]')[0].text_content()
        # hotel.review_num = str(review_num)
    except Exception, e:
        print str(e)
    print 'review_num=>%s' % hotel.review_num

    try:
        # info_table = encode_unicode(
        #     root.find_class('tab-pane')[0].find_class('col')[0].xpath('section')[0].text_content())
        internet_info = root.xpath('//div[@data-section="internet"]')[0].text_content()
        if '免费 WiFi' in internet_info:
            has_wifi = 'Yes'
            is_wifi_free = 'Yes'
        hotel.has_wifi = has_wifi
        hotel.is_wifi_free = is_wifi_free
    except Exception, e:
        hotel.has_wifi = 'No'
        hotel.is_wifi_free = 'No'
        print str(e)
    try:
        parking_info = root.xpath('//div[@data-section="parking"]')[0].text_content()
        if '收费' in parking_info:
            has_parking = 'Yes'
            is_parking_free = 'No'
        if '免费' in parking_info:
            has_parking = 'Yes'
            is_parking_free = 'Yes'
        hotel.has_parking = has_parking
        hotel.is_parking_free = is_parking_free
    except Exception as e:
        hotel.has_parking = 'No'
        Hotel.is_parking_free = 'No'
        print str(e)
    print 'has_wifi=>%s' % hotel.has_wifi
    print 'is_wifi_free=>%s' % hotel.is_wifi_free
    print 'has_parking=>%s' % hotel.has_parking
    print 'is_parking_free=>%s' % hotel.is_parking_free

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
    print 'service=>%s' % hotel.service
    try:
        # map_pattern = re.compile(r'var modelData =(.*?);')
        # map_detail = map_pattern.findall(content)[0]
        # map_json = json.loads(map_detail)
        # map_temp = map_json['latLong'].encode('utf-8').split('|')
        # map_info = map_temp[1] + ',' + map_temp[0]
        # hotel.map_info = map_info
        map_temp = re.findall(r'\"latlong\": \"(.*)\",', content)[0].encode('utf-8').split(',')
        map_info = map_temp[1] + ',' + map_temp[0]
        hotel.map_info = map_info
    except Exception, e:
        map_info = 'NULL'
        print str(e)

    print 'map_info=>%s' % map_info
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
    print 'img_items=>%s' % hotel.img_items
    try:
        desc = encode_unicode(root.find_class('hotel-description')[0].find_class('visuallyhidden')[0].tail.strip())
        hotel.description = desc
    except Exception, e:
        print str(e)
    print 'description=>%s' % hotel.description
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
    print 'accepted_cards=>%s' % hotel.accepted_cards
    try:
        policy_table = root.find_class('tab-pane')[0].find_class('col')[1].xpath('section')[0].getchildren()
        check_in_text = policy_table[2].xpath('p/text()')
        if '中午' in check_in_text:
            check_in_time = '中午'
        else:
            check_in_time = re.findall(r'(\d+.*)', check_in_text[0])[0]
        hotel.check_in_time = check_in_time
    except Exception, e:
        print str(e)
    print 'check_in_time=>%s' % hotel.check_in_time
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
    print 'check_out_time=>%s' % hotel.check_out_time
    hotel.hotel_url = url
    hotel.source = 'expedia'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


def encode_unicode(str):
    return str.replace('\u00', '\\x').decode('string-escape').encode('utf8')


if __name__ == '__main__':
    url = 'https://www.expedia.cn/h1000.Hotel-Information'
    # url = 'https://www.expedia.cn/cn/Red-Lodge-Hotels-Rock-Creek-Resort.h4738480.Hotel-Information?chkin=2017%2F03%2F10&chkout=2017%2F03%2F11&rm1=a2&regionId=0&hwrqCacheKey=1b1ae982-7ce1-495b-8e39-95fda9024720HWRQ1489143096310&vip=false&c=f14b28c2-998c-4ed9-be72-b832c4eb08ff&&exp_dp=1071.2&exp_ts=1489143098007&exp_curr=CNY&exp_pg=HSR'
    # url = 'https://www.expedia.cn/cn/Billings-Hotels-Yellowstone-River-Lodge.h13180651.Hotel-Information?chkin=2017%2F03%2F10&chkout=2017%2F03%2F11&rm1=a2&regionId=0&hwrqCacheKey=1b1ae982-7ce1-495b-8e39-95fda9024720HWRQ1489143192290&vip=false&c=4c8a0d41-19d1-4a60-8cef-757c92a29e97&'
    # url = 'https://www.expedia.cn/cn/Tainan-Hotels-The-Vintage-Maison-Tainan.h13323178.Hotel-Information'
    # url = 'https://www.expedia.cn/h15421134.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/h9999647.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Savannah-Hotels-Best-Western-Savannah-Historic-District.h454.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Chiang-Mai-Hotels-VCSuanpaak-Hotel-Serviced-Apartments.h6713388.Hotel-Information?chkin=2016%2F12%2F14&chkout=2016%2F12%2F15&rm1=a3&hwrqCacheKey=f03a3186-af50-40c4-881f-b5f8c58d19a7HWRQ1480420091939&c=4617cc10-b9c1-46dc-992b-5a6fe87f7f49&'
    url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_expedia_total_new&id=a2203d7df9960a271e52eedf8c008f65'
    other_info = {
        'source_id': '1000',
        'city_id': '50795'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = expedia_parser(content, url, other_info)
    print 'Hello World'
    # try:
    #     session = DBSession()
    #     session.merge(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
