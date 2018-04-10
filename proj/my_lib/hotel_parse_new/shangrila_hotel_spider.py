# coding=utf-8
from lxml import etree
from lxml import html as HTML
import re
import json
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
from mioji.common.class_common import Hotel, Hotel_New
from mioji.common import parser_except
from proj.my_lib.models.HotelModel import HotelNewBase


class ShangRiLaDetailSpider(Spider):
    source_type = 'shangrilaDetailHotel'

    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'shangrilaDetailHotel': {'required': ['room']}
    }

    def __init__(self, task=None):
        self.flag = False
        self.item = {}
        self.info_list = []
        super(ShangRiLaDetailSpider, self).__init__(task)

    def targets_request(self):
        self.url_index, self.hotel_name, self.hotel_code, self.country = self.task.content.split('&')[:-1]

        if not self.url_index.endswith('/'):
            self.url_index = '{}/'.format(self.url_index)
        if 'pre-opening' in self.url_index:
            self.url_index = self.url_index.replace('pre-opening/', '')

        # print self.url_index
        url_json = '{}NavigationMainMenuJson.json'.format(self.url_index)
        url_jsons = '{}about/NavigationJson.json'.format(self.url_index)
        self.city = self.url_index.split('/')[-3]
        self.index_url = '{}about'.format(self.url_index)

        @request(retry_count=3, proxy_type=PROXY_REQ, async=True)
        def crawl_index():
            p = []
            p.append({
                'req': {
                    'url': url_json, 'method': 'get', 'headers': {
                            'Host': 'www.shangri-la.com', 'Referer': self.url_index, 'Pragma': 'no-cache'}
                        },
                'user_handler': [self.parse_index], 'data': {'content_type': 'json'}
            })
            p.append({
                'req': {
                    'url': url_jsons, 'method': 'get', 'headers': {
                        'Host': 'www.shangri-la.com',  'Pragma': 'no-cache',
                    }
                },
                'user_handler': [self.parse_index], 'data': {'content_type': 'json'}
            })
            p.append({
                'req': {
                    'url': self.index_url, 'method': 'get', 'headers': {
                        'Host': 'www.shangri-la.com', 'Pragma': 'no-cache',
                        'Referer': 'http://www.shangri-la.com/cn/find-a-hotel/'
                    }
                },
                'user_handler': [self.parse_index]
            })
            return p
        yield crawl_index

        print self.info_list,"*"*80

        @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True)
        def crawl_details():
            pages = []
            for each_info_url in self.info_list:
                pages.append({
                    'req': {
                        'url': each_info_url, 'method': 'get', 'headers': {
                            'Host': 'www.shangri-la.com', 'Referer': self.url_index, 'Pragma': 'no-cache',
                            'Accept-Language': 'en;q=0.8',
                        }
                    },
                    'user_handler': [self.parse_detail]
                })
            return pages
        yield crawl_details
        # try:
        #     if self.img_url and self.review_url:
        if self.flag:
            @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel, async=True, new_session=True)
            def crawl_more():
                page = []
                page.append({
                            'req': {
                                'url': self.img_url, 'method': 'get', 'headers': {
                                    'referer': 'https://www.hoteljen.com/brisbane/romastreet/photos-videos/',
                                }
                            },
                            'data': {'content_type': 'json'}
                        })
                page.append({
                    'req': {
                        'url': self.review_url, 'method': 'get',
                        #  'headers': {
                        #     # 'Host': 'www.tripadvisor.cn', 'Pragma': 'no-cache', 'Referer': self.review_url,
                        #     # 'Cookie': 'SERVERID=srv-trustyou-web2_80'
                        #     # 'Cookie': self.cookie
                        # }
                    },
                })

                return page
            yield crawl_more
        else:
            @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel)
            def crawl_more():
                page = []
                page.append({
                    'req': {
                        'url': self.img_url, 'method': 'get', 'headers': {
                            'referer': 'https://www.hoteljen.com/brisbane/romastreet/photos-videos/',
                        }
                    },
                    'data': {'content_type': 'json'}
                })
                return page
            yield crawl_more
            # else:
            #     raise parser_except.ParserException(22, '代理失效')
        # except:
        #     raise parser_except.ParserException()

    def clean_data(self, str):
        str_l = str.replace(" ", "").replace("\r", "").replace("\n", "")
        return str_l

    def parse_index(self, req, resp):
        req_url = req['req']['url']
        print req_url
        # print req_url

        if 'NavigationMainMenuJson' in req_url:
            # print resp
            node_list = resp['MainMenu']
            self.info_list.extend(['http://www.shangri-la.com{}'.format(node['Url']) for node in node_list
                                   if 'about' in node['Url'] or 'reviews' in node['Url']])

        elif 'NavigationJson' in req_url:
            # print resp
            try:
                node_list = resp['NaviMenu']
                self.info_list.extend(
                    ['http://www.shangri-la.com{}'.format(node['Url']) for node in node_list if 'map' in node['Url']
                     or 'service' in node['Url']]
                )
            except KeyError:
                raise parser_except.ParserException(22, '请求失效，失效url为：{}'.format(req_url))
        else:
            tree = etree.HTML(resp)
            description = re.compile(r'<p>(.*?)</p>').findall(resp)
            description_info = ''
            for des in description:
                if u'本酒店可接受以下信用卡付款'  in des or u'退房时用信用卡结账需' in des:
                    pass
                else:
                    description_info += des
            # print description_info

            self.item['description'] = description_info
            try:
                hotel_phone = tree.xpath("//span[@id='ctl00_ContentPlaceHolder1_ltrPhone']/text()")[0]
                self.item['hotel_phone'] = hotel_phone
            except Exception as e:
                self.item['hotel_phone'] = 'NULL'

    def parse_detail(self, req, resp):
        tree = etree.HTML(resp)
        req_url = req['req']['url']
        print req['req']['url']
        self.item['source'] = 'shangrila'
        self.item['brand_name'] = '香格里拉'

        if 'about' in req_url:
            if 'service' in req_url:
                # try:
                #     service_title = tree.xpath('//div[contains(@class, "contentdiv")]/div/strong')
                #     service_info = tree.xpath('//div[contains(@class, "contentdiv")]/div/ul')
                # except:
                #     raise parser_except.ParserException(22, 'error')
                # service_list = []
                # for titles, infos in zip(service_title, service_info):
                #     title = titles.xpath('./text()')[0]
                #     print title
                #     if title:
                #         info = ','.join(infos.xpath('./li/text()'))
                #         service = '{}::{}'.format(title, info)
                #         service_list.append(service)
                # self.item['service'] = '|'.join(service_list)
                # self.item['has_wifi'] = ''
                # self.item['is_wifi_free'] = ''
                # if "免费上网" in self.item['service']:
                #     self.item['has_wifi'] = 'Yes'
                #     self.item['is_wifi_free'] = 'Yes'
                # self.item['has_parking'] = ''
                # self.item['is_parking_free'] = ''
                # if '停车场' in self.item['service']:
                #     self.item['has_parking'] = 'Yes'
                # return
                hotel2 = Hotel_New()

                try:
                    service_all = tree.xpath("//div[@class='control2_1column']/ul/li/text()")
                    facilities_dict = {'Swimming_Pool': '泳池', 'gym': '健身', 'SPA': 'SPA', 'Bar': '酒吧', 'Coffee_house': '咖啡厅',
                                       'Tennis_court': '网球场', 'Golf_Course': '高尔夫球场', 'Sauna': '桑拿', 'Mandara_Spa': '水疗中心',
                                       'Recreation': '儿童娱乐场', 'Business_Centre': '商务中心', 'Lounge': '行政酒廊',
                                       'Wedding_hall': '婚礼礼堂', 'Restaurant': '餐厅', 'Parking': '停车场',
                                       'Airport_bus': '机场', 'Valet_Parking': '代客泊车', 'Call_service': '叫车服务',
                                       'Rental_service': '租车服务', 'Room_wifi': '客房无线网络', 'Room_wired': '客房有线网络',
                                       'Public_wifi': '公共区域无线上网', 'Public_wired': '公共区域有线网络'}
                    reverse_facility_dict = {v: k for k, v in facilities_dict.items()}
                    service_dict = {'Luggage_Deposit': '行李寄存', 'front_desk': '24小时前台', 'Lobby_Manager': '24小时大堂经理',
                                    '24Check_in': '24小时办理入住', 'Security': '24小时安保', 'Protocol': '礼宾服务',
                                    'wake': '叫醒服务', 'Chinese_front': '中文前台', 'Postal_Service': '邮政服务',
                                    'Fax_copy': '传真/复印', 'Laundry': '洗衣', 'polish_shoes': '擦鞋服务', 'Frontdesk_safe': '保险',
                                    'fast_checkin': '快速办理登记入住及退房', 'ATM': '自动柜员机(ATM)/银行服务', 'child_care': '儿',
                                    'Food_delivery': '送餐服务'}
                    reverse_sevice_dict = {v: k for k, v in service_dict.items()}
                    for service in service_all:
                        for fac_value in facilities_dict.values():
                            if fac_value in service:
                                service = self.clean_data(service)
                                hotel2.facility[reverse_facility_dict[fac_value]] = service
                        for sev_value in service_dict.values():
                            if sev_value in service:
                                service = self.clean_data(service)
                                hotel2.service[reverse_sevice_dict[sev_value]] = service
                    self.item['service'] = hotel2.service
                    self.item['facility'] = hotel2.facility
                except Exception as e:
                    self.item['service'] = "NULL"
                    self.item['facility'] = "NULL"

            elif 'map' in req_url:
                print req['req']['url']
                try:
                    latitude = re.compile(r'"Lat":"(.*?)"', re.S).findall(resp)[0]
                    longitude = re.compile(r'"Lng":"(.*?)"', re.S).findall(resp)[0]
                except:
                    raise parser_except.ParserException(22, '代理失效')
                self.item['latitude'] = latitude
                self.item['longitude'] = longitude
                map_list = tree.xpath("//div[@class='control2_1column']/div[@class='map-list']/div/h4/text()")
                self.item['traffic'] = "NULL"
                traffic_str_all = ""
                index = 1
                for tra_str in map_list:
                    if tra_str == "公共交通":
                        traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                        traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                        traffic_str_all += tra_str + ":" + traffic_str
                    elif tra_str == "机场交通":
                        traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                        traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                        traffic_str_all += tra_str + ":" + traffic_str
                    elif tra_str == "地铁":
                        traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                        traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                        traffic_str_all += tra_str + ":" + traffic_str
                    elif tra_str == "出租车":
                        traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                        traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                        traffic_str_all += tra_str + ":" + traffic_str
                    elif tra_str == "高速磁悬浮列车":
                        traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                        traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                        traffic_str_all += tra_str + ":" + traffic_str
                    self.item['traffic'] = traffic_str_all
                    index += 1
                return
            elif 'about' in req['req']['url']:

                self.item['source_id'] = self.hotel_code

                self.img_url = 'http://www.shangri-la.com/HotelPhotoVideoJson.json?hotel_code={}&lang=cn'.format(self.hotel_code)

                # hotel_name_start = tree.xpath('//div[@class="logoOverLayer"]/img/@alt')[0]
                # print resp
                try:
                    hotel_name_info = tree.xpath('//meta[@property="og:title"]/@content')[0]
                except:
                    raise parser_except.ParserException(22, 'proxy error')
                # title = tree.xpath('//title/text()')
                # print title
                print hotel_name_info
                if '五星级' in hotel_name_info:
                    self.item['star'] = 5
                elif '四星级' in hotel_name_info:
                    self.item['star'] = 4
                elif '三星级' in hotel_name_info:
                    self.item['star'] = 3
                else:
                    self.item['star'] = ''
                # hotel_name = hotel_name_info.split('|')[-1]
                # self.item['hotel_name'] = hotel_name
                self.item['hotel_name_en'] = self.hotel_name
                try:
                    post_code = tree.xpath('//div[@class="widget-mid"]//span[@id="ctl00_ContentPlaceHolder1_ltrAddress"]/text()')
                    if len(post_code) <= 1:
                        p_codes = post_code.split(',')
                        p_code = p_codes[-2]
                        address = post_code[0]
                        # country = p_codes[-1]
                    else:
                        address = post_code[0]
                        p_code = re.compile(r'\d+').findall(post_code[1])[0]
                        print p_code
                except:
                    post_code = ''
                    p_code = ''
                    address = ''
                    # country = ''
                # self.item['country'] = country
                self.item['city'] = self.city

                self.item['postal_code'] = p_code
                self.item['address'] = address
                check_time = tree.xpath('//span[contains(@id, "ctl00_ContentPlaceHolder1_ltrChkInOut")]/text()')
                # check_time = tree.xpath('//div[contains(@class, "widgets_box")]/p[1]/span/p/text()')
                # check_in = re.findall(r'Check-in: (\w+)', check_time[0], re.S)[0]
                # check_out = re.findall(r'Check-out: (\w+)', check_time[1], re.S)[0]
                # print check_time[0], check_time[1]
                try:
                    self.item['check_in_time'] = check_time[0].split('：')[1]
                    self.item['check_out_time'] = check_time[1].split('：')[1]
                except:
                    self.item['check_in_time'] = ''
                    self.item['check_out_time'] = ''
                    # raise parser_except.ParserException(22, '失败的url为：{}'.format(req_url))
                try:
                    accepted_card_info = tree.xpath('//span[contains(@id, "ctl00_ContentPlaceHolder1_ltrPayment")]/text()')
                    # print accepted_card_info
                    accepted_cards = accepted_card_info[0].split('：')[-1].replace('、', '|').replace(u'及', "|")
                # print accepted_cards
                except:
                    accepted_cards = ''
                self.item['accepted_cards'] = accepted_cards

        elif 'reviews' in req_url:
            self.flag = True
            # print resp
            # self.cookie = self.browser.br.cookies.items()[0][1]
            try:
                link = tree.xpath('//iframe[contains(@id, "ChildFrame")]/@src')[0]
            except:
                raise parser_except.ParserException(22, 'proxy error')

            self.review_url = link
            if 'http' not in link:
                self.review_url = 'http:' + link

            self.review_url = self.review_url.strip()
            # print '3333'

    def parse_hotel(self, req, resp):
        result = []
        hotel = Hotel_New()
        hotel.hotel_name = self.hotel_name
        hotel.hotel_name_en = self.item['hotel_name_en']
        hotel.source = self.item['source']
        hotel.source_id = self.item['source_id']
        hotel.brand_name = self.item['brand_name']
        try:
            hotel.map_info = '{},{}'.format(self.item['longitude'], self.item['latitude'])
        except:
            hotel.map_info = ''
        hotel.address = self.item['address']
        hotel.city = self.item['city']
        hotel.country = self.country
        hotel.postal_code = self.item['postal_code']
        hotel.star = self.item['star']
        hotel.facility = self.item['facility']
        hotel.service = self.item['service']
        hotel.description = self.item['description']
        hotel.accepted_cards = self.item['accepted_cards']
        hotel.check_in_time = self.item['check_in_time']
        hotel.check_out_time = self.item['check_out_time']
        hotel.hotel_url = self.url_index
        hotel.hotel_phone = self.item['hotel_phone']
        hotel.traffic = self.item['traffic']
        req_url = req['req']['url']
        # print req_url

        if 'meta_review' in req_url or 'seal' in req_url or 'partnerId' in req_url:
            # print resp
            # 评论
            node = etree.HTML(resp)
            grade = ''
            try:
                # print resp
                grade = node.xpath('//div[@class="summary"]/p/span[2]/text()|//div[@class="value"]/text()')[0]
                grade = grade.replace('\n', '').strip()
            except:
                grade = ''
            hotel.grade = grade
            try:
                self.review_num = re.compile(r'\d*,*\d+').findall(node.xpath('//h1/text()|//div[@class="counter"]/text()')[0])[0]
            except:
                self.review_num = ''

        elif 'HotelPhotoVideoJson' in req_url or 'getphotosvideos' in req_url:
            if 'getphotosvideos' in req_url:
                self.img_list = '|'.join(["https://www.hoteljen.com{}".format(img['image']) for img in resp if img['image']])
            else:
                self.img_list = '|'.join(["http://www.shangri-la.com{}".format(img['image']) for img in resp if img['image']])


            # review_num = re.compile(r'\d*,*\d+').findall('你好350对不对')[0]
            try:
                hotel.review_num = self.review_num
            except:
                hotel.review_num = ''
            hotel.img_items = self.img_list
            img_l = self.img_list.split("|")
            hotel.Img_first = img_l[0]
            res = hotel.to_dict()
            # res = hotel
            # result.append(res)
            res = json.loads(res)
            print json.dumps(res, ensure_ascii=False)
            # with open('shangrila.json', 'a') as f:
            #     f.write(json.dumps(res, ensure_ascii=False) + '\n')
            return res


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy
    spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    spider = ShangRiLaDetailSpider()
    spider.task = task


    # task.content = 'http://www.shangri-la.com/cn/sydney/shangrila/&\xe6\x82\x89\xe5\xb0\xbc\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\&SLSN&\xe6\xbe\xb3\xe5\xa4\xa7\xe5\x88\xa9\xe4\xba\x9a&'
    # task.content = 'http://www.shangri-la.com/ulaanbaatar/shangrila/pre-opening/&乌兰巴托香格里拉大酒店&SLUB&蒙古&'
    # task.content = 'http://www.shangri-la.com/cn/tangshan/shangrila/pre-opening/&唐山香格里拉大酒店&SLTS&中国大陆&'
    # task.content = 'http://www.shangri-la.com/cn/lhasa/shangrila/&拉萨香格里拉大酒店&SLLS&中国大陆&'  # 0
    # task.content = 'http://www.shangri-la.com/cn/beijing/kerry/&北京嘉里大酒店&HBKC&中国大陆&'  # 0

    list1 = [
"http://www.shangri-la.com/cn/beijing/kerry/&北京嘉里大酒店&HBKC&中国大陆&",
"http://www.shangri-la.com/cn/hongkong/kerry/&香港嘉里酒店&KHHK&香港特别行政区，中国&",
"http://www.shangri-la.com/cn/shanghai/kerryhotelpudong/&上海浦东嘉里大酒店&KHPU&中国大陆&",
"http://www.shangri-la.com/cn/colombo/shangrila/&科伦坡香格里拉大酒店&SLCB&斯里兰卡&", ###
"http://www.shangri-la.com/cn/jinan/shangrila/&济南香格里拉大酒店&SLJI&中国大陆&",##
"http://www.shangri-la.com/cn/lhasa/shangrila/&拉萨香格里拉大酒店&SLLS&中国大陆&", ##
"http://www.shangri-la.com/cn/muscat/barraljissahresort/&香格里拉Barr Al Jissah度假酒店&SLMU&阿曼苏丹&", #
"http://www.shangri-la.com/cn/singapore/shangrilaapartment/&新加坡香格里拉公寓&SLSA&新加坡&", # 7
"http://www.shangri-la.com/cn/tangshan/shangrila/pre-opening/&唐山香格里拉大酒店&SLTS&中国大陆&",
"http://www.shangri-la.com/ulaanbaatar/shangrila/pre-opening/&乌兰巴托香格里拉大酒店&SLUB&蒙古&",
"http://www.shangri-la.com/cn/xiamen/shangrila/&厦门香格里拉大酒店&SLXM&中国大陆&", #
]

    task.content = list1[6]
    spider.crawl()

    print spider.result
    # for t in t_c:
    #     task.content = '{}&{}&{}&{}&'.format(t[-1], t[0], t[3], t[8])
    #     print task.content
    #     if "shangri" in t[-1]:
    #         spider.crawl()
    #         print spider.result
    #         # print "爬虫返回的状态码:{}".format(spider.code)
    #         if spider.code != 0:
    #             with open('log.txt', 'a+') as f:
    #                 f.write(str(spider.code)+task.content)
    #                 f.write('\n')

            # break
