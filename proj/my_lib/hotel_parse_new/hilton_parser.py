#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import requests
from lxml import etree
from proj.my_lib.models.HotelModel import HotelNewBase
import json


def hilton_parser(total_content, url, other_info):
    Hotel = HotelNewBase()
    content, map_info_content, desc_content, enDetail_content = total_content
    hotel_id = url.split("/")[-2].split("-")[-1]
    Hotel.source_id = hotel_id
    Hotel.hotel_url = url
    Hotel = get_detail(Hotel,enDetail_content)
    Hotel.source = 'hilton'
    Hotel.source_id = Hotel.source_id = other_info['source_id']
    Hotel.city_id = other_info['city_id']
    try:
        map_info_data = re.findall(r'var hotelJsonInfo = (.*?);', map_info_content)[0]
        map_info_data = eval(map_info_data)
        location = map_info_data.get('TxLocation', None) or map_info_data.get('Location', None)
        mmp = location.replace(' ', '').split(',')
        map_info = mmp[1].strip() + ',' + mmp[0].strip()

    except Exception as e:
        map_info = 'NULL'
        print e

    Hotel.map_info = map_info
    # print Hotel.map_info
    select = etree.HTML(content)
    full_address = select.xpath('//span[@class="addr"]/text()')
    if full_address:
        Hotel.address = full_address[0].encode('raw-unicode-escape')
    code = re.findall("(\d{5,6})",Hotel.address)
    if code:
        Hotel.hotel_zip_code = code[0]
    else:
        Hotel.hotel_zip_code = ''
    phone = select.xpath('//span[@class="tel tel-pc"]/text()')
    if phone:
        Hotel.hotel_phone = phone[0].replace("-",'')


    try:
        img_list = re.findall(r'var HotelAlbumList = (.*?)var HotelName', content, re.S)[0]
        img_list = re.findall(r'"ImageSrc":"(.*?)"', img_list, re.S)
        Hotel.Img_first = img_list[0]
        img_url_set = set()
        for img in img_list:
            img_url_set.add(img)
    except Exception, e:
        print e,1
    img_items = ''
    for ima in img_url_set:
        img_items += ima.encode('raw-unicode-escape')
        img_items += '|'

    Hotel.img_items = img_items
    select_map = etree.HTML(map_info_content)
    traffic = ''.join(select_map.xpath("//div[@class='access-guide-inner']/p/text()"))
    if traffic:
        Hotel.traffic = traffic.encode('raw-unicode-escape')

    select_desc = etree.HTML(desc_content)
    service_info_list = select_desc.xpath('//ul/li/span[2]/text()')
    hotel_name = select_desc.xpath('//h1/text()')[0]
    Hotel.hotel_name = hotel_name.encode('raw-unicode-escape')
    Hotel.check_in_time = ''
    Hotel.check_out_time = ''
    Hotel.pet_type = ''
    for s_str in service_info_list:
        s_str = s_str.encode('raw-unicode-escape')
        if '入住' in s_str:
            check_in_time = re.compile(r'(\d+:\d+)').findall(s_str)
            if check_in_time:
                Hotel.check_in_time = check_in_time[0]
        if '退房' in s_str:
            check_out_time = re.compile(r'(\d+:\d+)').findall(s_str)
            if check_out_time:
                Hotel.check_out_time = check_out_time[0]
        if '宠物' in s_str:
            Hotel.pet_type = s_str.replace('\r', '').replace('\n', '').strip()
    desc = select_desc.xpath('//div[@class="intro fix"]/p/text()')
    desc = ''.join(desc)
    if desc:
        Hotel.description = desc.encode('raw-unicode-escape')

    return Hotel.to_dict()


def get_detail(Hotel, enDetail_content):

    enselect = etree.HTML(enDetail_content)
    server_str_en = enselect.xpath('//div[@class="copy_area"]/ul/li/text()')
    print server_str_en
    server_str_en = '|'.join([s.replace('\\n', '').replace('\\t', '').replace('\\r', '').
                             replace('\n', '').replace('\t', '').replace('\r', '').strip() for s in server_str_en])
    Hotel.service = server_str_en
    Hotel.others_info = json.dumps({"hotel_services_info": server_str_en})
    hotel_name_en = enselect.xpath("//span[@class='property-name']/text()")
    if hotel_name_en:
        Hotel.hotel_name_en = hotel_name_en[0]
    res = Hotel
    return res


if __name__ == '__main__':
    import csv
    # from proj.my_lib.Common.Browser import MySession
    # session = MySession()
    # url = 'http://www.hilton.com.cn/zh-CN/hotel/Beijing/hilton-beijing-wangfujing-BJSWFHI/'
    url = 'http://www.hilton.com.cn/zh-cn/hotel/sharjah/hilton-sharjah-SHJHSHI/'
    # url = 'http://www.hilton.com.cn/zh-cn/hotel/new-york/millennium-hilton-new-york-one-un-plaza-NYCUPHH/'
    u_list = [
        'http://www.hilton.com.cn/zh-CN/hotel/Beijing/hilton-beijing-wangfujing-BJSWFHI/',
        # 'http://www.hilton.com.cn/zh-cn/hotel/sharjah/hilton-sharjah-SHJHSHI/',
        # 'http://www.hilton.com.cn/zh-cn/hotel/new-york/millennium-hilton-new-york-one-un-plaza-NYCUPHH/',
        # 'http://www.hilton.com.cn/zh-cn/hotel/Chicago/palmer-house-a-hilton-hotel-CHIPHHH/index.html'
    ]
    for url in u_list:
        detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'.format(url.split('/')[-2])
        enDetail_url = 'http://www3.hilton.com/en/hotels/{}/{}/about/amenities.html'.format(url.split("/")[-3], url.split("/")[-2])
        map_info_url = url + 'maps-directions.html'
        desc_url = url + 'about.html'
        print url
        print desc_url
        print detail_url
        print enDetail_url
        print map_info_url
        session = requests.session()
        content = session.get(url).text
        # detail_content = session.get(detail_url).text
        map_info_content = session.get(map_info_url).text
        desc_content = session.get(desc_url).text
        enDetail = session.get(enDetail_url)
        enDetail.encoding = 'utf8'
        enDetail_content = enDetail.text
        other_info = {
            'source_id': '1000',
            'city_id': '50795'
        }
        total_content = [content, map_info_content, desc_content, enDetail_content]
        result = hilton_parser(total_content, url, other_info)
        print result

        dicts = {}
        dicts.update(result.__dict__)
        # print type(r)
        s = [s for s in dicts.keys()]
        l = [f for f in dicts.values()]
        # 写入数据
        csvFile = open("/Users/mioji/Desktop/hilton.csv", "a+")
        #
        writer = csv.writer(csvFile)

        writer.writerow(s)
        writer.writerow(l)
        #
        csvFile.close()
    # 'http://www3.hilton.com/en/hotels/new-york/millennium-hilton-new-york-one-un-plaza-NYCUPHH/about/amenities.html'
    # 'http://www3.hilton.com/en/hotels/millennium-hilton-new-york-one-un-plaza-NYCUPHH//about/amenities.html'
