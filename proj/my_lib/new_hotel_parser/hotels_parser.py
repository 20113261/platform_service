#! /usr/bin/env python
# coding=utf-8

import sys

import re
import json
import requests
from lxml import html as HTML

# from data_obj import HotelsHotel  # , DBSession
from proj.my_lib.models.HotelModel import HotelsHotel

star_pat = re.compile(r'在此页面中显示为 (.*) 星')
num_pat = re.compile(r'\d+')
map_pat = re.compile(r'center=(.*?)&zoom', re.S)

check_in = re.compile(r'入住时间开始于(.*?)</li>')
check_out = re.compile(r'退房时间(.*?)</li>')

reload(sys)
sys.setdefaultencoding('utf-8')


def hotels_parser(content, url, other_info):
    hotel = HotelsHotel()
    content = content.decode('utf-8')
    root = HTML.fromstring(content)

    ""
    try:
        source_city_id = re.findall(r'\"cityId\":(\d+),', content)[0]
        hotel.source_city_id = source_city_id.encode('utf8')
    except Exception as e:
        print e

    print 'source_city_id=>%s' % hotel.source_city_id

    try:
        name_temp = root.xpath('//div[@class="property-description"]/div[@class="vcard"]/h1/text()')[0]
    except Exception as e:
        print(str(e))

    try:
        args = re.split('[(（]', name_temp, 2)
        # hotel.hotel_name = name_temp.split('(')[0].strip().encode('utf-8')
        hotel.hotel_name = args[0].strip().encode('utf-8')
        print('hotel_name=>%s' % hotel.hotel_name)
        try:
            hotel.hotel_name_en = args[-1].rsplit('-', 1)[0].replace(')', '').replace('）', '').strip().encode('utf-8')
            # hotel.hotel_name_en = re.findall('\(([\s\S]+?)\)', name_temp)[0].strip().encode('utf-8')
        except Exception:
            pass
        print('hotel_name_en=>%s' % hotel.hotel_name_en)
    except Exception as e:
        print(str(e))

    if hotel.hotel_name_en == 'NULL' and hotel.hotel_name == 'NULL':
        try:
            name_temp = root.xpath('//*[@class="vcard"]/h1/text()')[0].encode('utf-8')
        except Exception as e:
            print(str(e))

        try:
            hotel.hotel_name = name_temp.split('(')[0].strip().encode('utf-8')
            print ('hotel_name=>%s' % hotel.hotel_name)
            try:
                hotel.hotel_name_en = name_temp.split('(')[1].replace(')', '').strip().encode('utf-8')
            except Exception:
                hotel.hotel_name_en = 'NULL'
            # hotel.source_id = root.xpath('//*[@id="roomdesc_mainContainerSize1"]/input[1]/@value')[0]
            print ('hotel_name_en=>%s' % hotel.hotel_name_en)
        except Exception as e:
            print (str(e))
    # -- fengyufei
    if len(re.findall('[\x80-\xff]+', str(hotel.hotel_name_en))) > 0:
        print '------va---'
        name_temp = root.xpath('//div[@class="widget-query-group widget-query-destination"]/input/@value')[0]
        # re.findall('[a-zA-Z ]+',name_temp)
        hotel.hotel_name_en = re.findall('\((.*?)\)', name_temp)[0].encode('utf8')

        try:
            hotel.hotel_name = name_temp.split('({}'.format(hotel.hotel_name_en))[0].strip()
        except Exception:
            pass
        # # 城市清除
        # if '-' in hotel.hotel_name:
        #     hotel.hotel_name = hotel.hotel_name.split('-')[0].strip()

    # 城市清除
    if hotel.hotel_name_en in hotel.hotel_name:
        if '-' in hotel.hotel_name:
            hotel.hotel_name = hotel.hotel_name.split('-')[0].strip()

        if hotel.hotel_name == hotel.hotel_name_en:
            hotel.hotel_name = 'NULL'

    print('hotel_name=>%s' % hotel.hotel_name)
    print('hotel_name_en=>%s' % hotel.hotel_name_en)

    try:
        hotel.address = root.find_class('postal-addr')[0].text_content() \
            .encode('utf-8').strip().replace('\n', '').replace('  ', '')
    except:
        hotel.address = 'NULL'
    print ('address=>%s' % hotel.address)
    # print hotel.address
    try:
        temp = root.find_class('visible-on-small map-widget-wrapper')[0].xpath('div/@style')[0].encode('utf-8').strip()
        map_info = map_pat.findall(temp)[0]
        hotel.map_info = map_info.split(',')[1] + ',' + map_info.split(',')[0]
    except Exception as e:
        # print str(e)
        hotel.map_info = 'NULL'
    print ('map_info=>%s' % hotel.map_info)
    # print hotel.map_info
    try:
        # hotel.postal_code = root.find_class('postal-code')[0].text.strip() \
        #     .encode('utf-8').replace(',', '')
        hotel.postal_code = root.xpath('//span[@itemprop="postalCode"]/text()')[0].strip().encode('utf-8')
    except:
        hotel.postal_code = 'NULL'

    print('postal_code=>%s' % hotel.postal_code)
    # print hotel.postal_code
    star_nums = 0
    try:
        # temp_star = root.xpath('//div [@class="vcard"]/span/span')
        # print 'dasdsadsafdfd'
        # print temp_star
        temp_star = root.xpath('//div[@class="vcard"]/span/text()')[0].strip().encode('utf-8')
        # for i in temp_star:
        #     if i.xpath('./@class')[0] == 'icon icon-star':
        #         star_nums += 1
        #     if i.xpath('./@class')[0] == 'icon icon-star icon-star-scale icon-star-half-parent':
        #         star_nums += 0.5
        star_nums = re.findall(r'\d+', temp_star)
        hotel.star = int(star_nums[0])
    except:
        hotel.star = -1.0
    print ('star=>%s' % hotel.star)
    # print hotel.star
    try:
        hotel.grade = root.find_class('rating')[0].xpath('strong/text()')[0]
        hotel.grade = float(hotel.grade)
    except:
        try:
            if not hotel.grade:
                grade = root.xpath('//div[@class="logo-wrap"]/span[1]/text()')[0].encode('utf-8')
                grade = re.search(r'[0-9\.]+', grade).group(0)
                hotel.grade = float(grade)
        except Exception as e:
            print(e)
            hotel.grade = -1.0

    print ('hotel.grade=>%s' % hotel.grade)
    # print hotel.grade
    try:
        review_num_temp = root.find_class('total-reviews')[0].text
        review_num = num_pat.findall(review_num_temp)[0]
        hotel.review_num = int(review_num)
    except:
        hotel.review_num = -1

    print ('review_num_temp=>%s' % hotel.review_num)
    # print hotel.review_num

    first_img = None
    try:
        img_list = root.xpath('//div[@id="carousel-container"]/div[1]/ul/li[@data-src]')
        hotel.img_items = ''
        for i, li in enumerate(img_list):
            src = li.xpath('./@data-src')
            if len(src):
                size = li.xpath('./@data-sizes')
                if 'z' in size[0]:
                    img_url = src[0].strip().encode('utf-8').replace('{size}', 'z')
                else:
                    if 'y' in size[0]:
                        img_url = src[0].strip().encode('utf-8').replace('{size}', 'y')
                    else:
                        img_url = src[0].strip().encode('utf-8').replace('{size}', 'n')
                if i == 0:
                    first_img = img_url
                hotel.img_items += img_url + '|'
        hotel.img_items = hotel.img_items[:-1]

        if not hotel.img_items:
            img_list = root.xpath('//div[@id="carousel-container"]/div[1]/ul/li[@data-desktop]')
            hotel.img_items = ''
            for i, li in enumerate(img_list):
                img_url = li.xpath('./@data-desktop')[0]
                hotel.img_items += img_url + '|'

        hotel.img_items = hotel.img_items[:-1]
        # image_list = root.find_class('carousel-thumbnails')[0].xpath('ol/li')
        # hotel.img_items = ''
        # image_name = ''
        # hotel.img_items = ''
        # for each_image_ele in image_list:
        #     image_url = each_image_ele.xpath('a/@href')[0]
        #     hotel.img_items += image_url + '|'
        # hotel.img_items = hotel.img_items[:-1]
    except Exception as e:
        hotel.img_items = 'NULL'

    print ('hotel_img_items=>%s' % hotel.img_items)
    print 'first_img=>%s' % first_img
    # print hotel.img_items

    try:
        description_temp = root.get_element_by_id('overview').xpath('b/text()')[0] \
            .encode('utf-8').strip()
        hotel.description = description_temp
    except Exception as e:
        print (str(e))
        hotel.description = 'NULL'

    if hotel.description == 'NULL':
        try:
            hotel.description = root.xpath('// div[@class="tagline"]')[0].text_content().strip()
        except Exception as e:
            print(str(e))
            hotel.description = 'NULL'

    print ('description=>%s' % hotel.description)
    # print hotel.description

    try:
        service = ''
        service_list = root.xpath('//div[@id="overview-columns"]/div')
        for div in service_list:
            title = div.xpath('./h3/text()')[0].strip().encode('utf-8') + ':'
            li_list = div.xpath('./ul/li/text()')
            for li in li_list:
                title += li.strip().encode('utf-8') + ','
            # delete last comma
            service += title[:-1] + '|'
            # service_list = root.find_class('main-amenities two-columned')[0].xpath('ul/li')
            # for each in service_list:
            #     service += each.text_content().encode('utf-8').strip() + '|'
    except Exception as e:
        print (str(e))
        hotel.service = 'NULL'
    hotel.service = service[:-1]
    print ('service=>%s' % hotel.service)
    # print hotel.service

    try:
        temp = root.find_class('col-6-24 travelling-container resp-module')[0]
        wifi_text = temp.text_content()  # HTML.tostring(temp).encode('utf-8').strip()
        if 'WiFi' in wifi_text:
            hotel.has_wifi = 'Yes'
            if '免费WiFi' in wifi_text:
                hotel.is_wifi_free = 'Yes'
            else:
                hotel.is_wifi_free = 'No'
        else:
            hotel.has_wifi = 'No'
            hotel.is_wifi_free = 'NO'
    except Exception as e:
        print(str(e))
        hotel.has_wifi = 'NULL'

    print ('has_wifi=>%s' % hotel.has_wifi)
    print ('is_wifi_free=>%s' % hotel.is_wifi_free)
    # print hotel.has_wifi

    try:
        temp = root.find_class('col-6-24 transport-container last resp-module')[0]
        car_text = temp.text_content()  # HTML.tostring(temp).encode('utf-8').strip()
        if '无停车' not in car_text:
            hotel.has_parking = 'Yes'
            if '免费自助停车' in car_text:
                hotel.is_parking_free = 'Yes'
            else:
                hotel.is_parking_free = 'No'
        else:
            hotel.has_parking = 'No'
            hotel.is_parking_free = 'No'
            # if car_text.find('免费自助停车'):
            #     hotel.has_parking = 'Yes'
            #     hotel.is_parking_free = 'Yes'
            # if car_text.find('停车场'):
            #     hotel.has_parking = 'Yes'
    except Exception as e:
        print(str(e))
        hotel.has_parking = 'NULL'
        hotel.is_parking_free = 'NULL'
    print ('has_park=>%s' % hotel.has_parking)
    # print hotel.has_parking

    print ('is_parking_free=>%s' % hotel.is_parking_free)
    # print hotel.is_parking_free

    try:
        temp = root.xpath('//*[@id="at-a-glance"]/div/div[1]/div[2]/div/ul[2]')[0]
        check_in_time = temp.xpath('./li[1]/text()')[0]
        check_out_time = temp.xpath('./li[2]/text()')[0]
    except Exception as e:
        print(str(e))
        check_in_time = 'NULL'
        check_out_time = 'NULL'

    hotel.check_in_time = check_in_time.encode('utf-8')
    hotel.check_out_time = check_out_time.encode('utf-8')
    print('hotelcheck_in_time=>%s' % hotel.check_in_time)
    # print hotel.check_in_time
    print('hotel_check_out_time=>%s' % hotel.check_out_time)
    # print hotel.check_out_time
    hotel.source = 'hotels'

    hotel.hotel_url = url
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    if first_img:
        hotel.others_info = json.dumps({'first_img': first_img})

    return hotel


