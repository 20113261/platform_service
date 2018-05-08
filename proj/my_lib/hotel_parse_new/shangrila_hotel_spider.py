# coding=utf-8
from lxml import etree
from lxml import html as HTML
import re
import json
from mioji.common.spider import Spider, request, PROXY_REQ, PROXY_FLLOW
# from mioji.common.class_common import Hotel_New
# from mioji.common.class_common import Hotel_New
from proj.my_lib.models.HotelModel import HotelNewBase as Hotel_New
from mioji.common import parser_except


class ShangRiLaDetailSpider(Spider):
    source_type = 'shangrilaDetailHotel'

    targets = {
        'hotel': {}
    }
    old_spider_tag = {
        'shangrilaDetailHotel': {'required': ['room', 'hotel']}
    }

    def __init__(self, task=None):
        self.flag = False
        self.item = {}
        self.hotel = Hotel_New()
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

        # print self.info_list,"*"*80

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
            @request(retry_count=3, proxy_type=PROXY_FLLOW, binding=self.parse_hotel, async=False, new_session=True)
            def crawl_more():
                page = []
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
        # print req_url
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
            print description_info
            description_info = re.sub(r'<.*?>', '', description_info)
            print description_info
            self.item['description'] = description_info
            try:
                hotel_phone = tree.xpath("//span[@id='ctl00_ContentPlaceHolder1_ltrPhone']/text()")[0]
                self.item['hotel_phone'] = hotel_phone
            except Exception as e:
                self.item['hotel_phone'] = 'NULL'
            self.item['source_id'] = self.hotel_code

            self.img_url = 'http://www.shangri-la.com/HotelPhotoVideoJson.json?hotel_code={}&lang=cn'.format(
                self.hotel_code)

            # hotel_name_start = tree.xpath('//div[@class="logoOverLayer"]/img/@alt')[0]
            # print resp
            try:
                hotel_name_info = tree.xpath('//meta[@property="og:title"]/@content')[0]
            except:
                raise parser_except.ParserException(22, 'proxy error')
            # title = tree.xpath('//title/text()')
            # print title
            # print hotel_name_info
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
                # print resp
                post_code = tree.xpath(
                    '//div[@class="widget-mid"]//span[@id="ctl00_ContentPlaceHolder1_ltrAddress"]/text()')
                if not post_code:
                    post_code = tree.xpath('//span[@id="ctl00_ContentPlaceHolder1_ltrAddress"]/text()')

                if len(post_code) <= 1:
                    p_codes = post_code[0].split(',')
                    try:
                        p_code = p_codes[-2]
                        n = re.compile(r'(\d+)').findall(p_code)
                        if not n:
                            p_code = ''
                    except:
                        p_code = ''
                    address = post_code[0]
                else:
                    address = post_code[0]
                    p_code = re.compile(r'\d+').findall(post_code[1])[0]
            except:
                post_code = ''
                p_code = ''
                address = ''

            self.item['city'] = self.city

            self.item['postal_code'] = p_code
            self.item['address'] = address
            print req['req']['url']
            # print resp
            try:
                self.img_first = 'http://www.shangri-la.com{}'.format(tree.xpath('//div[@id="background"]/img/@src')[0])
            except:
                self.img_first = ''
            try:
                check_time = tree.xpath('//span[@id="ctl00_ContentPlaceHolder1_ltrChkInOut"]/text()')

                if not check_time:
                    check_time = tree.xpath('//span[@id="ctl00_ContentPlaceHolder1_ltrChkInOut"]/p/text()')

                    if check_time[1] == u'\xa0':
                        check_time1 = tree.xpath('//span[@id="ctl00_ContentPlaceHolder1_ltrChkInOut"]/p/text()')[0]
                        check_time2 = tree.xpath('//span[@id="ctl00_ContentPlaceHolder1_ltrChkInOut"]/p/span/text()')[0]
                        check_time = [check_time1, check_time2]

                try:
                    # print check_time[0]
                    self.item['check_in_time'] = check_time[0].split('：')[1]
                    self.item['check_out_time'] = check_time[1].split('：')[1]
                except:
                    self.item['check_in_time'] = ''
                    self.item['check_out_time'] = ''
            except:
                self.item['check_in_time'] = ''
                self.item['check_out_time'] = ''
            try:
                accepted_card_info = tree.xpath(
                    '//span[contains(@id, "ctl00_ContentPlaceHolder1_ltrPayment")]/p/text()')
                if not accepted_card_info:
                    accepted_card_info = tree.xpath(
                        '//span[contains(@id, "ctl00_ContentPlaceHolder1_ltrPayment")]/text()')
                print accepted_card_info
                accepted_card_info = [a for a in accepted_card_info if '酒店可接受以下信用卡付款' in a]
                try:
                    accepted_card_infos = accepted_card_info[0].replace(':', '：')
                    accepted_cards = accepted_card_infos.split('：')[-1].replace('、', '|').replace('，', '|'). \
                        replace(u'及', "|").replace('。', '')
                except:
                    accepted_cards = accepted_card_info[-1].replace('、', '|').replace('，', '|'). \
                        replace(u'及', "|").replace('。', '')
            except:
                accepted_cards = ''
            self.item['accepted_cards'] = accepted_cards

    def parse_detail(self, req, resp):
        tree = etree.HTML(resp)
        req_url = req['req']['url']
        # print req['req']['url']
        self.item['source'] = 'shangrila'
        self.item['brand_name'] = '香格里拉'

        if 'about' in req_url:
            if 'service' in req_url:
                try:
                    # service_title = tree.xpath('//div[contains(@class, "contentdiv")]/div/strong')
                    service_info = tree.xpath('//div[contains(@class, "contentdiv")]/div/ul')
                except:
                    raise parser_except.ParserException(22, 'error')
                service_list = []
                for infos in service_info:
                    # title = titles.xpath('./text()')[0]
                    # print title
                    # if title:
                    service_lists = infos.xpath('./li/text()')
                    # service = '{}'.format(title, info)
                    service_list.extend(service_lists)
                print service_list
                self.item['service1'] = '|'.join(service_list)

                hotel2 = Hotel_New()

                try:
                    service_all = tree.xpath("//div[@class='control2_1column']/ul/li/text()")
                    # facilities_dict = {'Swimming_Pool': '泳池', 'gym': '健身', 'SPA': 'SPA', 'Bar': '酒吧', 'Coffee_house': '咖啡厅',
                    #                    'Tennis_court': '网球场', 'Golf_Course': '高尔夫球场', 'Sauna': '桑拿', 'Mandara_Spa': '水疗中心',
                    #                    'Recreation': '儿童娱乐场', 'Business_Centre': '商务中心', 'Lounge': '行政酒廊',
                    #                    'Wedding_hall': '婚礼礼堂', 'Restaurant': '餐厅', 'Parking': '停车场',
                    #                    'Airport_bus': '机场', 'Valet_Parking': '代客泊车', 'Call_service': '叫车服务',
                    #                    'Rental_service': '租车服务', 'Room_wifi': '客房无线网络', 'Room_wired': '客房有线网络',
                    #                    'Public_wifi': '公共区域无线上网', 'Public_wired': '公共区域有线网络'}

                    facilities_dict = {'Swimming_Pool': ['游泳池'], 'gym': ['健身房'], 'SPA': ['SPA'], 'Bar': ['酒吧'],
                                       'Coffee_house': ['咖啡厅'],
                                       'Tennis_court': ['网球场'], 'Golf_Course': ['高尔夫球场'], 'Sauna': ['桑拿'],
                                       'Mandara_Spa': ['水疗中心'],
                                       'Recreation': ['儿童娱乐场', '儿童游乐场'], 'Business_Centre': ['商务中心'],
                                       'Lounge': ['行政酒廊'],
                                       'Wedding_hall': ['婚礼礼堂'], 'Restaurant': ['餐厅'],
                                       'Airport_bus': ['机场班车', '班车服务', '班车服务(收费)'], 'Valet_Parking': ['代客泊车'],
                                       'Call_service': ['叫车服务'], 'Rental_service': ['租车服务'],
                                       'Room_wifi': ['客房无线网络'], 'Room_wired': ['客房有线网络'],
                                       'Public_wifi': ['公共区域无线上网'], 'Public_wired': ['公共区域有线网络']
                                       }
                    # reverse_facility_dict = {v: k for k, v in facilities_dict.items()}
                    service_dict = {'Luggage_Deposit': '行李寄存', 'front_desk': '24小时前台', 'Lobby_Manager': '24小时大堂经理',
                                    '24Check_in': '24小时办理入住', 'Security': '24小时安保', 'Protocol': '礼宾服务',
                                    'wake': '叫醒服务', 'Chinese_front': '中文前台', 'Postal_Service': '邮政服务',
                                    'Fax_copy': '传真/复印', 'Laundry': '洗衣', 'polish_shoes': '擦鞋服务', 'Frontdesk_safe': '保险',
                                    'fast_checkin': '快捷入住及退房服务', 'ATM': '自动柜员机(ATM)/银行服务', 'child_care': '儿',
                                    'Food_delivery': '送餐服务'}
                    reverse_sevice_dict = {v: k for k, v in service_dict.items()}
                    for service in service_all:
                        for keys,fac_value in facilities_dict.items():
                            if fac_value in service:
                                service = self.clean_data(service)
                                if keys in hotel2.facility_content:
                                    hotel2.facility_content[keys] = hotel2.facility_content[keys] + ',' + service
                                else:
                                    hotel2.facility_content[keys] = service
                        for sev_value in service_dict.values():
                            if sev_value in service:
                                service = self.clean_data(service)
                                hotel2.service_content[reverse_sevice_dict[sev_value]] = service
                    self.item['service'] = hotel2.service_content
                    self.item['facility'] = hotel2.facility_content


                except Exception as e:
                    self.item['service'] = "NULL"
                    self.item['facility'] = "NULL"

            elif 'map' in req_url:
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
                traffic_info_1 = ''.join(tree.xpath('//div[@class="control2_1column"]/p/span/text()|//div[@class="control2_1column"]/p/text()'))

                traffic_info_2 = ''.join(tree.xpath('//div[@class="control2_1column"]/div[@id="ctl00_ContentPlaceHolder1_pnlAirportConnection"]/p/span/text()'
                                                    '|//div[@class="control2_1column"]/div[@id="ctl00_ContentPlaceHolder1_pnlAirportConnection"]/p/text()'))

                for tra_str in map_list:
                    # if tra_str == "公共交通":
                    traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()"
                                               "|//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/span/text()|"
                                               "//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/u/text()|"
                                               "//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/span/u/text()".format(index, index,index, index))
                    try:
                        ol_trafiic = ''.join(tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/ol/li/text()|"
                                            "//div[@class='control2_1column']/div[@class='map-list'][{}]/div/ol/li/span/text()".format(index, index)))
                    except:
                        ol_trafiic = ''
                    traffic_str = " ".join(traffic_str_l).strip().replace(" ", "").replace('\r', '').replace('\n', '')
                    traffic_str_all += tra_str + ":" + traffic_str + ol_trafiic
                    # if tra_str == "机场交通":
                    #     traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                    #     traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                    #     traffic_str_all += tra_str + ":" + traffic_str
                    # if tra_str == "地铁":
                    #     traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                    #     traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                    #     traffic_str_all += tra_str + ":" + traffic_str
                    # if tra_str == "出租车":
                    #     traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                    #     traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                    #     traffic_str_all += tra_str + ":" + traffic_str
                    # if tra_str == "高速磁悬浮列车":
                    #     traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                    #     traffic_str = " ".join(traffic_str_l).strip().replace(" ", "")
                    #     traffic_str_all += tra_str + ":" + traffic_str
                    # if tra_str == "酒店豪华桥车":
                    #     traffic_str_l = tree.xpath("//div[@class='control2_1column']/div[@class='map-list'][{}]/div/p/text()".format(index))
                    #     traffic_str = " ".join(traffic_str_l).strip().replace(" ", "").replace('\r', '').replace('\n', '')
                    #     traffic_str_all += tra_str + ":" + traffic_str

                    index += 1
                self.item['traffic'] = traffic_info_1 + traffic_info_2 + traffic_str_all
                print self.item['traffic']
                return

        elif 'reviews' in req_url:
            self.flag = True

            try:
                link = tree.xpath('//iframe[contains(@id, "ChildFrame")]/@src')[0]
            except:
                raise parser_except.ParserException(22, 'proxy error')

            self.review_url = link
            if 'http' not in link:
                self.review_url = 'http:' + link

            self.review_url = self.review_url.strip()

    def parse_hotel(self, req, resp):


        req_url = req['req']['url']

        if 'meta_review' in req_url or 'seal' in req_url or 'partnerId' in req_url:
            node = etree.HTML(resp)



            grade = ''
            try:
                grade = node.xpath('//div[@class="summary"]/p/span[2]/text()|//div[@class="value"]/text()')[0]
                grade = grade.replace('\n', '').strip()
            except:
                grade = ''
                self.hotel.grade = grade
            try:
                try:
                    self.review_num = \
                    re.compile(r'\d*,*\d+').findall(node.xpath('//h1/text()|//div[@class="counter"]/text()')[0])[0]
                except:
                    self.review_num = \
                    re.compile(r'\d*,*\d+').findall((node.xpath('//div[@class="numReviews"]/text()'))[0])[0]
            except:
                self.review_num = ''
            try:
                self.hotel.review_num = self.review_num
            except:
                self.hotel.review_num = ''

        elif 'HotelPhotoVideoJson' in req_url or 'getphotosvideos' in req_url:

            self.hotel.hotel_name = self.hotel_name
            self.hotel.hotel_name_en = self.item['hotel_name_en']
            self.hotel.source = self.item['source']
            self.hotel.source_id = self.item['source_id']
            self.hotel.brand_name = self.item['brand_name']
            try:
                self.hotel.map_info = '{},{}'.format(self.item['longitude'], self.item['latitude'])
            except:
                self.hotel.map_info = ''
            self.hotel.address = self.item['address']
            self.hotel.city = self.item['city']
            self.hotel.country = self.country
            self.hotel.postal_code = self.item['postal_code']
            self.hotel.star = self.item['star']
            self.hotel.facility = self.item['facility']
            self.hotel.service = self.item['service1']
            self.hotel.description = self.item['description']
            self.hotel.accepted_cards = self.item['accepted_cards']
            self.hotel.check_in_time = self.item['check_in_time']
            self.hotel.check_out_time = self.item['check_out_time']
            self.hotel.hotel_url = self.url_index
            self.hotel.hotel_phone = self.item['hotel_phone']
            self.hotel.traffic = self.item['traffic']
            self.hotel.others_info = json.dumps({'hotel_services_info': self.item['service1']})
            print self.item['service1'], '--------------'
            if 'getphotosvideos' in req_url:
                self.img_list = '|'.join(
                    ["https://www.hoteljen.com{}".format(img['image']) for img in resp if img['image']])
            else:
                self.img_list = '|'.join(
                    ["http://www.shangri-la.com{}".format(img['image']) for img in resp if img['image']])

            self.hotel.img_items = self.img_list
            img_l = self.img_list.split("|")
            print self.img_first
            if not self.img_first:
                self.hotel.Img_first = img_l[0]
            else:
                self.hotel.Img_first = self.img_first

            res = self.hotel.to_dict()
            return [res.__dict__]


