#! /usr/bin/python
# coding=utf-8
import sys
import re
import requests
import json
from lxml import html as HTML
# from data_obj import BookingHotel
# from mioji.common.class_common import Hotel_New
# from common.common import get_proxy
# from proj.my_lib.Common.KeyMatch import key_is_legal

reload(sys)
sys.setdefaultencoding('utf-8')


def booking_parser(content, url, other_info):
    hotel = Hotel_New()
    try:
        root = HTML.fromstring(content)
    except Exception as e:
        print e.message
    hotel.hotel_name = re.findall(r'b_hotel_name:.*?\'(.+?)\',', content)[0].strip()
    hotel.hotel_name_en = re.findall(r'hotelName:.*?\"(.+?)\",', content)[0].strip()
    hotel.source = 'booking'
    hotel.source_id = other_info['source_id']
    latitude = re.findall(r'b_map_center_latitude = (.*?);', content)[0].strip()
    longitude = re.findall(r'b_map_center_longitude = (.*?);', content)[0].strip()
    hotel.map_info = '{},{}'.format(latitude, longitude)
    location_dict = json.loads(
        re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.S)[0].replace('\n', '').strip())
    hotel.address = location_dict['address']['streetAddress']
    hotel.city = re.findall(r'city_name:.*?\'(.*?)\'', content)[0].strip()
    hotel.country = location_dict['address']['addressCountry']
    hotel.city_id = other_info['city_id']
    hotel.postal_code = re.findall(r'"postalCode".*?\"(.*?)\"', content, re.S)[0].strip()
    try:
        hotel.star = root.xpath('//*[@id="wrap-hotelpage-top"]/div[@class="hp__hotel-title"]/span/span[@class="hp__hotel_ratings__stars nowrap"]/i/@title')[0].encode('utf-8').replace('星级酒店', '')
    except IndexError as e:
        print('Parser ERROR, NO Star Infomation.The reason follows: %s' % e.message)
    hotel.grade = location_dict['aggregateRating']['ratingValue']
    hotel.review_num = location_dict['aggregateRating']['reviewCount']
    hotel.Img_first = location_dict['image']
    # hotel.other_info =
    # hotel.hotel_phone =
    # hotel_zip_code =
    # hotel.feature =
    # hotel.brand_name =
    # hotel.continent =
    try:
        hotel.traffic = ','.join([root.xpath('//*[@id="public_transport_options"]/div/text()')[1].strip('\n').strip(),
                                  root.xpath('//*[@id="public_transport_options"]/ul/li/div[1]/text()')[1].strip('\n').strip(),
                                  root.xpath('//*[@id="public_transport_options"]/ul/li/div[2]/text()')[0].strip('\n').strip()])
    except IndexError as e:
        print('Parser ERROR, NO Traffic Infomation.The reason follows: %s' % e.message)
    # hotel.chiled_bed_type = '\n'.join(root.xpath('//*[@id="children_policy"]/p[position()>1]/text()'))
    hotel.chiled_bed_type = ''.join(
        [i.replace('\n', '').strip() for i in root.xpath('//*[@id="children_policy"]/p[position()>1]//text()') if
         i.replace('\n', '').strip()])
    hotel.pet_type = ''.join([i.replace('\n', '').strip() for i in root.xpath(
        '//*[@id="hotelPoliciesInc"]/div[@class="description"]/p[position()>1]//text()') if
                              i.replace('\n', '').strip()])
    # －2:宠物  1:综合设施  2:活动设施  3:服务项目  5：浴室  6:媒体／科技  7:餐饮服务  11：网络  13:户外  16:停车场  17：卧室
    # 21:游泳及康复设施  27：商务设施
    hot_facilities = [i.replace('\n', '').strip() for i in root.xpath('//*[@id="hp_facilities_box"]/div[@class="facilities-sliding-keep"]/div/div[@class="important_facility "]//text()') if i.replace('\n', '').strip()]
    wifi = ''.join([i.replace('\n', '').strip() for i in root.xpath('//*[@id="hp_facilities_box"]//div[@data-section-id=11]/ul/li[@class="policy"]/p/span//text()') if i.replace('\n', '').strip()])
    if u'免费无线网络连接' in hot_facilities or u'免费！住宿方于各处提供WiFi（免费）。' in wifi:
        hotel.facility['Public_wifi'] = wifi
    elif u'免费！住宿方于客房提供WiFi（免费）。' in wifi:
        hotel.facility['Room_wifi'] = wifi
    elif u'客房' in wifi and u'有线网络' in wifi:
        hotel.facility['Room_wired'] = wifi
    elif u'公共' in wifi or u'各处' in wifi and u'有线网络' in wifi:
        hotel.facility['Public_wired'] = wifi
    parking = ''.join([i.replace('\n', '').strip() for i in root.xpath('//*[@id="hp_facilities_box"]//div[@data-section-id=16]//p//text()') if i.replace('\n', '').strip()])
    hotel.facility['Parking'] = parking

    # 设施新字段添加到facilities_dict， 即可自动匹配
    facilities_dict = {'Swimming_Pool': '游泳池', 'gym': '健身房', 'SPA': 'SPA', 'Bar': '酒吧', 'Coffee_house': '咖啡厅',
                       'Tennis_court': '网球场', 'Golf_Course': '高尔夫球场', 'Sauna': '桑拿', 'Mandara_Spa': '水疗中心',
                       'Recreation': '儿童娱乐场', 'Business_Centre': '商务中心', 'Lounge': '行政酒廊',
                       'Wedding_hall': '婚礼礼堂', 'Restaurant': '餐厅',
                       'Airport_bus': '机场班车', 'Valet_Parking': '代客泊车', 'Call_service': '叫车服务', 'Rental_service': '租车服务'}
    part_facilities = map(lambda x: x.encode('utf-8').replace('\n', '').strip(), root.xpath(
        '//*[@id="hp_facilities_box"]/div[@class="facilitiesChecklist"]/div/ul/li/span[@data-name-en]/text()'))
    parser_list = []
    reverse_facility_dict = {v: k for k, v in facilities_dict.items()}
    for every in part_facilities:
        value = every.replace('咖啡', '咖啡厅').replace('网球', '网球场').replace('健身', '健身房').replace('儿童娱乐', '儿童游乐').upper()
        for faci in facilities_dict.values():
            if faci in value:
                hotel.facility[reverse_facility_dict[faci]] = every
                parser_list.append(every)
    print('酒店设施：{}'.format(', '.join(part_facilities)))
    print('已解析出：%s' % ', '.join(parser_list))
    service_list = map(lambda x: x.encode('utf-8').replace('\n', '').strip(),
                       root.xpath('//*[@id="hp_facilities_box"]//div[@data-section-id=3]/ul/li/span[1]/text()'))

    # 服务新字段添加到facilities_dict， 即可自动匹配
    service_dict = {'Luggage_Deposit': '行李寄存', 'front_desk': '24小时前台', 'Lobby_Manager': '24小时大堂经理',
                    '24Check_in': '24小时办理入住', 'Security': '24小时安保', 'Protocol': '礼宾服务',
                    'wake': '叫醒服务', 'Chinese_front': '中文前台', 'Postal_Service': '邮政服务',
                    'Fax_copy': '传真/复印', 'Laundry': '洗衣服务', 'polish_shoes': '擦鞋服务', 'Frontdesk_safe': '前台保险柜',
                    'fast_checkin': '快速办理入住/退房', 'ATM': '自动柜员机(ATM)/银行服务', 'child_care': '儿童看护服务',
                    'Food_delivery': '送餐服务'}
    reverse_sevice_dict = {v: k for k, v in service_dict.items()}
    parser_sevice_list = []
    for every in part_facilities:
        for serv in service_dict.values():
            value = serv.replace('服务', '')
            if value in every:
                hotel.service[reverse_sevice_dict[serv]] = every
                parser_sevice_list.append(every)
    print('酒店服务：{}'.format(', '.join(service_list) or '如果你看见了这句话请不要好奇，它表示酒店服务项目是空的'))
    print('已解析出：%s' % ', '.join(parser_sevice_list))
    hotel.img_items = '|'.join(root.xpath('//*[@id="photos_distinct"]/a[position()<last()-1]/@href'))
    hotel.description = '\n'.join(
        map(lambda x: x.strip(), root.xpath('//*[@id="summary"]/p/text()')))
    hotel.accepted_cards = '|'.join(root.xpath('//*[@class="jq_tooltip payment_methods_overall"]/button/@aria-label'))
    hotel.check_in_time = re.sub(pattern=r'<script.+?script>', repl='',
                                 string=root.xpath('//*[@id="checkin_policy"]/p/span/@data-caption')[0].encode('utf-8'),
                                 flags=re.S).strip()
    hotel.check_out_time = re.sub(pattern=r'<script.+?script>', repl='',
                                  string=root.xpath('//*[@id="checkout_policy"]/p/span/@data-caption')[0].encode(
                                      'utf-8'), flags=re.S).strip()
    hotel.hotel_url = url.encode('utf-8')
    return hotel.to_dict()


if __name__ == '__main__':
    # from time import time
    # from gevent import monkey
    # monkey.patch_all()
    # from gevent.queue import Queue
    # import gevent
    #
    #
    # def list_to_queue(_):
    #     global queue
    #     for each in _:
    #         queue.put_nowait(each)
    #     return queue
    # start = time()
    # other_info = {'source_id': '1016533', 'city_id': '10067'}
    # queue = Queue()
    # url_list = (i for i in open(r'/Users/mioji/Desktop/booking_detail_url.txt', 'r'))
    # gevent.spawn(list_to_queue, url_list).join()
    # print(queue.qsize())
    #
    # def f(que):
    #     while not que.empty():
    #         url = que.get_nowait()
    #         while True:
    #             try:
    #                 content = requests.get(url).text
    #             except:
    #                 pass
    #             else:
    #                 break
    #         print(url)
    #         result = booking_parser(content, url, other_info)
    #         print(result)
    #         print('- ' * 100)
    #
    # gevent.joinall([gevent.spawn(f, queue) for i in range(10)])
    # end = time()
    # print('Total time is %.2f s' % (end - start))
