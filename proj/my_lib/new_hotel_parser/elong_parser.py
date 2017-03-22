#! /usr/bin/env python
# coding=utf-8

import sys

import re
import requests
from lxml import html as HTML

from data_obj import Hotel

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
        # temp_name = root.find_class('t24 yahei')[0].xpath('./text()')[0].strip().encode('utf-8')
        temp_name = root.xpath('//div[@class="t24"]/@title')[0].strip().encode('utf-8')
        k = temp_name.find('(')
        j = temp_name.find(')')
        hotel.hotel_name = temp_name[:k]
        hotel.hotel_name_en = temp_name[k + 1:j]
    except Exception, e:
        print str(e)
        # return hotel_tuple

    print 'hotel.hotel_name=>%s' % hotel.hotel_name
    # print hotel.hotel_name
    print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
    # print hotel.hotel_name_en

    print 'brand=>%s' % hotel.brand_name
    # print hotel.brand_name

    # 解析酒店地址
    try:
        # hotel.address = root.find_class('mr5 left')[0].xpath('./text()')[0].strip().encode('utf-8').spilt(':')[1]
        temp = root.xpath('//span[@class="mr5 left"]/text()')
        hotel.address = temp[0].encode('utf-8').strip().split('：')[1]  # special chinese colon
    except Exception as e:
        print e
        hotel.address = 'NULL'

    print 'hotel.address=>%s' % hotel.address
    # print hotel.address

    try:
        #map_temp = root.xpath('//img[@method="OpenMap"]/@data-src')[0]
        #map_infos = map_pat.findall(map_temp)[0]
        map_infos = map_pat.findall(content)[0]
        hotel.map_info = map_infos[1] + ',' + map_infos[0]
    except Exception, e:
        hotel.map_info = 'NULL'

    print 'map_info=>%s' % hotel.map_info
    # print hotel.map_info

    # 解析酒店星级

    try:
        # star_temp = root.find_class('t24 yahei')[0].xpath('b/@class')[0].encode('utf-8')
        star_temp = root.xpath('//b[contains(@class, "icon_stars")]/@class')[0].encode('utf-8')
        hotel.star = star_temp[-1]
        if hotel.star == ' ':
            hotel.star = -1
    except Exception, e:
        hotel.star = -1

    print 'star=>%s' % hotel.star
    # print hotel.star
    # 解析酒店评分
    try:
        # tp = root.xpath('//div[@class="pertxt_num"]/text()')[0].encode('utf-8')
        tp = root.xpath('//div[contains(@class, "pertxt_num")]/text()')[0].encode('utf-8')
        # t_grade = grade_pat.findall(tp)[0]
        # print 't_grade', t_grade
        hotel.grade = float(tp) * 2 # float(t_grade) * 0.05
    except Exception, e:
        hotel.grade = 'NULL'
    print 'grade=>%s' % hotel.grade
    # print hotel.grade

    # 解析酒店评论数
    try:
        # review_num_str = root.find_class('hrela_comt_total')[0]. \
        #     xpath('a/text()')[0].encode('utf-8').strip()
        # print review_num_str
        review_num_str = root.find_class('fl sum-txt')[0].text_content().strip().encode('utf-8')
        hotel.review_num = int(grade_pat.findall(review_num_str)[0])
    except Exception as e:
        hotel.review_num = -1

    print 'review=>%s' % hotel.review_num
    # print hotel.review_num

    # 解析酒店简介
    try:
        p_tags = root.find_class('dview_info')[0].xpath('dl[1]/dd/p')
        description = ''
        for p in p_tags:
            b_text = p.xpath('./b/text()')  # title
            p_text = p.xpath('./text()')  # description
            if len(b_text):
                description += b_text[0].strip().decode('utf-8') + ':' + p_text[1].strip().decode('utf-8') + '|'

        hotel.description = description[:-1]
    except Exception as e:
        hotel.description = 'NULL'

    print 'description=>%s' % hotel.description
    # print hotel.description

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
    print 'check_in=>%s' % hotel.check_in_time
    # print hotel.check_in_time

    print 'check_out=>%s' % hotel.check_out_time
    # print hotel.check_out_time
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
    print 'hotel.service=>%s' % hotel.service
    # print hotel.service

    if '免费自助停车设施' in hotel.service:
        hotel.is_parking_free = 'Yes'
        hotel.has_parking = 'Yes'
    if '收费自助停车设施' in hotel.service:
        hotel.has_parking = 'Yes'
        hotel.is_parking_free = 'No'
    if '免费 Wi-Fi' in hotel.service:
        hotel.has_wifi = 'Yes'
        hotel.is_wifi_free = 'Yes'

    print 'has_parking=>%s' % hotel.has_parking
    # print hotel.has_parking
    print 'is_parking_free=>%s' % hotel.is_parking_free
    # print hotel.is_parking_free
    print 'has_wifi=>%s' % hotel.has_wifi
    # print hotel.has_wifi
    print 'has_free_wifi=>%s' % hotel.is_wifi_free
    # print hotel.is_wifi_free

    img_items = ''
    try:
        img_list = root.xpath('//ul[@class="hrela_spic_list"]/li/img/@src')
        for img_src in img_list:
            if '306' in img_src:
                img_src = img_src.replace('306', '307')
            img_items += img_src + '|'
        hotel.img_items = img_items[:-1]
    except Exception as e:
        hotel.img_items = 'NULL'

    print 'img_items=>%s' % hotel.img_items
    # print hotel.img_items
    hotel.source = 'elong'
    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']
    return hotel


if __name__ == '__main__':
    # url = 'http://ihotel.elong.com/101703/'
    # url = 'http://ihotel.elong.com/670847/'
    url = 'http://ihotel.elong.com/331466/'
    other_info = {u'source_id': u'670847', u'city_id': u'20236'}
    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.content
    result = elong_parser(content, url, other_info)

    # 如果需要，可以在这里用 print 打印 hotel 对象中的内容。也可直接使用 debug 调试查看 result
    print result.address
