# -*- coding: utf-8 -*-
import re
import json
import requests
from lxml import etree
from proj.my_lib.models.HotelModel import HotelNewBase
from proj.my_lib import parser_exception


def bestwestern_parser(content, url, other_info):
    lng_lat = content[0]
    html = etree.HTML(content[1])
    hotel = HotelNewBase()

    # 酒店名
    hotel.hotel_name = html.xpath('//div[contains(@class,"hotelImagebloc")]//h1[@id="hotel-name"]/a/text()')[0]
    # 酒店英文名
    hotel.hotel_name_en = hotel.hotel_name
    # 酒店源
    hotel.source = 'bestwestern'
    # 酒店id
    hotel.source_id = url.split('-')[-1]
    # 酒店品牌名
    hotel.brand_name = get_brand_name(html)
    # 酒店经纬度
    hotel.map_info = get_map_info(lng_lat)
    # 酒店地址
    hotel.address = "".join(html.xpath('//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span/text()'))
    # 酒店所在城市
    hotel.city = html.xpath('//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span[@id="address-1-city-state-zip"]/text()')[0]
    # 酒店所在国家
    hotel.country = html.xpath('//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]/span')[-1].text
    # 城市ID（mioji）
    hotel.city_id = other_info['city_id']
    # 酒店邮编
    hotel.postal_code = html.xpath('//div[contains(@class,"hotelImagebloc")]//div[contains(@class,"addressContainer")]//span[@class="postalCode"]/text()')[0]
    # 酒店星级
    hotel.star = 5
    # 酒店评分
    hotel.grade = html.xpath('//div[@class="tripAdvisorOwl"]/img/@src')[0].split("/")[-1].split('-')[0]
    # 酒店评论数
    try:
        hotel.review_num = re.search(r'\d+', html.xpath('//div[@class="hotelDetailsContainer"]//div[@id="hotel-reviews"]//div[@class="reviewRatingCount"]/text()')[0]).group()
    except Exception:
        hotel.review_num = 0
    # 酒店头图
    hotel.Img_first = html.xpath("//div[contains(@class, 'hotelImageSlider')]//li/img/@src")[0]
    # 酒店电话
    hotel.hotel_phone = html.xpath('//div[@class="phoneNumbers"]//p[@class="phoneNumber"]/a/text()')[0]
    # 酒店邮编
    hotel.hotel_zip_code = html.xpath('//div[@class="phoneNumbers"]//p[@class="phoneNumber"]/a/text()')[1]
    # 到达酒店的交通信息
    hotel.traffic = 'NULL'
    # 儿童和加床政策
    hotel.chiled_bed_type = 'NULL'
    # 宠物政策
    hotel.pet_type = html.xpath('//div[@class="policyContent uk-margin-small-left"]/text()')[0]
    # 酒店特色
    get_feature(hotel, html)
    # 设施信息
    get_facility(hotel, html)
    # 服务信息
    get_service(hotel, html)
    # 酒店照片
    hotel.img_items = ",".join(html.xpath("//div[contains(@class, 'hotelImageSlider')]//li/img/@src"))
    # 酒店描述
    hotel.description = html.xpath('//div[@class="hotelOverviewDetailSection"]/div[@class="overviewText"]/text()')[0].strip()
    # 支付接受的卡
    hotel.accepted_cards = 'NULL'
    # 入住时间
    hotel.check_in_time = html.xpath('//div[@class="uk-width-3-10 checkInPositionContainer addressCheckInTableCell"]/p[2]/text()')[0]
    # 退房时间
    hotel.check_out_time = html.xpath('//div[@class="phoneNumbers"]/div[contains(@class,"phonesRow")][1]/div[2]/p[2]/text()')[0]
    # 酒店url
    hotel.hotel_url = url
    print hotel.to_dict()
    return hotel.to_dict()


