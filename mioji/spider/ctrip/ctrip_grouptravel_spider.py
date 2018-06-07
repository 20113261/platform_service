#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import re
import requests
import time
import datetime
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from ctrip_grouptravel_parser import CtripGrouptravel
from bs4 import BeautifulSoup
from lxml import etree
from mioji.common import spider
spider.pool.set_size(2014)
spider.NEED_FLIP_LIMIT = False


# class CtripGrouptravel:
#     def __init__(self):
#         self.source_type = "Ctirp|vacation"    # OK
#         self.pid = "gty+yyyMMdd+number"
#         self.pid_3rd = ""
#         self.first_image = ""
#         self.sid = ""
#         self.ccy = ""
#         self.feature = ""
#         self.dest = []
#         self.dept_city = []
#         self.extra_traffic = 0
#         self.extra_city = []
#         self.name = ""  # 产品名称 OK
#         self.date = ""  # 出发日期 OK
#         self.set_name = ""  # 套餐名称（线路）OK
#         self.set_id = ""  # 套餐ID OK
#         self.star_level = 1  # 行程星级 OK
#         self.time = 0  # 行程天数（日）OK
#         self.highlight = ""  # 产品亮点
#         self.confirm = 0  # 预定确认方式，默认给0 OK
#         self.sell_date_late = ""  # 最晚可售日期
#         self.book_pre = 0  # 提前预定天数，0表示不限
#         self.tag = ""  # 特色标签ID 给空 OK
#         self.image_list = []  # 轮播图列表 OK
#         self.rec = ""  # 产品经理推荐内容 OK
#         self.stat = 0   # 录入审核状态 OK
#         self.hotel = {"desc": "", "plans": []}  # 参考酒店信息  plans里是这样的{"name": "NULL", "name_en": "NULL", "addr": "NULL", "intro": "NULL", "img": "NULL"}多个字典  OK
#         self.expense = [{"type": 0, "title": "", "content": ""}, {"type": 1, "title": "", "content": ""},
#                         {"type": 2, "title": "", "content": ""}]  # 费用说明  OK
#         self.other = [{"title": "pre_info", "content": ""}, {"title": "visa_info", "content": ""}]  # 其他说明 OK
#         self.disable = 0  # OK
#         self.single_room = float(0.0)  # 单房差  OK
#         self.tourist = []  # 不同人员类型的详细价格和库存，没有可以给空 OK
#         self.tour_stat = 0  # 成团状态，0：未成团， 1：已成团 OK
#         self.ctime = ""  # 爬取时间戳  OK
#         self.route_day = []  # 行程介绍  OK
#         # [{"city": {"id": "NULL", "name": "NULL"}, "desc": "NULL", "detail": [{"type": "0", "stime": "NULL", "dur": 0, "name": "NULL", "desc": "NULL", "image_list": []}]}]
#         self.is_multi_city = "no"
#         self.multi_city = []
#         self.dept = ""
#
#     def items(self):
#         results = []
#         for k, v in self.__dict__.items():
#             results.append((k, str(v).decode("UTF-8")))
#         return results


# class Package_Tour:
#     def __init__(self):
#         self.pid = ""
#         self.ptid = ""
#         self.pid_3rd = ""
#         self.name = ""
#         self.sid = ""
#         self.dest = []
#         self.highlight = ""
#         self.tag = ""
#         self.dept_city = []
#         self.sell_date_late = ""
#         self.confirm = 0
#         self.extra_traffic = 0
#         self.extra_city = []
#         self.first_image = ""
#         self.image_list = ""
#         self.rec = ""
#         self.disable = 0
#         self.is_mulit_city = "no"
#         self.multi_city = []
#
#     def items(self):
#         results = []
#         for k, v in self.__dict__.items():
#             results.append((k, str(v).decode("UTF-8")))
#         return results
#
#
# class Package_Tour_Set:
#     def __init__(self):
#         self.pid = ""
#         self.set_id = ""
#         self.set_name = ""
#         self.book_pre = ""
#         self.ccy = ""
#         self.tourist = []
#         self.traffic = {}
#         self.hotel = {}
#         self.feature = ""
#         self.route_day = []
#         self.expense = []
#         self.other = []
#         self.disable = 0
#
#     def items(self):
#         results = []
#         for k, v in self.__dict__.items():
#             results.append((k, str(v).decode("UTF-8")))
#         return results
#
#
# class Package_Tour_Set_Price:
#     def __init__(self):
#         self.pid = ""
#         self.set_id = ""
#         self.ccy = ""
#         self.date = ""
#         self.single_room = 0.0
#         self.tourist = []
#         self.tour_stat = 0
#         self.disable = 0
#
#     def items(self):
#         results = []
#         for k, v in self.__dict__.items():
#             results.append((k, str(v).decode("UTF-8")))
#         return results
#