if __name__ == '__main__':
    # url = 'http://www.hotels.cn/hotel/details.html?WOE=2&q-localised-check-out=2015-11-10&WOD=1&q-room-0-children=0&pa=252&tab=description&q-localised-check-in=2015-11-09&hotel-id=119538&q-room-0-adults=2&YGF=14&MGT=1&ZSX=0&SYE=3'
    # url = 'https://ssl.hotels.cn/hotel/details.html?pa=1&tab=description&hotel-id=430714&q-room-0-adults=2&ZSX=0&SYE=3&q-room-0-children=0'
    # url = 'https://zh.hotels.com/ho182001/?MGT=1&SYE=3&WOD=6&WOE=7&YGF=14&ZSX=0&pa=188&q-check-in=2017-06-03&q-check-out=2017-06-04&q-room-0-adults=2&q-room-0-children=0&tab=description'
    other_info = {
        'source_id': '119538',
        'city_id': '10001'
    }
    # url = 'http://zh.hotels.com/hotel/details.html?q-check-out=2018-01-04&q-check-in=2018-01-03&WOE=4&WOD=3&q-room-0-children=0&pa=157&tab=description&hotel-id=666153&q-room-0-adults=2&YGF=14&MGT=1&ZSX=0&SYE=3'
    # url = 'https://zh.hotels.com/ho223637/'
    # url = 'https://zh.hotels.com/ho536186/'
    from proj.my_lib.Common.Browser import MySession

    # url = 'https://zh.hotels.com/ho619519840/'
    # url = 'https://zh.hotels.com/ho416746/'
    url = 'https://zh.hotels.com/ho416746/'
    url = 'https://zh.hotels.com/ho223798/'
    with MySession(need_cache=True) as session:
        # page = requests.get(url)
        page = session.get(url=url)
    page.encoding = 'utf8'
    content = page.text
    result = hotels_parser(content, url, other_info)

    # try:
    #     session = DBSession()
    #     session.add(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
