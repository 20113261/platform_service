#! /usr/bin/python
# coding=utf-8

import sys

import re
import requests
from lxml import html as HTML

from data_obj import Hotel
from common.common import get_proxy

from proj.my_lib.Common.KeyMatch import key_is_legal

reload(sys)
sys.setdefaultencoding('utf-8')

img_pat = re.compile(r'slideshow_photos(.*?)];', re.S)
brand_pat = re.compile(r'连锁酒店:(.*?)\.', re.S)
hotel_id_pat = re.compile(r'data-hotel-id="(.*?)"', re.S)
num_pat = re.compile(r'\d', re.S)
grade_pat = re.compile(r'\d+/\d+', re.S)
map_pat = re.compile(r'center=(.*?)&size', re.S)
re_num_pat = re.compile(r'showReviews: parseInt\("(.*?)",', re.S)
re_num_pat2 = re.compile(r'来自.*?(\d+).*?条评语', re.S)


def booking_parser(content, url, other_info):
    hotel = Hotel()
    print 'url=>%s' % url
    # print url
    try:
        content = str(content).decode('utf-8')
        root = HTML.fromstring(content)
    except Exception, e:
        print str(e)

    # 解析酒店中英文名，如果没有中文名则置为英文名，如果都解析失败则退出
    try:
        name_temp = root.xpath('//*[@id="hp_hotel_name"]')[
            0].text_content().encode('utf-8').strip('\t').strip('\n')
        hotel.hotel_name = hotel.hotel_name_en = name_temp
    except Exception:
        pass
        # try:
        #     name_temp = root.xpath('//*[@class="sr-hotel__name"]/text()')[
        #         0].strip().encode('utf-8')
        #
        #     hotel.hotel_name_en = name_temp.split('（')[0].replace('"',
        #                                                           '""').strip()
        #     print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
        #     # print hotel.hotel_name_en
        # except:
        #     try:
        #         name_temp = root.xpath('//div[@id="b_mainContent"]/h1/text()')[
        #             0].strip().encode('utf-8')
        #         hotel.hotel_name = name_temp
        #     except Exception as e:
        #         print '----------', str(e)
        #         # return hotel_tuple
        #         # print 'vvvvvvvvvvvvvvvvv'
    print 'hotel.hotel_name=>%s' % hotel.hotel_name
    print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
    # print hotel.hotel_name
    # 解析酒店品牌名称
    try:
        hotel.brand_name = brand_pat.findall(content)[0].strip().replace('"',
                                                                         '""')
    except Exception, e:
        # print str(e)
        hotel.brand_name = 'NULL'
    print 'brad_name=>%s' % hotel.brand_name
    # print hotel.brand_name
    try:
        pp = root.xpath('//*[@class="map_static_zoom_images"]/img/@src')[
            0].strip().encode('utf-8')
        try:
            map_infos = str(map_pat.findall(pp)[0])
            hotel.map_info = map_infos.split(',')[1] + ',' + map_infos.split(
                ',')[0]
        except Exception, e:
            print 'vvvvv\n'
    except:
        try:
            map_infos = root.xpath(
                '//span[contains(@class , "hp_address_subtitle")]/@data-bbox')[
                0].strip().split(',')
            hotel.map_info = str(
                float(float(map_infos[0]) + float(map_infos[2])) /
                2.0) + ',' + str(
                float(float(map_infos[1]) + float(map_infos[3])) / 2.0)
        except Exception, e:
            print str(e)
            try:
                # map_infos = root.xpath('//span[@itemprop="address"]/@data-bbox')[0].split(',')
                map_infos = root.xpath(
                    '//span[contains(@class , "hp_location_address_line")]/@data-bbox'
                )[0].strip().split(',')
                hotel.map_info = str(
                    float(float(map_infos[0]) + float(map_infos[2])) /
                    2.0) + ',' + str(
                    float(float(map_infos[1]) + float(map_infos[3])) / 2.0)
            except Exception, e:
                map_infos = root.xpath('//a[@id="show_map"]/@data-coords')
                if map_infos:
                    map_infos = str(map_infos[0]).split(',')
                    hotel.map_info = map_infos[0] + ',' + map_infos[1]
                else:
                    latitude = re.findall('booking.env.b_map_center_latitude = (\d+.\d+);', content)[0]
                    longitude = re.findall('booking.env.b_map_center_longitude = (\d+.\d+);', content)[0]
                    hotel.map_info = '{0},{1}'.format(longitude, latitude)
                print str(e)
    print 'map_info=>%s' % hotel.map_info

    # print hotel.map_info
    # 解析酒店地址
    try:
        # hotel.address = root.get_element_by_id('hp_address_subtitle') \
        #     .xpath('text()')[0].encode('utf-8').strip().replace('"', '""')
        strs = root.xpath(
            '//span[contains(@class, "hp_address_subtitle")]/text()')
        hotel.address = strs[0].encode('utf-8').strip().replace('"', '""')
    except Exception as e:
        strs = root.xpath(
            '//span[contains(@class, "hp_location_address_line")]/text()')
        if len(strs):
            hotel.address = strs[0].encode('utf-8').strip().replace('"', '""')
        else:
            try:
                adress_temp = root.xpath(
                    '//p[@class="b_hotelAddress"]//text()')
                adress_temp = ' '.join(map(lambda x: x.replace('\n', ''), adress_temp))
                hotel.address = adress_temp.replace('显示地图', '')
            except Exception as e:
                print e

    print 'address=>%s' % hotel.address
    # print hotel.address
    # 解析酒店星级
    hotel.star = -1
    try:
        star_temp = root.find_class('hp__hotel_ratings__stars')[0].xpath(
            'i/@class')[0].strip()
        hotel.star = num_pat.findall(star_temp)[0]
        hotel.star = int(hotel.star)
    except Exception, e:
        try:
            star_title = root.xpath('//*[@class="nowrap hp__hotel_ratings"]//span[@class="invisible_spoken"]/text()')
            if star_title:
                star = re.findall('(\d+)', star_title[0])
                if star:
                    hotel.star = int(star[0])

            # 当初先非官方评定 start 时，使用 svg 中的 class 获取星级
            if hotel.star == -1:
                star_svg = root.xpath('//*[@class="nowrap hp__hotel_ratings"]//svg/@class')
                if star_svg:
                    star = re.findall('-sprite-ratings_circles_(\d+)', star_svg[0])
                    if star:
                        hotel.star = int(star[0])
        except Exception as e:
            pass
    print 'star=>%s' % hotel.star
    # print hotel.star
    # 解析酒店评分
    try:
        grade_temp = root.xpath(
            '//div[contains(@class, "hotel_large_photp_score")]/@data-review-score'
        )
        hotel.grade = str(grade_temp[0])
    except:
        try:
            grade_temp = root.xpath(
                '//div[@id="review_block_top"]/text()')[1].strip().encode('utf-8')
            hotel.grade = grade_temp
        except Exception as e:
            hotel.grade = 'NULL'
    print 'grade=>%s' % hotel.grade
    # print hotel.grade
    # 解析酒店评论数
    try:
        re_start = root.find_class('trackit score_from_number_of_reviews')[0].xpath('strong/text()') \
            [0].encode('utf-8').strip()
        hotel.review_num = re_start
    except:
        try:
            re_start = root.xpath('//div[@class="location_score_tooltip"]/p[1]/small/strong/text()')[0]
            hotel.review_num = int(re_start)
        except:
            try:
                re_num = root.xpath(
                    '//div[@id="review_block_top"]/text()')[0].strip().encode('utf-8')
                re_num = re.findall(r'\d+', re_num)[0]
                hotel.review_num = re_num
            except Exception as e:
                print e
                hotel.review_num = -1
    print 'review_num=>%s' % hotel.review_num
    # print hotel.review_num
    # 解析酒店简介
    try:
        hotel.description = root.get_element_by_id('summary') \
            .text_content().encode('utf-8').strip().replace('"', '""').replace('\n', '')
        infos = root.xpath(
            '//div[@class="hotel_description_wrapper_exp hp-description"]/p[@class="geo_information"]/text()'
        )
        if len(infos):
            hotel.description += infos[0].strip().replace('\r', '').replace(
                '\n', '')
    except:
        try:
            desc = root.xpath('//div[@class="b_hotelDescription"]/p/text()')
            desc = ''.join(desc)
            hotel.description = desc
        except Exception as e:
            hotel.description = 'NULL'
    print 'description=>%s' % hotel.description
    # print hotel.description
    # 解析酒店接受的银行卡
    try:
        card_list = root.find_class('creditcard')
        card_str_list = []
        hotel.accepted_cards = ''
        for each_card_ele in card_list:
            card_str_list.append(each_card_ele.attrib['class'].replace('creditcard', '') \
                                 .strip())

        for each_card_str in set(card_str_list):
            hotel.accepted_cards += each_card_str + '|'

        hotel.accepted_cards = hotel.accepted_cards[:-1].replace('"', '""')
        if not len(card_list):
            try:
                card_list = root.xpath('//div[@class="description"]/ul/li/text()')[:-1]
                hotel.accepted_cards = '|'.join(card_list)
            except Exception as e:
                hotel.accepted_cards = 'NULL'
    except:
        try:
            card_list = root.xpath('//div[@class="description"]/ul/li/text()')[:-1]
            hotel.accepted_cards = '|'.join(card_list)
        except Exception as e:
            hotel.accepted_cards = 'NULL'

    print 'accepted_card=>%s' % hotel.accepted_cards
    # print hotel.accepted_cards

    # parse check_in time info
    try:
        hotel.check_in_time = root.get_element_by_id('checkin_policy').text_content() \
            .encode('utf-8').strip().replace('\n', ' ').replace('"', '""')
    except:
        try:
            check_in_time = root.xpath(
                '//div[@class="description"]/p[1]/text()')
            hotel.check_in_time = check_in_time[0].strip().encode('utf-8')
        except Exception as e:
            hotel.check_in_time = 'NULL'

    # parse check out time info
    try:
        hotel.check_out_time = root.get_element_by_id('checkout_policy').text_content() \
            .encode('utf-8').strip().replace('\n', ' ').replace('"', '""')
    except:
        try:
            check_out_time = root.xpath(
                '//div[@class="description"]/p[2]/text()')
            hotel.check_out_time = check_out_time[0].strip().encode('utf-8')
        except Exception as e:
            hotel.check_out_time = 'NULL'

    print 'checkintime=>%s' % hotel.check_in_time
    # print hotel.check_in_time

    print 'checkouttime=>%s' % hotel.check_out_time
    # print hotel.check_out_time
    # parse all services at this hotel
    try:
        service_temp_list = root.get_element_by_id('hp_facilities_box').xpath(
            'div')
        servce_ele_parents = []
        for each_service_parent in service_temp_list:
            try:
                if 'facilities' in each_service_parent.attrib['class']:
                    service_parent = each_service_parent
                    break
            except:
                continue
        service_ele_list = root.xpath(
            '//div [@class="facilitiesChecklistSection"]')
        hotel.service = ''
        for each_service_ele in service_ele_list:
            try:
                service_item_name = each_service_ele.xpath('h5/text()')
                for s in service_item_name:
                    if s != '\n':
                        service_item_name = s.strip().decode('utf-8')
                        break
                service_items = each_service_ele.xpath('./ul/li//text()') or each_service_ele.xpath(
                    './div/ul/li/text()')  # \
                service_items = [x for x in map(lambda x: x.replace('\n', '').strip().encode('utf-8'), service_items) if
                                 x]
                service_temp = '|'.join(service_items)
                service_temp = service_item_name + '::' + service_temp + '|'
                if '停车场' in service_temp:
                    hotel.has_parking = 'Yes'
                    if ('付费' or '收费') in service_temp:
                        hotel.is_parking_free = 'No'
                    elif '免费' in service_temp:
                        hotel.is_parking_free = 'Yes'
                if 'WiFi' in service_temp:
                    hotel.has_wifi = 'Yes'
                    if ('付费' or '收费') in service_temp:
                        hotel.is_wifi_free = 'No'
                    elif '免费' in service_temp:
                        hotel.is_wifi_free = 'Yes'
                hotel.service += service_temp
                # .strip().encode('utf-8').replace('\n', '')
                # if service_items[0]:
                #     service_item = each_service_ele.xpath('ul/li/p/span')[0] \
                #         .text_content().strip().encode('utf-8').replace('\n', '')

                #     if '停车场' in service_item_name:
                #         if '无' not in service_item or '不提供' not in service_items:
                #             hotel.has_parking = 'Yes'
                #         else:
                #             hotel.has_parking = 'No'

                #         if '免费' in service_item:
                #             hotel.has_parking = 'Yes'
                #             hotel.is_parking_free = 'Yes'

                #         if '收费' in service_item:
                #             hotel.has_parking = 'Yes'
                #             hotel.is_parking_free = 'No'
                #     if 'WiFi' in service_item_name:
                #         if 'WiFi' in service_item:
                #             hotel.has_wifi = 'Yes'
                #         else:
                #             hotel.has_wifi = 'No'
                #         if '免费' in service_item:
                #             hotel.is_wifi_free = 'Yes'
                #         else:
                #             hotel.is_wifi_free = 'No'
                # else:
                #     p = ''
                #     for each in service_items:
                #         p += each + ','
                #     service_item = p[:-1].replace('\n', '')
            except:
                '''There is a pit, I step on, the next person to continue'''
                continue
        # :-1 delete one |
        hotel.service = hotel.service[:-1]  # .replace('||','|').replace('"','""').encode('utf-8')
    except:
        try:
            elements = root.xpath('//div[@class="hotel_facilities_block"]')
            service = ''
            for s in elements:
                con = s.xpath('./ul[@class="b_newHotelFacilities"]/li/text()') or s.xpath(
                    './p[@class="b_hotelFacilities"]/text()')
                if not len(con):
                    continue
                title = s.xpath('./h3/text()')[0].strip().encode('utf-8')
                temp = title + '::' + '|'.join(map(lambda x: x.strip().encode('utf-8'), con)) + '|'
                if '停车场' in temp:
                    hotel.has_parking = 'Yes'
                    if ('付费' or '收费') in temp:
                        hotel.is_parking_free = 'No'
                    elif '免费' in temp:
                        hotel.is_parking_free = 'Yes'
                if 'WiFi' in temp:
                    hotel.has_wifi = 'Yes'
                    if ('付费' or '收费') in temp:
                        hotel.is_wifi_free = 'No'
                    elif '免费' in temp:
                        hotel.is_wifi_free = 'Yes'
                service += temp
            hotel.service = service[:-1]
        except Exception as e:
            hotel.service = 'NULL'

    print 'service=>%s' % hotel.service
    # print hotel.service
    print 'hotel.has_parking=>%s' % hotel.has_parking
    # print hotel.has_parking
    print 'hotel.is_parking_free=>%s' % hotel.is_parking_free
    # print hotel.is_parking_free
    print 'has_wifi=>%s' % hotel.has_wifi
    # print hotel.has_wifi
    print 'is_wifi_free=>%s' % hotel.is_wifi_free
    # print hotel.is_wifi_free

    # parse all photos link of this hotel
    # try:
    #     hotel.img_items = ''
    #     image_list = root.xpath('//div[@id="photos_distinct"]/a/@href')
    #     for each_img_link in image_list:
    #         hotel.img_items += each_img_link.encode('utf-8') + '|'
    #     hotel.img_items = hotel.img_items[:-1].replace('"', '').encode('utf-8')
    # except Exception, e:
    #     print "kkkk"
    # new img func
    # if hotel.img_items == '':
    try:
        hotelPhoto_str = re.findall('hotelPhotos:([\s\S]+?)]', content)[0] + ']'
        hotel.img_items = '|'.join(
            map(lambda x: x.replace('\'', '').strip() + '.jpg',
                re.findall('large_url:([\s\S]+?).jpg', hotelPhoto_str)))
    except:
        pass

    if not key_is_legal(hotel.img_items):
        try:
            hotels_class = root.find_class('hp-gallery-slides hp-gallery-top')[0]
            img_src = hotels_class.xpath('.//img/@src')[0]
            img_lazy = hotels_class.xpath('.//img/@data-lazy')
            img_items = img_src + '|' + '|'.join(img_lazy)
            hotel.img_items = img_items
        except:
            try:
                img_items = root.xpath('//div[@id="b_imgList"]/ul/li/a/@href')
                img_items = '|'.join(img_items)
                hotel.img_items = img_items
            except Exception as e:
                hotel.img_items = 'NULL'

    print 'img_item=>%s' % hotel.img_items
    # print hotel.img_items
    hotel.source = 'booking'
    hotel.hotel_url = url.encode('utf-8')
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    # url = 'http://www.booking.com/hotel/es/can-daniel.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmaDGIAQGYATK4AQTIAQTYAQPoAQH4AQuoAgM;sid=1a3888c9a794fa93c207d7706d195160;checkin=2017-01-29;checkout=2017-01-30;ucfs=1;soh=1;highlighted_blocks=;all_sr_blocks=;room1=A,A;soldout=0,0;hpos=8;dest_type=region;dest_id=767;srfid=7f4d0bb71de80e36e71921b5dbec9de897b1dbbbX578;highlight_room='
    # url = 'http://www.booking.com/hotel/es/agroturismo-vall-de-pollensa.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmaDGIAQGYATK4AQTIAQTYAQHoAQH4AQuoAgM;sid=04bb4f5be7caced0d2801004dd9e9bec;src=clp;openedLpRecProp=1;ccpi=1'
    # url = 'http://www.booking.com/hotel/es/la-goleta-de-mar-adults-only.zh-cn.html?aid=304142;label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmaDGIAQGYATK4AQTIAQTYAQHoAQH4AQuoAgM;sid=04bb4f5be7caced0d2801004dd9e9bec;dlpvhclck=1'
    # url = 'http://www.booking.com/hotel/gr/boat-in-kalamaki-15-metres-1.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=8bdc392e7d5c8c230273f6a364f8310a;checkin=2017-03-21;checkout=2017-03-22;ucfs=1;highlighted_blocks=123898401_92835396_10_0_0;all_sr_blocks=123898401_92835396_10_0_0;room1=A;hpos=2;dest_type=city;dest_id=-814876;srfid=97c87e489585f18f0756927923581be7fc3f403dX437;from=searchresults;highlight_room='
    # url = 'http://www.booking.com/hotel/lu/b-amp-b-camping-um-gritt.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=04bb4f5be7caced0d2801004dd9e9bec;dest_id=-1735767;dest_type=city;dist=0;group_adults=2;hpos=1;room1=A%2CA;sb_price_type=total;srfid=8f81a85e275aeac120e90e6988461a380a6c849cX1;type=total;ucfs=1&#hotelTmpl'
    # url = 'https://www.booking.com/hotel/th/happy-ville-1.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=760b4b8ac503b49f5d89e67ec36a2fa9;all_sr_blocks=206063304_100081577_2_0_0;checkin=2017-08-03;checkout=2017-08-04;dest_id=-3255732;dest_type=city;dist=0;highlighted_blocks=206063304_100081577_2_0_0;hpos=3;room1=A%2CA;sb_price_type=total;srfid=7078e96d0aca48337ba20a54f0a96429386a2fcfX3;type=total;ucfs=1&#hotelTmpl'
    # url = 'http://www.booking.com/hotel/th/baan-siripornchai.zh-cn.html?aid=376390;label=misc-aHhSC9cmXHUO1ZtqOcw05wS94870954985%3Apl%3Ata%3Ap1%3Ap2%3Aac%3Aap1t1%3Aneg%3Afi%3Atikwd-11455299683%3Alp9061505%3Ali%3Adec%3Adm;sid=1ed4c8a52860a4f5a93489f7b31a8863;checkin=2017-08-03;checkout=2017-08-04;ucfs=1;highlighted_blocks=206274801_98817269_2_0_0;all_sr_blocks=206274801_98817269_2_0_0;room1=A%2CA;hpos=4;dest_type=city;dest_id=-3255732;srfid=7078e96d0aca48337ba20a54f0a96429386a2fcfX4;from=searchresults;highlight_room=#hotelTmpl'
    # url = 'https://www.booking.com/hotel/tr/salim-bey-apartments.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNiBW5vcmVmaDGIAQGYATLCAQNhYm7IAQTYAQPoAQH4AQuoAgQ;sid=0eb36e254059b03c70de3b00ac4ecebd;dcid=12;checkin=2016-05-24;checkout=2016-05-25;ucfs=1;room1=A,A;dest_type=city;dest_id=-755070;srfid=f48fa56e2878c2360bafc2a5cd8bba475e908755X701;highlight_room='
    # url = 'https://www.booking.com/hotel/vn/monte-carlo.zh-cn.html'
    # url = 'http://www.booking.com/hotel/hk/m.zh-cn.html'
    # url = 'http://www.booking.com/hotel/hk/bridal-tea-house-hunghom.zh-cn.html'
    url = 'https://www.booking.com/hotel/de/langerfelder-hof.zh-cn.html'
    other_info = {'source_id': '1016533', 'city_id': '10067'}
    # headers = {
    #     'User-Agent':
    #         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    #     'Referer':
    #         'http://www.booking.com'
    # }
    # PROXY = get_proxy(source="Platform")
    # proxies = {
    #     'http': 'socks5://' + PROXY,
    #     'https': 'socks5://' + PROXY
    # }
    # page = requests.get(url=url, headers=headers, timeout=30)
    import pymongo
    import zlib

    # client = pymongo.MongoClient(host='10.10.231.105')
    # collections = client['PageSaver']['hotel_base_data_170612']
    #
    # content = zlib.decompress(list(collections.find({'source_id': '482499'}).limit(1))[0]['content'])
    # content = requests.get(
    #     'https://www.booking.com/hotel/it/ai-piedi-delle-colline.zh-cn.html').text

    # content = requests.get(
    #     'https://www.booking.com/hotel/us/racpanos-modern-stays-jersey-city.zh-cn.html').text

    content = requests.get(
        'http://10.10.180.145:8888/hotel_page_viewer?task_name=hotel_base_data_booking_new&id=3824a0f6469e5343d25b27f77be83cdc').text

    # print(list(collections.find({'source_id': '482499'}))[0]['task_id'])
    result = booking_parser(content, url, other_info)

    # 如果需要，可以在这里用 print 打印 hotel 对象中的内容。也可直接使用 debug 调试查看 result
    print result.address
