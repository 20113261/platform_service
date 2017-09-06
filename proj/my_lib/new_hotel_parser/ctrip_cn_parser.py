#! /usr/bin/env python
# -*- coding:utf-8 -*-

"""
    @desc: 抓取ctrip国内酒店详情

"""
import requests
from lxml import html
from data_obj import Hotel
from mioji.common.parser_except import PARSE_ERROR
import traceback
import re
import execjs
from mioji.common.logger import logger
from mioji.common.func_log import current_log_tag
from urlparse import urljoin


# from data_obj import Hotel
def ctrip_cn_parser(content, url, other_info):
    hotel = Hotel()
    try:
        root = html.fromstring(content.decode('utf-8'))
    except Exception as e:
        print traceback.format_exc()
        raise PARSE_ERROR

    try:
        phantomjs = execjs.get('PhantomJS')
        js_str = root.xpath("//script[contains(text(),'hotelDomesticConfig')]/text()")[0]
        page_js = phantomjs.compile(js_str[:js_str.index('function loadCallback()')])
    except Exception as e:
        print traceback.format_exc()
        logger.debug(current_log_tag() + '[获取JS中数据失败]')

    try:
        hotel_name = root.xpath('//h2[@class="cn_n"]/text()')[0]

        temp = re.findall(ur'([\u4e00-\u9fa5\s]*)', hotel_name)
        zh_name_tmep = [t for t in temp if t and t != ' ']
        if len(zh_name_tmep) == 1:
            hotel.hotel_name = zh_name_tmep[0].encode('utf8')
        elif len(zh_name_tmep) > 1:
            temp_ii = hotel_name.find(zh_name_tmep[-1]) + len(zh_name_tmep[-1])
            temp_iii = hotel_name.find(')', temp_ii)
            if temp_iii>-1:
                hotel.hotel_name = hotel_name[:temp_iii+1].encode('utf8')
        else:
            hotel.hotel_name = ''

        if not zh_name_tmep:
            hotel.hotel_name_en = hotel_name.encode('utf8').strip(')').strip('(').strip('）').strip('（').strip()
        else:
            name_en_temp = hotel_name[hotel_name.find(zh_name_tmep[-1]) + len(zh_name_tmep[-1])+1:]
            hotel.hotel_name_en = name_en_temp.encode('utf8').strip(')').strip('(').strip('）').strip('（').strip()
    except Exception as e:
        print traceback.format_exc()
        logger.debug(current_log_tag() + '[解析英文名失败]')

    # try:
    #     hotel_name = root.xpath('//h2[@class="cn_n"]/text()')[0].strip()
    #     hotel.hotel_name = re.search(u'[\u4e00-\u9fa5]+', hotel_name).group()
    # except Exception as e:
    #     print traceback.format_exc()
    #     logger.debug(current_log_tag() + '【解析中文名失败】')

    print "中文名：", hotel.hotel_name
    print "英文名：", hotel.hotel_name_en

    try:
        position = page_js.eval('hotelDomesticConfig')['hotel']['position'].split('|')
        hotel.map_info = position[1] + ',' + position[0]
        print "hotel.map_info:", hotel.map_info
    except Exception as e:
        try:
            position_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip().split('|')
            hotel.map_info = position_temp[1] + ',' + position_temp[0]

        except Exception, e:
            print traceback.format_exc()
            logger.debug(current_log_tag() + '【解析酒店地址失败】')
            hotel.map_info = 'NULL'

    try:
        star = root.xpath("//span[@id='ctl00_MainContentPlaceHolder_commonHead_imgStar']")[0]
        print "star:", star.attrib['title'].encode('utf-8')
        hotel.star = int(re.search(r'([\d]+)', star.attrib['title'].encode('utf-8')).group(1))
        print "hotel.star:", hotel.star
    except:
        hotel.star = -1
        logger.debug(current_log_tag() + '[解析酒店星级失败]')

    try:
        grade = root.xpath("//span[@class='score']/text()")[0]
        hotel.grade = float(grade)
        print "hotel.grade:", hotel.grade
    except:
        try:
            grade = root.xpath("//span[@class='n']/text()")[0]
            hotel.grade = float(grade)
            print "hotel.grade：", hotel.grade
        except:
            hotel.grade = -1
            logger.debug(current_log_tag() + '[解析酒店评分失败]')

    try:
        address = root.xpath('//div[@class="adress"]/span/text()')
        hotel.address = ''.join(address).strip()
        print "hotel.address:", hotel.address
    except:
        logger.debug(current_log_tag() + '[解析酒店地址是失败]')

    try:
        desc = root.xpath('//span[@id="ctl00_MainContentPlaceHolder_hotelDetailInfo_lbDesc"]/text()')[0]
        hotel.description = desc
        print "hotel.description:", hotel.description
    except:
        hotel.description = 'NULL'
        logger.debug(current_log_tag() + '[解析酒店描述失败]')

    try:
        review_num = root.xpath('//span[@itemprop="reviewCount"]/text()')[0].encode('utf-8')
        hotel.review_num = re.search(r'(\d+)', review_num).group(1)
        print "hotel.review_num:", hotel.review_num
    except:
        logger.debug(current_log_tag() + '[解析酒店评论数失败]')
    try:
        img_list = root.xpath("//div[@id='topPicList']/div/div/@_src")
        hotel.img_items = '|'.join([urljoin('http:', img) for img in img_list])
        print "hotel.img_items:", hotel.img_items
    except:
        logger.debug(current_log_tag() + '[解析酒店图片失败]')

    try:
        time_str = root.xpath('//table[@class="detail_extracontent"]/tr[1]/td/text()')[0]
        print "time_str:", time_str.encode('utf-8')
        hotel.check_in_time = time_str[5:13].encode('utf-8').strip()
        hotel.check_out_time = time_str[-7:].encode('utf-8').strip()
        print "time:", hotel.check_in_time, hotel.check_out_time
    except:
        logger.debug(current_log_tag() + "[解析入住时间和离开时间]")

    try:
        card_name = []
        bank_card = root.xpath('//div[@class="detail_extracontent layoutfix"]/span')
        for bank in bank_card:
            result_judge = re.search(
                u'<div class="jmp_bd">\u5883\u5916\u53d1\u884c\u4fe1\u7528\u5361 -- [\u4e00-\u9fa5]*\(?([a-zA-Z]+)\)?',
                bank.attrib['data-params'])
            if result_judge:
                card_name.append(result_judge.group(1).strip())
            else:
                result_judge = re.search(u'<div class="jmp_bd">([\u4e00-\u9fa5]+)', bank.attrib['data-params'])
                if result_judge:
                    card_name.append(result_judge.group(1).strip())
        hotel.accepted_cards = u'|'.join(card_name)
    except:
        logger.debug(current_log_tag() + "[解析酒店支持的银行支付]")

    try:
        services = root.xpath("//div[@id='J_htl_facilities']//tr/td/ul/li/@title")[:-1]
        hotel.service = u'|'.join(services)
        if u'有可无线上网的公共区域免费' in hotel.service:
            hotel.has_wifi = 'Yes'
        if u'免费停车场' in hotel.service:
            hotel.is_parking_free = 'Yes'
        if u'收费停车场' in hotel.service:
            hotel.is_parking_free = 'No'
        if u'停车场' in hotel.service:
            hotel.has_parking = 'Yes'
    except:
        logger.debug(current_log_tag() + "[解析WIFI以及停车场]")
    hotel.hotel_url = url
    hotel.source = 'ctrip'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']

    return hotel


if __name__ == "__main__":
    url = "http://hotels.ctrip.com/hotel/1867988.html?isFull=F#ctm_ref=hod_sr_map_dl_txt_9"
    response = requests.get(url)
    response.encoding = 'utf-8'
    content = response.content

    other_info = {
        'source_id': '1867988',
        'city_id': '20043'
    }
    result = ctrip_cn_parser(content, url, other_info)
