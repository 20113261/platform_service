#! /usr/bin/env python
# coding=UTF8

'''
    @author:fangwang
    @date:2014-05-13
    @desc: crawl and parse ctrip room data via API

    @update:jiangzhao
    @date:2018-03-27
    @desc: add more than one new field
'''

import sys
import execjs
import traceback
import time
import re
import requests
from lxml import html as HTML
from urlparse import urljoin
# from data_obj import Hotel, DBSession
# from mioji.common.class_common import Hotel_New as CtripHotelNewBase
from proj.my_lib.models.HotelModel import CtripHotelNewBase, Facilities, Service, Feature
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
    # import time
    # t1 = time.time()
    hotel = CtripHotelNewBase()
    service_content = Service()
    facility_content = Facilities()
    feature_content = Feature()
    try:
        root = HTML.fromstring(page.decode('utf-8'))
    except Exception, e:
        print str(e)

    ph_runtime = execjs.get('PhantomJS')
    js_str = root.xpath('//script[contains(text(),"hotelDomesticConfig")]/text()')[0]
    print js_str
    page_js = ph_runtime.compile(js_str[:js_str.index('function  loadCallback_roomList()')])
    hotelDomesticConfig = page_js.eval('hotelDomesticConfig')
    pictureConfigNew = page_js.eval('pictureConfigNew')

    try:
        hotel.hotel_name = root.xpath('//*[@class="name"]/text()')[0].encode('utf-8').strip()
    except Exception, e:
        traceback.print_exc(e)

    try:
        hotel.hotel_name_en = root.xpath('//*[@class="name"]/span/text()')[0].encode('utf8').strip()
    except Exception, e:
        traceback.print_exc(e)

    # print 'hotel_name =>', hotel.hotel_name
    # print 'hotel_name_en =>', hotel.hotel_name_en

    try:
        position = hotelDomesticConfig['hotel']['position'].split('|')
        hotel.map_info = position[1] + ',' + position[0]
    except:
        try:
            position_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip().split('|')
            hotel.map_info = position_temp[1] + ',' + position_temp[0]
        except Exception, e:
            print str(e)
            hotel.map_info = 'NULL'

    # print 'hotel.map_info => ', hotel.map_info

    try:
        hotel.star = int(int(hotelDomesticConfig['hotel']['star']))
    except:
        hotel.star = -1

    # print 'hotel.star => ', hotel.star

    try:
        grade = root.xpath('//*[@class="score_text"]/text()')[0]
        hotel.grade = float(grade.encode('utf-8').strip())
    except Exception:
        try:
            hotel.grade = float(root.xpath('//*[@class="cmt_summary_num_score"]/text()')[0])
        except Exception:
            hotel.grade = -1

    # print 'grade =>', hotel.grade
    try:
        address = root.xpath('//div [@class="adress"]/span/text()')[0]
        hotel.address = address.encode('utf-8').strip()
    except Exception, e:
        print str(e)

    # print 'address =>', hotel.address

    try:
        hotel.review_num = ''.join(re.findall('(\d+)', root.xpath('//*[@id="commnet_score"]/text()')[0]))
    except Exception:
        try:
            review = root.xpath('//*[@id="commnet_score"]/span[3]/span/text()')[0]
            hotel.review_num = review.encode('utf-8').strip()
        except Exception, e:
            print str(e)

    # print 'review_nums =>', hotel.review_num

    try:
        desc = ''.join(root.xpath('//div[@id="detail_content"]/span/div/div/text()'))
        hotel.description = desc.encode(
            'utf-8').strip().rstrip().replace('  ', '').replace('\n', '。').replace('。。', '。')
    except Exception, e:
        hotel.description = 'NULL'
        print str(e)

    # print 'description => ', hotel.description

    try:
        hotel.img_items = '|'.join(map(lambda x: 'http:' + x['max'], pictureConfigNew['hotelUpload']))
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

    try:
        hotel.brand_name = root.xpath("//div[@id='groupBrandDesc']/div[@class='textbox']/p/b/text()")[0]
    except Exception as e:
        pass

    # print 'hotel.img_items =>', hotel.img_items

    accepted_cards = []
    try:
        for card in root.xpath("//div[@class='card_cont_img']/img/@alt"):
            # re.findall('([\s\S]+?)',cards)
            # res = re.findall('\(([\s\S]+?)\)', card)
            # if res:
            accepted_cards.append(card.lower())
    except Exception as exc:
        print(exc)

    hotel.accepted_cards = '|'.join(accepted_cards)
    # print('hotel.accept_cards =>', hotel.accepted_cards)

    try:
        # items = root.xpath('//*[@id="detail_content"]/div[2]/table/tbody/tr')
        # if items:
        #     item_str = ''
        #     for each in items:
        #         try:
        #             item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
        #             item = each.xpath('./td/ul/li')
        #             temp = ''
        #             for each1 in item:
        #                 temp += each1.xpath('./text()')[0].encode('utf-8').strip() + '|'
        #             item_str += item_name + '::' + temp
        #         except:
        #             pass
        #     hotel.service = item_str[:-1]
        items = root.xpath("//*[@id='detail_content']/div[@id='J_htl_facilities']/table/tbody/tr/td/ul/li/text()")
        print items
        for item in items:
            item = item.lower()
            if "客房wifi" in item:
                facility_content['Room_wifi'] = item
            elif "客房有线网络" in item:
                facility_content['Room_wired'] = item
            elif "公" and "WiFi".lower() in item:
                facility_content['Public_wifi'] = item
            elif "公" and "有线网络" in item:
                facility_content['Public_wired'] = item
            elif "停车场" in item:
                facility_content['Parking'] = item
            elif "机场班车" in item:
                facility_content['Airport_bus'] = item
            elif "代客泊车" in item:
                facility_content['Valet_Parking'] = item
            elif "叫车服务" in item:
                facility_content['Call_service'] = item
            elif "租车服务" in item:
                facility_content['Rental_service'] = item
            elif "游泳池" in item:
                facility_content['Swimming_Pool'] = item
            elif "健身" in item:
                facility_content['gym'] = item
            elif "SPA".lower() in item:
                facility_content['SPA'] = item
            elif "酒吧" in item:
                facility_content['Bar'] = item
            elif "咖啡厅" in item:
                facility_content['Coffee_house'] = item
            elif "网球场" in item:
                facility_content['Tennis_court'] = item
            elif "高尔夫球场" in item:
                facility_content['Golf_Course'] = item
            elif "桑拿" in item:
                facility_content['Sauna'] = item
            elif "水疗中心" in item:
                facility_content['Mandara_Spa'] = item
            elif "儿童娱乐场" in item:
                facility_content['Recreation'] = item
            elif "商务中心" in item:
                facility_content['Business_Centre'] = item
            elif "行政酒廊" in item:
                facility_content['Lounge'] = item
            elif "婚礼礼堂" in item:
                facility_content['Wedding_hall'] = item
            elif "餐厅" in item:
                facility_content['Restaurant'] = item
            elif "行李寄存" in item:
                service_content['Luggage_Deposit'] = item
            elif "24小时前台" in item:
                service_content['front_desk'] = item
            elif "24小时大堂经理" in item:
                service_content['Lobby_Manager'] = item
            elif "24小时办理入住" in item:
                service_content['24Check_in'] = item
            elif "24小时安保" in item:
                service_content['Security'] = item
            elif "礼宾服务" in item:
                service_content['Protocol'] = item
            elif "叫醒服务" in item:
                service_content['wake'] = item
            elif "中文前台" in item:
                service_content['Chinese_front'] = item
            elif "邮政服务" in item:
                service_content['Postal_Service'] = item
            elif "传真/复印" in item:
                service_content['Fax_copy'] = item
            elif "洗衣服务" in item:
                service_content['Laundry'] = item
            elif "擦鞋服务" in item:
                service_content['polish_shoes'] = item
            elif "前台保险柜" in item:
                service_content['Frontdesk_safe'] = item
            elif "快速办理入住/退房" in item:
                service_content['fast_checkin'] = item
            elif "自动柜员机(ATM)/银行服务" in item:
                service_content['ATM'] = item
            elif "儿童看护服务" in item:
                service_content['child_care'] = item
            elif "送餐服务" in item:
                service_content['Food_delivery'] = item

            hotel.service = service_content.to_values()
            hotel.facility = facility_content.to_values()

    except Exception, e:
        print str(e)

    # print 'hotel.service =>', hotel.service

    #获取酒店城市信息
    try:
        pattern_str = root.xpath('//form[@id="aspnetForm"]')[0].attrib['action']
        source_city_id = re.search(r'international/([0-9a-zA-Z]+)',pattern_str).group(1)
        hotel.source_city_id = source_city_id
    except Exception as e:
        print e

    # print "hotel.source_city_id:",hotel.source_city_id
    #获取others_info信息
    first_img = None
    try:
        first_img = urljoin('http:', root.xpath('//div[@id="picList"]/div/div')[0].attrib['_src'])
        hotel.Img_first = first_img
    except Exception as e:
        print e

    # print 'first_img=>%s' % first_img

    try:
        city_name = hotelDomesticConfig['query']['cityName']
        hotel.city = city_name
        # city_name = page_js.eval('hotelDomesticConfig')['query']['cityName'].encode('raw-unicode-escape')
        country_id = hotelDomesticConfig['query']['country']
    except Exception as e:
        print e

    try:
        list1 = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr/th/text()")
        index = 1
        for th_name in list1:
            if th_name == "儿童及加床政策":
                chiled_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td/ul/li/text()" % index)
                hotel.chiled_bed_type = " ".join(chiled_list)
            elif th_name == "宠物":
                pet_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td/text()" % index)
                hotel.pet_type = " ".join(pet_list)
            # elif th_name == "入住和离店":
            #     checkin_out_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td//span[@class='text_bold']/text()" % index)
            #     if len(checkin_out_list) == 2:
            #         hotel.check_in_time = checkin_out_list[0] + "以后"
            #         hotel.check_out_time = checkin_out_list[1] + "以前"
            #     elif len(checkin_out_list) == 4:
            #         hotel.check_in_time = checkin_out_list[0] + "-" + checkin_out_list[1]
            #         hotel.check_out_time = checkin_out_list[2] + "-" + checkin_out_list[3]
            #     elif len(checkin_out_list) == 3:
            #         hotel.check_in_time = checkin_out_list[0] + "-" + checkin_out_list[1]
            #         hotel.check_out_time = checkin_out_list[2] + "以前"
            #     elif len(checkin_out_list) == 5:
            #         hotel.check_in_time = checkin_out_list[0] + "-" + checkin_out_list[1]
            #         hotel.check_out_time = checkin_out_list[2] + "-" + checkin_out_list[3]
            index += 1
    except Exception as e:
        print e

    try:
        p = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']")[0]
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

        hotel.check_in_time = check_in_time.encode('utf-8').strip().replace("<span class=\"text_bold\">", "").replace("</span>", "").replace("<br>&#37202;&#24215;&#21069;&#21488;&#26381;&#21153;&#26102;&#38388;&#33267;&#65306;23:59", "")
        hotel.check_out_time = check_out_time.encode('utf-8').strip().replace("<span class=\"text_bold\">", "").replace("</span>", "").replace("<br>&#37202;&#24215;&#21069;&#21488;&#26381;&#21153;&#26102;&#38388;&#33267;&#65306;23:59", "")
    except Exception, e:
        # print str(e)
        traceback.print_exc(e)
    # print "pet_type==>%s" % hotel.pet_type
    # print "chiled_bed_type==>%s" % hotel.chiled_bed_type
    # print 'check_in =>', hotel.check_in_time
    # print 'check_out =>', hotel.check_out_time
    try:
        address_l = address.split(",")
        country = address_l[-1] if address_l else 'NULL'
        hotel.country = country
    except Exception as e:
        hotel.country = 'NULL'


    try:
        address_l = address.split(",")
        zip_code = address_l[-2]
        if zip_code[:2].isdigit():
            hotel.hotel_zip_code = zip_code
            hotel.postal_code = zip_code
        else:
            hotel.hotel_zip_code = "NULL"
            hotel.postal_code = "NULL"
    except Exception as e:
        print e
    # print "hotel_zip_code==>%s" % hotel.hotel_zip_code

    try:
        fea_params = root.xpath("//a[@class='icon_crown2']/@data-params")
        fea_params2 = root.xpath("//div[@class='htl_info']/div/div[@class='htl_info_tags']/span/text()")
        if fea_params:
            fea_params = str(fea_params[0])
            # fea_dict = json.loads(fea_params[0])
            # fea_content = fea_dict['options']['content']['txt']
            fea_content = re.findall(r"{'txt':'(.*?)'}", fea_params)[0]
            # html_obj = HTML.fromstring(fea_content[0])
            # fea_name = html_obj.xpath("//div[@class='pops-hovertips-tit']/text()")[0]
            # service_list = html_obj.xpath("//ul[@class='service_list']/li/text()")
            fea_name = re.findall(r"“(.*?)”", fea_content)[0]
            fea_service_list = re.findall(r"</i>(.*?)</li>", fea_content)
            if "华人礼遇" in fea_name:
                feature_content['China_Friendly'] = " ".join(fea_service_list)
            elif "浪漫情侣" in fea_name:
                feature_content['Romantic_lovers'] = " ".join(fea_service_list)
            elif "亲子时光" in fea_name:
                feature_content['Parent_child'] = " ".join(fea_service_list)
            elif "海滨风光" in fea_name:
                feature_content['Beach_Scene'] = " ".join(fea_service_list)
            elif "温泉酒店" in fea_name:
                feature_content['Hot_spring'] = " ".join(fea_service_list)
            elif "日式旅馆" in fea_name:
                feature_content['Japanese_Hotel'] = " ".join(fea_service_list)
            elif "休闲度假" in fea_name:
                feature_content['Vacation'] = " ".join(fea_service_list)
            hotel.feature = feature_content.to_values()
        if fea_params2:
            for fea in fea_params2:
                if "华人礼遇" in fea:
                    feature_content['China_Friendly'] = fea
                elif "浪漫情侣" in fea:
                    feature_content['Romantic_lovers'] = fea
                elif "亲子酒店" in fea:
                    feature_content['Parent_child'] = fea
                elif "海滨风光" in fea:
                    feature_content['Beach_Scene'] = fea
                elif "温泉酒店" in fea:
                    feature_content['Hot_spring'] = fea
                elif "日式旅馆" in fea:
                    feature_content['Japanese_Hotel'] = fea
                elif "休闲度假" in fea:
                    feature_content['Vacation'] = fea
                hotel.feature = feature_content.to_values()

        # print "hotel.feature==>%s" % hotel.feature_content
    except Exception as e:
        print e
    hotel.hotel_url = url
    hotel.source = 'ctrip'
    hotel.source_id = other_info['source_id']
    hotel.city_id = other_info['city_id']
    hotel_services_info = ""
    try:
        items = root.xpath("//*[@id='detail_content']/div[@id='J_htl_facilities']/table/tbody/tr")
        if items:
            item_str = ''
            for each in items:
                try:
                    item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
                    item = each.xpath('./td/ul/li')
                    temp = ''
                    for each1 in item:
                        temp += each1.xpath('string(.)').encode('utf-8').strip() + '|'
                    item_str += item_name + '::' + temp
                except:
                    pass
            hotel_services_info += item_str
        if fea_params:
            fea_str = fea_name
            hotel_services_info += "特色::" + fea_str + "|"
        if fea_params2:
            fea_str2 = "|".join(fea_params2)
            if "特色::" in hotel_services_info:
                hotel_services_info += fea_str2
            else:
                hotel_services_info += "特色::" + fea_str2
    except:
        hotel_services_info = hotel_services_info
    # try:
    #     resrve_info = root.xpath("//div[@id='hotelAdd']/p[@id='bookingTip']/text()")
    #     resrve_str = ''.join(map(lambda x: x.strip(), resrve_info))
    # except:
    #     resrve_str = "NULL"
    hotel.others_info = json.dumps({'first_img': first_img, 'city_name': city_name,
                                    'country_id': country_id, 'hotel_services_info': hotel_services_info,
                                    })
    # hotel.facility = str(hotel.facility_content)
    # hotel.service = str(hotel.service_content)
    # hotel.feature = str(hotel.feature_content)
    # res = json.loads(res)
    # res = json.dumps(res, ensure_ascii=False)
    # print res
    # with open("ctrip.json", 'a') as f:
    #     f.write(res + "\n")
    # t2 = time.time()
    # print t2 - t1
    return hotel


