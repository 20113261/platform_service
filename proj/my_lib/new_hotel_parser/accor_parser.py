#!/usr/bin/python
# -*- coding: UTF-8 -*-
import re
import json
import requests
from lxml.etree import HTML
from pyquery import PyQuery as pq
from proj.my_lib.models.HotelModel import HotelBase
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def accor_parser(content, url, other_info):
    hotel = HotelBase()
    data = content.decode('utf-8')
    hotel_code = re.findall('https://www.accorhotels.com/zh/hotel-(.*?)-.*?/index.shtml', url)[0].lower()

    hotel_url = url
    source = 'accorHotel'
    source_city_id = 'NULL'
    source_id = other_info['source_id']
    city_id = other_info['city_id']
    brand_name = "NULL"
    star = re.findall('<div class="main-rating stars stars--(\d+)"\s*data-halfstars=', data)[0]
    postal_code = re.findall('<meta content="(.*?)" property="og:postal-code">', data)[0]
    hotel_name = re.findall('<meta name="twitter:title" content="(.*?)">', data)[0]
    hotel_name_en = "NULL"
    map_info = ",".join(re.findall('<meta content="(.*?)" name="geo.position"/>', data)[0].split(';')[::-1])
    street = re.findall('<span itemprop="streetAddress">(.*?)</span><br>', data)[0]
    location = re.findall('<span itemprop="addressLocality">(.*?)</span><br>', data)[0]
    _country = re.findall('<span itemprop="addressCountry">(.*?)</span>', data)[0]
    address = _country + location + street
    country = re.findall('<meta content="(.*?)" property="og:country-name">', data)[0]
    city = re.findall('<meta content="(.*?)" property="og:city">', data)[0]
    grade = re.findall(
        '<span class="rating"><span itemprop="ratingValue">\s*(.*?)</span>/<span itemprop="bestRating">5</span>\s*</span>',
        data)[0]
    review = re.findall('<span class="rating-baseline">(.*?)</span>', data)[0]
    review_num = "".join(re.findall('\d+', review))
    has_wifi = 'Yes' if re.findall('<i\s*class="icon icon_wifi"></i>', data) else 'No'
    if has_wifi == 'Yes':
        is_wifi_free = 'Yes' if re.findall('<li\s*class="service-item "\s*data-servicename="wifi">', data) else 'No'
    else:
        is_wifi_free = 'NULL'
    has_parking = 'Yes' if re.findall('<i\s*class="icon icon_parking"></i>', data) else 'No'
    if has_wifi == 'Yes':
        is_parking_free = 'No' if re.findall('<li\s*class="service-item\s*payable"\s*data-servicename="parking">',
                                             data) else 'Yes'
    else:
        is_parking_free = 'NULL'
    img_items = ",".join(re.findall('www.ahstatic.com/photos/' + hotel_code + '_\w+_\d+_p_2048x1536.jpg', data))
    service = pq(data)('div.expandable-content').find('li').text().replace("\t", "").replace("\n", "").replace(" ", "|")
    description = HTML(data).xpath("//p[@itemprop='description']/text()")[0]
    accepted_cards = "NULL"
    check_in_time = re.findall('<i class="icon icon_times"></i>(.*?)</div>', data)[0]
    check_out_time = re.findall('<div class="col col-checkout">(.*?)</div>', data)[0]

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
    hotel.has_wifi = has_wifi
    hotel.is_wifi_free = is_wifi_free
    hotel.has_parking = has_parking
    hotel.is_parking_free = is_parking_free
    hotel.service = service
    hotel.img_items = img_items
    hotel.description = description
    hotel.accepted_cards = accepted_cards
    hotel.check_in_time = check_in_time
    hotel.check_out_time = check_out_time
    hotel.hotel_url = hotel_url
    hotel.others_info = json.dumps(other_info)
    return hotel


if __name__ == '__main__':
    url = 'https://www.accorhotels.com/zh/hotel-A4Z1-%E5%85%A8%E5%AD%A3%E6%9D%AD%E5%B7%9E%E8%A5%BF%E6%B9%96%E5%87%A4%E8%B5%B7%E8%B7%AF%E9%85%92%E5%BA%97/index.shtml'
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
