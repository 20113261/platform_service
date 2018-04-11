#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import requests
from lxml import etree
from proj.my_lib.models.HotelModel import HotelNewBase
from proj.my_lib import parser_exception


def hilton_parser(total_content, url, other_info):
    Hotel = HotelNewBase()
    content, detail_content, map_info_content, desc_content, enDetail_content = total_content
    select_detail =etree.HTML(detail_content)
    check_in_time = ''
    check_out_time = ''
    hotel_id = url.split("/")[-2].split("-")[-1]
    Hotel.hotel_url = url
    try:
        ALL = select_detail.xpath("//td[@headers='compare_{} compare_registration']/text()".format(hotel_id))
        ALL = u'：'.join(ALL)
        check_time = ALL.replace('\n', '').replace('\t', '').replace(' ', '')
        check_time = check_time.split(u'：')
        check_in_time = check_time[1]
        check_out_time = check_time[-1]
    except Exception, e:
        print str(e)
    Hotel.check_in_time = check_in_time
    Hotel.check_out_time = check_out_time
    Hotel = get_detail(Hotel, detail_content,enDetail_content,hotel_id)
    Hotel.source = 'source'
    Hotel.source_id = Hotel.source_id = other_info['source_id']
    Hotel.city_id = other_info['city_id']
    try:
        map_info_data = re.findall(r'var hotelJsonInfo = (.*?);', map_info_content)[0]
        map_info_data = eval(map_info_data)
        location = map_info_data.get('TxLocation', None) or map_info_data.get('Location', None)
        mmp = location.replace(' ', '').split(',')
        map_info = mmp[1].strip() + ',' + mmp[0].strip()

    except Exception as e:
        map_info = 'NULL'
        print e

    Hotel.map_info = map_info
    # print Hotel.map_info
    select = etree.HTML(content)
    full_address = select.xpath('//span[@class="addr"]/text()')
    if full_address:
        Hotel.address = full_address[0]
    code = re.findall("(\d{5,6})",Hotel.address)
    if code:
        Hotel.hotel_zip_code = code[0]
    phone = select.xpath('//span[@class="tel tel-pc"]/text()')
    if phone:
        Hotel.hotel_phone = phone[0].replace("-",'')


    try:
        img_list = re.findall(r'var HotelAlbumList = (.*?)var HotelName', content, re.S)[0]
        img_list = re.findall(r'"ImageSrc":"(.*?)"', img_list, re.S)
        Hotel.Img_first = img_list[0]
        img_url_set = set()
        for img in img_list:
            img_url_set.add(img)
    except Exception, e:
        print e
    img_items = ''
    for ima in img_url_set:
        img_items += ima.encode('raw-unicode-escape')
        img_items += '|'

    Hotel.img_items = img_items
    select_map = etree.HTML(map_info_content)
    traffic = select_map.xpath("//div[@class='access-guide-inner']/p/text()")
    if traffic:
        Hotel.traffic = traffic[0].encode('raw-unicode-escape')

    select_desc = etree.HTML(desc_content)
    desc = select_desc.xpath('//div[@class="intro fix"]/p/text()')
    if desc:
        Hotel.description = desc[0].encode('raw-unicode-escape')
    # hotel = Hotel.to_dict()
    return Hotel


