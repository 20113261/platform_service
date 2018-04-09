# #! /usr/bin/env python
# # coding=UTF8
#
# '''
#     @author:fangwang
#     @date:2014-05-13
#     @desc: crawl and parse ctrip room data via API
#
#     @update:jiangzhao
#     @date:2018-03-27
#     @desc: add more than one new field
# '''
#
# import sys
# import execjs
# import traceback
#
# import re
# import requests
# from lxml import html as HTML
# from urlparse import urljoin
# # from data_obj import Hotel, DBSession
# from mioji.common.class_common import Hotel_New
# import json
# reload(sys)
# sys.setdefaultencoding('utf8')
#
# URL = 'http://openapi.ctrip.com/Hotel/OTA_HotelDescriptiveInfo.asmx?wsdl'
#
# TASK_ERROR = 12
#
# PROXY_NONE = 21
# PROXY_INVALID = 22
# PROXY_FORBIDDEN = 23
# DATA_NONE = 24
#
# pat1 = re.compile(r'HotelName="(.*?)" AreaID=".*?" HotelId="(.*?)">', re.S)
# pat2 = re.compile(r'Latitude="(.*?)" Longitude="(.*?)"', re.S)
#
#
# def ctrip_parser(page, url, other_info):
#     hotel = Hotel_New()
#     try:
#         root = HTML.fromstring(page.decode('utf-8'))
#     except Exception, e:
#         print str(e)
#
#     ph_runtime = execjs.get('PhantomJS')
#     js_str = root.xpath('//script[contains(text(),"hotelDomesticConfig")]/text()')[0]
#     print js_str
#     page_js = ph_runtime.compile(js_str[:js_str.index('function  loadCallback_roomList()')])
#     page_js.eval('hotelDomesticConfig')
#     page_js.eval('pictureConfigNew')
#
#     try:
#         hotel.hotel_name = root.xpath('//*[@class="name"]/text()')[0].encode('utf-8').strip()
#     except Exception, e:
#         traceback.print_exc(e)
#
#     try:
#         hotel.hotel_name_en = root.xpath('//*[@class="name"]/span/text()')[0].encode('utf8').strip()
#     except Exception, e:
#         traceback.print_exc(e)
#
#     print 'hotel_name =>', hotel.hotel_name
#     print 'hotel_name_en =>', hotel.hotel_name_en
#
#     try:
#         position = page_js.eval('hotelDomesticConfig')['hotel']['position'].split('|')
#         hotel.map_info = position[1] + ',' + position[0]
#     except:
#         try:
#             position_temp = root.xpath('//*[@id="hotelCoordinate"]/@value')[0].encode('utf-8').strip().split('|')
#             hotel.map_info = position_temp[1] + ',' + position_temp[0]
#         except Exception, e:
#             print str(e)
#             hotel.map_info = 'NULL'
#
#     print 'hotel.map_info => ', hotel.map_info
#
#     try:
#         hotel.star = int(int(page_js.eval('hotelDomesticConfig')['hotel']['star']))
#     except:
#         hotel.star = -1
#
#     print 'hotel.star => ', hotel.star
#
#     try:
#         grade = root.xpath('//*[@class="score_text"]/text()')[0]
#         hotel.grade = float(grade.encode('utf-8').strip())
#     except Exception:
#         try:
#             hotel.grade = float(root.xpath('//*[@class="cmt_summary_num_score"]/text()')[0])
#         except Exception:
#             hotel.grade = -1
#
#     print 'grade =>', hotel.grade
#     try:
#         address = root.xpath('//div [@class="adress"]/span/text()')[0]
#         hotel.address = address.encode('utf-8').strip()
#     except Exception, e:
#         print str(e)
#
#     print 'address =>', hotel.address
#
#     try:
#         hotel.review_num = ''.join(re.findall('(\d+)', root.xpath('//*[@id="commnet_score"]/text()')[0]))
#     except Exception:
#         try:
#             review = root.xpath('//*[@id="commnet_score"]/span[3]/span/text()')[0]
#             hotel.review_num = review.encode('utf-8').strip()
#         except Exception, e:
#             print str(e)
#
#     print 'review_nums =>', hotel.review_num
#
#     try:
#         desc = ''.join(root.xpath('//div[@id="detail_content"]/span/div/div/text()'))
#         hotel.description = desc.encode(
#             'utf-8').strip().rstrip().replace(' ', '').replace('\n', '。').replace('。。', '。')
#     except Exception, e:
#         hotel.description = 'NULL'
#         print str(e)
#
#     print 'description => ', hotel.description
#
#     try:
#         hotel.img_items = '|'.join(map(lambda x: 'http:' + x['max'], page_js.eval('pictureConfigNew')['hotelUpload']))
#     except Exception as e:
#         try:
#             pic_list = root.xpath('//div[@id="picList"]/div/div/@_src')
#             if pic_list:
#                 img_items = ''
#                 for each in pic_list:
#                     s = each.encode('utf-8').strip()
#                     img_items += s + '|'
#                 hotel.img_items = img_items[:-1]
#         except Exception, e:
#             traceback.print_exc(e)
#
#     print 'hotel.img_items =>', hotel.img_items
#
#     # try:
#     #     p = root.xpath('//div[@id="detail_content"]/div')[2]
#     #     q = HTML.tostring(p)
#     #     checkin_pat = re.compile(
#     #         r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;')
#     #     check_in = checkin_pat.findall(q)
#     #     if not check_in:
#     #         checkin_pat1 = re.compile(
#     #             r'&#20837;&#20303;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21518;')
#     #         check_in_time = checkin_pat1.findall(q)[0].encode('utf-8') + '以后'
#     #     else:
#     #         check_in_str = check_in[0].encode('utf-8')
#     #         time = re.findall('(\d{1,2}:\d{1,2}).*?(\d{1,2}:\d{1,2})', check_in_str)[0]
#     #         # time = check_in_str.split('</span>-<span class="text_bold">')
#     #         check_in_time = time[0] + '-' + time[1]
#     #
#     #     checkout_pat = re.compile(
#     #         r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span>&#20197;&#21069;')
#     #     check_out = checkout_pat.findall(q)
#     #     if not check_out:
#     #         checkout_pat1 = re.compile(
#     #             r'&#160;&#160;&#160;&#160;&#160;&#160;&#31163;&#24215;&#26102;&#38388;&#65306;<span class=\"text_bold\">(.*?)</span></td></tr>')
#     #         check_out_str = checkout_pat1.findall(q)[0]
#     #         time = re.findall('(\d{1,2}:\d{1,2}).*?(\d{1,2}:\d{1,2})', check_in_str)[0]
#     #         # time = check_out_str.split('</span>-<span class="text_bold">')
#     #         check_out_time = time[0] + '-' + time[1]
#     #     else:
#     #         check_out_time = check_out[0].encode('utf-8') + '以前'
#     #
#     #     hotel.check_in_time = check_in_time.encode('utf-8').strip()
#     #     hotel.check_out_time = check_out_time.encode('utf-8').strip()
#     # except Exception, e:
#     #     # print str(e)
#     #     traceback.print_exc(e)
#
#     accepted_cards = []
#     try:
#         for card in root.xpath('// *[@class="detail_extracontent layoutfix"]/*[@class="card_cont_img"]/img/@alt'):
#             # re.findall('([\s\S]+?)',cards)
#             res = re.findall('\(([\s\S]+?)\)', card)
#             if res:
#                 accepted_cards.append(res[0].lower())
#     except Exception as exc:
#         print(exc)
#
#     hotel.accepted_cards = '|'.join(accepted_cards)
#     print('hotel.accept_cards =>', hotel.accepted_cards)
#
#     try:
#         # items = root.xpath('//*[@id="detail_content"]/div[2]/table/tbody/tr')
#         # if items:
#         #     item_str = ''
#         #     for each in items:
#         #         try:
#         #             item_name = each.xpath('./th/text()')[0].encode('utf-8').strip()
#         #             item = each.xpath('./td/ul/li')
#         #             temp = ''
#         #             for each1 in item:
#         #                 temp += each1.xpath('./text()')[0].encode('utf-8').strip() + '|'
#         #             item_str += item_name + '::' + temp
#         #         except:
#         #             pass
#         #     hotel.service = item_str[:-1]
#         items = root.xpath("//*[@id='detail_content']/div[@id='J_htl_facilities']/table/tbody/tr/td/ul/li/text()")
#         print items
#         for item in items:
#             item = item.lower()
#             if "客房wifi" in item:
#                 hotel.facility['Room_wifi'] = item
#             elif "客房有线网络" in item:
#                 hotel.facility['Room_wired'] = item
#             elif "公" and "WiFi".lower() in item:
#                 hotel.facility['Public_wifi'] = item
#             elif "公" and "有线网络" in item:
#                 hotel.facility['Public_wired'] = item
#             elif "停车场" in item:
#                 hotel.facility['Parking'] = item
#             elif "机场班车" in item:
#                 hotel.facility['Airport_bus'] = item
#             elif "代客泊车" in item:
#                 hotel.facility['Valet_Parking'] = item
#             elif "叫车服务" in item:
#                 hotel.facility['Call_service'] = item
#             elif "租车服务" in item:
#                 hotel.facility['Rental_service'] = item
#             elif "游泳池" in item:
#                 hotel.facility['Swimming_Pool'] = item
#             elif "健身" in item:
#                 hotel.facility['gym'] = item
#             elif "SPA".lower() in item:
#                 hotel.facility['SPA'] = item
#             elif "酒吧" in item:
#                 hotel.facility['Bar'] = item
#             elif "咖啡厅" in item:
#                 hotel.facility['Coffee_house'] = item
#             elif "网球场" in item:
#                 hotel.facility['Tennis_court'] = item
#             elif "高尔夫球场" in item:
#                 hotel.facility['Golf_Course'] = item
#             elif "桑拿" in item:
#                 hotel.facility['Sauna'] = item
#             elif "水疗中心" in item:
#                 hotel.facility['Mandara_Spa'] = item
#             elif "儿童娱乐场" in item:
#                 hotel.facility['Recreation'] = item
#             elif "商务中心" in item:
#                 hotel.facility['Business_Centre'] = item
#             elif "行政酒廊" in item:
#                 hotel.facility['Lounge'] = item
#             elif "婚礼礼堂" in item:
#                 hotel.facility['Wedding_hall'] = item
#             elif "餐厅" in item:
#                 hotel.facility['Restaurant'] = item
#             elif "行李寄存" in item:
#                 hotel.service['Luggage_Deposit'] = item
#             elif "24小时前台" in item:
#                 hotel.service['front_desk'] = item
#             elif "24小时大堂经理" in item:
#                 hotel.service['Lobby_Manager'] = item
#             elif "24小时办理入住" in item:
#                 hotel.service['24Check_in'] = item
#             elif "24小时安保" in item:
#                 hotel.service['Security'] = item
#             elif "礼宾服务" in item:
#                 hotel.service['Protocol'] = item
#             elif "叫醒服务" in item:
#                 hotel.service['wake'] = item
#             elif "中文前台" in item:
#                 hotel.service['Chinese_front'] = item
#             elif "邮政服务" in item:
#                 hotel.service['Postal_Service'] = item
#             elif "传真/复印" in item:
#                 hotel.service['Fax_copy'] = item
#             elif "洗衣服务" in item:
#                 hotel.service['Laundry'] = item
#             elif "擦鞋服务" in item:
#                 hotel.service['polish_shoes'] = item
#             elif "前台保险柜" in item:
#                 hotel.service['Frontdesk_safe'] = item
#             elif "快速办理入住/退房" in item:
#                 hotel.service['fast_checkin'] = item
#             elif "自动柜员机(ATM)/银行服务" in item:
#                 hotel.service['ATM'] = item
#             elif "儿童看护服务" in item:
#                 hotel.service['child_care'] = item
#             elif "送餐服务" in item:
#                 hotel.service['Food_delivery'] = item
#
#     except Exception, e:
#         print str(e)
#
#     # print 'hotel.service =>', hotel.service
#
#     #获取酒店城市信息
#     try:
#         pattern_str = root.xpath('//form[@id="aspnetForm"]')[0].attrib['action']
#         source_city_id = re.search(r'international/([0-9a-zA-Z]+)',pattern_str).group(1)
#         hotel.source_city_id = source_city_id
#     except Exception as e:
#         print e
#
#     # print "hotel.source_city_id:",hotel.source_city_id
#     #获取others_info信息
#     first_img = None
#     try:
#         first_img = urljoin('http:', root.xpath('//div[@id="picList"]/div/div')[0].attrib['_src'])
#         hotel.Img_first = first_img
#     except Exception as e:
#         print e
#
#     print 'first_img=>%s' % first_img
#
#     try:
#         city_name = page_js.eval('hotelDomesticConfig')['query']['cityName']
#         # city_name = page_js.eval('hotelDomesticConfig')['query']['cityName'].encode('raw-unicode-escape')
#         country_id = page_js.eval('hotelDomesticConfig')['query']['country']
#     except Exception as e:
#         print e
#     print "city_name",city_name,country_id
#
#     hotel.others_info = json.dumps({'first_img': first_img, 'city_name': city_name, 'country_id': country_id})
#
#     print "hotel.others_info:",hotel.others_info
#
#     try:
#         list1 = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr/th/text()")
#         index = 1
#         for th_name in list1:
#             if th_name == "儿童及加床政策":
#                 chiled_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td/ul/li/text()" % index)
#                 hotel.chiled_bed_type = " ".join(chiled_list)
#             elif th_name == "宠物":
#                 pet_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td/text()" % index)
#                 hotel.pet_type = " ".join(pet_list)
#             elif th_name == "入住和离店":
#                 checkin_out_list = root.xpath("//div[@id='detail_content']/div[@class='htl_info_table detail_con_3']/table/tbody/tr[%s]/td//span[@class='text_bold']/text()" % index)
#                 if len(checkin_out_list) == 2:
#                     hotel.check_in_time = checkin_out_list[0] + "以后"
#                     hotel.check_out_time = checkin_out_list[1] + "以前"
#                 else:
#                     hotel.check_in_time = checkin_out_list[0] + "-" + checkin_out_list[1]
#                     hotel.check_out_time = checkin_out_list[2] + "-" + checkin_out_list[3]
#                 # else:
#                 #     hotel.check_in_time = checkin_out_list[0] + "-" + checkin_out_list[1]
#                 #     hotel.check_out_time = checkin_out_list[2] + "以前"
#             index += 1
#     except Exception as e:
#         print e
#     print "pet_type==>%s" % hotel.pet_type
#     print "chiled_bed_type==>%s" % hotel.chiled_bed_type
#     print 'check_in =>', hotel.check_in_time
#     print 'check_out =>', hotel.check_out_time
#
#     try:
#         address_l = address.split(",")
#         zip_code = address_l[-2]
#         if zip_code[:2].isdigit():
#             hotel.hotel_zip_code = zip_code
#         else:
#             hotel.hotel_zip_code = "NULL"
#     except Exception as e:
#         print e
#     print "hotel_zip_code==>%s" % hotel.hotel_zip_code
#
#     try:
#         fea_params = root.xpath("//a[@class='icon_crown2']/@data-params")
#         fea_params2 = root.xpath("//div[@class='htl_info']/div/div[@class='htl_info_tags']/span/text()")
#         if fea_params:
#             fea_params = str(fea_params[0])
#             # fea_dict = json.loads(fea_params[0])
#             # fea_content = fea_dict['options']['content']['txt']
#             fea_content = re.findall(r"{'txt':'(.*?)'}", fea_params)[0]
#             # html_obj = HTML.fromstring(fea_content[0])
#             # fea_name = html_obj.xpath("//div[@class='pops-hovertips-tit']/text()")[0]
#             # service_list = html_obj.xpath("//ul[@class='service_list']/li/text()")
#             fea_name = re.findall(r"“(.*?)”", fea_content)[0]
#             fea_service_list = re.findall(r"</i>(.*?)</li>", fea_content)
#             if "华人礼遇" in fea_name:
#                 hotel.feature['China_Friendly'] = " ".join(fea_service_list)
#             elif "浪漫情侣" in fea_name:
#                 hotel.feature['Romantic_lovers'] = " ".join(fea_service_list)
#             elif "亲子时光" in fea_name:
#                 hotel.feature['Parent_child'] = " ".join(fea_service_list)
#             elif "海滨风光" in fea_name:
#                 hotel.feature['Beach_Scene'] = " ".join(fea_service_list)
#             elif "温泉酒店" in fea_name:
#                 hotel.feature['Hot_spring'] = " ".join(fea_service_list)
#             elif "日式旅馆" in fea_name:
#                 hotel.feature['Japanese_Hotel'] = " ".join(fea_service_list)
#             elif "休闲度假" in fea_name:
#                 hotel.feature['Vacation'] = " ".join(fea_service_list)
#         if fea_params2:
#             for fea in fea_params2:
#                 if "华人礼遇" in fea:
#                     hotel.feature['China_Friendly'] = fea
#                 elif "浪漫情侣" in fea:
#                     hotel.feature['Romantic_lovers'] = fea
#                 elif "亲子酒店" in fea:
#                     hotel.feature['Parent_child'] = fea
#                 elif "海滨风光" in fea:
#                     hotel.feature['Beach_Scene'] = fea
#                 elif "温泉酒店" in fea:
#                     hotel.feature['Hot_spring'] = fea
#                 elif "日式旅馆" in fea:
#                     hotel.feature['Japanese_Hotel'] = fea
#                 elif "休闲度假" in fea:
#                     hotel.feature['Vacation'] = fea
#
#         print "hotel.feature==>%s" % hotel.feature
#     except Exception as e:
#         print e
#     hotel.hotel_url = url
#     hotel.source = 'ctrip'
#     hotel.source_id = other_info['source_id']
#     hotel.city_id = other_info['city_id']
#
#     res = hotel.to_dict()
#     return res
#
#
# if __name__ == '__main__':
#     import threading
#     import time
#     # url = 'http://hotels.ctrip.com/international/992466.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/3723551.html' # OK
#     # url = 'http://hotels.ctrip.com/international/2611722.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/3681269.html'  # OK 正则匹配日期
#     # url = 'http://hotels.ctrip.com/international/747361.html'  # OK re
#     # url = 'http://hotels.ctrip.com/international/10146828.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/2081704.html'  # OK re
#     # url = 'http://hotels.ctrip.com/international/771969.html' # OK
#     # url = 'http://hotels.ctrip.com/international/2802259.html' # OK
#     # url = 'http://hotels.ctrip.com/international/3723826.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/1983097.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/4389196.html'  # OK  re
#     # url = 'http://hotels.ctrip.com/international/981517.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/983720.html'  # OK
#     # url = 'http://hotels.ctrip.com/international/2612287.html'  # OK re
#     # url = 'http://hotels.ctrip.com/international/737038.html'  # OK re
#     # url = 'http://hotels.ctrip.com/international/705353.html'  # OK xpath
#     # url = 'http://hotels.ctrip.com/international/713478.html'  # OK xpath
#     # url = 'http://hotels.ctrip.com/international/3084846.html' #  OK
#     # url = 'http://hotels.ctrip.com/international/5128857.html'  # OK
#     url = 'http://hotels.ctrip.com/international/684981.html'
#     url_list = ['http://hotels.ctrip.com/international/992466.html',
#                 'http://hotels.ctrip.com/international/2611722.html',
#                 'http://hotels.ctrip.com/international/3681269.html',
#                 'http://hotels.ctrip.com/international/747361.html',
#                 'http://hotels.ctrip.com/international/10146828.html',
#                 'http://hotels.ctrip.com/international/2081704.html',
#                 'http://hotels.ctrip.com/international/771969.html',
#                 'http://hotels.ctrip.com/international/2802259.html',
#                 'http://hotels.ctrip.com/international/3723826.html',
#                 'http://hotels.ctrip.com/international/1983097.html',
#                 'http://hotels.ctrip.com/international/4389196.html',
#                 'http://hotels.ctrip.com/international/981517.html',
#                 'http://hotels.ctrip.com/international/983720.html',
#                 'http://hotels.ctrip.com/international/2612287.html',
#                 'http://hotels.ctrip.com/international/737038.html',
#                 'http://hotels.ctrip.com/international/705353.html',
#                 'http://hotels.ctrip.com/international/713478.html',
#                 'http://hotels.ctrip.com/international/3084846.html',
#                 'http://hotels.ctrip.com/international/5128857.html',
#                 'http://hotels.ctrip.com/international/684981.html']
#     other_info = {
#         'source_id': '1039433',
#         'city_id': '10074'
#     }
#
#     page = requests.get(url)
#     page.encoding = 'utf8'
#     content = page.text
#     result = ctrip_parser(content, url, other_info)
#     res = json.loads(result)
#     res = json.dumps(res, ensure_ascii=False)
#     print res
#
#     # def send_request(url):
#     #     page = requests.get(url)
#     #     page.encoding = 'utf8'
#     #     content = page.text
#     #     result = ctrip_parser(content, url, other_info)
#     #
#     #
#     # for url in url_list:
#     #     thread1 = threading.Thread(target=send_request, args=(url,))
#     #     thread1.start()
#
#
#     '''
#     try:
#         session = DBSession()
#         session.add(result)
#         session.commit()
#         session.close()
#     except Exception as e:
#         print str(e)
#     '''
