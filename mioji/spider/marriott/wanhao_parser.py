# -*- coding:utf-8 -*-

import json
import requests
import sys
from proj.my_lib.models.HotelModel import HotelBase
from lxml import etree
reload(sys)
sys.setdefaultencoding("utf-8")


def wanhao_parser(content, url):
    hotel = HotelBase()
    html_obj = etree.HTML(content[0])
    html2_obj = etree.HTML(content[1])
    html3_obj = etree.HTML(content[2])
    hotel_name = html_obj.xpath("//h1[@class='hotel-name']/a/span/text()")
    if hotel_name:
        hotel.hotel_name = hotel_name[0]
    hotel.source = 'wanhao'
    source_id = html_obj.xpath("//input[@id='hotel-code']/@value")
    if source_id:
        hotel.source_id = source_id[0]
    city = html_obj.xpath("//span[@itemprop='addressLocality']/text()")
    if city:
        hotel.city = city[0]
    country = html_obj.xpath("//span[@itemprop='addressCountry']/text()")
    if country:
        hotel.country = country[0]
    review_num = html_obj.xpath("//div[@class='l-float-left l-margin-left-quarter']/span/text()")
    if review_num:
        hotel.review_num = review_num[0]
    address_info = html_obj.xpath("//address/span/text()")
    if address_info:
        address_str = ""
        for address in address_info[0:len(address_info)-1]:
            address_str += address
        hotel.address = address_str
    hotel.hotel_url = url
    description = html_obj.xpath("//p[@id='property-description']/text()")[0].strip()
    if description:
        hotel.description = description
    has_parking = html3_obj.xpath("//ul[@class='l-mml-col-12']/li/text()")
    if has_parking:
        hotel.has_parking = "YES"
        # parking_info中的是停车信息
        parking_info = has_parking[0]
    hotel.has_wifi = "YES"
    postal_code = html_obj.xpath("//span[@itemprop='postalCode']/text()")
    if postal_code:
        hotel.postal_code = postal_code[0]
    # img = html_obj.xpath("//div[@class='layout-13']/div[@class='block-1 is-cursor-pointer']/div/img/@src")
    # if img:
    #     hotel.img_items = img[0]
    service_str = ""
    airport_str = "机场："
    airport_info_node = html3_obj.xpath("//p[@class='h4Class l-airportHeading']/text()")
    if airport_info_node:
        for airport_name in airport_info_node:
            airport_str += airport_name.replace("\t", "").replace("\n", "").strip() + "  "
        hotel.map_info = airport_str
    infrastructure_str = ""
    infrastructure = html_obj.xpath("//span[@class='t-keyAmenitiesName']/text()")
    if infrastructure:
        for infrastructure_name in infrastructure:
            infrastructure_str += infrastructure_name + "  "
            service_str = infrastructure_str
        hotel.service = service_str
    if "免费高速上网" in hotel.service:
        hotel.is_wifi_free = "YES"
    with open("img.html", "wb") as f:
        f.write(content[1])

    hotel.img_items = ""
    imges = html2_obj.xpath("//div[@class='l-s-col-2 l-m-col-2 l-margin-bottom']/p/a/img/@src")
    if imges:
        for img in imges:
            hotel.img_items += img + "  "
    first_img = None
    if hotel.img_items:
        first_img = hotel.img_items.split("  ")[0]
    hotel.others_info = json.dumps({'city': hotel.city, 'country': hotel.country, 'first_img':first_img}, ensure_ascii=False)

    return hotel


if __name__ == '__main__':
    url = "https://www.marriott.com.cn/hotels/travel/laxjw-jw-marriott-los-angeles-la-live/"
    url2 = url.replace("travel", "hotel-photos")
    # url2 = "http://www.marriott.com.cn/hotels/hotel-photos/laxjw-jw-marriott-los-angeles-la-live/"
    url3 = url.replace("travel/", "maps/travel/")
    # url3 = "https://www.marriott.com.cn/hotels/maps/travel/laxjw-jw-marriott-los-angeles-la-live/"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:47.0) Gecko/20100101 Firefox/47.0'}
    html = requests.get(url=url, headers=headers).content
    html2 = requests.get(url=url2, headers=headers).content
    html3 = requests.get(url=url3, headers=headers).content
    result = wanhao_parser(content=[html, html2, html3], url=url)
    print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])