# 获取酒店服务
def get_service(hotel, html):
    hotel_facility = get_hotel_facility(html)
    description = html.xpath('//div[@class="hotelOverviewDetailSection"]/div[@class="overviewText"]/text()')[0].strip()
    service_content = hotel.service_content
    for service in [hotel_facility, description]:
        if re.findall(r'行李寄存'.decode('utf8'), service):
            service_content['Luggage_Deposit'] = '行李寄存'
        if re.findall(r'接待台|前台'.decode('utf8'), service):
            service_content['front_desk'] = '24小时前台'
        if re.findall(r'大堂经理'.decode('utf8'), service):
            service_content['Lobby_Manager'] = '24小时大堂经理'
        if re.findall(r'24小时办理入住'.decode('utf8'), service):
            service_content['24Check_in'] = '24小时办理入住'
        if re.findall(r'24小时安保'.decode('utf8'), service):
            service_content['Security'] = '24小时安保'
        if re.findall(r'礼宾服务'.decode('utf8'), service):
            service_content['Protocol'] = '礼宾服务'
        if re.findall(r'叫醒|叫醒电话'.decode('utf8'), service):
            service_content['wake'] = '叫醒服务'
        if re.findall(r'中文前台|中文'.decode('utf8'), service):
            service_content['Chinese_front'] = '中文前台'
        if re.findall(r'邮政服务|邮寄'.decode('utf8'), service):
            service_content['Postal_Service'] = '邮政服务'
        if re.findall(r'传真|复印'.decode('utf8'), service):
            service_content['Fax_copy'] = '传真/复印'
        if re.findall(r'洗衣店|洗衣'.decode('utf8'), service):
            service_content['Laundry'] = '洗衣服务'
        if re.findall(r'前台保险柜|前台'.decode('utf8'), service):
            service_content['Frontdesk_safe'] = '前台保险柜'
        if re.findall(r'快速办理'.decode('utf8'), service):
            service_content['fast_checkin'] = '快速办理入住/退房'
        if re.findall(r'ATM|银行'.decode('utf8'), service):
            service_content['ATM'] = '自动柜员机(ATM)/银行服务'
        if re.findall(r'儿童看护|看护'.decode('utf8'), service):
            service_content['child_care'] = '儿童看护服务'
        if re.findall(r'送餐'.decode('utf8'), service):
            service_content['Food_delivery'] = '送餐服务'


# 获取酒店设施
def get_facility(hotel, html):
    hotel_facility= get_hotel_facility(html)
    facility = hotel.facility
    if re.findall(r'有线网络|高速互联网'.decode('utf8'), hotel_facility):
        facility['Room_wired'] = '客房有线网络'
    if re.findall(r'无线网络'.decode('utf8'), hotel_facility):
        facility['Room_wifi'] = '客房wifi'
    if re.findall(r'无线网络'.decode('utf8'), hotel_facility):
        facility['Public_wired'] = '公共区域有线网络'
    if re.findall(r'高速互联网'.decode('utf8'), hotel_facility):
        facility['Public_wifi'] = '公共区域WiFi'
    if re.findall(r'停车场'.decode('utf8'), hotel_facility):
        facility['Parking'] = '停车场'
    if re.findall(r'机场班车'.decode('utf8'), hotel_facility):
        facility['Airport_bus'] = '机场班车'
    if re.findall(r'代客泊车'.decode('utf8'), hotel_facility):
        facility['Valet_Parking'] = '代客泊车'
    if re.findall(r'叫车服务'.decode('utf8'), hotel_facility):
        facility['Call_service'] = '叫车服务'
    if re.findall(r'租车服务|租车'.decode('utf8'), hotel_facility):
        facility['Rental_service'] = '租车服务'
    if re.findall(r'游泳池'.decode('utf8'), hotel_facility):
        facility['Swimming_Pool'] = '游泳池'
    if re.findall(r'健身房'.decode('utf8'), hotel_facility):
        facility['gym'] = '健身房'
    if re.findall(r'SPA', hotel_facility):
        facility['SPA'] = 'SPA'
    if re.findall(r'酒吧'.decode('utf8'), hotel_facility):
        facility['Bar'] = '酒吧'
    if re.findall(r'咖啡厅'.decode('utf8'), hotel_facility):
        facility['Coffee_house'] = '咖啡厅'
    if re.findall(r'网球场'.decode('utf8'), hotel_facility):
        facility['Tennis_court'] = '网球场'
    if re.findall(r'健身房'.decode('utf8'), hotel_facility):
        facility['gym'] = '健身房'
    if re.findall(r'高尔夫球场'.decode('utf8'), hotel_facility):
        facility['Golf_Course'] = '高尔夫球场'
    if re.findall(r'桑拿'.decode('utf8'), hotel_facility):
        facility['Sauna'] = '桑拿'
    if re.findall(r'水疗中心'.decode('utf8'), hotel_facility):
        facility['Mandara_Spa'] = '水疗中心'
    if re.findall(r'儿童娱乐场|儿童'.decode('utf8'), hotel_facility):
        facility['Recreation'] = '儿童娱乐场'
    if re.findall(r'商务中心'.decode('utf8'), hotel_facility):
        facility['Business_Centre'] = '商务中心'
    if re.findall(r'行政酒廊|酒廊'.decode('utf8'), hotel_facility):
        facility['Lounge'] = '行政酒廊'
    if re.findall(r'婚礼礼堂|婚礼'.decode('utf8'), hotel_facility):
        facility['Wedding_hall'] = '婚礼礼堂'
    if re.findall(r'餐厅|餐馆'.decode('utf8'), hotel_facility):
        facility['Restaurant'] = '餐厅'


