# -*- coding:utf-8 -*-

import re
import json
import requests
import sys
from proj.my_lib.models.HotelModel import HotelBase
from lxml import etree
from bs4 import BeautifulSoup
reload(sys)
sys.setdefaultencoding("utf-8")


def marriott_parser(content, url, other_info):
    if len(content) == 2:
        return ritzcarlton_parser(content, url, other_info)
    else:
        return marriott_hotel_parser(content, url, other_info)


def marriott_hotel_parser(content, url, other_info):
    hotel = HotelBase()
    html_obj = etree.HTML(content[0])
    html2_obj = etree.HTML(content[1])
    html3_obj = etree.HTML(content[2])
    html4_obj = etree.HTML(content[3])
    soup = BeautifulSoup(content[3], 'lxml')
    hotel_name = html_obj.xpath("//h1[@class='hotel-name']/a/span/text()")
    if hotel_name:
        hotel.hotel_name = hotel_name[0]
    hotel.source = 'marriott'
    # source_id = html_obj.xpath("//input[@id='hotel-code']/@value")
    # if source_id:
    #     hotel.source_id = source_id[0]
    brand_str = html_obj.xpath("//span[@itemprop='branchof']/text()")
    if brand_str:
        hotel.brand_name = brand_str[0]
    city = html_obj.xpath("//span[@itemprop='addressLocality']/text()")
    if city:
        hotel.city = city[0]
    country = html_obj.xpath("//span[@itemprop='addressCountry']/text()")
    if country:
        hotel.country = country[0]
    review_num = html_obj.xpath("//div[@class='l-float-left l-margin-left-quarter']/span/text()")
    if review_num:
        hotel.review_num = review_num[0].replace("评论", "")
    else:
        hotel.review_num = '-1'
    address_info = html_obj.xpath("//address/span/text()")
    if address_info:
        address_str = ""
        for address in address_info[0:len(address_info)-1]:
            address_str += address
        hotel.address = address_str
    hotel.hotel_url = url
    description = html_obj.xpath("//p[@id='property-description']/text()")
    if description:
        hotel.description = description[0].strip()
    has_parking = html3_obj.xpath("//ul[@class='l-mml-col-12']/li/text()")
    if has_parking:
        hotel.has_parking = "YES"
        # parking_info中的是停车信息
        parking_info = has_parking[0]
        if "免费停车" in parking_info:
            hotel.is_parking_free = "YES"
    hotel.has_wifi = "YES"
    postal_code = html_obj.xpath("//span[@itemprop='postalCode']/text()")
    if postal_code:
        hotel.postal_code = postal_code[0]
    # img = html_obj.xpath("//div[@class='layout-13']/div[@class='block-1 is-cursor-pointer']/div/img/@src")
    # if img:
    #     hotel.img_items = img[0]
    service_str = ""
    # latitude = html_obj.xpath("//span[@itemprop='latitude']/text()")[0]
    # longitude = html_obj.xpath("//span[@itemprop='longitude']/text()")[0]
    # map_info_str = longitude + "," + latitude
    # hotel.map_info = map_info_str
    infrastructure_str = ""
    infrastructure = html_obj.xpath("//span[@class='t-keyAmenitiesName']/text()")
    if infrastructure:
        for infrastructure_name in infrastructure:
            infrastructure_str += infrastructure_name + "|"
            service_str = infrastructure_str
        hotel.service = service_str
    grade_str = html_obj.xpath("//span[@itemprop='ratingValue']/text()")
    if grade_str:
        hotel.grade = grade_str[0]
    else:
        hotel.grade = '-1.0'
    # check_in_time = html4_obj.xpath("//ul[@class='cs-custom-list t-toggle-container open-by-default']/li[1]/text()")
    # check_out_time = html4_obj.xpath("//ul[@class='cs-custom-list t-toggle-container open-by-default']/li[2]/text()")
    # if check_in_time:
    #     hotel.check_in_time = check_in_time[0].strip()
    # if check_out_time:
    #     hotel.check_out_time = check_out_time[0].strip()
    check_in_str = soup.find('ul', {'class': 'cs-custom-list t-toggle-container open-by-default'})
    if check_in_str:
        check_in_str2 = check_in_str.find_all('li')
        hotel.check_in_time = check_in_str2[0].get_text().strip()
        hotel.check_out_time = check_in_str2[1].get_text().strip()
    has_wifi_list = html4_obj.xpath("//ul[@class='cs-custom-list t-toggle-container l-em-reset']/li/text()")
    if has_wifi_list:
        has_wifi_str = ""
        for has_wifi in has_wifi_list:
            has_wifi_str += has_wifi
        if "免费无线" in has_wifi_str:
            hotel.is_wifi_free = 'YES'
    hotel.img_items = ""
    imges = html2_obj.xpath("//div[@class='l-s-col-2 l-m-col-2 l-margin-bottom']/p/a/img/@src")
    if imges:
        for img in imges:
            hotel.img_items += img.replace("&downsize=*:138px", "") + "|"
    first_img = None
    if hotel.img_items:
        first_img = hotel.img_items.split("|")[0]
    hotel.star = '-1'
    hotel.source_id = other_info.get('source_id')
    hotel.city_id = other_info.get('city_id')
    if other_info.get('longtitude', ''):
        if other_info.get('latitude', ''):
            hotel.map_info = other_info.get('longtitude', '') + ',' + other_info.get('latitude', '')
    hotel.hotel_name_en = other_info.get('hotel_name_en', '')
    hotel.others_info = json.dumps({'city': hotel.city, 'country': hotel.country, 'first_img':first_img}, ensure_ascii=False)
    return hotel


