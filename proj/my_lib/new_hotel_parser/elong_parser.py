#! /usr/bin/env python
# coding=utf-8

import sys
import traceback
import re
import requests
from lxml import html as HTML
# from selenium.webdriver.phantomjs import webdriver
# from data_obj import ElongHotel
from proj.my_lib.models.HotelModel import ElongHotel
import json
import execjs
from urlparse import urljoin
reload(sys)
sys.setdefaultencoding('utf-8')

map_pat = re.compile(r'center=(.*?),(.*?)&', re.S)
num_pat = re.compile(r'\d+', re.S)
hotel_id_pat = re.compile(r'HotelId":(.*?),"HotelLowestPrice', re.S)
grade_pat = re.compile(r'(\d+)', re.S)


def elong_parser(content, url, other_info):
    hotel = ElongHotel()

    try:
        root = HTML.fromstring(content.decode('utf-8'))
        phantom_js = execjs.get('PhantomJS')
        js_str = root.xpath('//script[contains(text(),"window.newDetailController")]/text()')[0]
        page_js = phantom_js.compile(js_str[js_str.index('window.newDetailController'):][:-1])
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
    except Exception as e:
        try:
            hotel.hotel_name = root.find_class('hrela_name-cn')[0].xpath('./text()')[0].strip()
            hotel.hotel_name_en = root.find_class('hrela_name-en')[0].xpath('./text()')[0].strip()
        except Exception as e:
            print(str(e))
            # return hotel_tuple

    # 中英文名相同时只保留一个
    if hotel.hotel_name == hotel.hotel_name_en:
        if isinstance(hotel.hotel_name, str):
            hotel_name = hotel.hotel_name
        else:
            hotel_name = hotel.hotel_name.decode('utf8')
        if any(map(lambda x: u'\u4e00' <= x <= u'\u9fa5', hotel_name)):
            hotel.hotel_name_en = 'NULL'
        else:
            hotel.hotel_name = 'NULL'

    print('hotel.hotel_name=>%s' % hotel.hotel_name)
    # print hotel.hotel_name
    print('hotel.hotel_name_en=>%s' % hotel.hotel_name_en)
    # print hotel.hotel_name_en
    print('brand=>%s' % hotel.brand_name)
    # print hotel.brand_name

    # 解析酒店地址
    try:
        # hotel.address = root.find_class('mr5 left')[0].xpath('./text()')[0].strip().encode('utf-8').spilt(':')[1]
        temp = root.xpath('//span[@class="mr5 left"]/text()')
        hotel.address = temp[0].encode('utf-8').strip().split('：')[1]  # special chinese colon
    except Exception as e:
        print(e)
        hotel.address = 'NULL'

    if hotel.address == 'NULL':
        try:
            hotel.address = root.xpath('//span[@class="icon-address"]/text()')[0].replace('地址：', '').strip()
        except Exception as e:
            print(e)
            hotel.address = 'NULL'

    print('hotel.address=>%s' % hotel.address)
    # print hotel.address

    try:
        lat = re.findall(r'"lat":"([-+\d\.]*)"', content)[0]
        lon = re.findall(r'"lon":"([-+\d\.]*)"', content)[0]
        # map_infos = map_pat.findall(content)[0]
        hotel.map_info = '{},{}'.format(lon, lat)
    except:
        try:
            map_infos = page_js.eval('window.newDetailController').get('AjaxHotelInfo',{}).get('HotelGeoInfo',{})
            lat = map_infos.get('Lat',None)
            lon = map_infos.get('Long',None)
            hotel.map_info = '{0},{1}'.format(lon,lat)
        except Exception as e:
            hotel.map_info = 'NULL'
            print traceback.format_exc(e)

    print 'map_info=>%s' % hotel.map_info
    # print hotel.map_info

    # 解析酒店星级

    try:
        # star_temp = root.find_class('t24 yahei')[0].xpath('b/@class')[0].encode('utf-8')
        star_temp = root.xpath('//b[contains(@class, "icon_stars")]/@class')[0].encode('utf-8')
        hotel.star = star_temp[-1]
        if hotel.star == ' ':
            hotel.star = -1
    except:
        try:
            star_temp = page_js.eval('window.newDetailController').get('RecommendHotelRequest',{}).get('starLevel','')
            if json.loads(star_temp):
                hotel.star = json.loads(star_temp)[0]
        except Exception as e:
            hotel.star = -1

    print 'star=>%s' % hotel.star
    # print hotel.star
    # 解析酒店评分
    try:
        grade = page_js.eval('window.newDetailController').get('scoreInfo', {}).get('comment_score', '')
        hotel.grade = grade

    except:
        try:
            grade = root.xpath('//div[@id="hover-hrela"]/p[1]')
            hotel.grade = float(re.search(r'[0-9\.]+', grade[0].text).group(0))
        except:
            try:
                # tp = root.xpath('//div[@class="pertxt_num"]/text()')[0].encode('utf-8')
                tp = root.xpath('//div[contains(@class, "pertxt_num")]/text()')[0].encode('utf-8')
                # t_grade = grade_pat.findall(tp)[0]
                # print 't_grade', t_grade
                hotel.grade = float(tp)  # float(t_grade) * 0.05
            except Exception as e:
                hotel.grade = 'NULL'
    print 'grade=>%s' % hotel.grade
    # print hotel.grade

    # 解析酒店评论数
    try:
        review_num_str = page_js.eval('window.newDetailController').get('scoreInfo', {}).get('comment_count', '')
        hotel.review_num = review_num_str
    except Exception as e:
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
        hotel.description = description[:-1].encode('utf-8')
        if hotel.description == '':
            hotel.description = p_tags[0].text_content().strip().encode('utf-8')
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
        k = temp_time.find('退房时间：')
        if k != -1:
            hotel.check_out_time = temp_time[k + 15:]
    except:
        hotel.check_out_time = 'NULL'
    print 'check_in=>%s' % hotel.check_in_time
    # print hotel.check_in_time

    print 'check_out=>%s' % hotel.check_out_time
    # print hotel.check_out_time
    # parse all services at this hotel

    try:
        service = ''
        accept_card = []
        service_list = root.xpath('//*[@id="serverall"]/li/text()')
        for each in service_list:
            service += each.encode('utf-8').strip() + '|'
            if '卡' in each:
                accept_card.append(each.strip())
        hotel.service = service[:-1]
    except Exception, e:
        hotel.service = 'NULL'
    if accept_card:
        hotel.accepted_cards = '|'.join(accept_card).encode('utf-8')
    print 'hotel.service=>%s' % hotel.service
    print 'hotel.accept_cards=>%s' % hotel.accepted_cards
    # print hotel.service
    first_img = None
    try:
        pattern_img = root.xpath('//div[@class="newdetaiL-img imgMore"]/@style')[0]
        first_img = re.search(r'url\(([^)]+)\)', pattern_img).group(1)
    except Exception as e:
        print e
    #others_info信息
    print 'first_img=>%s' % first_img

    city_name = 'NULL'
    try:
        city_name = page_js.eval('window.newDetailController')['Region']['RegionName']
    except Exception as e:
        print e
    print city_name
    hotel.city = city_name
    hotel.others_info = json.dumps({'city_name': city_name, 'first_img': first_img, 'hid':other_info.get('hid', 'NULL')})

    #获取source_city_id

    source_city_id = 'NULL'
    try:
        pattern_city_id = root.xpath('//p[@class="link555 t12"]/a[contains(@href,"region")]/@href')[0]
        source_city_id = re.search(r'[0-9]+',pattern_city_id).group()
    except Exception as e:
        print e
    hotel.source_city_id = source_city_id
    print "hotel.source_city_id",hotel.source_city_id
    # print "hotel.others_info:",hotel.others_info

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

        base_url = page_js.eval('window.newDetailController').get('BaseUrl')
        base_url = urljoin(base_url,'ihotel_848_470_all/')
        if not img_items:
            keys = page_js.eval('window.newDetailController').get('HotelImageTagList',{}).get("urlList",{}).keys()
            img_lists =[]
            for key in keys:
                img_list = page_js.eval('window.newDetailController').get('HotelImageTagList',{}).get("urlList",{}).get(key,{}).get('tagUrlList',{})
                img_lists.extend(img_list.values())
        img_lists = [base_url+img for img in img_lists]
        hotel.img_items = '|'.join(img_lists).encode('utf-8')
    except Exception as e:
        hotel.img_items = 'NULL'

    print 'img_items=>%s' % hotel.img_items
    # print hotel.img_items
    info_list = hotel.address.split(' ')
    hotel.country = info_list[-1]
    hotel.source = 'elong'
    hotel.hotel_url = url
    if other_info.get('hid'):
        hotel.source_id = re.search('/(\d+)/', url).groups()[0]
        # hotel.source_id = re.search('RegionId: ?"(\d+)"', content).groups()[0]
    else:
        hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    # others_info_dict = hotel.__dict__
    # if first_img:
    #     others_info_dict['first_img'] = first_img
    # hotel.others_info = json.dumps(others_info_dict)
    # if first_img:
    #     del others_info_dict['first_img']
    # print hotel

    return hotel


