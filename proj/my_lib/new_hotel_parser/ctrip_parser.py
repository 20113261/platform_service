#! /usr/bin/env python
# coding=UTF8

'''
    @author:fangwang
    @date:2014-05-13
    @desc: crawl and parse ctrip room data via API
'''

import sys
import execjs
import traceback

import re
import requests
from lxml import html as HTML

from data_obj import Hotel, DBSession

reload(sys)
sys.setdefaultencoding('utf8')

URL = 'http://openapi.ctrip.com/Hotel/OTA_HotelDescriptiveInfo.asmx?wsdl'

TASK_ERROR = 12

PROXY_NONE = 21
PROXY_INVALID = 22
PROXY_FORBIDDEN = 23
DATA_NONE = 24

pat1 = re.compile(r'HotelName="(.*?)" AreaID=".*?" HotelId="(.*?)">', re.S)
pat2 = re.compile(r'Latitude="(.*?)" Longitude="(.*?)"', re.S)


def ctrip_parser(page, url, other_info):
    hotel = Hotel()
    try:
        root = HTML.fromstring(page.decode('utf-8'))
    except Exception, e:
        print str(e)

    ph_runtime = execjs.get('PhantomJS')
    js_str = root.xpath('//script[contains(text(),"hotelDomesticConfig")]/text()')[0]
    page_js = ph_runtime.compile(js_str[:js_str.index('function  loadCallback_roomList()')])
    page_js.eval('hotelDomesticConfig')
    page_js.eval('pictureConfigNew')

    try:
        hotel.hotel_name = root.xpath('//*[@class="name"]/text()')[0].encode('utf-8').strip()
    except Exception, e:
        traceback.print_exc(e)

    try:
        hotel.hotel_name_en = root.xpath('//*[@class="name"]/span/text()')[0].encode('utf8').strip()
    except Exception, e:
        traceback.print_exc(e)

    print 'hotel_name =>', hotel.hotel_name
    print 'hotel_name_en =>', hotel.hotel_name_en

    try:
        position = page_js.eval('hotelDomesticConfig')['hotel']['position'].split('|')
        hotel.map_info = position[1] + ',' + position[0]
    except:
        try:
            position_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip().split('|')
            hotel.map_info = position_temp[1] + ',' + position_temp[0]
        except Exception, e:
            print str(e)
            hotel.map_info = 'NULL'

    print 'hotel.map_info => ', hotel.map_info

    try:
        hotel.star = int(int(page_js.eval('hotelDomesticConfig')['hotel']['star']))
    except:
        hotel.star = -1

    print 'hotel.star => ', hotel.star

    try:
        grade = root.xpath('//*[@class="score_text"]/text()')[0]
        hotel.grade = float(grade.encode('utf-8').strip())
    except Exception:
        try:
            hotel.grade = float(root.xpath('//*[@class="cmt_summary_num_score"]/text()')[0])
        except Exception:
            hotel.grade = -1

    print 'grade =>', hotel.grade
    try:
        address = root.xpath('//div [@class="adress"]/span/text()')[0]
        hotel.address = address.encode('utf-8').strip()
    except Exception, e:
        print str(e)

    print 'address =>', hotel.address

    try:
        hotel.review_num = ''.join(re.findall('(\d+)', root.xpath('//*[@id="commnet_score"]/text()')[0]))
    except Exception:
        try:
            review = root.xpath('//*[@id="commnet_score"]/span[3]/span/text()')[0]
            hotel.review_num = review.encode('utf-8').strip()
        except Exception, e:
            print str(e)

    print 'review_nums =>', hotel.review_num

    try:
        desc = root.xpath('//div[@id="detail_content"]/span/div/div')[0]
        hotel.description = desc.text_content().encode('utf-8').strip().rstrip().replace(' ','').replace('\n','。')
    except Exception, e:
        hotel.description = 'NULL'
        print str(e)

    print 'description => ', hotel.description

    try:
        hotel.img_items = '|'.join(map(lambda x: 'http:' + x['max'], page_js.eval('pictureConfigNew')['hotelUpload']))
    except Exception as e:
        try:
            pic_list = root.xpath('//div[@id="picList"]/div/div/@_src')
            if pic_list:
                img_items = ''
                for each in pic_list:
                    s = each.encode('utf-8').strip()
                    img_items += s + '|'
                hotel.img_items = img_items[:-1]
        except Exception, e:
            traceback.print_exc(e)

    print 'hotel.img_items =>', hotel.img_items

    try:
        p = root.xpath('//div[@id="detail_content"]/div')[2]
        q = HTML.tostring(p)
        checkin_pat = re.compile(
            r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;')
        check_in = checkin_pat.findall(q)
        if not check_in:
            checkin_pat1 = re.compile(
                r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21518;')
            check_in_time = checkin_pat1.findall(q)[0].encode('utf-8') + '以后'
        else:
            check_in_str = check_in[0].encode('utf-8')
            time = check_in_str.split('</span>-<span class="text_bold">')
            check_in_time = time[0] + '-' + time[1]

        checkout_pat = re.compile(
            r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21069;')
        check_out = checkout_pat.findall(q)
        if not check_out:
            checkout_pat1 = re.compile(
                r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span></td></tr>')
            check_out_str = checkout_pat1.findall(q)[0]
            time = check_out_str.split('</span>-<span class="text_bold">')
            check_out_time = time[0] + '-' + time[1]
        else:
            check_out_time = check_out[0].encode('utf-8') + '以前'

        hotel.check_in_time = check_in_time.encode('utf-8').strip()
        hotel.check_out_time = check_out_time.encode('utf-8').strip()
    except Exception, e:
        # print str(e)
        traceback.print_exc(e)

    print 'check_in =>', hotel.check_in_time
    print 'check_out =>', hotel.check_out_time

    try:
        card_pat = re.compile(r'<div class="card_cont_img">(.*?)</div></<div></td></tr>')
        search_card = card_pat.findall(page)[0]
        card_pat1 = re.compile(r'<img alt=(.*?) title=')
        card = card_pat1.findall(search_card)
        temp_name = ''
        for each in card:
            temp_name += each.encode('utf-8').strip()[1:-1] + '|'
        hotel.accepted_cards = temp_name[:-1]
    except Exception, e:
        print str(e)
    print 'hotel.accept_cards =>', hotel.accepted_cards

    try:
        items = root.xpath('//*[@id="detail_content"]/div[2]/table/tbody/tr')
        if items:
            item_str = ''
            for each in items:
                item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
                item = each.xpath('./td/ul/li')
                temp = ''
                for each1 in item:
                    temp += each1.xpath('./text()')[0].encode('utf-8').strip() + '|'
                item_str += item_name + '::' + temp
            hotel.service = item_str[:-1]
    except Exception, e:
        print str(e)

    print 'hotel.service =>', hotel.service

    try:
        if '停车场' in hotel.service:
            hotel.has_parking = 'Yes'
        if '免费停车场' in hotel.service:
            hotel.is_parking_free = 'Yes'
        if '收费停车场' in hotel.service:
            hotel.is_parking_free = 'No'
        if '无线上网' in hotel.service:
            hotel.has_wifi = 'Yes'
    except Exception, e:
        print str(e)

    print 'hotel.has_wifi =>', hotel.has_wifi

    print 'hotel.is_wifi_free =>', hotel.is_wifi_free

    print 'hotel.has_parking =>', hotel.has_parking

    print 'hotel.is_parking_free =>', hotel.is_parking_free
    
    #----feng
    pay_method = ''
    method = root.xpath('//*[@id="room_select_box"]/div[2]/ul/li')

    for pay in method:
        try:
            content = pay.xpath('@data-value')[0]
            if content.count('付'):
                pay_method += content +'|'
        except :
            pass
    hotel.pay_method = pay_method

    print 'pay method-->>',hotel.pay_method


    hotel.hotel_url = url
    hotel.source = 'ctrip'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == '__main__':
    # url = 'http://hotels.ctrip.com/international/992466.html'
    #url = 'http://hotels.ctrip.com/international/3723551.html?IsReposted=3723551'
    url = 'http://hotels.ctrip.com/international/1479993.html'
    #url = 'http://hotels.ctrip.com/international/10146828.html'
    other_info = {
        'source_id': '1039433',
        'city_id': '10074'
    }
    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = ctrip_parser(content, url, other_info)
    '''
    try:
        session = DBSession()
        session.add(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
    '''