def ritzcarlton_parser(content, url, other_info):
    hotel = HotelBase()
    html_obj = etree.HTML(content[0])
    html2_obj = etree.HTML(content[1])
    hotel_name_str = html_obj.xpath("//span[@class='property-name']/text()")
    if hotel_name_str:
        hotel.hotel_name = hotel_name_str[0]
    hotel.source = "marriott"
    source_id = re.search(r"rfPropertyCode=([A-Z]+)", content[0])
    # if source_id:
    #     hotel.source_id = source_id.group(1)
    hotel.brand_name = "丽思卡尔顿"
    postal_code = html_obj.xpath("//span[@itemprop='postalCode']/text()")
    if postal_code:
        hotel.postal_code = postal_code[0]
    address_city = html_obj.xpath("//span[@itemprop='addressLocality']/text()")
    address_street = html_obj.xpath("//span[@itemprop='streetAddress']/text()")
    if address_city and address_street:
        hotel.address = address_city[0] + "," + address_street[0]
        hotel.city = address_city[0]
    country_str = html_obj.xpath("//span[@itemprop='addressCountry']/text()")
    if country_str:
        hotel.country = country_str[0]
    desc_list = html_obj.xpath("//div[@class='small-12 large-6 columns']/p/text()")
    if desc_list:
        desc_str = ""
        for desc in desc_list:
            desc_str += desc.strip()
        hotel.description = desc_str
    hotel.hotel_url = url
    imges = html_obj.xpath("//source/@data-srcset")
    if imges:
        img_str = ""
        for img in imges:
            img_str += img + "|"
        hotel.img_items = img_str
        first_img = img_str.split("|")[0]
    service_str = ""
    service_list = html2_obj.xpath("//div[@class='basecomponent text'][3]/div[@class='row']/div/div/div/ul/li/text()")
    if service_list:
        for service in service_list:
            service_str += service.strip() + "|"
        hotel.service = service_str
    check_in_out_time = html2_obj.xpath("//div[@class='basecomponent text'][5]/div[@class='row']/div/div/div/ul/li/text()")
    if check_in_out_time:
        check_in_out_str = ""
        for check_str in check_in_out_time:
            check_in_out_str += check_str + "，"
        check_in = re.search(u"入住时间为(.*?)，", check_in_out_str)
        if check_in:
            hotel.check_in_time = check_in.group(1)
        check_out = re.search(u"退房时间为(.*?)，", check_in_out_str)
        if check_out:
            hotel.check_out_time = check_out.group(1)
    has_wifi_str = ""
    has_wifi_list = html2_obj.xpath("//div[@class='basecomponent text'][4]/div[@class='row']/div/div/div/ul/li/text()")
    if has_wifi_list:
        hotel.has_wifi = "YES"
        for has_wifi in has_wifi_list:
            has_wifi_str += has_wifi.strip()
        if "免费无线" in has_wifi_str:
            hotel.is_wifi_free = "YES"
    hotel.review_num = '-1'
    hotel.grade = '-1.0'
    hotel.star = '-1'
    hotel.source_id = other_info.get('source_id')
    hotel.city_id = other_info.get('city_id')
    if other_info.get('longtitude', ''):
        if other_info.get('latitude', ''):
            hotel.map_info = other_info.get('longtitude', '') + ',' + other_info.get('latitude', '')
    hotel.hotel_name_en = other_info.get('hotel_name_en', '')
    hotel.others_info = json.dumps({'city': hotel.city, 'country': hotel.country, 'first_img': first_img},ensure_ascii=False)
    return hotel


if __name__ == '__main__':
    # url = "https://www.ritzcarlton.com/zh-cn/hotels/china/shanghai-pudong"
    # url = "http://www.ritzcarlton.com/zh-cn/hotels/china/shanghai"
    # url = "http://www.ritzcarlton.com/zh-cn/hotels/china/beijing-financial-street"
    url = "http://www.ritzcarlton.com/?marshaCode=WASRT&locale=zh_CN#####The Ritz-Carlton, Washington, DC#####longtitude=-77.049034#####latitude=38.904434"
    url_list = url.split('#####')
    url = url_list[0]
    other_info = {
        'source_id': 'aaaaa',
        'city_id': '111111'
    }
    for i in url_list:
        if len(i.split('=')) > 1:
            key, value = i.split('=')[0], i.split('=')[1]
            if key == 'longtitude':
                other_info['longtitude'] = value
            if key == 'latitude':
                other_info['latitude'] = value
        else:
            if url_list.index(i) == 1:
                other_info['hotel_name_en'] = i
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0'}
    if "https://www.marriott.com" in url:
        url2 = url.replace("travel", "hotel-photos")
        url3 = url.replace("travel/", "maps/travel/")
        url4 = url.replace("hotels/", "hotels/fact-sheet/")
        html = requests.get(url=url, headers=headers).content
        html2 = requests.get(url=url2, headers=headers).content
        html3 = requests.get(url=url3, headers=headers).content
        html4 = requests.get(url=url4, headers=headers).content

        result = marriott_parser(content=[html, html2, html3, html4], url=url, other_info=other_info)
        print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])
    else:
        url2 = url + "/hotel-overview"
        html = requests.get(url=url, headers=headers).content
        html2 = requests.get(url=url2, headers=headers).content

        result = ritzcarlton_parser(content=[html, html2], url=url, other_info=other_info)
        print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])