# 获取酒店特色
def get_feature(hotel, html):
    description = html.xpath('//div[@class="hotelOverviewDetailSection"]/div[@class="overviewText"]/text()')[0].strip()
    feature = hotel.feature
    if re.findall(r'华人|华人礼遇'.decode('utf8'), description):
        feature['China_Friendly'] = '华人礼遇'
    if re.findall(r'浪漫|浪漫情侣'.decode('utf8'), description):
        feature['Romantic_lovers'] = '浪漫情侣'
    if re.findall(r'亲子|亲子酒店'.decode('utf8'), description):
        feature['Parent_child'] = '亲子酒店'
    if re.findall(r'海滨|海滨风光'.decode('utf8'), description):
        feature['Beach_Scene'] = '海滨风光'
    if re.findall(r'温泉|温泉酒店'.decode('utf8'), description):
        feature['Hot_spring'] = '温泉酒店'
    if re.findall(r'日式|日式旅馆'.decode('utf8'), description):
        feature['Japanese_Hotel'] = '日式旅馆'
    if re.findall(r'休闲|休闲度假'.decode('utf8'), description):
        feature['Vacation'] = '休闲度假'


# 获取酒店品牌名
def get_brand_name(html):
    src = html.xpath('//div[contains(@class,"hotelImagebloc")]//div[@class="uk-width-1-1"]/img/@src')[0]
    brand_name = src.split("/")[-1].split('_')[0]
    return brand_name


# 获取酒店经纬度
def get_map_info(lng_lat):
    map = ",".join(lng_lat)
    return map


# 获取酒店服务
def get_hotel_facility(html):
    hotel_facility = ";".join(html.xpath('//div[@class="hotelAmenities"]//div[contains(@class,"hotelAmenities")]//div[contains(@class,"hotelAmenities")]/ul//li/text()'))
    room_facility = ";".join(html.xpath('//div[@class="hotelAmenities"]//div[contains(@class,"roomAmenities")]//ul[@id="roomamenities"]/li/text()'))
    facility = ";".join([hotel_facility, room_facility])
    return facility


if __name__ == '__main__':
    url = "https://www.bestwestern.net.cn/booking-path/hotel-details/best-western-victoria-palace-london-83873"
    req = requests.session()
    resp = req.get(url)
    cookies = resp.cookies
    # 经纬度
    lng_lat = [cookies['search_locationLng'], cookies['search_locationLat']]
    # 页面详情
    html = resp.content
    other_info = {
        "source_id": "best-western-victoria-palace-london-83873",
        "city_id": ""
    }
    content = [lng_lat, html]
    bestwestern_parser(content, url, other_info)
