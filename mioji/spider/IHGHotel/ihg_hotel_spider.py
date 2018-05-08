#coding:utf-8
import re
import json
import datetime
from mioji.common import parser_except
from mioji.common.spider import Spider, request, PROXY_FLLOW, PROXY_REQ
from mioji.common.class_common import Room
from lxml import etree
default_dict = {'01':'00','02':'01','03':'02','04':'03','05':'04','06':'05','07':'06','08':'07','09':'08','10':'09','11':'10','12':'11'}

class IhgHotelSpider(Spider):
    source_type = 'ihgHotel'
    targets = {'room': {'version': 'InsertHotel_room3'}}
    old_spider_tag = {'ihgHotel': {'required': ['room']}}

    def __init__(self, task=None):
        super(IhgHotelSpider, self).__init__(task)
        self.rooms = []
        self.rooms_count = 1
        self.adult = 2
        self.hotel_id = ''
        self.check_in = ''
        self.check_out = ''
        self.dept_day = ''
        self.dept_my = ''
        self.dest_day = ''
        self.dest_my = ''

    def targets_request(self):
        room_info = self.task.ticket_info.get('room_info', [])
        self.rooms_count = room_info[0].get('num', 1)
        self.adult = int(room_info[0].get('occ', 1)) * int(self.rooms_count)
        content = self.task.content.split('&')
        if len(content) != 3:
            raise parser_except.ParserException(12, '任务参数有误')
        self.hotel_id = content[0]
        self.check_in = datetime.datetime(int(content[2][:4]), int(content[2][4:6]), int(content[2][6:])).strftime(
            '%Y-%m-%d')
        self.check_out = (
        datetime.datetime(int(content[2][:4]), int(content[2][4:6]), int(content[2][6:])) + datetime.timedelta(
            days=int(content[1]))).strftime('%Y-%m-%d')
        self.dept_day = self.check_in[-2:]
        self.dept_my = default_dict[self.check_in[5:7]] + self.check_in[:4]
        self.dest_day = self.check_out[-2:]
        self.dest_my = default_dict[self.check_out[5:7]] + self.check_out[:4]

        @request(retry_count=3, proxy_type=PROXY_REQ, async=False)
        def get_hotel_data():
            return{'req': {'url': 'https://www.ihg.com/hotels', 'method': 'get'}}

        @request(retry_count=3, proxy_type=PROXY_FLLOW, async=False)
        def get_hotel3_data():
            url = 'https://www.ihg.com/hotels/cn/zh/reservation/book?method=roomRate&qAAR=6CBARC' \
                  '&qRtP=6CBARC&qAdlt=%s&qChld=0&qCiD=%s&qCiMy=%s&qCoD=%s&qCoMy=%s&qRms=%s&qSlH=%s&srb_u=1' % (
                  self.adult, self.dept_day, self.dept_my, self.dest_day, self.dest_my, self.rooms_count, self.hotel_id)
            return {'req': {'url': url,'method': 'get',},
                    'user_handler': [self.parse_first]}

        yield get_hotel_data
        yield get_hotel3_data

        selecte_types = self.html.xpath(u'//input[contains(@value,"预订此客房")]')
        common_list = []
        for selecte_type in selecte_types:
            selecte_type_name = re.findall(r'selectedRoom_(.*?)_', selecte_type.xpath('./@name')[0])
            if selecte_type_name:
                selecte_type_name = selecte_type_name[0]
                url = 'https://www.ihg.com/hotels/cn/zh/reservation/reservation/roomdescription?qAAR=6CBARC&qAdlt=%s&qChld=0&qCiD=%s&qCiMy=%s&qCoD=%s&qCoMy=%s&qRms=%s&qSlH=%s' \
                      '&srb_u=1' % (self.adult, self.dept_day, self.dept_my, self.dest_day, self.dest_my, self.rooms_count, self.hotel_id)
                common_list.append({'req': {'url': url, 'method': 'post', 'data': {'roomCode': selecte_type_name}, 'select_type': selecte_type}})
        res_list = self.list_of_groups(common_list, 10)
        for pro_list in res_list[:min(len(res_list),5)]:
            @request(retry_count=3, proxy_type=PROXY_FLLOW, async=True, binding=['room'])
            def get_price_page():
                return pro_list[:min(len(pro_list),5)]
            yield get_price_page

    def parse_first(self, req, resp):
        self.html = etree.HTML(resp)

    def list_of_groups(self, lia, lena):
        list_of_groups = zip(*(iter(lia),) * lena)
        end_list = [list(i) for i in list_of_groups]
        count = len(lia) % lena
        end_list.append(lia[-count:]) if count != 0 else end_list
        return end_list

    def parse_room(self, req, resp):
        # print resp.decode('utf-8')
        rooms = []
        html = etree.HTML(resp)
        select_type = req['req']['select_type']
        room = Room()
        hotel_name = select_type.xpath('./ancestor::body//a[@class="sel_hoteldetail_link"]/@title')
        if hotel_name:
            room.hotel_name = hotel_name[0]
        room.source = 'ihg'
        room.source_hotelid = self.hotel_id
        selecte_type_name = re.findall(r'selectedRoom_(.*?)_', select_type.xpath('./@name')[0])
        if selecte_type_name:
            room.source_roomid = selecte_type_name[0]
        room.real_source = 'ihg'
        room_type = select_type.xpath('./ancestor::div[@class="ratesListing roomsView "]//a[@class="roomTypeDescriptionToggle"]/text()')
        if room_type:
            room.room_type = room_type[0]
        occupancy = select_type.xpath('./ancestor::div[@class="ratesListing roomsView "]//span[contains(@class, "maxPeoplePerRoom")]//span[@class="notranslate"]/text()')
        if occupancy:
            room.occupancy = int(occupancy[0])
        size = select_type.xpath('./ancestor::div[@class="ratesListing roomsView "]//span[@class="roomLongDescription"]/text()')
        if size:
            size = re.findall(r'(\d+\s*)平方米', str(size[0]))
            if size:
                room.size = size[0]
        room.check_in = self.check_in
        room.check_out = self.check_out
        tables = html.xpath(u'//*[contains(text(),"估算总额")]/ancestor::table')
        for table in tables:
            # print d.xpath('string(.)')
            taxs = table.xpath(u'.//*[contains(text(), "税费")]')
            total_price = html.xpath(u'//*[contains(text(),"估算总额")]/text()')
            if taxs:
                prices = table.xpath(u'.//*[contains(text(), "房价")]/following-sibling::td[1]/text()')
                if prices:
                    room.price = prices[0].strip().replace(',', '')
                    room.price = re.findall(r'\d+\.*\d+', room.price)[0]
                    room.tax = taxs[0].xpath('./following-sibling::td[1]/text()')[0].strip()
                    room.tax = re.findall(r'\d+\.*\d+', room.tax)[0]
            elif total_price:
                room.price = total_price[0].strip().replace(',', '')
                room.price = re.findall(r'\d+\.*\d+', room.price)[0]
        currency = select_type.xpath('./ancestor::div[@class="ratesListing roomsView "]//span[@class="curCode cc_code"]/text()')
        if currency:
            room.currency = currency[0]
        room.pay_method = '在线支付'
        is_extrabed = html.xpath(u'//li[contains(text(), "加床")]')
        if is_extrabed:
            room.is_extrabed = 'Yes'
            is_extrabed = is_extrabed[0].xpath('string(.)').replace(' ', '')
            if '未包含' in is_extrabed:
                room.is_extrabed_free = 'No'
            else:
                room.extrabed_rule = is_extrabed
        else:
            room.is_extrabed = 'No'
            room.is_extrabed_free = 'No'
        if '含早餐' in html.xpath('string(.)'):
            room.has_breakfast = 'Yes'
            room.is_breakfast_free = 'Yes'
        else:
            room.has_breakfast = 'No'
            room.is_breakfast_free = 'No'
        return_rule= html.xpath(u'//*[text()="取消政策："]/following-sibling::*[1]/span/text()')
        if "取消预订不会收费" in return_rule:
            room.is_cancel_free = 'Yes'
        else:
            room.is_cancel_free = 'No'
        room.return_rule = return_rule
        room.room_desc = ''
        dt_desc = html.xpath('//div[@class="fullDescription"]//dd/preceding-sibling::dt[1]')
        for desc in dt_desc:
            if desc.xpath('./text()'):
                room.room_desc = room.room_desc + desc.xpath('./text()')[0].strip() + ' '
                dd_desc = desc.xpath('./following-sibling::dd[1]')
                room.room_desc = room.room_desc + dd_desc[0].xpath('string(.)').strip() + '|'
        room_tuple = (str(room.hotel_name), str(room.city), str(room.source), \
                      str(room.source_hotelid), str(room.source_roomid), \
                      str(room.real_source), str(room.room_type), int(room.occupancy), \
                      str(room.bed_type), float(room.size), int(room.floor), str(room.check_in), \
                      str(room.check_out), int(room.rest), float(room.price), float(room.tax), \
                      str(room.currency), str(room.pay_method), str(room.is_extrabed), str(room.is_extrabed_free), \
                      str(room.has_breakfast), str(room.is_breakfast_free), \
                      str(room.is_cancel_free), str(room.extrabed_rule), str(room.return_rule),
                      str(room.change_rule), \
                      str(room.room_desc), str(room.others_info), str(room.guest_info))
        if room.price:
            rooms.append(room_tuple)
        return rooms

    def get_first(self, data, str):
        if len(data) > 0:
            return data[0]
        else:
            return str

if __name__ == '__main__':
    from mioji.common.task_info import Task
    from mioji.common.utils import simple_get_socks_proxy
    from mioji.common import spider
    # spider.slave_get_proxy = simple_get_socks_proxy

    task = Task()
    # task.content = 'TYOHC&20180018&20180019'
    task.content = 'LAXCA&1&20180412'
    task.ticket_info = {"room_info": [{"occ": 2, "num": 1}]}
    task.source = 'ihg'
    spider = IhgHotelSpider()
    spider.task = task
    print spider.crawl()
    print json.dumps(spider.result, ensure_ascii=False)
