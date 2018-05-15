#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import json
import requests
from lxml.etree import HTML
from pyquery import PyQuery as pq
from mioji.common import parser_except
# from proj.my_lib.models.HotelModel import HotelBase
from mioji.common.class_common import Hotel_New as HotelBase
# from proj.my_lib.models.HotelModel import CtripHotelNewBase
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def get_blank(content):
    return 'NULL' if content == [] else content[0]


def accor_parser(content, url, other_info):
    hotel = HotelBase()
    html_obj = HTML(content)
    data = content.decode('utf-8')
    if '<title>Book a hotel online with Accor Hotels</title>' in data:
        raise parser_except.ParserException(29, '网站暂时维护中')
    hotel_code = re.findall('https://www.accorhotels.com/zh/hotel-(.*?)-.*?/index.shtml', url)[0].lower()
    hotel_url = url
    source = 'accorHotel'
    source_city_id = 'NULL'
    brand_name = "NULL"
    _star = re.findall('<div class="main-rating stars stars--(\d+)"\s*data-halfstars=', data)
    star = _star[0] if _star != [] else -1
    _postal_code = html_obj.xpath("//span[@itemprop='postalCode']/text()")
    postal_code = _postal_code[0] if _postal_code else "NULL"
    hotel_name = re.findall('<meta name="twitter:title" content="(.*?)">', data)[0]
    hotel_name_en = "NULL"
    _map_info = html_obj.xpath("//meta[@name='geo.position']/@content")
    map_info = _map_info[0].replace(";", ",") if _map_info else "NULL"
    # street = re.findall('<span itemprop="streetAddress">(.*?)</span><br>', data)[0]
    _street = html_obj.xpath("//span[@itemprop='streetAddress']/text()")
    street = ' '.join(_street) if _street else ""
    # location = re.findall('<span itemprop="addressLocality">(.*?)</span><br>', data)[0]
    _location = html_obj.xpath("//span[@itemprop='addressLocality']/text()")
    location = ' '.join(_location) if _location else ""
    _country1 = re.findall('<span itemprop="addressCountry">(.*?)</span>', data)[0]
    country_ = html_obj.xpath("//span[@itemprop='addressCountry']/text()")
    _country = ' '.join(country_) if country_ else ""
    address = street + postal_code + location + _country
    country = _country1
    _city = html_obj.xpath("//meta[@property='og:city']/@content")
    city = _city[0] if _city else "NULL"
    _grade = re.findall(
        '<span class="rating"><span itemprop="ratingValue">\s*(.*?)</span>/<span itemprop="bestRating">5</span>\s*</span>',
        data)
    grade = _grade[0] if _grade != [] else -1.0
    review = get_blank(re.findall('<span class="rating-baseline">(.*?)</span>', data))
    review_num = "".join(re.findall('\d+', review)) or -1
    img_items = "|".join(re.findall('www.ahstatic.com/photos/' + hotel_code + '_\w+_\d+_p_2048x1536.jpg', data))
    source_id = other_info['source_id']
    city_id = other_info['city_id']
    first_img = None
    if img_items:
        first_img = img_items.split('|')[0]
    # service = pq(data)('div.expandable-content').find('li').text().replace("\t", "").replace("\n", "").replace(" ", "|")
    try:
        service_1_l = html_obj.xpath("//section[@id='section-services']/div[@class='section__content']/div[@class='services__container']/div[@class='services__category services__category-main']/ul/li")
        service_1 = "|".join(map(lambda x: x.xpath("string(.)").replace(" ", "").strip(), service_1_l))
        service_2_l = html_obj.xpath("//section[@id='section-services']/div[@class='section__content']/div[@class='services__container']/div[@class='expandable-container']//div[@class='services__category']/ul/li")
        service_2 = "|".join(map(lambda x: x.xpath("string(.)").replace(" ", "").strip(), service_2_l))
        # service = service_1 + "|" + service_2
        room_service_l = html_obj.xpath("//ul[@class='bxslider-amenities']/li/ul/li/text()")
        room_service = "|".join(room_service_l)
        service = service_1 + "|" + service_2 + "|" + room_service
    except Exception as e:
        service = "NULL"
    _traffic = html_obj.xpath("//ul[@class='transportation__list']/li/text()")
    traffic = " ".join(filter(lambda x: x != "", _traffic)) if _traffic else "NULL"
    others_info = {"city": city, "country": country, "first_img": first_img, "source_city_id": source_city_id, "hotel_services_info": service}
    _description = HTML(data).xpath("//p[@itemprop='description']/text()")
    description = " ".join(_description) if _description else "NULL"
    accepted_cards = "NULL"
    check_in_time = get_blank(re.findall('<i class="icon icon_times"></i>(.*?)</div>', data))
    check_out_time = get_blank(re.findall('<div class="col col-checkout">(.*?)</div>', data))

    hotel.hotel_name = hotel_name
    hotel.hotel_name_en = hotel_name_en
    hotel.source = source
    hotel.source_id = source_id
    hotel.source_city_id = source_city_id
    hotel.brand_name = brand_name
    hotel.map_info = map_info
    hotel.address = address
    hotel.city = city
    hotel.country = country
    hotel.city_id = city_id
    hotel.postal_code = postal_code
    hotel.star = star
    hotel.grade = grade
    hotel.review_num = review_num
    # hotel.service = service
    hotel.img_items = img_items
    hotel.Img_first = first_img
    hotel.description = description
    hotel.accepted_cards = accepted_cards
    hotel.check_in_time = check_in_time
    hotel.check_out_time = check_out_time
    hotel.hotel_url = hotel_url
    hotel.traffic = traffic
    hotel.others_info = json.dumps(others_info)
    print hotel.to_dict()
    return hotel.to_dict()


if __name__ == '__main__':
    url = 'https://www.accorhotels.com/zh/hotel-8098-%E7%8F%A0%E6%B5%B7%E4%B8%AD%E6%B5%B7%E9%93%82%E5%B0%94%E6%9B%BC%E9%85%92%E5%BA%97/index.shtml'
    # url = 'https://www.accorhotels.com/zh/hotel-0338-%E5%AE%9C%E5%BF%85%E6%80%9D%E9%98%BF%E8%8E%B1%E6%96%AF%E4%B8%AD%E5%BF%83%E9%85%92%E5%BA%97/index.shtml'
    other_info = {
        'source_id': '119538',
        'city_id': '10001'
    }

    def get_page(url):
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"}
        html = requests.get(url, headers=headers, verify=False)
        if html.status_code == 200:
            return html.text

    g = get_page(url)
    accor_parser(g, url, other_info)