class CitripGrouptravelSpider(Spider):
    # 抓取目标 如城市列表、酒店列表 等对象
    source_type = 'Ctrip|vacation'

    # 数据目标 如城市、酒店数据、酒店房型数据等。
    #   一个抓取目标可以对应多个，数据对象。
    #   一个抓取数据对应一个解析方法 parse_xxx 如：parse_hotelList_hotel，parse_hotelList_room
    targets = {
        'vacation': {},
        # 例行需指定数据版本：InsertHotel_room4
    }

    # 对应多个老原爬虫
    old_spider_tag = {
        # 例行sectionname
        'ctrip|vacation_detail': {'required': ['vacation']}
    }

    def __init__(self, task=None):
        Spider.__init__(self, task=task)

    def targets_request(self):
        # u can get task info from self.task
        task = self.task
        self.count = 0
        self.pid = "gty" + datetime.datetime.now().strftime('%Y-%m-%d') + '%s' % int(time.time() * 100)
        base_url = self.task.ticket_info['vacation_info']['url']
        product_id = self.task.ticket_info['vacation_info']['pid_3rd']
        referer = self.task.ticket_info['vacation_info']['url']
        referer_url = self.task.ticket_info['vacation_info']['url']
        self.price_list = []
        tid = 0
        used_times = 0

        @request(retry_count=3, proxy_type=PROXY_REQ, store_page_name="base_request_{}_{}".format(tid, used_times))
        def base_request():
            return {'req': {'url': base_url},
                    'user_handler': [self.get_static_data]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, store_page_name="first_request_{}_{}".format(tid, used_times))
        def first_request():
            first_url = "http://vacations.ctrip.com/bookingnext/CalendarV2/CalendarInfo?ProductID={5}&StartCity={0}" \
                        "&SalesCity={1}&EffectDate={2}&ExpireDate={3}&ClientSource=Online&uid=&TourGroupProductIds=%5B{4}%5D" \
                        "&CurrencyCode=1".format(self.startcityid, self.salescity, self.effectDate, self.expireDate, product_id, product_id)
            return {'req': {'url': first_url,
                            'headers': {'Referer': referer}},
                    'user_handler': [self.get_calendar]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_vacation, store_page_name="second_request_{}_{}".format(tid, used_times))
        def second_request():
            calendar_list = self.calendar_list
            req_list = []
            second_url = "http://vacations.ctrip.com/bookingnext/Product/TourIntroduction?ProductID={}"
            for calendar in calendar_list:
                product_id_list = []
                price_list = []
                stock_list = []
                is_group = []
                req_dict = {}
                req_dict['date'] = calendar['Date']
                now_time = datetime.datetime.now()
                now_time_str = now_time.strftime('%Y-%m-%d')
                d1 = datetime.datetime.strptime(now_time_str, '%Y-%m-%d')
                d2 = datetime.datetime.strptime(calendar['Date'], '%Y-%m-%d')
                days = (d2 - d1).days
                if days <= 30:
                    for product_id in calendar['TourGroupCalenderInfo']:
                        product_id_list.append(product_id['ProductID'])
                        price_list.append(product_id['MinPrice'])
                        stock_list.append(product_id['RemainingInventory'])
                        is_group.append(product_id['IsAnnouncedGroup'])
                    req_dict['product_id_list'] = product_id_list
                    req_dict['price_list'] = price_list
                    req_dict['stock_list'] = stock_list
                    req_dict['is_group'] = is_group
                    for req_info in zip(req_dict['product_id_list'], req_dict['price_list'], req_dict['stock_list'], req_dict['is_group']):
                        req_list.append({'req': {'url': second_url.format(req_info[0]),
                                                 'date': req_dict['date'],
                                                 'isgroup': req_info[3],
                                                 'stock': req_info[2],
                                                 'set_name': self.set_dict.get(str(req_info[0]), "无"),
                                                 'headers': {'Referer': referer_url}},
                                         'user_handler': [self.get_hotel_info]})
                        self.count += 1
            return req_list

        @request(retry_count=3, proxy_type=PROXY_FLLOW, store_page_name="third_request_{}_{}".format(tid, used_times))
        def third_request():
            # product_id = self.task.ticket_info['vacation_info']['id']
            # referer = self.task.ticket_info['vacation_info']['url']
            data = {
                "ChangeSetId": "0",
                "ProductID": product_id,
                "StartCity": self.startcityid,
                "SalesCity": self.salescity,
                "IsCruise": "0",
                "IsCircleLine": "0",
                "DestinationCityID": self.destcityID,
            }
            return {'req': {'url': "http://vacations.ctrip.com/bookingnext/Product/DescriptionInfo",
                            'method': 'post',
                            'data': data,
                            'headers': {'Referer': referer}},
                    'user_handler': [self.process_decsription]
                    }

        @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True, store_page_name="get_price_{}_{}".format(tid, used_times))
        def get_price():
            req_list = []
            calendar_list = self.calendar_list
            for calendar in calendar_list:
                date = calendar['Date']
                now_time = datetime.datetime.now()
                now_time_str = now_time.strftime('%Y-%m-%d')
                d1 = datetime.datetime.strptime(now_time_str, '%Y-%m-%d')
                d2 = datetime.datetime.strptime(calendar['Date'], '%Y-%m-%d')
                days = (d2 - d1).days
                if days <= 30:
                    for calendar2 in calendar['TourGroupCalenderInfo']:
                        proid = calendar2['ProductID']
                        departid = self.task.ticket_info['vacation_info']['dept_id']
                        salesid = self.task.ticket_info['vacation_info']['dept_id']
                        payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; " \
                                  "name=\"query\"\r\n\r\n{\"DepartCityId\":%s,\"SalesCityId\":%s,\"ProductId\":%s,\"Adults\":1,\"Childs\":1,\"DepartDate\":\"%s\"}\r\n" \
                                  "------WebKitFormBoundary7MA4YWxkTrZu0gW--" % (departid, salesid, proid, date)
                        req_list.append({'req': {'url': "http://vacations.ctrip.com/bookingnext/Resource/RecommendSearchWithXResource",
                                                 'method': 'post',
                                                 'data': payload,
                                                 'date': date,
                                                 'headers': {'Referer': referer,
                                                 'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
                                        }},
                                         'user_handler': [self.get_price]
                                        })
            return req_list

        yield base_request
        yield first_request
        yield third_request
        yield get_price
        yield second_request
        # if self.hotel_id_list:
        #     yield hotel_request

    def get_static_data(self, req, data):
        # 可以通过request binding=[]指定解析方法
        html_obj = etree.HTML(data)
        self.source_type = "Ctirp|vacation"
        pd_name = html_obj.xpath("//h1[@itemprop='name']/text()")
        if pd_name:
            self.name = pd_name[0].strip()
        star_list = html_obj.xpath("//h1[@itemprop='name']/i/@class")
        if star_list:
            star_str = star_list[0]
            star = re.search(r"diamond_(.*)", star_str)
            if star:
                self.star = int(star.group(1))
            else:
                self.star = 1
        else:
            self.star = 1
        self.confirm = 0
        self.tag = ""
        self.image_list = []
        image_list = html_obj.xpath("//div[@class='small_photo_wrap']/ul/li/a/img/@data-big-url")
        if image_list:
            for image_src in image_list:
                self.image_list.append(image_src.replace("_C_500_280", ""))
        rec_list = html_obj.xpath("//div[@class='pm_recommend']/ul/li/text()")
        rec2 = html_obj.xpath("//div[@class='pm_recommend']/ul/li/a/text()")
        if rec_list:
            rec_str = ""
            for rec in rec_list:
                # print(len(rec))
                if len(rec) <= 2:
                    rec_str += rec
                else:
                    rec_str += rec + "<br/>"
            if rec2:
                rec_str += rec2[0]
            self.rec = rec_str
        result = re.findall('"effectDate":"(.*?)", "expireDate":"(.*?)"', data)
        self.effectDate = result[0][0]
        self.expireDate = result[0][1]
        self.startcityid = re.findall('StartCityID: (.*?),', data)[0]
        self.salescity = re.findall('SalesCity: (.*?),', data)[0]
        self.destcityID = re.findall('DestinationCityID:(.*?)', data)[0]
        # days = html_obj.xpath("//div[@class='detail']/a")
        # days = html_obj.xpath("//div[@id='simpleJourneyBox_0']/table/tbody/tr")
        # self.days = len(days) - 1
        set_id_list = html_obj.xpath("//dt[@class='basefix']/a/@pid")
        set_name = html_obj.xpath("//dt[@class='basefix']/a/text()")
        set_name_list = []
        if set_id_list and set_name:
            for setname in set_name:
                setname = setname.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                if setname != "":
                    set_name_list.append(setname)
            set_dict = dict(zip(set_id_list, set_name_list))
        else:
            set_dict = {}
        self.set_dict = set_dict

    def get_calendar(self, req, data):
        res = json.loads(data)
        calendar_list = res['calendar']['bigCalendar']['availableDate']
        self.calendar_list = calendar_list
        departurecity_list = res['departureCity']
        if len(departurecity_list) <= 1:
            self.is_multi_city = "no"
        else:
            self.is_multi_city = "yes"
        dept_list = []
        for dept_city in departurecity_list:
            dept_dict = dict()
            dept_dict['city_id'] = dept_city['cityId']
            dept_dict['city_name'] = dept_city['name']
            dept_dict['price'] = dept_city['minPrice']
            dept_list.append(dept_dict)
        self.multi_city = dept_list

    def get_price(self, req, data):
        dict = {}
        # dict[req['req']['date']] = []
        list1 = []
        data = json.loads(data)
        Price_list = data['data']['PriceInfo']['PriceList']
        single_price_list = data['data']['Resource']['OtherItems']
        price_list = []
        single_price = 0.0
        if single_price_list:
            for source in single_price_list:
                if source['ResourceName'] == "单房差" or source['ResourceName'] == "单人房差":
                    price = source['Inventory'][0]['Price']
                    price_list.append(price)
                    single_price = price_list[0]
        if Price_list:
            price_list = Price_list[0]['TotalPrice']
            adult_price = price_list['AdultPrice']
            chlid_price = price_list['ChildPrice']
            list1.append(adult_price)
            list1.append(chlid_price)
            list1.append(single_price)
        dict[req['req']['date']] = list1
        self.price_list.append(dict)
        print(self.price_list)

    def process_decsription(self, req, data):
        expense = []
        feeinfo = json.loads(data)
        for feeinfos in feeinfo['data']['FeeInfos']:
            if feeinfos['TitleName'] == "费用包含":
                feeinfo_dict = {}
                feeinfo_dict['type'] = 0
                feeinfo_dict['title'] = "费用包含"
                content = ""
                for pkg_desc in feeinfos['PkgDescEntitys']:
                    content += pkg_desc['Detail'].replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "").replace("<br>", "").replace("<br/>", "").replace("<a>", "").replace("</a>", "") + "<br/>"
                feeinfo_dict['content'] = content
                self.child_standard = feeinfos['PkgDescEntitys'][-1]['Detail']
                expense.append(feeinfo_dict)
            elif feeinfos['TitleName'] == "自理费用":
                feeinfo_dict2 = {}
                feeinfo_dict2['type'] = 1
                feeinfo_dict2['title'] = "自理费用"
                content2 = ""
                for pkg_desc2 in feeinfos['PkgDescEntitys']:
                    content2 += pkg_desc2['Detail'].replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "").replace("<br>", "").replace("<br/>", "") + "<br/>"
                feeinfo_dict2['content'] = content2
                expense.append(feeinfo_dict2)
        self.expense = expense
        other = []
        feeinfo_dict3 = {}
        content3 = ""
        feeinfo_dict3['title'] = "pre_info"
        for feeinfos in feeinfo['data']['OrderingNeedToKnowInfo']['OrderingNeedToKnowInfoDetails']:
            try:
                for pre_info in feeinfos['Details']:
                    # for pre_str in pre_info['Details']:
                        content3 += pre_info['Detail'].replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "").replace("<br>", "").replace("<br/>", "").replace("<ahref=", "").replace("<a>", "").replace("</a>", "") + "<br/>"
            except Exception:
                content3 = ""
        feeinfo_dict3['content'] = content3
        other.append(feeinfo_dict3)
        feeinfo_dict4 = {}
        feeinfo_dict4['title'] = "visa_info"
        content4 = ""
        try:
            for feeinfos in feeinfo['data']['VisaInfo']['VisaContainDetails']:
                content4 += feeinfos['Detail'].replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "").replace("<br>", "").replace("<br/>", "").replace("<ahref=", "").replace("<a>", "").replace("</a>", "") + "<br/>"
        except Exception:
            content4 = ""
        feeinfo_dict4['content'] = content4
        other.append(feeinfo_dict4)
        self.other = other

    def get_hotel_info(self, req, data):
        referer_url = self.task.ticket_info['vacation_info']['url']
        soup = BeautifulSoup(data, 'lxml')
        soup = soup.prettify()
        html_obj = etree.HTML(soup)
        hotel_node = html_obj.xpath("//div[@class='day_detail']/p/a/@hotelid")
        hotel_id_list = list(set(hotel_node))
        if hotel_id_list is None:
            hotel = {}
            self.hotel = hotel
        else:
            # self.hotel_id_list = hotel_id_list
            url = "http://vacations.ctrip.com/bookingnext/Hotel/HotelDetailInfo"
            headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                        'Referer': referer_url}
            hotel_desc = ""
            plans = []
            for hotel_id in hotel_id_list:
                proxies = dict()
                # proxy_info = requests.get(
                #     "http://10.10.32.22:48200/?type=px001&qid=0&query={%22req%22:%20[{%22source%22:%20%22ctripFlight%22,%20%22num%22:%201,%20%22type%22:%20%22verify%22,%20%22ip_type%22:%20%22test%22}]}&ptid=test&uid=test&tid=tid&ccy=spider_test").content
                # proxy = json.loads(proxy_info)['resp'][0]['ips'][0]['inner_ip']
                # proxies['socks'] = "socks5://" + proxy.encode('utf-8')
                proxy_info = requests.get("http://10.10.239.46:8087/proxy?source=pricelineFlight&user=crawler&passwd=spidermiaoji2014").content
                proxies['socks'] = "socks5://" + proxy_info.encode('utf-8')
                data = {"HotelID": hotel_id,
                        "showComment": 1}
                html = requests.post(url=url, data=data, headers=headers, proxies=proxies).content
                try:
                    html_json = json.loads(html)
                    hotel_desc += html_json['data']['HotelCnName'] + "|"
                    hotel_dict = {}
                    hotel_dict['name'] = html_json['data']['HotelCnName']
                    hotel_dict['name_en'] = html_json['data']['HotelEnName']
                    hotel_dict['addr'] = html_json['data']['Address']
                    hotel_dict['intro'] = html_json['data']['HotelDesc'].replace("<br>", "")
                    hotel_dict['img'] = html_json['data']['HotelUrl']
                    plans.append(hotel_dict)
                except:
                    hotel_desc = ""
            hotel = {}
            hotel['desc'] = hotel_desc
            hotel['plans'] = plans
        self.hotel = hotel

    # def get_hotel(self, req, data):
    #     hotel_desc = ""
    #     plans = []
    #     html_json = json.loads(data)
    #     hotel_desc += html_json['data']['HotelCnName'] + "|"
    #     hotel_dict = {}
    #     hotel_dict['name'] = html_json['data']['HotelCnName']
    #     hotel_dict['name_en'] = html_json['data']['HotelEnName']
    #     hotel_dict['addr'] = html_json['data']['Address']
    #     hotel_dict['intro'] = html_json['data']['HotelDesc'].replace("<br>", "")
    #     hotel_dict['img'] = html_json['data']['HotelUrl']
    #     plans.append(hotel_dict)
    #     hotel = {}
    #     hotel['desc'] = hotel_desc
    #     hotel['plans'] = plans
    #     self.hotel = hotel

    def parse_vacation(self, req, data):
        html_obj = etree.HTML(data)
        soup = BeautifulSoup(data, 'lxml')
        travel = []
        route_day = []
        days_list = html_obj.xpath("//div[@class='day_list']")
        for days in days_list:
            day_dict = {}
            ctiy_node = days.xpath("./div[@class='day_title']/h4/text()")
            city_str = ""
            for city in ctiy_node:
                city = city.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                if city != "":
                    city_str += city + " "
            day_dict['citys'] = [{'id': 'NULL', 'name': city_str}]
            desc_list = days.xpath(".//i[contains(@class, 'icon_ms icon_ms_other')]/../p/text()")
            desc_str = ""
            # if desc_list:
            #     for desc in desc_list:
            #         desc_str += desc
            #     day_dict['desc'] = desc_str
            # else:
            day_dict['desc'] = desc_str
            detail_list = []
            detail_node = days.xpath("./div[@class='day_content']/ul/li")
            # 节点类型 0:其他 10:交通 11:飞机 20:景点 21:用餐 22:玩乐 23:自由活动 30:酒店
            type_dict = {}
            type_dict['icon_ms icon_ms_plane'] = 11
            type_dict['icon_ms icon_ms_other'] = 0
            type_dict['icon_ms icon_ms_traffic'] = 10
            type_dict['icon_ms icon_ms_htl'] = 30
            type_dict['icon_ms icon_ms_food'] = 21
            type_dict['icon_ms icon_ms_scene'] = 20
            type_dict['icon_ms icon_ms_free'] = 23
            for detail_info in detail_node:
                detail_dict = {}
                type_str = detail_info.xpath("./div[@class='day_detail']/i/@class")
                type_str2 = type_dict.get(type_str[0].strip())
                if type_str2 is None:
                    detail_dict['type'] = 0
                else:
                    detail_dict['type'] = type_str2
                s_time_list = detail_info.xpath("./h5[@class='time_list']/text()")
                s_time = ""
                for s_time2 in s_time_list:
                    s_time2 = s_time2.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                    if s_time2 != "":
                        s_time = s_time2
                detail_dict['stime'] = s_time.replace("：", ":")
                dur_list = detail_info.xpath("./div[@class='day_detail']/p[@class='bg_important']/text()")
                # if dur_list:
                #     detail_dict['dur'] = dur_list[0]
                # else:
                #     detail_dict['dur'] = ""
                detail_dict['dur'] = None
                name_list1 = detail_info.xpath(".//h6/a/text()")
                name_list2 = detail_info.xpath(".//h6/text()")
                name_str = ""
                name_str2 = ""
                if name_list1 and name_list2:
                    for name in name_list1:
                        name_str += name + " "
                    for name2 in name_list2:
                        name2 = name2.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                        if name2 != "":
                            name_str2 += name2
                    detail_dict['name'] = name_str + name_str2
                elif name_list1:
                    # detail_dict['name'] = name_list[0]
                    for name in name_list1:
                        name_str += name + " "
                    detail_dict['name'] = name_str
                elif name_list2:
                    for name in name_list2:
                        name = name.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                        if name != "":
                            name_str = name
                    detail_dict['name'] = name_str
                else:
                    detail_dict['name'] = name_str
                li_desc1 = detail_info.xpath("./div[@class='day_detail']/div/p/text()")
                li_desc2 = detail_info.xpath("./div[@class='day_detail']//*/text()")
                li_desc3 = detail_info.xpath("./div[@class='day_detail']/p[2]/text()")
                if li_desc1 and li_desc3:
                    li_str = ""
                    for li in li_desc1:
                        li_str += li + "<br/>"
                    li_str.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                    for li2 in li_desc3:
                        li_str += li2.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "") + "<br/>"
                    detail_dict['desc'] = li_str
                elif li_desc1:
                    li_str = ""
                    for li in li_desc1:
                        li_str += li + "<br/>"
                    li_str.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                    detail_dict['desc'] = li_str
                elif li_desc2:
                    li_str = ""
                    for li in li_desc2:
                        li_str += li
                    li_str.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                    detail_dict['desc'] = li_str
                elif li_desc3:
                    li3_str = ""
                    for li3 in li_desc3:
                        li3_str += li3 + "<br/>"
                    li3_str.replace("\n", "").replace("\t", "").replace("\r", "").replace(" ", "")
                    detail_dict['desc'] = li3_str
                # else:
                #     detail_dict['desc'] = ""
                img_list = detail_info.xpath("./div[@class='day_detail']/div/div/a/img/@_src")
                image_list = []
                # if name_str:
                #     img_list = soup.find_all("img", {"title": name_str})
                #     if img_list:
                #         image_list.append(img_list[0].get("_src"))
                #         detail_dict['image_list'] = image_list
                #     else:
                #         detail_dict['image_list'] = image_list
                # else:
                #     detail_dict['image_list'] = image_list
                if img_list:
                    for img in img_list:
                        img = img.replace("_C_210_118", "")
                        image_list.append(img)
                    detail_dict['image_list'] = image_list
                else:
                    detail_dict['image_list'] = image_list
                detail_list.append(detail_dict)
            day_dict['detail'] = detail_list
            route_day.append(day_dict)
        date = req['req']['date']
        for dict1 in self.price_list:
            print(len(self.price_list))
            ctrip_vacation = CtripGrouptravel()
            ctrip_vacation.sid = ""
            ctrip_vacation.name = self.name
            ctrip_vacation.sell_date_late = self.price_list[-1].keys()[0]
            ctrip_vacation.first_image = self.task.ticket_info['vacation_info']['first_image']
            ctrip_vacation.star_level = self.star
            ctrip_vacation.rec = self.rec
            ctrip_vacation.image_list = self.image_list
            ctrip_vacation.date = req['req']['date'].replace("-", "")
            ctrip_vacation.tag = []
            url = req['req']['url']
            set_id = re.search(r"ProductID=(.*)", url).group(1)
            ctrip_vacation.set_id = set_id
            ctrip_vacation.set_name = req['req']['set_name']
            # ctrip_vacation.price = req['req']['price']
            if req['req']['isgroup'] is True:
                ctrip_vacation.tour_stat = 1
            else:
                ctrip_vacation.tour_stat = 0
            # ctrip_vacation.stock = req['req']['stock']
            tourist1 = {}
            tourist1['name'] = "成人"
            adult_list = dict1.get(date)
            if adult_list is None:
                break
            self.price_list.remove(dict1)
            tourist1['price'] = adult_list[0]
            tourist1['rest'] = int(req['req']['stock'])
            tourist2 = {}
            tourist2['name'] = "儿童"
            tourist2['price'] = dict1.get(date)[1]
            tourist2['rest'] = int(req['req']['stock'])
            ctrip_vacation.tourist.append(tourist1)
            ctrip_vacation.tourist.append(tourist2)
            ctrip_vacation.single_room = dict1.get(date)[2]
            ctrip_vacation.expense = self.expense
            ctrip_vacation.other = self.other
            # ctrip_vacation.time = self.days
            ctrip_vacation.hotel = self.hotel
            ctrip_vacation.route_day = route_day
            ctrip_vacation.time = len(ctrip_vacation.route_day)
            ctrip_vacation.ctime = int(time.time())
            ctrip_vacation.highlight = self.task.ticket_info['vacation_info']['highlight']
            ctrip_vacation.pid_3rd = str(self.task.ticket_info['vacation_info']['pid_3rd'])
            ctrip_vacation.pid = self.pid
            ctrip_vacation.ccy = "CNY"
            ctrip_vacation.dest = [{"id": self.task.ticket_info['vacation_info']['dest_id'],
                                    "name": self.task.ticket_info['vacation_info']['search_dest_city'],
                                    "mode": 1}]
            ctrip_vacation.dept = [{"id": str(self.task.ticket_info['vacation_info']['dept_id']), "name": self.task.ticket_info['vacation_info']['dept_city']}]
            ctrip_vacation.is_multi_city = self.is_multi_city
            ctrip_vacation.multi_city = self.multi_city
            ctrip_vacation.dept_city = [{"id": self.task.ticket_info['vacation_info']['dept_id'], "name": self.task.ticket_info['vacation_info']['dept_city']}]
            ctrip_vacation.ptid = self.task.ticket_info['vacation_info']['supplier']
            ctrip_vacation.child_standard = self.child_standard

        # package_tour = Package_Tour()
        # package_tour.pid = ctrip_vacation.pid
        # package_tour.pid_3rd = ctrip_vacation.pid_3rd
        # package_tour.name = ctrip_vacation.name
        # package_tour.sid = ctrip_vacation.sid
        # package_tour.dest = ctrip_vacation.dest
        # package_tour.highlight = ctrip_vacation.highlight
        # package_tour.tag = ctrip_vacation.tag
        # package_tour.dept_city = ctrip_vacation.dept
        # package_tour.sell_date_late = ctrip_vacation.sell_date_late
        # package_tour.confirm = ctrip_vacation.confirm
        # package_tour.extra_traffic = ctrip_vacation.extra_traffic
        # package_tour.extra_city = ctrip_vacation.extra_city
        # package_tour.first_image = ctrip_vacation.first_image
        # package_tour.image_list = ctrip_vacation.image_list
        # package_tour.rec = ctrip_vacation.rec
        # package_tour.disable = ctrip_vacation.disable
        # package_tour.is_mulit_city = ctrip_vacation.is_multi_city
        # package_tour.multi_city = ctrip_vacation.multi_city
        #
        # package_tour_set = Package_Tour_Set()
        # package_tour_set.pid = ctrip_vacation.pid
        # package_tour_set.set_id = ctrip_vacation.set_id
        # package_tour_set.set_name = ctrip_vacation.set_name
        # package_tour_set.book_pre = ctrip_vacation.book_pre
        # package_tour_set.ccy = ctrip_vacation.ccy
        # package_tour_set.tourist = ctrip_vacation.tourist
        # package_tour_set.hotel = ctrip_vacation.hotel
        # package_tour_set.feature = ctrip_vacation.feature
        # package_tour_set.route_day = ctrip_vacation.route_day
        # package_tour_set.expense = ctrip_vacation.expense
        # package_tour_set.other = ctrip_vacation.other
        # package_tour_set.disable = ctrip_vacation.disable
        #
        # package_tour_set_price = Package_Tour_Set_Price()
        # package_tour_set_price.pid = ctrip_vacation.pid
        # package_tour_set_price.set_id = ctrip_vacation.set_id
        # package_tour_set_price.ccy = ctrip_vacation.ccy
        # package_tour_set_price.date = ctrip_vacation.date
        # package_tour_set_price.single_room = ctrip_vacation.single_room
        # package_tour_set_price.tourist = ctrip_vacation.tourist
        # package_tour_set_price.tour_stat = ctrip_vacation.tour_stat
        # package_tour_set_price.disable = ctrip_vacation.disable

        # p_tuple = (ctrip_vacation.name, ctrip_vacation.rec, ctrip_vacation.image_list, ctrip_vacation.date, ctrip_vacation.tag, ctrip_vacation.set_id,
        #            ctrip_vacation.set_name, ctrip_vacation.tourist, ctrip_vacation.tour_stat, ctrip_vacation.expense, ctrip_vacation.time, ctrip_vacation.hotel,
        #            ctrip_vacation.route_day, ctrip_vacation.ctime, ctrip_vacation.is_multi_city, ctrip_vacation.multi_city)
        # travel.append(package_tour.__dict__)
        # travel.append(package_tour_set.__dict__)
        # travel.append(package_tour_set_price.__dict__)
            travel.append(ctrip_vacation.__dict__)
            print self.count

        return travel


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy, httpset_debug

    spider.slave_get_proxy = simple_get_socks_proxy

    spider = CitripGrouptravelSpider()
    # l1 = []
    # with open("list_data.json", "r") as f:
    #     for i in f:
    #       l1.append(i)
    # for t in l1:
    #     t = json.loads(t)
    #     task = Task()
    #     task.ticket_info['vacation_info'] = {
    #         "id": t['pid_3rd'],
    #         "search_dept_city_id": "1",
    #         "search_dept_city": "北京",
    #         "search_dest_city_id": "438",
    #         "search_dest_city": "巴厘岛",
    #         "dept_city": t['search_dept_city'],
    #         "highlight": t['highlight'],
    #         "first_image": t['first_image'],
    #         "url": t['url'],
    #         "supplier": t['supplier'],
    #         "brand": t['brand']
    #     }
    #     spider.task = task
    #     # print spider.crawl()
    #     spider.crawl()
    #   print json.dumps(spider.result, ensure_ascii=False)
    task = Task()
    task.ticket_info['vacation_info'] = {
        "pid_3rd": "15714215",
        "dept_id": "1",
        "search_dept_city": "北京",
        "dest_id": "",
        "search_dest_city": "巴黎",
        "dept_city": "北京",
        "highlight": [
                "春季旅游节",
                "无购物",
                "无自费",
                "独栋别墅"
            ],
        "first_image": "列表页传入",
        "url": "http://vacations.ctrip.com/grouptravel/p15714215s1.html",
        "supplier": "列表页传入",
        "brand": "列表页出传入"
    }
    spider.task = task
    # print spider.crawl()
    spider.crawl()
    print json.dumps(spider.result, ensure_ascii=False)
    # print spider.result
