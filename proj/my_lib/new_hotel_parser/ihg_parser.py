#coding:utf-8
import requests
import re
import json
from lxml import etree
from lxml import html as HTML
from proj.my_lib.models.HotelModel import HotelBase

def ihg_parser(content, url, o_info):
    hotel = HotelBase()
    html = etree.HTML(content[0])
    hotel_name = html.xpath('//*[@id="hotelname"]/@value')
    if hotel_name:
        hotel.hotel_name = hotel_name[0]
    hotel_name_en = html.xpath('//*[@id="hotelnameEnglish"]/@value')
    if hotel_name_en:
        hotel.hotel_name_en = hotel_name_en[0]
    hotel.source = 'ihg'
    source_id = html.xpath('//*[@id="hotelCode"]/@value')
    if source_id:
        hotel.source_id = source_id[0]
    city = html.xpath('//*[@id="city"]/@value')
    if city:
        hotel.city = city[0]
    brand_name = html.xpath('//*[@id="brand-name"]/@value')
    if brand_name:
        hotel.brand_name = brand_name[0]
    longitude = html.xpath('//*[@id="longitude"]/@value')
    if longitude:
        longitude = longitude[0]
        latitude = html.xpath('//*[@id="latitude"]/@value')
        if latitude:
            latitude = latitude[0]
            hotel.map_info = longitude + ',' + latitude
    # address = html.xpath('//div[@class="address"]/a//span/text()')
    # hotel.address = ''
    # for one_address in address:
    #     hotel.address += one_address
    # print hotel.address
    country = html.xpath('//*[@itemprop="addressCountry"]/text()')
    if country:
        hotel.country = country[0]
    # postal_code = html.xpath('//*[@itemprop="zipCode"]/text()')
    # if postal_code:
    #     hotel.postal_code = postal_code[0]
    grade = html.xpath('//*[@itemprop="ratingValue"]/text()')
    if grade:
        hotel.grade = grade[0]
    num = html.xpath('//*[@itemprop="reviewCount"]/text()')
    if num:
        hotel.review_num = num[0]
    hotel.img_items = ''
    imgs = html.xpath('//div[@id="photo-1-thumbnail"]//img')
    # print len(imgs)
    for img in imgs:
        img_url = img.xpath('./@data-desktop')
        if img_url:
            hotel.img_items += 'https:'
            hotel.img_items += img_url[0]
            hotel.img_items += '|'
    # print hotel.img_items
    # description = html.xpath('//div[contains(@class,"hotel-description")]')
    # if description:
    #     hotel.description = str(description[0].xpath('string(.)')).strip()
    # print hotel.description
    html2 = HTML.fromstring(content[1])
    description = html2.xpath('//*[@class="lessDesc"]/span/text()')
    if description:
        hotel.description = str(description[0]).strip()
    hotel.address = ''
    address = html2.xpath(u'//h5[text()="地址"]/following-sibling::dl[1]/dd')
    for one_address in address:
        hotel.address += one_address.xpath('string(.)').strip()
    if '获取指南' in hotel.address:
        hotel.address = hotel.address.replace('获取指南', '')
    postal_code = re.findall(r'\d{5,}', hotel.address)
    if postal_code:
        hotel.postal_code = postal_code[0]
    has_wifi = html2.xpath(u'//h5[text()="上网"]/..//dd/text()')
    if has_wifi:
        hotel.has_wifi = 'Yes'
        hotel.is_wifi_free = ''
        for one_wifi in has_wifi:
            hotel.is_wifi_free += one_wifi
    # print hotel.is_wifi_free
    has_parking = html2.xpath(u'//h5[text()="停车"]/..//dd/text()')
    if has_parking:
        hotel.has_parking = 'Yes'
        hotel.is_parking_free = ''
        for one_parking in has_parking:
            hotel.is_parking_free += one_parking
    service_rows = html2.xpath('//div[@class="col-md-4 well well-noborder"]')
    hotel.service = ''
    for row in service_rows:
        for div in row.xpath('./div'):
            h5 = div.xpath('.//h5/text()')
            if len(h5) > 0:
                h5 = h5[0] + ':'
                dds = div.xpath('.//dd')
                hotel.service += str(h5)
                for dd in dds:
                    dd_content = dd.xpath('string(.)')
                    if len(dd_content) > 0:
                        dd_content = dd_content + '|'
                        hotel.service += str(dd_content)
    # print hotel.service
    check_in_time = html2.xpath(u'//h5[text()="入住"]/following-sibling::dl[1]/dd/span/text()')
    check_out_time = html2.xpath(u'//h5[text()="退房"]/following-sibling::dl[1]/dd/span/text()')
    if check_in_time:
        hotel.check_in_time = check_in_time[0].strip()
        # print hotel.check_in_time
    if check_out_time:
        hotel.check_out_time = check_out_time[0].strip()
        # print hotel.check_out_time
    hotel.hotel_url = url
    if hotel.img_items:
        first_img = hotel.img_items.split('|')[0]
    hotel.others_info = json.dumps({"city": hotel.city, "country": hotel.country, "first_img": first_img, "source_city_id": hotel.source_city_id})
    return hotel

if __name__ == '__main__':
    url = 'https://www.ihg.com/hotels/cn/zh/brooklyn/bxyev/hoteldetail?qRef=sr&qDest=%E7%BA%BD%E7%BA%A6%E5%9F%8E%2C+NY%2C+%E7%BE%8E%E5%9B%BD&qRpn=2&qChld=0&qAAR=6CBARC&qSrt=sDD&qSHp=1&qSmP=3&qIta=99602392&qGRM=0&qLng=-73.985626&qRdU=1&qRms=1&srb_u=1&qAdlt=1&qPSt=0&qRtP=6CBARC&qCiMy=012018&qCoD=16&qLat=40.757996&qCiD=15&qCoMy=012018&qRmP=3&qRRSrt=rt&qRad=30&qRpp=20&qBrs=6c.hi.ex.rs.ic.cp.in.sb.cw.cv.ul.vn.ki.sp.nd.ct&qWch=0'
    url2 = 'https://www.ihg.com/hotels/cn/zh/reservation/searchresult/viewhoteldetail/pegha?qDest=北京&qRpn=1&qChld=0&qAAR=6CBARC&qRms=1&srb_u=1&qAdlt=1&qCiMy=002018&qCoD=20&qCiD=18&qCoMy=002018'
    page = requests.get(url)
    content = page.text
    page2 = requests.get(url2)
    content2 = page2.text
    result = ihg_parser([content, content2], url)
    print '\n'.join(['%s:%s' % item for item in result.__dict__.items()])