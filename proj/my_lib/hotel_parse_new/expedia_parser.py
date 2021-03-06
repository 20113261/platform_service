#! /usr/bin/env python
# coding=utf-8

import json
import sys

import re
import urlparse
import requests
import json
# from common.logger import logger
from lxml import html as HTML
# from data_obj import ExpediaHotel  # DBSession
from proj.my_lib.models.HotelModel import HotelNewBase
# from mioji.common.class_common import Hotel_New as HotelNewBase

reload(sys)
sys.setdefaultencoding('utf-8')
map_pattern = re.compile(r'center=(.*?)')


def expedia_parser(content, url, other_info):
    hotel = HotelNewBase()
    try:
        html = HTML.fromstring(content.decode('utf-8'))
        html = HTML.make_links_absolute(html, base_url=url)
    except Exception, e:
        print str(e)

    try:
        root = html.find_class('hotelInformation')[0]
    except Exception, e:
        print str(e)

    try:
        source_city_id = re.findall(r"cityRegionId: '(\d+)',", content)[0]
        if str(source_city_id) == '0':
            source_city_id_str = re.search(r'backToSearchParams:(.*)(?=,)',content).group(1)
            source_city_id = json.loads(source_city_id_str.strip()).get('regionId','NULL')
        hotel.source_city_id = source_city_id.encode('utf8')
    except Exception as e:
        print e
    # print 'source_city_id=>%s' % hotel.source_city_id


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
    # print 'hotel_brand_name=>%s' % hotel.brand_name
    # print 'hotel_name=>%s' % hotel.hotel_name
    # print 'hotel_name_en=>%s' % hotel.hotel_name_en
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
    # print 'postal_code=>%s' % hotel.postal_code
    # print 'address=>%s' % hotel.address
    try:
        # grade = root.find_class('guest-rating')[0].find_class('rating-number')[0].text_content()
        grade_str = html.xpath("//span[@class='rating-scale-low-res']/text()")[0]
        grade = re.search(u"评分：(.*)/", grade_str.strip()).group(1)
        hotel.grade = float(grade)
    except Exception, e:
        print str(e)

    # print 'grade=>%s' % hotel.grade
    try:
        star = root.xpath('//span[contains(@class, "stars-grey value-title")]')[0].attrib['title']
        hotel.star = str(int(float(star)))
    except Exception as e:
        print e
        hotel.star = -1
    # print 'star=>%s' % hotel.star

    try:
        review_num = re.findall(r'\"totalReviews\":(\d+),', content)
        hotel.review_num = review_num[0].strip().encode('utf-8')
        # review_num = root.find_class('cols-nested')[0].xpath('a/span[@itemprop="reviewCount"]')[0].text_content()
        # hotel.review_num = str(review_num)
    except Exception, e:
        print str(e)
    # print 'review_num=>%s' % hotel.review_num

    # try:
    #     # info_table = encode_unicode(
    #     #     root.find_class('tab-pane')[0].find_class('col')[0].xpath('section')[0].text_content())
    #     internet_info = root.xpath('//div[@data-section="internet"]')[0].text_content()
    #     # if '免费 WiFi' in internet_info or '免費無線上網' in internet_info:
    #     #     has_wifi = 'Yes'
    #     #     is_wifi_free = 'Yes'
    #     # hotel.has_wifi = has_wifi
    #     # hotel.is_wifi_free = is_wifi_free
    #     internet_info = internet_info.lower()
    #     if 'WiFi'.lower() in internet_info:
    #         hotel.facility['Room_wifi'] = internet_info
    #         hotel.facility['Public_wifi'] = internet_info
    # except Exception, e:
    #     print str(e)
    # try:
    #     parking_info = root.xpath('//div[@data-section="parking"]')[0].text_content()
    #     # if '收费' in parking_info or '收費' in parking_info:
    #     #     has_parking = 'Yes'
    #     #     is_parking_free = 'No'
    #     # if '免费' in parking_info or '免費' in parking_info:
    #     #     has_parking = 'Yes'
    #     #     is_parking_free = 'Yes'
    #     # hotel.has_parking = has_parking
    #     # hotel.is_parking_free = is_parking_free
    #     if "停车" in parking_info:
    #         hotel.facility['Parking'] = parking_info
    # except Exception as e:
    #     print str(e)
    # print 'has_wifi=>%s' % hotel.has_wifi
    # print 'is_wifi_free=>%s' % hotel.is_wifi_free
    # print 'has_parking=>%s' % hotel.has_parking
    # print 'is_parking_free=>%s' % hotel.is_parking_free

    try:
        info_table = root.find_class('tab-pane')[0].find_class('col')[0].xpath('section')[0]
        category_num = len(info_table.xpath('h3'))
        service = ''
        try:
            facilities_dict = {'Swimming_Pool': '游泳池', 'gym': '健身', 'SPA': 'SPA', 'Bar': '酒吧', 'Coffee_house': '咖啡厅',
                               'Tennis_court': '网球场', 'Golf_Course': '高尔夫球场', 'Sauna': '桑拿', 'Mandara_Spa': '水疗中心',
                               'Recreation': '儿童娱乐场', 'Business_Centre': '商务中心', 'Lounge': '行政酒廊',
                               'Wedding_hall': '婚礼礼堂', 'Restaurant': '餐厅',
                               'Airport_bus': '机场', 'Valet_Parking': '代客泊车', 'Call_service': '叫车服务',
                               'Rental_service': '租车服务'}
            reverse_facility_dict = {v: k for k, v in facilities_dict.items()}
            service_dict = {'Luggage_Deposit': '行李寄存', 'front_desk': '24小时前台', 'Lobby_Manager': '24小时大堂经理',
                            '24Check_in': '24小时办理入住', 'Security': '24小时安保', 'Protocol': '礼宾服务',
                            'wake': '叫醒服务', 'Chinese_front': '中文前台', 'Postal_Service': '邮政服务',
                            'Fax_copy': '传真/复印', 'Laundry': '洗衣', 'polish_shoes': '擦鞋服务', 'Frontdesk_safe': '保险',
                            'fast_checkin': '快速办理入住', 'ATM': '自动柜员机(ATM)/银行服务', 'child_care': '儿童看护',
                            'Food_delivery': '送餐服务'}
            reverse_sevice_dict = {v: k for k, v in service_dict.items()}
            # general = info_table.xpath('div[@data-section="amenities-general"]')[0]
            fea_list = html.xpath("//div[@data-section='amenities-general']/article/section/ul/li/text()")
            for each in fea_list:
                each = each.rstrip(' ').lower().replace(" ", "")
                for fac_value in facilities_dict.values():
                    if fac_value in each:
                        hotel.facility_content[reverse_facility_dict[fac_value]] = each
                        break
                for serv_value in service_dict.values():
                    if serv_value in each:
                        hotel.service_content[reverse_sevice_dict[serv_value]] = each
                        break
        except Exception, e:
            print "解析hotel.service/facilities出错:  {}".format(e)

        try:
            internet_info_list = html.xpath("//div[@data-section='internet']/p/text()")
            position_info = html.xpath("//div[@data-section='internet']/p/span/text()")
            internet_info_list2 = map(lambda x: x.strip().replace("\n", ""), internet_info_list)
            internet_info = []
            for internet in internet_info_list2:
                if internet != "":
                    internet_info.append(internet)
            for tump in zip(position_info, internet_info):
                internet_str = tump[0] + tump[1]
                internet_str = internet_str.lower()
                if u"客房" in internet_str:
                    if u"wifi" in internet_str or u"无线" in internet_str:
                        hotel.facility_content['Room_wifi'] = internet_str
                if u"客房" in internet_str and u"有线" in internet_str:
                    hotel.facility_content['Room_wired'] = internet_str
                if u"公共区域" in internet_str:
                    if u"wifi" in internet_str or u"无线" in internet_str:
                        hotel.facility_content['Public_wifi'] = internet_str
                if u"公共区域" in internet_str and u"有线" in internet_str:
                    hotel.facility_content['Public_wired'] = internet_str
        except Exception, e:
            print "解析facility['Room_wifi']出错: {}".format(e)

        try:
            parking_info = html.xpath("//div[@data-section='parking']/p/text()")
            parking_info_str = " ".join(parking_info).strip().replace("\n", "")
            if u"停车" in parking_info_str:
                hotel.facility_content['Parking'] = parking_info_str
        except Exception as e:
            print "解析facility['Parking']出错: {}".format(e)

        try:
            basics_facilities = info_table.xpath('div[@data-section="amenities-general"]/article/section/ul/li/text()')
            facilities = encode_unicode(','.join(map(lambda x: x.strip(), basics_facilities)))
            basics_hidden_fac = info_table.xpath('div[@data-section="amenities-general"]/article/section/ul/li/span/text()')
            if basics_hidden_fac:
                hidden_fac = encode_unicode(",".join(map(lambda x: x.strip(), basics_hidden_fac)))
                service += '酒店基础设施：' + facilities + ','
                service += hidden_fac + '|'
            else:
                service += '酒店基础设施：' + facilities + '|'
        except Exception as e:
            print e

        try:
            house_facilities = info_table.xpath('div[@data-section="amenities-family"]/article/section/ul/li/text()')
            facilities = encode_unicode(','.join(facilitie.strip() for facilitie in house_facilities))
            house_hidden_fac = info_table.xpath('div[@data-section="room"]/article/section/ul/li/span/text()')
            if house_hidden_fac:
                hidden_fac = encode_unicode(",".join(map(lambda x: x.strip(), house_hidden_fac)))
                service += '家居型设施：' + facilities + ','
                service += hidden_fac + '|'
            else:
                service += '家居型设施：' + facilities + '|'
            # print service
        except Exception as e:
            print e

        try:
            guestroom_facilities = info_table.xpath('div[@data-section="room"]/article/section/ul/li/text()')
            facilities = encode_unicode(','.join(facilitie.strip() for facilitie in guestroom_facilities))
            guestroom_hidden_fac = info_table.xpath('div[@data-section="room"]/article/section/ul/li/span/text()')
            if guestroom_hidden_fac:
                hidden_fac = encode_unicode(",".join(map(lambda x: x.strip(), guestroom_hidden_fac)))
                service += '客房设施：' + facilities +','
                service += hidden_fac + '|'
            else:
                service += '客房设施：' + facilities + '|'
            # print service
        except Exception as e:
            print e

        try:
            foods = info_table.xpath('div[@data-section="dining"]/article/section/p/text()')
            facilities = encode_unicode(','.join(facilitie.strip() for facilitie in foods))
            service += '美食佳肴：' + facilities + '|'
            # print service
        except Exception as e:
            print e

        try:
            accessibility = info_table.xpath('div[@data-section="accessibility"]/article/section/p/text()')
            facilities = encode_unicode(','.join(facilitie.strip() for facilitie in accessibility))
            service += '无障碍设施：' + facilities + '|'
            # print service
        except Exception as e:
            print e
        # hotel.others_info = json.dumps({'hotel_services_info': service})

    except Exception as e:
        print e
    try:
        # map_part = root.xpath('//div[@class="map"]/a/figure/@data-src')
        # map_str = map_part[-1]
        # google_map_info = urlparse.parse_qs(map_str)['center'][-1]
        # map_info = ','.join(google_map_info.split(',')[::-1])
        # hotel.map_info = map_info
        map_temp = html.xpath("//div[@class='map uitk-col']/a/figure/@data-src")[0]
        map_info_str = re.search(r"&center=(.*)&size", map_temp).group(1)
        map_info = ",".join(map_info_str.split(",")[::-1])
        hotel.map_info = map_info
    except Exception, e:
        map_info = 'NULL'
        print str(e)

    # print 'map_info=>%s' % map_info
    first_img = None
    try:
        img_list = root.find_class('jumbo-wrapper')[0].find_class('jumbo-hero')[0].xpath('img')
        img_url_set = set()
        for each in img_list:
            try:
                each_url = urlparse.urljoin('https:', each.get('data-src'))
                if each_url == 'https:':
                    raise Exception
            except:
                try:
                    each_url = urlparse.urljoin('https:', each.get('src'))
                    first_img = each_url
                except:
                    pass
            if each_url != 'https:':
                img_url_set.add(each_url)
        hotel.img_items = '|'.join(img_url_set)
        hotel.Img_first = first_img
    except Exception, e:
        print str(e)
    # print 'img_items=>%s' % hotel.img_items
    # print 'first_img=>%s' % first_img
    try:
        # desc = encode_unicode(root.find_class('hotel-description')[0].find_class('visuallyhidden')[0].tail.strip())
        h3s = root.xpath('//div[@class="hotel-description"]/h3//text()')
        ps = root.xpath('//div[@class="hotel-description"]/p//text()')
        desc = '|_|'.join([title + '::' + value for title, value in zip(h3s, ps)])
        hotel.description = desc.encode('utf-8')
    except Exception, e:
        print str(e)
    # print 'description=>%s' % hotel.description
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
    # print 'accepted_cards=>%s' % hotel.accepted_cards
    try:
        # policy_table = root.find_class('tab-pane')[0].find_class('col')[1].xpath('section')[0].getchildren()
        policy_table = root.xpath('//div[@data-section="checkIn"]/p/text()')
        for text in policy_table:
            index = max(text.find('入住时间'), text.find('入住登記開始時間： 14:00'))
            if index > -1:
                check_in_time = text.split(' ')[-1]
                break
        # check_in_text = policy_table[2].xpath('p/text()')
        # if '中午' in check_in_text:
        #     check_in_time = '中午'
        # else:
        #     check_in_time = re.findall(r'(\d+.*)', check_in_text[0])[0]
        hotel.check_in_time = check_in_time
    except Exception, e:
        print str(e)
    # print 'check_in_time=>%s' % hotel.check_in_time
    try:
        policy_table = root.xpath('//div[@data-section="checkOut"]/p/text()')
        for text in policy_table:
            index = max(text.find('退房时间为'), text.find('退房時間'))
            if index > -1:
                check_out_time = text.split(' ')[-1]
                break
        # policy_table = root.find_class('tab-pane')[0].find_class('col')[1].xpath('section')[0].getchildren()
        # check_out_text = policy_table[4].xpath('p/text()')[0].encode('utf-8').strip()
        # if '中午' in check_out_text:
        #     check_out_time = '中午'
        # else:
        #     check_out_time = check_out_text.split('退房时间为 ')[1]
        hotel.check_out_time = check_out_time
    except Exception, e:
        print str(e)
    # print 'check_out_time=>%s' % hotel.check_out_time

    try:
        child_beds = html.xpath("//div[@data-secion='childBeds']/div[@class='paragraph-hack']/ul/li/text()")
        hotel.chiled_bed_type = " ".join(child_beds)
    except Exception as e:
        print e
    # print 'child_bed_type ==> %s' % hotel.chiled_bed_type

    try:
        pet = html.xpath("//div[contains(@data-section, 'pets')]/div[@class='paragraph-hack']/ul/li/text()")
        hotel.pet_type = " ".join(pet)
    except Exception as e:
        print e
    # print 'pet_type ==> %s' % hotel.pet_type
    hotel.hotel_url = url
    hotel.source = 'expedia'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    if first_img:
        hotel.others_info = json.dumps({'first_img':first_img,'hotel_services_info': service})
    try:
        hotel_phone = html.xpath("//span[@itemprop='telephone']/text()")[0]
        hotel.hotel_phone = hotel_phone.strip()
    except Exception as e:
        print '解析hotel.hotel_phone出错：{}'.format(e)

    res = hotel.to_dict()
    
    return res


