#! /usr/bin/python
# coding=utf-8

import sys

import re
import requests
import json
from lxml import html as HTML

# from data_obj import BookingHotel
from proj.my_lib.models.HotelModel import BookingHotel
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
    hotel = BookingHotel()
    print 'url=>%s' % url
    # print url
    try:
        content = str(content).decode('utf-8')
        root = HTML.fromstring(content)
    except Exception, e:
        print str(e)

    try:
        source_city_id = re.findall(r'params.context_dest_id = \'([-+]?\d+)\'', content)[0]
        hotel.source_city_id = source_city_id.encode('utf8')
    except Exception as e:
        print e

    print 'source_city_id=>%s' % hotel.source_city_id

    # 解析酒店中英文名，如果没有中文名则置为英文名，如果都解析失败则退出
    # try:
    #     name_temp = root.xpath('//*[@class="hp__hotel-name"]')[
    #         0].text_content().strip('\t').strip('\n')
    #
    #     temp = re.findall(ur'([\u4e00-\u9fa5])*', name_temp)
    #     zh_name_tmep = [t for t in temp if t and t!=' ']
    #     if len(zh_name_tmep)>0:
    #         hotel.hotel_name = zh_name_tmep[0].encode('utf8')
    #     else:
    #         hotel.hotel_name = ''
    #
    #     if not zh_name_tmep:
    #         hotel.hotel_name_en = name_temp.strip(')').strip('(').strip('）').strip('（').strip().encode('utf8')
    #     else:
    #         name_en_temp = name_temp[:name_temp.find(zh_name_tmep[0][0])] + name_temp[
    #                                                                         name_temp.find(zh_name_tmep[0][-1])+1:]
    #         hotel.hotel_name_en = name_en_temp.strip(')').strip('(').strip('）').strip('（').strip().encode('utf8')
    # except Exception as e:
    #     print e
    try:
        name_temp = root.xpath('//*[@class="hp__hotel-name"]')[
            0].text_content().strip('\t').strip('\n')
        temp_name = name_temp.split('（')
        if len(temp_name) == 1:
            temp_name = name_temp.split('(')
        if len(temp_name) == 2:
            hotel.hotel_name_en, hotel.hotel_name = temp_name[0].encode('utf8'), temp_name[1].strip(')').strip(
                '）').encode('utf8')
        elif len(temp_name) == 1:
            temp = re.findall(r'\w+', temp_name[0])
            if len(temp) == 0:
                hotel.hotel_name = temp_name[0].encode('utf8')
                hotel.hotel_name_en = 'NULL'
            else:
                hotel.hotel_name = 'NULL'
                hotel.hotel_name_en = temp_name[0].encode('utf8')
    except Exception as e:
        print e

    # try:
    #         name_temp = root.xpath('//*[@class="sr-hotel__name"]/text()')[
    #             0].strip().encode('utf-8')
    #
    #         hotel.hotel_name_en = re.split('（')[0].replace('"',
    #                                                               '""').strip()
    #         print 'hotel.hotel_name_en=>%s' % hotel.hotel_name_en
    #         # print hotel.hotel_name_en
    #     except:
    #         try:
    #             name_temp = root.xpath('//div[@id="b_mainContent"]/h1/text()')[
    #                 0].strip().encode('utf-8')
    #             hotel.hotel_name = name_temp
    #         except Exception as e:
    #             print '----------', str(e)
    #             # return hotel_tuple
    #             # print 'vvvvvvvvvvvvvvvvv'
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
                    lat_tmp = re.findall('booking.env.b_map_center_latitude = (-+\d+.\d+);', content)
                    latitude = lat_tmp[0] if len(lat_tmp) > 0 else 0
                    lon_tmp = re.findall('booking.env.b_map_center_longitude = (-+\d+.\d+);', content)
                    longitude = lon_tmp[0] if len(lon_tmp) > 0 else 0
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
    except:
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
            if hotel.star == -1:
                star_svg = root.xpath('//span[@class="hp__hotel_ratings__stars"]//svg[@class]')
                print "star_svg:", star_svg
                if star_svg:
                    hotel.star = int(re.search(r'\d+', star_svg[0].attrib.get('class')).group(0))

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
        score = re.findall('(\d+)', root.xpath(
            '//a[@class="hp_nav_reviews_link toggle_review track_review_link_zh"]/span/text()')[1])[0]
        # re_start = root.find_class('trackit score_from_number_of_reviews')[0].xpath('strong/text()') \
        #     [0].encode('utf-8').strip()
        # hotel.review_num = re_start
        hotel.review_num = score.encode('utf8')
    except Exception as e:
        print e
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
            .text_content().encode('utf-8').strip().replace('"', '""').replace('\n', '').replace(
            '抱歉，该住宿简介暂无您所选择的语言版本，目前正在更新中。', '')
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
            '//div[@class="facilitiesChecklistSection"]')
        service_ele_list.extend(root.xpath(
            '//div[@class="facilitiesChecklistSection\n"]'))
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
                hotel.service += service_temp.encode('utf-8')
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
                service += temp.encode('utf-8')
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

    first_img = None
    if not key_is_legal(hotel.img_items):
        try:
            hotels_class = root.find_class('hp-gallery-slides hp-gallery-top')[0]
            img_src = hotels_class.xpath('.//img/@src')[0]
            img_lazy = hotels_class.xpath('.//img/@data-lazy')
            img_items = img_src + '|' + '|'.join(img_lazy)
            first_img = img_src
            hotel.img_items = img_items
        except:
            try:
                img_items = root.xpath('//div[@id="b_imgList"]/ul/li/a/@href')
                img_items = '|'.join(img_items)
                hotel.img_items = img_items
            except Exception as e:
                hotel.img_items = 'NULL'

            try:
                first_img = root.xpath('//a[contains(@class, "active-image")]/img/@src')[0]
                if not hotel.img_items:
                    hotel.img_items += first_img
            except Exception as e:
                print e

    print 'img_item=>%s' % hotel.img_items
    print 'first_img=>%s' % first_img
    # print hotel.img_items
    hotel.source = 'booking'
    hotel.hotel_url = url.encode('utf-8')
    if other_info.get('hid'):
        hotel.source_id = re.search("b_hotel_id: ?'(-?\d+)'", content).groups()[0]
        # hotel.source_id = re.search('dest_id=(-?\d+)', content).groups()[0]
    else:
        hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    if first_img:
        hotel.others_info = json.dumps({'first_img':first_img, 'hid':other_info.get('hid', 'NULL')})

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
    # url = 'https://www.booking.com/hotel/de/langerfelder-hof.zh-cn.html'
    other_info = {'source_id': '1016533', 'city_id': '10067', 'hid':1234}
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
    # url = 'http://www.booking.com/hotel/de/convita.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19kZYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC6gCBA;sid=92b989ea6f07f4de2b13417b5ee27147;checkin=2017-06-03;checkout=2017-06-04;ucfs=1;aer=1;group_adults=3;group_children=0;req_adults=3;req_children=0;room1=A%2CA%2CA;highlighted_blocks=6808902_89933034_0_1_0%2C6808901_89933034_0_1_0;all_sr_blocks=6808902_89933034_0_1_0%2C6808901_89933034_0_1_0;hpos=6;dest_type=city;dest_id=-1876189;srfid=c597a73a7c35b00d3a02a668f2b753cada34ce8aX21;from=searchresults;highlight_room=;spdest=ci/-1876189;spdist=9.1;shp=1#hotelTmpl'
    # url = 'http://www.booking.com/hotel/es/tagara-apartment.zh-cn.html'
    # url = 'http://www.booking.com/hotel/fr/ibis-cdg-paris-nord-2.zh-cn.html'
    url = 'https://www.booking.com/hotel/ec/iguana-crossing-boutique.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ;sid=4a276ca86d3797ed736f2d6001496e2f;dest_id=722;dest_type=region;dist=0;hapos=9;hpos=9;room1=A%2CA;sb_price_type=total;srepoch=1506333740;srfid=1dc4de7f7618b923f33a72e5cd5d959ad27f62e5X9;srpvid=f06a4695a2200507;type=total;ucfs=1&#hotelTmpl'
    # url = 'http://www.booking.com/hotel/fr/ibis-cdg-paris-nord-2.zh-cn.html'
    from proj.my_lib.Common.Browser import MySession
    url = 'https://www.booking.com/hotel/fr/mattle.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNYBHIFdXNfY2GIAQGYATLCAQNhYm7IAQzYAQPoAQGSAgF5qAIE;sid=c475c497528f36b236ee530edb71bb6a;all_sr_blocks=24239201_89341537_0_2_0;bshb=2;checkin=2017-12-15;checkout=2017-12-16;dest_id=-1456928;dest_type=city;dist=0;dotd_fb=1;group_adults=2;hapos=1;highlighted_blocks=24239201_89341537_0_2_0;hpos=1;room1=A%2CA;sb_price_type=total;srepoch=1512100793;srfid=148ffde1200dcb2f7dffa4b7b7586b050a6af7f4X1;srpvid=4f041c1bc7720018;type=total;ucfs=1&#hotelTmpl'
    # url = 'https://www.booking.com/hotel/fj/nanuya-island-resort.zh-cn.html?label=gen173nr-1FCAEoggJCAlhYSDNiBW5vcmVmcgV1c19jYYgBAZgBMsIBA2FibsgBDNgBAegBAfgBC5ICAXmoAgQ;sid=4a276ca86d3797ed736f2d6001496e2f;dest_id=4853;dest_type=region;dist=0;group_adults=3;group_children=0;hapos=1;hpos=1;room1=A%2CA;sb_price_type=total;srepoch=1506333732;srfid=452f34ec0e2eeb2f13d876a3d651ba87b1a3b91fX1;srpvid=2a1b469190400118;type=total;ucfs=1&#hotelTmpl'
    url = 'https://www.booking.com/hotel/fr/minerve.zh-cn.html?label=gen173nr-1DCAEoggJCAlhYSDNYBHIFdXNfY2GIAQGYATLCAQNhYm7IAQzYAQPoAQGSAgF5qAIE;sid=c475c497528f36b236ee530edb71bb6a;all_sr_blocks=38107304_101309992_0_2_0;bshb=2;checkin=2017-12-15;checkout=2017-12-16;dest_id=-1456928;dest_type=city;dist=0;group_adults=2;hapos=4;highlighted_blocks=38107304_101309992_0_2_0;hpos=4;room1=A%2CA;sb_price_type=total;srepoch=1512100793;srfid=148ffde1200dcb2f7dffa4b7b7586b050a6af7f4X4;srpvid=4f041c1bc7720018;type=total;ucfs=1&#hotelTmpl'
    content = requests.get(url).text
    # print(list(collections.find({'source_id': '482499'}))[0]['task_id'])
    result = booking_parser(content, url, other_info)

    # 如果需要，可以在这里用 print 打印 hotel 对象中的内容。也可直接使用 debug 调试查看 result
    print result.address