# def elong_json_parser(url):
#     browser = webdriver.WebDriver(executable_path='/Users/miojilx/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs')
#     browser.get(url)
#     elong_json = browser.execute_script("return window.newDetailController")
#     hotel = Hotel()
#
#     # 解析酒店中英文名，如果没有中文名则置为英文名，如果都解析失败则退出
#     try:
#         hotel_name = elong_json.get("AjaxHotelInfo",{}).get("HotelDisplayName",None)
#         if hotel_name:
#             hotel.hotel_name = re.search(r'(\W+)\(',hotel_name.decode('utf-8')).group(1)
#             hotel.hotel_name_en = re.search(r'\(([\w ]*)\)',hotel_name.decode('utf-8')).group(1)
#             print hotel.hotel_name,hotel.hotel_name_en
#     except Exception as e:
#         hotel.hotel_name_en = ''
#         hotel.hotel_name = ''
#     print "hotel_name:",hotel.hotel_name
#     print "hotel_name_en:",hotel.hotel_name_en
#     #解析酒店地址
#     try:
#         pass
#     except Exception as e:
#         print "address:",hotel.address
#
#     #解析酒店经纬度
#     try:
#         lon = elong_json.get("RecommendHotelRequest",{}).get("Geo_Info.lon",None)
#         lat = elong_json.get("RecommendHotelRequest",{}).get("Geo_Info.lat")
#         if  lon and lat :
#             hotel.map_info = lon + ',' + lat
#         else:
#             lon = elong_json.get("AjaxHotelInfo",{}).get("HotelGeoInfo",{}).get("Long",None)
#             lat = elong_json.get("AjaxHotelInfo",{}).get("HotelGeoInfo",{}).get("Lat",None)
#             if lon and lat:
#                 hotel.map_info = lon+','+lat
#     except Exception as e:
#         print e
#     print "map_info:",hotel.map_info
#
#     # 解析酒店星级
#     try:
#         star = elong_json.get("RecommendHotelRequest",{}).get("starLevel",None)
#         if star:
#             hotel.star = re.search(r'[\d\.]+',star).group(0)
#     except Exception as e:
#         hotel.star = -1
#     print "star:",hotel.star
#
#     #解析酒店评分
#     try:
#         grade = elong_json.get("scoreInfo",{}).get("comment_score",None)
#         if grade:
#             hotel.grade = float(grade)
#     except Exception as e:
#         hotel.grade = 'NULL'
#
#     #解析酒店评论数
#     try:
#         pass
#     except Exception as e:
#         hotel.review_num = -1
#
#     #图片列表解析
#     try:
#         pass
#     except Exception as e:
#         pass

