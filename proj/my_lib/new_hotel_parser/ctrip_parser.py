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
from urlparse import urljoin
from data_obj import Hotel, DBSession
from proj.my_lib.models.HotelModel import CtripHotel
import json
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
    hotel = CtripHotel()
    try:
        root = HTML.fromstring(page.decode('utf-8'))
    except:
        #print str(e)
        pass

    ph_runtime = execjs.get('PhantomJS')
    try:
        js_str = root.xpath('//script[contains(text(),"hotelDomesticConfig")]/text()')[0]
        page_js = ph_runtime.compile(js_str[:js_str.index('function  loadCallback_roomList()')])
    except:
        try:
            page_js = ph_runtime.compile(js_str[:js_str.index('function loadCallback()')])
        except:
            pass
    # page_js.eval('hotelDomesticConfig')
    # page_js.eval('pictureConfigNew')

    try:
        hotel.hotel_name = root.xpath('//*[@class="name"]/text()')[0].encode('utf-8').strip()
    except:pass
        # traceback.print_exc(e)

    try:
        hotel.hotel_name_en = root.xpath('//*[@class="name"]/span/text()')[0].encode('utf8').strip()
    except:pass
        # traceback.print_exc(e)

    #print 'hotel_name =>', hotel.hotel_name
    #print 'hotel_name_en =>', hotel.hotel_name_en

    try:
        HotelMaiDianData = page_js.eval('HotelMaiDianData')['value']
        hotellon = HotelMaiDianData.get('hotellon', None)
        hotellat = HotelMaiDianData.get('hotellat', None)
        hotel.map_info = hotellon + ',' + hotellat
    except:
        try:
            position = page_js.eval('hotelDomesticConfig')['hotel']['position'].split('|')
            hotel.map_info = position[1] + ',' + position[0]
        except:
            try:
                position_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip().split('|')
                hotel.map_info = position_temp[1] + ',' + position_temp[0]
            except:
                #print str(e)
                hotel.map_info = 'NULL'

    #print 'hotel.map_info => ', hotel.map_info

    try:
        hotel.star = int(int(page_js.eval('hotelDomesticConfig')['hotel']['star']))
    except:
        hotel.star = -1

    #print 'hotel.star => ', hotel.star

    try:
        grade = root.xpath('//*[@class="score_text"]/text()')[0]
        hotel.grade = float(grade.encode('utf-8').strip())
    except Exception:
        try:
            hotel.grade = float(root.xpath('//*[@class="cmt_summary_num_score"]/text()')[0])
        except Exception:
            hotel.grade = -1

    #print 'grade =>', hotel.grade
    try:
        address = root.xpath('//div [@class="adress"]/span/text()')[0]
        hotel.address = address.encode('utf-8').strip()
    except:
        #print str(e)
        pass

    #print 'address =>', hotel.address

    try:
        hotel.review_num = ''.join(re.findall('(\d+)', root.xpath('//*[@id="commnet_score"]/text()')[0]))
    except Exception:
        try:
            review = root.xpath('//*[@id="commnet_score"]/span[3]/span/text()')[0]
            hotel.review_num = review.encode('utf-8').strip()
        except:
            #print str(e)
            pass

    #print 'review_nums =>', hotel.review_num

    try:
        desc = ''.join(root.xpath('//div[@id="detail_content"]/span/div/div/text()'))
        hotel.description = desc.encode(
            'utf-8').strip().rstrip().replace(' ', '').replace('\n', '。').replace('。。', '。')
    except:
        hotel.description = 'NULL'
        #print str(e)

    #print 'description => ', hotel.description

    try:
        hotel.img_items = '|'.join(map(lambda x: 'http:' + x['max'], page_js.eval('pictureConfigNew')['hotelUpload']))
    except:
        try:
            pic_list = root.xpath('//div[@id="picList"]/div/div/@_src')
            if pic_list:
                img_items = ''
                for each in pic_list:
                    s = each.encode('utf-8').strip()
                    img_items += s + '|'
                hotel.img_items = img_items[:-1]
        except:
            pass
            # traceback.print_exc(e)

    #print 'hotel.img_items =>', hotel.img_items

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
            time = re.findall('(\d{1,2}:\d{1,2}).*?(\d{1,2}:\d{1,2})', check_in_str)[0]
            # time = check_in_str.split('</span>-<span class="text_bold">')
            check_in_time = time[0] + '-' + time[1]

        checkout_pat = re.compile(
            r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21069;')
        check_out = checkout_pat.findall(q)
        if not check_out:
            checkout_pat1 = re.compile(
                r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span></td></tr>')
            check_out_str = checkout_pat1.findall(q)[0]
            time = re.findall('(\d{1,2}:\d{1,2}).*?(\d{1,2}:\d{1,2})', check_in_str)[0]
            # time = check_out_str.split('</span>-<span class="text_bold">')
            check_out_time = time[0] + '-' + time[1]
        else:
            check_out_time = check_out[0].encode('utf-8') + '以前'

        hotel.check_in_time = check_in_time.encode('utf-8').strip()
        hotel.check_out_time = check_out_time.encode('utf-8').strip()
    except:
        # #print str(e)
        # traceback.print_exc(e)
        pass
    #print 'check_in =>', hotel.check_in_time
    #print 'check_out =>', hotel.check_out_time

    # try:
    #     card_pat = re.compile(r'<div class="card_cont_img">(.*?)</div></<div></td></tr>')
    #     search_card = card_pat.findall(page)[0]
    #     card_pat1 = re.compile(r'<img alt=(.*?) title=')
    #     card = card_pat1.findall(search_card)
    #     temp_name = ''
    #     for each in card:
    #         temp_name += each.encode('utf-8').strip()[1:-1] + '|'
    #     hotel.accepted_cards = temp_name[:-1]
    # except:
    #     #print str(e)
    # #print 'hotel.accept_cards =>', hotel.accepted_cards

    # accept cards
    accepted_cards = []
    try:
        for card in root.xpath('// *[@class="detail_extracontent layoutfix"]/*[@class="card_cont_img"]/img/@alt'):
            # re.findall('([\s\S]+?)',cards)
            res = re.findall('\(([\s\S]+?)\)', card)
            if res:
                accepted_cards.append(res[0].lower())
    except:
        #print(exc)
        pass

    hotel.accepted_cards = '|'.join(accepted_cards)
    #print('hotel.accept_cards =>', hotel.accepted_cards)

    try:
        items = root.xpath('//*[@id="detail_content"]/div[2]/table/tbody/tr')
        if items:
            item_str = ''
            for each in items:
                try:
                    item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
                    item = each.xpath('./td/ul/li')
                    temp = ''
                    for each1 in item:
                        temp += each1.xpath('./text()')[0].encode('utf-8').strip() + '|'
                    item_str += item_name + '::' + temp
                except:
                    pass
            hotel.service = item_str[:-1]
    except:
        #print str(e)
        pass

    #print 'hotel.service =>', hotel.service

    try:
        if '停车场' in hotel.service:
            hotel.has_parking = 'Yes'
        if '免费停车场' in hotel.service:
            hotel.is_parking_free = 'Yes'
        if '收费停车场' in hotel.service:
            hotel.is_parking_free = 'No'
        if '无线上网' in hotel.service:
            hotel.has_wifi = 'Yes'
    except:
        #print str(e)
        pass

    #获取酒店城市信息
    try:
        pattern_str = root.xpath('//form[@id="aspnetForm"]')[0].attrib['action']
        source_city_id = re.search(r'international/([0-9a-zA-Z]+)',pattern_str).group(1)
        hotel.source_city_id = source_city_id
    except:
        #print e
        pass

    #print "hotel.source_city_id:",hotel.source_city_id
    #获取others_info信息
    first_img = None
    try:
        first_img = urljoin('http:', root.xpath('//div[@id="picList"]/div/div')[0].attrib['_src'])
    except:
        #print e
        pass

    #print 'first_img=>%s' % first_img

    try:
        city_name = page_js.eval('hotelDomesticConfig')['query']['cityName']
        # city_name = page_js.eval('hotelDomesticConfig')['query']['cityName'].encode('raw-unicode-escape')
        country_id = page_js.eval('hotelDomesticConfig')['query']['country']
    except:
        #print e
        city_name = 'NULL'
        country_id = 'NULL'
    #print "city_name",city_name,country_id

    hotel.others_info = json.dumps({'first_img': first_img, 'city_name': city_name, 'country_id': country_id, 'hid':other_info.get('hid', 'NULL')})

    #print "hotel.others_info:",hotel.others_info
    #print 'hotel.has_wifi =>', hotel.has_wifi

    #print 'hotel.is_wifi_free =>', hotel.is_wifi_free

    #print 'hotel.has_parking =>', hotel.has_parking

    #print 'hotel.is_parking_free =>', hotel.is_parking_free

    # # ----feng
    # pay_method = ''
    # method = root.xpath('//*[@id="room_select_box"]/div[2]/ul/li')
    #
    # l_method = []
    # for pay in method:
    #     try:
    #         content = pay.xpath('@data-value')[0]
    #         if content.count('付'):
    #             l_method.append(content)
    #     except:
    #         pass
    # hotel.pay_method = '|'.join(l_method)
    #
    # #print 'pay method-->>', hotel.pay_method


    hotel.hotel_url = url
    hotel.source = 'ctrip'
    if other_info.get('hid'):
        hotel.source_id = re.findall('/(\d+)\.html', url)[0]
        # hotel.source_id = page_js.eval('hotelDomesticConfig.query.cityId')
    else:
        hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    # others_info_dict = hotel.__dict__
    # if first_img:
    #     others_info_dict['first_img'] = first_img
    # hotel.others_info = json.dumps(others_info_dict)
    # if first_img:
    #     del others_info_dict['first_img']
    # #print hotel

    return hotel


if __name__ == '__main__':
    # url = 'http://hotels.ctrip.com/international/992466.html'
    # url = 'http://hotels.ctrip.com/international/3723551.html?IsReposted=3723551'
    # url = 'http://hotels.ctrip.com/international/2611722.html'
    # url = 'http://hotels.ctrip.com/international/3681269.html'
    # url = 'http://hotels.ctrip.com/hotel/2387745.html?isFull=F#ctm_ref=hod_sr_map_dl_txt_1'
    url = 'http://hotels.ctrip.com/international/1741965.html'
    # url = 'http://hotels.ctrip.com/international/747361.html'
    # url = 'http://hotels.ctrip.com/international/10146828.html'
    other_info = {
        'source_id': '1039433',
        'city_id': '10074',
        'hid': 1234
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
    except:
        #print str(e)
    '''
