#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import json
import requests
from lxml import etree
from proj.my_lib.models.HotelModel import HotelNewBase
from proj.my_lib import parser_exception


def gha_parser(total_content, url, other_info):
    hotel = HotelNewBase()
    hotel.city_id = other_info.get("city_id", "NULL")

    select = etree.HTML(total_content)
    info = re.compile("pins\.gha_hotel\.push\((.*?)\)", re.S)
    address = re.compile("<script type=\"application/ld\+json\">(.*?)</script>", re.S)
    address = json.loads(address.findall(total_content)[0].replace('	', ''))
    info = json.loads(info.findall(total_content)[0])
    hotel.hotel_name = info["title"]
    hotel.hotel_name_en = address["name"]
    hotel.source = "gha"
    hotel.source_id = info["id"]
    hotel.brand_name = info["brand_name"]
    hotel.map_info = str(info["lon"]) + "," + str(info["lat"])
    hotel.address = ''.join(select.xpath("//adress/text()")).strip()
    hotel.country = address["address"]["addressCountry"]
    hotel.city = address["address"]["addressLocality"]
    hotel.postal_code = address["address"]["postalCode"]
    hotel.star = '5'
    hotel.Img_first = select.xpath("//div[@class='FlexEmbed-item']/span/img/@src")
    hotel.hotel_phone = address.get("telephone", 'NULL')
    hotel.hotel_zip_code = address["address"]["postalCode"]
    service = select.xpath('//ul[@class="prop-Amenities"]/li/span/text()')
    servicestr = ''.join(service)
    description = select.xpath("//div[@id='content-about-hotel']/p/text()")
    hotel.description = ''.join(description)
    if u'无线' in servicestr:
        hotel.facility["Room_wifi"] = u'无线上网'
        hotel.facility["Public_wifi"] = u'无线上网'
    if u'泳' in servicestr:
        hotel.facility["Swimming_Pool"] = u'泳池'
    if u'健身' in servicestr:
        hotel.facility["gym"] = u"健身中心"
    if u'水疗' in servicestr:
        hotel.facility['Mandara_Spa'] = u"水疗中心"
    if u'酒吧' in hotel.description:
        hotel.facility["Bar"] = u'酒吧'
    if u'儿童俱乐部' in hotel.description:
        hotel.facility["Recreation"] = u"儿童俱乐部"
    if u'餐' in servicestr:
        hotel.facility["Restaurant"] = u"餐饮"
    if u'商务中心' in servicestr:
        hotel.facility["Business_Centre"] = u'商务中心'
    if u'亲子' in servicestr:
        hotel.feature["Parent_child"] = u'亲子'
    img_list = select.xpath('//div[@class="RotateBanner-itemImg"]/span/@style')
    imgurl = re.compile("url\('(.*?)'\)")
    imgurl_list = []
    for img in img_list:
        imgurl_list.append(imgurl.findall(img)[0])

    hotel.img_items = '|'.join(imgurl_list)

    hotel.check_in_time = '14:00'
    hotel.check_out_time = '12:00'
    reviewsurl = re.compile('<script src="//(.*?)"')
    urls = reviewsurl.findall(total_content)
    if urls[0]:
        reviewsurl = "http://" + urls[0]
    else:
        hotel.grade = '0.0'
        hotel.review_num = 0
        hotel.hotel_url = url
        return hotel.to_dict()
    comment = requests.get(reviewsurl).content
    grade = re.compile('<div class=\\\\"rating-value\\\\">\\\\n(.*?)%', re.S)
    try:
        hotel.grade = str(float(grade.findall(comment)[0].strip()) / 10)
    except:
        hotel.grade = '0.0'
    review = re.compile('<div class=\\\\"review-count\\\\">\\\\n(.*?)reviews', re.S)
    try:
        hotel.review_num = review.findall(comment)[0].strip()
    except:
        hotel.review_num = 0
    hotel.hotel_url = url
    # print room_tuple
    print hotel.to_dict()
    return hotel.to_dict()


if __name__ == '__main__':
    url = "https://zh.gha.com/Alila-Hotels-And-Resorts/Alila-Anji"
    other_info = {
            'source_id': '1039433',
            'city_id': '10074'
        }
    req = requests.get(url, verify=False)
    content = req.content
    gha_parser(content, url, other_info)