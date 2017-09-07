#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import requests
from lxml import html as HTML
from data_obj import HiltonHotel

# ----from data_obj import ExpediaHotel  # DBSession

reload(sys)
sys.setdefaultencoding('utf-8')

detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'
map_info = 'maps-directions.html'


def hilton_parser(total_content, url, other_info):
    hotel = HiltonHotel()
    # ----hotel = ExpediaHotel()
    content, detail_content, map_info_content, desc_content = total_content
    # ----------request -----
    html_detail = HTML.fromstring(detail_content)
    # html_map = HTML.fromstring(map_info_content.decode('utf-8'))
    html_desc = HTML.fromstring(desc_content)
    # ------request--end-----

    # -----content----start-
    try:
        html = HTML.fromstring(content)
        html = HTML.make_links_absolute(html, base_url=url)
    except Exception, e:
        print '----fuck'
        print str(e)

    try:
        root = html.find_class('mainbody-gallery')[0]
    except Exception, e:
        print str(e)

    try:
        # 匹配英文名
        # eng_pattern = re.compile(r'([a-zA-Z].*[a-zA-Z]?)', re.S)
        name_all = re.findall(r'var HotelName = "(.*?)";', content)[0]
        hotel.hotel_name_en = name_all
        hotel.hotel_name = name_all

    except Exception, e:
        print str(e)
    print 'hotel.hotel_brand_name=>%s' % hotel.hotel_name
    print 'hotel.hotel_name=>%s' % hotel.hotel_name
    print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en

    try:
        full_address = root.xpath('//span[@class="addr"]/text()')
        add_temp = full_address[0]
        hotel.address = add_temp
        print 'hotel.address=>%s' % hotel.address
        # ----VON-NONE---hotel.postal_code = full_address[-1].strip().encode('utf-8')
        # hotel.address = address
    except Exception, e:
        print str(e)
        # ----hotel.address = 'NULL'
    # ----print 'postal_code=>%s' % hotel.postal_code

    # ----print 'address=>%s' % hotel.address
    try:
        img_list = re.findall(r'var HotelAlbumList = (.*?)var HotelName', content, re.S)[0]
        img_list = re.findall(r'"ImageSrc":"(.*?)"', img_list, re.S)
        img_url_set = set()
        for img in img_list:
            img_url_set.add(img)
    except Exception, e:
        print e
    # print 'img_items=>%s' % hotel.img_items
    # print hotel.img_items
    img_items = ''
    for ima in img_url_set:
        img_items += ima.encode('raw-unicode-escape')
        img_items += '|'

    hotel.img_items = img_items
    print "hotel.img_items=>", hotel.img_items
    # -----content ---end-

    # ------detail and map content ----start-
    try:
        map_info_data = re.findall(r'var hotelJsonInfo = (.*?);', map_info_content)[0]
        map_info_data = eval(map_info_data)
        location = map_info_data.get('TxLocation', None) or map_info_data.get('Location', None)
        mmp = location.split(',')
        map_info = mmp[0] + ',' + mmp[1]


    except Exception as e:
        map_info = 'NULL'
        print e

    hotel.map_info = map_info
    print 'hotel.map_info=>%s' % hotel.map_info

    service = ''

    is_wifi_free = ''
    try:
        WIFI = html_detail.xpath('//td[@id="compare_internet"]/text()')[0]
        if "无线上网" in WIFI:
            has_wifi = 'Yes'
            is_wifi_free = 'Yes'
        else:
            has_wifi = 'No'
            is_wifi_free = 'No'
    except Exception as e:
        print e
        has_wifi = 'No'
    print 'has_wifi=>%s' % has_wifi

    try:
        PARK = html_detail.xpath('//td[@id="compare_parkdist"]/text()')[0]
        if '泊车' in PARK:
            has_parking = 'Yes'
        else:
            has_parking = 'No'
    except Exception as e:
        print e
        has_parking = 'No'
    print 'has_parking=>%s' % has_parking

    hotel.has_wifi = has_wifi
    hotel.is_wifi_free = is_wifi_free
    hotel.has_parking = has_parking

    print 'has_wifi=>%s' % hotel.has_wifi
    print 'is_wifi_free=>%s' % hotel.is_wifi_free
    print 'has_parking=>%s' % hotel.has_parking
    print 'is_parking_free=>%s' % hotel.is_parking_free

    service = ''
    try:
        service += '交通：'
        ALL = html_detail.xpath('//tbody[@id="tbodytransportation"]')[0]
        info1 = ''
        for each in ALL:
            cc = process_text(each.text_content())
            service += cc
            service += '|'
    except Exception as e:
        print e

    try:
        service += '设施：'
        ALL = html_detail.xpath('//tbody[@id="tbodyfacilities"]')
        info1 = ''
        for each in ALL:
            cc = process_text1(each.text_content())
            service += cc

    except Exception as e:
        print e
    try:
        service += '服务与设施：'
        ALL = html_detail.xpath('//tbody[@id="tbodyservices"]')
        info1 = ''
        for each in ALL:
            cc = process_text1(each.text_content())
            service += cc

    except Exception as e:
        print e

    hotel.service = service
    print 'hotel.service=>', hotel.service

    check_in_time = ''
    check_out_time = ''
    try:
        ALL = html_detail.xpath('//tbody[@class="tbodyElementsShownByDefault"]')
        check_time = ALL[-1][-1].text_content().replace('\n', '').replace('\t', '').replace(' ', '')
        check_time = check_time.split('：')
        check_in_time = check_time[1][:-4]
        check_out_time = check_time[-1]
    except Exception, e:
        print str(e)

    hotel.check_in_time = check_in_time
    hotel.check_out_time = check_out_time
    print 'hotel.check_in_time=>', hotel.check_in_time
    print 'hotel.check_out_time=>', hotel.check_out_time

    try:
        ALL = html_desc.xpath('//div[@class="intro fix"]/p')
        desc = ''
        for each in ALL:
            desc+= each.text_content().encode('raw-unicode-escape')
    except Exception, e:
        print str(e)

    hotel.description = desc
    print 'hotel.description=>', hotel.description

    hotel.hotel_url = url
    hotel.source = 'hilton'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


def process_text(str):
    # str = str.encode('raw-unicode-escape')
    lis = re.split('[ \n\t]', str)
    liss = filter(lambda x: x != '', lis)
    ss = liss[0] + '::'
    for l in liss[1:]:
        ss += l
    return ss


def process_text1(str):
    lis = re.split('[ \n\t]', str)
    liss = filter(lambda x: x != '', lis)
    ss = ''
    for i in range(len(liss)):
        if i % 2 == 0:
            ss += liss[i] + '::' + liss[i + 1] + '|'
    return ss


def encode_unicode(str):
    return str.replace('\u00', '\\x').decode('string-escape').encode('utf8')


if __name__ == '__main__':
    url = 'http://www.hilton.com.cn/zh-CN/hotel/Beijing/hilton-beijing-wangfujing-BJSWFHI/'
    url = 'http://www.hilton.com.cn/zh-cn/hotel/san-diego/hilton-san-diego-resort-and-spa-SANHIHF/'
    detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'.format(url.split('/')[-2])
    map_info_url = url + 'maps-directions.html'
    desc_url = url + 'about.html'

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    detail_content = requests.get(detail_url).text
    map_info_content = requests.get(map_info_url).text
    desc_content = requests.get(desc_url).text

    total_content = [content, detail_content, map_info_content, desc_content]
    other_info = {
        'source_id': '1000',
        'city_id': '50795'
    }
    result = hilton_parser(total_content, url, other_info)
    # try:
    #     session = DBSession()
    #     session.merge(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)