if __name__ == '__main__':
    import threading
    import time
    # url = 'http://hotels.ctrip.com/international/992466.html'  # OK
    # url = 'http://hotels.ctrip.com/international/3723551.html' # OK
    # url = 'http://hotels.ctrip.com/international/2611722.html'  # OK
    # url = 'http://hotels.ctrip.com/international/3681269.html'  # OK 正则匹配日期
    # url = 'http://hotels.ctrip.com/international/747361.html'  # OK re
    # url = 'http://hotels.ctrip.com/international/10146828.html'  # OK
    # url = 'http://hotels.ctrip.com/international/2081704.html'  # OK re
    # url = 'http://hotels.ctrip.com/international/771969.html' # OK
    # url = 'http://hotels.ctrip.com/international/2802259.html' # OK
    # url = 'http://hotels.ctrip.com/international/3723826.html'  # OK
    # url = 'http://hotels.ctrip.com/international/1983097.html'  # OK
    # url = 'http://hotels.ctrip.com/international/4389196.html'  # OK  re
    # url = 'http://hotels.ctrip.com/international/981517.html'  # OK
    # url = 'http://hotels.ctrip.com/international/983720.html'  # OK
    # url = 'http://hotels.ctrip.com/international/2612287.html'  # OK re
    # url = 'http://hotels.ctrip.com/international/737038.html'  # OK re
    # url = 'http://hotels.ctrip.com/international/705353.html'  # OK xpath
    # url = 'http://hotels.ctrip.com/international/713478.html'  # OK xpath
    # url = 'http://hotels.ctrip.com/international/3084846.html' #  OK
    # url = 'http://hotels.ctrip.com/international/5128857.html'  # OK
    # url = 'http://hotels.ctrip.com/international/684981.html'
    # url = 'http://hotels.ctrip.com/international/10000063.html'
    # url = 'http://hotels.ctrip.com/international/10000124.html'
    # url = 'http://hotels.ctrip.com/international/10000149.html'
    # url = 'http://hotels.ctrip.com/international/10000158.html'
    # url = 'http://hotels.ctrip.com/international/10000165.html'
    # url = 'http://hotels.ctrip.com/international/10000250.html'
    # url = 'http://hotels.ctrip.com/international/11494485.html'
    # url = 'http://hotels.ctrip.com/international/2002721.html'
    # url = 'http://hotels.ctrip.com/international/2002366.html'
    # url = 'http://hotels.ctrip.com/international/2216831.html'
    # url = 'http://hotels.ctrip.com/international/713478.html'
    url = 'http://hotels.ctrip.com/international/713478.html'
    # url = 'http://hotels.ctrip.com/international/2216831.html'
    url_list = ['http://hotels.ctrip.com/international/992466.html',
                'http://hotels.ctrip.com/international/2611722.html',
                'http://hotels.ctrip.com/international/3681269.html',
                'http://hotels.ctrip.com/international/747361.html',
                'http://hotels.ctrip.com/international/10146828.html',
                'http://hotels.ctrip.com/international/2081704.html',
                'http://hotels.ctrip.com/international/771969.html',
                'http://hotels.ctrip.com/international/2802259.html',
                'http://hotels.ctrip.com/international/3723826.html',
                'http://hotels.ctrip.com/international/1983097.html',]
                # 'http://hotels.ctrip.com/international/4389196.html',
                # 'http://hotels.ctrip.com/international/981517.html',
                # 'http://hotels.ctrip.com/international/983720.html',
                # 'http://hotels.ctrip.com/international/2612287.html',
                # 'http://hotels.ctrip.com/international/737038.html',
                # 'http://hotels.ctrip.com/international/705353.html',
                # 'http://hotels.ctrip.com/international/713478.html',
                # 'http://hotels.ctrip.com/international/3084846.html',
                # 'http://hotels.ctrip.com/international/5128857.html',
                # 'http://hotels.ctrip.com/international/684981.html']
    url_list2 = [
        'http://hotels.ctrip.com/international/11494485.html',
        'http://hotels.ctrip.com/international/2002721.html',
        'http://hotels.ctrip.com/international/2002366.html',
        'http://hotels.ctrip.com/international/2216831.html',
        'http://hotels.ctrip.com/international/713478.html',
        'http://hotels.ctrip.com/international/2158769.html',
    ]
    other_info = {
        'source_id': '1039433',
        'city_id': '10074'
    }
    #
    # for url in url_list2:
    #     page = requests.get(url)
    #     page.encoding = 'utf8'
    #     content = page.text
    #     result = ctrip_parser(content, url, other_info)
    #     res = json.loads(result)
    #     res = json.dumps(res, ensure_ascii=False)
    #     print res

    page = requests.get(url)
    page.encoding = 'utf8'
    content = page.text
    result = ctrip_parser(content, url, other_info)
    # res = json.loads(result)
    # res = json.dumps(res, ensure_ascii=False)
    print result

    # def send_request(url):
    #     page = requests.get(url)
    #     page.encoding = 'utf8'
    #     content = page.text
    #     result = ctrip_parser(content, url, other_info)
    #
    #
    # for url in url_list:
    #     thread1 = threading.Thread(target=send_request, args=(url,))
    #     thread1.start()


    '''
    try:
        session = DBSession()
        session.add(result)
        session.commit()
        session.close()
    except Exception as e:
        print str(e)
    '''