def encode_unicode(str):
    return str.replace('\u00', '\\x').decode('string-escape').encode('utf8')


if __name__ == '__main__':
    from proj.my_lib.new_hotel_parser.lang_convert import tradition2simple

    # url = 'https://www.expedia.cn/h1000.Hotel-Information'
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
    # url = 'https://www.expedia.com.hk/Hotels-Sahara-Motel.h13279481.Hotel-Information'
    # url = 'https://www.expedia.com.hk/cn/Mauritius-Island-Hotels-Ocean-Villas.h1466602.Hotel-Information?chkin=2017%2F11%2F25&chkout=2017%2F11%2F26&rm1=a2&regionId=6051080&sort=recommended&hwrqCacheKey=58665cc7-0e73-4f2d-89da-6cf5f79637efHWRQ1506387257474&vip=false&c=251228bc-5980-49ea-ac6d-87d847977318&'
    # url = 'https://www.expedia.com.hk/Hotels-Saint-Georges-Hotel.h1.Hotel-Information?chkin=2017%2F11%2F7&chkout=2017%2F11%2F8&rm1=a2&regionId=178279&sort=recommended&hwrqCacheKey=3a7247f4-a225-4f75-afd4-8fd3463f2d85HWRQ1506618956146&vip=false&c=c6d00f50-8b75-4eec-b23c-f9c20f690aa8&'
    # url = 'https://www.expedia.cn/cn/Lansing-Hotels-The-English-Inn.h36874.Hotel-Information?chkin=2017%2F10%2F19&chkout=2017%2F10%2F20&rm1=a2&regionId=100011&hwrqCacheKey=9cbe2ff3-4cb7-497c-95dc-6dbde2ac34beHWRQ1508384715126&vip=false&c=f41b55eb-3095-45d6-ba58-ef205e58f100&&exp_dp=762.15&exp_ts=1508384715401&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia.com.hk/cn/Salvador-Hotels-Lindo-Village-Em-Itacimirim.h20176166.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=601935&sort=recommended&hwrqCacheKey=aecb76ac-5c80-4031-9121-0e14a862cfc7HWRQ1511793011756&vip=false&c=660706b3-a71d-4608-b43d-6658fab0907a&'
    # url = 'https://www.expedia.com.hk/cn/Phetchabun-Hotels-Tonkaew-Khaokho-Resort.h20575001.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=6131746&sort=recommended&hwrqCacheKey=48693fa5-54ea-4f8d-acff-2658de10c675HWRQ1511793063089&vip=false&c=c0e12fca-078e-43e3-9525-b63c505c4be6&'
    # url = 'https://www.expedia.com.hk/Khao-Kho-Hotels-Raiphuduen-Resort.h20574520.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=6131746&sort=recommended&hwrqCacheKey=48693fa5-54ea-4f8d-acff-2658de10c675HWRQ1511793063089&vip=false&c=c0e12fca-078e-43e3-9525-b63c505c4be6&'
    # url = 'https://www.expedia.com.hk/Hotels-Upscale-3BR-Pad-In-Plateau-Montreal-By-Host-Kick.h20193722.Hotel-Information?chkin=2017%2F12%2F6&chkout=2017%2F12%2F7&rm1=a2&regionId=178288&sort=recommended&hwrqCacheKey=1b19fce7-f3f9-4a70-8b4d-bfedd0cb3969HWRQ1511802368580&vip=false&c=8978761e-8607-49e8-bc1f-e8a4dbf8c462&'
    # url = 'https://www.expedia.com/Paris-Hotels-Maison-Albar-Hotel-Paris-Champs-Elysees-Formerly-Mac-Mahon.h53564.Hotel-Information?chkin=12%2F1%2F2017&chkout=12%2F2%2F2017&rm1=a2&regionId=179898&hwrqCacheKey=4d9d56dc-f47b-41f2-bde6-8a47ff954388HWRQ1512100403589&vip=false&c=d44429b6-4c6e-408f-bf40-1c35ad4ef1c5&&exp_dp=217.41&exp_ts=1512100404426&exp_curr=USD&swpToggleOn=false&exp_pg=HSR'


    # url = 'https://www.expedia.com.hk/cn/New-York-Hotels-PUBLIC.h17117062.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178293&hwrqCacheKey=e0be673e-eca6-45be-bd2b-ea5bf0dd0eebHWRQ1522392221194&vip=false&c=1e3b30f7-285b-4ae4-9b91-1a178037b7a0&&exp_dp=2158.23&exp_ts=1522392225366&exp_curr=HKD&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia.com.hk/cn/New-York-Hotels-1-Hotel-Central-Park.h9215515.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178293&hwrqCacheKey=e0be673e-eca6-45be-bd2b-ea5bf0dd0eebHWRQ1522652432294&vip=false&c=01bac27d-9159-4817-b69f-db3e14f44fb5&&exp_dp=3683.05&exp_ts=1522652433372&exp_curr=HKD&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia.com.hk/cn/New-York-Hotels-The-Roosevelt-Hotel.h41864.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178293&hwrqCacheKey=e0be673e-eca6-45be-bd2b-ea5bf0dd0eebHWRQ1522652432294&vip=false&c=01bac27d-9159-4817-b69f-db3e14f44fb5&&exp_dp=1978.89&exp_ts=1522652433378&exp_curr=HKD&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia.com.hk/cn/New-York-Hotels-The-Belvedere-Hotel.h104193.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178293&hwrqCacheKey=e0be673e-eca6-45be-bd2b-ea5bf0dd0eebHWRQ1522652432294&vip=false&c=01bac27d-9159-4817-b69f-db3e14f44fb5&&exp_dp=2137.49&exp_ts=1522652433378&exp_curr=HKD&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Hotel-Angeleno.h21848.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=1203.75&exp_ts=1522655643080&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Avenue-Hotel.h15985.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=1380.55&exp_ts=1522655643081&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-GuestHouse-Hotel-Norwalk.h973796.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=551.01&exp_ts=1522655643081&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Best-Western-Plus-Gardena-Inn-Suites.h13145369.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=865.96&exp_ts=1522655643083&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Hotel-Angeleno.h21848.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=1203.75&exp_ts=1522655643080&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Downtown-Los-Angeles-Condos.h21935757.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=789.46&exp_ts=1522655643083&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-Foghorn-Harbor-Inn.h2200019.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=1396.26&exp_ts=1522655643084&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    url = 'https://www.expedia-cn.com/Los-Angeles-Hotels-La-Quinta-Inn-Suites-LAX.h3919.Hotel-Information?chkin=2018%2F4%2F4&chkout=2018%2F4%2F7&rm1=a2&regionId=178280&hwrqCacheKey=12615292-7c53-4da3-abab-25be787b8beaHWRQ1522655626214&vip=false&c=a7d9cdf1-93da-4c02-8579-f53214cea6d4&&exp_dp=877.59&exp_ts=1522655643088&exp_curr=CNY&swpToggleOn=false&exp_pg=HSR'
    # url = 'https://www.expedia.com.hk/cn/Hoi-An-Hotels-Green-Areca-Villa.h10000424.Hotel-Information?chkin=2018%2F5%2F2&chkout=2018%2F5%2F3&rm1=a2&regionId=6347736&sort=recommended&hwrqCacheKey=c4472144-5be0-494a-b1cf-8c4a2efbe52dHWRQ1521553199897&vip=false&c=73bf84c1-f939-4ee2-9e98-f73d21b84db0&'
    # url = 'https://www.expedia.com.hk/cn/Haines-Hotels-Aspen-Suites-Hotel-Haines.h10002872.Hotel-Information?chkin=2018%2F5%2F15&chkout=2018%2F5%2F16&rm1=a2&regionId=1490&sort=recommended&hwrqCacheKey=be8657ae-80c5-455a-a087-d0b04f6def3bHWRQ1521553140407&vip=false&c=2305b055-e4cb-4ad4-b180-9a5061b34731&'
    # url = 'https://www.expedia.com.hk/cn/Odense-Hotels-Amalie-Bed-And-Breakfast-Apartments.h10121034.Hotel-Information?chkin=2018%2F5%2F29&chkout=2018%2F5%2F30&rm1=a2&regionId=6143836&sort=recommended&hwrqCacheKey=e8cacb15-f961-43b7-9dca-6af28b4b0677HWRQ1521553159212&vip=false&c=22c9b92d-4d8d-497d-b775-e8acd0ba2f16&'
    # url = 'https://www.expedia.com.hk/cn/Fyn-Hotels-Amalie-Bed-And-Breakfast-Apartments.h10121034.Hotel-Information?chkin=2018%2F5%2F29&chkout=2018%2F5%2F30&rm1=a2&regionId=6143836&sort=recommended&hwrqCacheKey=e8cacb15-f961-43b7-9dca-6af28b4b0677HWRQ1521553159212&vip=false&c=22c9b92d-4d8d-497d-b775-e8acd0ba2f16&'
    other_info = {
        'source_id': '1000',
        'city_id': '50795'
    }
    proxies = dict()
    proxy_info = requests.get(
        "http://10.10.32.22:48200/?type=px001&qid=0&query={%22req%22:%20[{%22source%22:%20%22ctripFlight%22,%20%22num%22:%201,%20%22type%22:%20%22verify%22,%20%22ip_type%22:%20%22test%22}]}&ptid=test&uid=test&tid=tid&ccy=spider_test").content
    proxy = json.loads(proxy_info)['resp'][0]['ips'][0]['inner_ip']
    proxies['socks'] = "socks5://" + proxy.encode('utf-8')
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'}
    page = requests.get(url, headers=headers, proxies=proxies, verify=False)
    page.encoding = 'utf8'
    content = page.text
    result = expedia_parser(content, url, other_info)
    # res = json.loads(result)
    # res = json.dumps(res, ensure_ascii=False)
    # result = json.loads(result)
    # print json.dumps(result, ensure_ascii=False)
    print result

    # print '#' * 100
    # keys = ['hotel_name', 'hotel_name_en', 'brand_name', 'address', 'service', 'description', 'accepted_cards']
    #
    # for key in keys:
    #     if not getattr(result, key):
    #         setattr(result, key, 'NULL')
    #     setattr(result, key, tradition2simple(getattr(result, key).decode()))
    # result.hotel_name = tradition2simple(result.hotel_name.decode())
    # result.hotel_name_en = tradition2simple(result.hotel_name_en.decode())
    # result.brand_name = tradition2simple(result.brand_name.decode())
    # result.address = tradition2simple(result.address.decode())
    # result.service = tradition2simple(result.service.decode())
    # result.description = tradition2simple(result.description.decode())
    # result.accepted_cards = tradition2simple(result.accepted_cards.decode())
    # for k, v in result.__dict__.items():
    #     print k, '=>', v
    # print 'Hello World'
    # try:
    #     session = DBSession()
    #     session.merge(result)
    #     session.commit()
    #     session.close()
    # except Exception as e:
    #     print str(e)