if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common import spider
    from mioji.common.utils import simple_get_socks_proxy_new
    # spider.slave_get_proxy = simple_get_socks_proxy_new
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active

    task = Task()
    spider = ShangRiLaDetailSpider()
    spider.task = task

    # task.content = 'http://www.shangri-la.com/cn/jinan/shangrila/&济南香格里拉大酒店&SLJI&中国大陆&'

    content = [
        # 'http://www.shangri-la.com/cn/manila/edsashangrila/&\xe9\xa9\xac\xe5\xb0\xbc\xe6\x8b\x89\xe8\x89\xbe\xe8\x8e\x8e\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&ESL&\xe8\x8f\xb2\xe5\xbe\x8b\xe5\xae\xbe&',
        # 'http://www.shangri-la.com/cn/cebu/mactanresort/&\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe9\xba\xa6\xe4\xb8\xb9\xe5\xb2\x9b\xe5\xba\xa6\xe5\x81\x87\xe9\x85\x92\xe5\xba\x97&MAC&\xe8\x8f\xb2\xe5\xbe\x8b\xe5\xae\xbe&',
        # 'http://www.shangri-la.com/cn/colombo/shangrila/&\xe7\xa7\x91\xe4\xbc\xa6\xe5\x9d\xa1\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLCB&\xe6\x96\xaf\xe9\x87\x8c\xe5\x85\xb0\xe5\x8d\xa1&',
        # 'http://www.shangri-la.com/cn/dubai/shangrila/&\xe8\xbf\xaa\xe6\x8b\x9c\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLDB&\xe9\x98\xbf\xe6\x8b\x89\xe4\xbc\xaf\xe8\x81\x94\xe5\x90\x88\xe9\x85\x8b\xe9\x95\xbf\xe5\x9b\xbd&',
        # 'http://www.shangri-la.com/cn/hambantota/shangrila&\xe6\x96\xaf\xe9\x87\x8c\xe5\x85\xb0\xe5\x8d\xa1\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe6\xb1\x89\xe7\x8f\xad\xe6\x89\x98\xe5\xa1\x94\xe9\xab\x98\xe5\xb0\x94\xe5\xa4\xab\xe5\xba\xa6\xe5\x81\x87\xe9\x85\x92\xe5\xba\x97&SLHT&\xe6\x96\xaf\xe9\x87\x8c\xe5\x85\xb0\xe5\x8d\xa1&',
        # 'http://www.shangri-la.com/cn/paris/shangrila/&\xe5\xb7\xb4\xe9\xbb\x8e\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLPR&\xe6\xb3\x95\xe5\x9b\xbd&',
        'http://www.shangri-la.com/cn/tokyo/shangrila/&\xe4\xb8\x9c\xe4\xba\xac\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLTY&\xe6\x97\xa5\xe6\x9c\xac&',
        # 'http://www.shangri-la.com/cn/kualalumpur/shangrila/&\xe5\x90\x89\xe9\x9a\x86\xe5\x9d\xa1\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLKL&\xe9\xa9\xac\xe6\x9d\xa5\xe8\xa5\xbf\xe4\xba\x9a&',
        # 'http://www.shangri-la.com/cn/cairns/shangrila/&\xe5\x87\xaf\xe6\x81\xa9\xe6\x96\xaf\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLMC&\xe6\xbe\xb3\xe5\xa4\xa7\xe5\x88\xa9\xe4\xba\x9a&',
        # 'http://www.shangri-la.com/cn/singapore/shangrila/&\xe6\x96\xb0\xe5\x8a\xa0\xe5\x9d\xa1\xe9\xa6\x99\xe6\xa0\xbc\xe9\x87\x8c\xe6\x8b\x89\xe5\xa4\xa7\xe9\x85\x92\xe5\xba\x97&SLS&\xe6\x96\xb0\xe5\x8a\xa0\xe5\x9d\xa1&'
        ]
    import csv
    for c in content:
        print c
        task.content = c
        spider.crawl()
        print spider.code
        print spider.result


        # # 文件头，一般就是数据名
        # # fileHeader = ["name", "score"]
        # # 假设我们要写入的是以下两行数据
        # fileHeader = spider.result['hotel'][0]
        # s = [s for s in fileHeader.keys()]
        # l = [f for f in fileHeader.values()]
        # # 写入数据
        # csvFile = open("/Users/mioji/Desktop/shangrila2.csv", "w")
        #
        # writer = csv.writer(csvFile)
        # # 写入的内容都是以列表的形式传入函数
        # print l
        # l[16] = json.loads(l[16])['hotel_services_info']
        # writer.writerow(s)
        # writer.writerow(l)
        #
        # csvFile.close()