if __name__ == '__main__':
    # url = 'http://ihotel.elong.com/101703/'
    # url = 'http://ihotel.elong.com/670847/'
    # url = 'http://ihotel.elong.com/331466/'
    url = 'http://ihotel.elong.com/323558/'
    #url = 'http://ihotel.elong.com/343475/'
    #url = 'http://ihotel.elong.com/443150/'
    #url = 'http://ihotel.elong.com/589177/'
    #url = 'http://ihotel.elong.com/31131/'
    #url = 'http://ihotel.elong.com/308868/'
    url = 'http://ihotel.elong.com/765629/'
    url = 'http://ihotel.elong.com/611803/'
    url = 'http://ihotel.elong.com/133277/'
    url = 'http://ihotel.elong.com/72746/'
    url = 'http://ihotel.elong.com/302895/'
    url = 'http://ihotel.elong.com/592426/'
    url = 'http://ihotel.elong.com/590800/'
    other_info = {u'source_id': u'670847', u'city_id': u'20236', 'hid':1234}

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.content
    # with open('content.txt','w+') as temp:
    #     temp.write(content)
    result = elong_parser(content, url, other_info)

    # 如果需要，可以在这里用 print 打印 hotel 对象中的内容。也可直接使用 debug 调试查看 result
    print result.address