def get_detail(Hotel, content, enDetail_content,hotel_id):
    select = etree.HTML(content)
    hotel_name = select.xpath('//td[@class="tdHotelName"]/h3/a/text()')
    if hotel_name:
        Hotel.hotel_name = hotel_name[0]
    else:
        raise parser_exception.ParserException(29, "解析失败")
    pet = select.xpath('//td[@headers="compare_{} compare_pets"]/text()'.format(hotel_id))
    if pet:
        Hotel.pet_type = pet[0].strip()
    facilities = select.xpath("//tbody[@id='tbodyfacilities']/tr")
    for facility in facilities:
        info = facility.xpath('./td/text()|./td/span/text()')
        info_list = []
        for item in info:
            if item.strip():
                info_list.append(item.strip())
            else:
                continue
        if u'不适用' in info_list[1]:
            continue
        if u"客房内有线上网" in info_list[0]:
            Hotel.facility_content["Room_wired"] = info_list[0]
        if u"客房内无线上网" in info_list[0]:
            Hotel.facility_content["Room_wifi"] = info_list[0]
        if u"公共区域无线上网" in info_list[0]:
            Hotel.facility_content["Public_wifi"] = info_list[0]
        if u"餐厅" in info_list[0]:
            Hotel.facility_content["Restaurant"] = info_list[0]
        if u"酒吧" in info_list[0]:
            Hotel.facility_content["Bar"] = info_list[0]
    servers = select.xpath("//tbody[@id='tbodyservices']/tr")
    for server in servers:
        info = server.xpath('./td/text()|./td/span/text()')
        info_list = []
        for item in info:
            if item.strip():
                info_list.append(item.strip())
            else:
                continue
        if u'商务中心	' in info_list[0]:
            Hotel.facility_content["Business_Centre"] = info_list[0]
        if u'水疗中心	' in info_list[0]:
            Hotel.facility_content["Mandara_Spa"] = info_list[0]
    traffics = select.xpath("//tbody[@id='tbodytransportation']/tr")
    for traffic in traffics:
        info = traffic.xpath('./td/text()|./td/span/text()')
        info_list = []
        for item in info:
            if item.strip():
                info_list.append(item.strip())
            else:
                continue
        if u'泊车' in info_list[0]:
            Hotel.facility_content["Valet_Parking"] = info_list[1]
            # print info_list[1]
    try:
        PARK = select.xpath('//td[@id="compare_parkdist"]/text()')
        if u'泊车' in PARK[0]:
            Hotel.facility["Parking"] = '停车场'
        else:
            pass
    except Exception as e:
        print e
    if u'Complimentary Printing Service' in enDetail_content:
        Hotel.service_content["Fax_copy"] = u"免费打印服务、传真"
    if u'Baggage Storage' in enDetail_content:
        Hotel.service_content["Luggage_Deposit"] = u'行李寄存'
    if u'Concierge Desk' in enDetail_content:
        Hotel.service_content["Protocol"] = u"礼宾接待处"
    if u'Multi-Lingual Staff' in enDetail_content:
        Hotel.service_content["Chinese_front"] = u'多语种工作人员'
    if u'Safety Deposit Box' in enDetail_content:
        Hotel.service_content["Frontdesk_safe"] = u'保险箱'
    Hotel.service = str(Hotel.service_content)
    if u'Fitness Room' in enDetail_content:
        Hotel.facility_content["gym"] = u"健身房"
    if u'Tennis Court' in enDetail_content:
        Hotel.facility_content['Tennis_court'] = u'网球场'
    if u'Laundry/Valet Service' in enDetail_content:
        Hotel.facility_content["Laundry"] = u"洗衣/代客服务"
    if u'Automated Teller (ATM)' in enDetail_content:
        Hotel.facility_content["ATM"] = u"自动柜员机（ATM）"
    if u'Sauna' in enDetail_content:
        Hotel.facility_content["Sauna"] = u'桑拿'
    if u'Pool' in enDetail_content:
        Hotel.facility_content["Swimming_Pool"] = '水池'
    enselect = etree.HTML(enDetail_content)
    hotel_name_en = enselect.xpath("//span[@class='property-name']/text()")
    if hotel_name_en:
        Hotel.hotel_name_en = hotel_name_en[0]
    res = Hotel.to_dict()
    return res
    # print enDetail_content
        # if
        # try:
        #     name, value = server.xpath('./td/text()|./td/span/text()')
        # except:
        #     print(server.xpath('./td/text()|./td/span/text()'))
        #     continue
        # print name,value
    # print content


if __name__ == '__main__':
    # from proj.my_lib.Common.Browser import MySession
    # session = MySession()
    # url = 'http://www.hilton.com.cn/zh-CN/hotel/Beijing/hilton-beijing-wangfujing-BJSWFHI/'
    # url = 'http://www.hilton.com.cn/zh-cn/hotel/sharjah/hilton-sharjah-SHJHSHI/'
    url = 'http://www.hilton.com.cn/zh-cn/hotel/new-york/millennium-hilton-new-york-one-un-plaza-NYCUPHH/'
    detail_url = 'http://www3.hilton.com/zh_CN/hotels/china/{}/popup/hotelDetails.html'.format(url.split('/')[-2])
    enDetail_url = 'http://www3.hilton.com/en/hotels/{}/{}/about/amenities.html'.format(url.split("/")[-3], url.split("/")[-2])
    map_info_url = url + 'maps-directions.html'
    desc_url = url + 'about.html'
    session = requests.session()
    content = session.get(url).text
    detail_content = session.get(detail_url).text
    map_info_content = session.get(map_info_url).text
    desc_content = session.get(desc_url).text
    enDetail = session.get(enDetail_url)
    enDetail.encoding = 'utf8'
    enDetail_content = enDetail.text
    other_info = {
        'source_id': '1000',
        'city_id': '50795'
    }
    total_content = [content, detail_content, map_info_content, desc_content, enDetail_content]
    result = hilton_parser(total_content, url, other_info)
    print result
# 'http://www3.hilton.com/en/hotels/new-york/millennium-hilton-new-york-one-un-plaza-NYCUPHH/about/amenities.html'
# 'http://www3.hilton.com/en/hotels/millennium-hilton-new-york-one-un-plaza-NYCUPHH//about/amenities.html'
