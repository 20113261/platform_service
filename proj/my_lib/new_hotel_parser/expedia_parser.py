#! /usr/bin/env python
# coding=utf-8

import json
import sys

import re
import urlparse
import requests
# from common.logger import logger
from lxml import html as HTML

from data_obj import ExpediaHotel  # DBSession

reload(sys)
sys.setdefaultencoding('utf-8')
map_pattern = re.compile(r'center=(.*?)')


def expedia_parser(content, url, other_info):
    hotel = ExpediaHotel()

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

    hotel.brand_name = 'NULL'
    hotel.hotel_name = 'NULL'
    hotel.hotel_name_en = 'NULL'
    try:
        # 匹配英文名
        # eng_pattern = re.compile(r'([a-zA-Z].*[a-zA-Z]?)', re.S)
        name = root.find_class('page-header')[0].find_class('section-header-main')[0].text.strip()
        name_all = root.find_class('page-header')[0].find_class('section-header-main')[0].text_content().strip()

        if name != name_all and name in name_all:
            hotel_name = name
            hotel_name_en = name_all.replace(name, '')
        else:
            hotel_name = name
            hotel_name_en = name

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
    except Exception, e:
        print str(e)
    print 'hotel_brand_name=>%s' % hotel.brand_name
    print 'hotel_name=>%s' % hotel.hotel_name
    print 'hotel_name_en=>%s' % hotel.hotel_name_en
    try:
        address = ''
        # full_address = root.xpath('//div[@class="full-address"]//span/text()')
        # add_temp = full_address[:-1]
        # address = ','.join(add_temp)
        # hotel.postal_code = full_address[-1].strip().encode('utf-8')
        # hotel.address = address
        address_list = root.find_class('page-header')[0].find_class('address')[0]  # .xpath('span')[0]
        a = address_list.find_class('street-address')
        if len(a)>0:
            address += encode_unicode(a[0].text_content().strip())
        aa = address_list.find_class('city')
        if len(aa) > 0:
            address += ',' + encode_unicode(aa[0].text_content().strip())
        aaa = address_list.find_class('province')
        if len(aaa)>0:
            address += ',' + encode_unicode(aaa[0].text_content().strip())
        # address += ','
        # address += encode_unicode(address_list.find_class('country')[0].text_content().strip())
        hotel.address = address
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
        star = root.xpath('//span[contains(@class, "stars-grey value-title")]')[0].attrib['title']
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
        hotel.is_parking_free = 'No'
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
        map_part = root.xpath('// div[@class="map"]/a/figure/@data-src')
        map_str = map_part[-1]
        google_map_info = urlparse.parse_qs(map_str)['center'][-1]
        map_info = ','.join(google_map_info.split(',')[::-1])
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
        # desc = encode_unicode(root.find_class('hotel-description')[0].find_class('visuallyhidden')[0].tail.strip())
        h3s = root.xpath('//div[@class="hotel-description"]/h3//text()')
        ps = root.xpath('//div[@class="hotel-description"]/p//text()')
        desc = '|_|'.join([title + '::' + value for title, value in zip(h3s, ps)])
        hotel.description = desc
    except Exception, e:
        print str(e)
    print 'description=>%s' % hotel.description
    try:
        card_list = root.xpath('//div[@class="payment-logos"]/figure/@data-alt')
        accepted_card = ''
        for each in card_list:
            accepted_card += encode_unicode(each)
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
    from proj.my_lib.new_hotel_parser.lang_convert import tradition2simple

    url = 'https://www.expedia.cn/h1000.Hotel-Information'
    # url = 'https://www.expedia.cn/cn/Red-Lodge-Hotels-Rock-Creek-Resort.h4738480.Hotel-Information?chkin=2017%2F03%2F10&chkout=2017%2F03%2F11&rm1=a2&regionId=0&hwrqCacheKey=1b1ae982-7ce1-495b-8e39-95fda9024720HWRQ1489143096310&vip=false&c=f14b28c2-998c-4ed9-be72-b832c4eb08ff&&exp_dp=1071.2&exp_ts=1489143098007&exp_curr=CNY&exp_pg=HSR'
    # url = 'https://www.expedia.cn/cn/Billings-Hotels-Yellowstone-River-Lodge.h13180651.Hotel-Information?chkin=2017%2F03%2F10&chkout=2017%2F03%2F11&rm1=a2&regionId=0&hwrqCacheKey=1b1ae982-7ce1-495b-8e39-95fda9024720HWRQ1489143192290&vip=false&c=4c8a0d41-19d1-4a60-8cef-757c92a29e97&'
    # url = 'https://www.expedia.cn/cn/Tainan-Hotels-The-Vintage-Maison-Tainan.h13323178.Hotel-Information'
    # url = 'https://www.expedia.cn/h15421134.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/h9999647.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Savannah-Hotels-Best-Western-Savannah-Historic-District.h454.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Chiang-Mai-Hotels-VCSuanpaak-Hotel-Serviced-Apartments.h6713388.Hotel-Information?chkin=2016%2F12%2F14&chkout=2016%2F12%2F15&rm1=a3&hwrqCacheKey=f03a3186-af50-40c4-881f-b5f8c58d19a7HWRQ1480420091939&c=4617cc10-b9c1-46dc-992b-5a6fe87f7f49&'
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_expedia_total_new&id=ef1d21e286502f87feaea39098c11b1c'
    # url = 'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_expedia_total_new&id=0035837c89d997704b1312cd3cf6c50e'
    # url = 'https://www.expedia.com.hk/cn/h10000.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Wagga-Wagga-Hotels-International-Hotel-Wagga-Wagga.h8966967.Hotel-Information?chkin=2017%2F9%2F25&chkout=2017%2F9%2F26&rm1=a2&regionId=181592&hwrqCacheKey=cf20f4e6-25d7-4183-99d0-954735abcb77HWRQ1506309449240&vip=false&c=297cd267-27af-484b-9117-f3f38e35362c&&exp_dp=729.14&exp_ts=1506309449666&exp_curr=HKD&swpToggleOn=false&exp_pg=HSR'
    url = 'https://www.expedia.com.hk/Hotels-Sahara-Motel.h13279481.Hotel-Information'
    url = 'https://www.expedia.com.hk/cn/Mauritius-Island-Hotels-Ocean-Villas.h1466602.Hotel-Information?chkin=2017%2F11%2F25&chkout=2017%2F11%2F26&rm1=a2&regionId=6051080&sort=recommended&hwrqCacheKey=58665cc7-0e73-4f2d-89da-6cf5f79637efHWRQ1506387257474&vip=false&c=251228bc-5980-49ea-ac6d-87d847977318&'
    other_info = {
        'source_id': '1000',
        'city_id': '50795'
    }

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = expedia_parser(content, url, other_info)

    print '#' * 100
    keys = ['hotel_name', 'hotel_name_en', 'brand_name', 'address', 'service', 'description', 'accepted_cards']

    for key in keys:
        if not getattr(result, key):
            setattr(result, key, 'NULL')
        setattr(result, key, tradition2simple(getattr(result, key).decode()))
    # result.hotel_name = tradition2simple(result.hotel_name.decode())
    # result.hotel_name_en = tradition2simple(result.hotel_name_en.decode())
    # result.brand_name = tradition2simple(result.brand_name.decode())
    # result.address = tradition2simple(result.address.decode())
    # result.service = tradition2simple(result.service.decode())
    # result.description = tradition2simple(result.description.decode())
    # result.accepted_cards = tradition2simple(result.accepted_cards.decode())
    for k, v in result.__dict__.items():
        print k, '=>', v
    print 'Hello World'
    # try:
    #     session = DBSession()
    #     session.merge(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
