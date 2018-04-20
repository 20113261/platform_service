#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import time
import types

from mioji.common import parser_except
from mioji.common.class_common import Room
from mioji.common.spider import Spider, request, PROXY_NONE, PROXY_NEVER


class EanSpider(Spider):
    source_type = 'eanApiHotel'
    targets = {
        'room': {'version': 'InsertHotel_room4'}
    }
    old_spider_tag = {
        'eanApiHotel': {
            'required': ['room']
        }
    }

    def __init__(self, task=None):
        super(EanSpider, self).__init__(task)

        self.redis_key = 'NULL'
        if hasattr(self.task, 'redis_key'):
            self.redis_key = self.task.redis_key

    def targets_request(self):
        _auth = self.task.ticket_info.get("auth", {})
        if isinstance(_auth, types.StringTypes):
            _auth = json.loads(_auth)
        elif isinstance(_auth, types.DictType):
            _auth = _auth
        else:
            _auth = {}

        api_key = _auth.get("apiKey", None)
        secret = _auth.get("secret", None)
        url_part = _auth.get("url", None)

        if not api_key or not secret or not url_part:
            raise parser_except.ParserException(121, "无认证信息")

        self.user_datas["api_key"] = api_key
        self.user_datas["secret"] = secret
        self.user_datas["url_part"] = url_part

        @request(retry_count=3, proxy_type=PROXY_NEVER, binding=self.parse_room)
        def request_properties():
            query_data = self.make_data(self.task.content)

            URL = self.user_datas[
                      "url_part"] + """properties/availability?arrival={arrival}&currency={currency}&sort_type={sort_type}&country_code={country_code}&language={language}&sales_channel={sales_channel}&property_id={property_id}&departure={departure}&occupancy={occupancy}&sales_environment={sales_environment}""".format(
                **query_data)
            headers = {
                'Accept': "application/json",
                'Accept-Encoding': "gzip",
                'Customer-Ip': "10.10.10.10",
                'Authorization': self.get_authHeaderValue(api_key, secret),
            }
            return {
                "req": {
                    "url": URL,
                    "headers": headers
                },
            }

        yield request_properties

    def make_data(self, content):
        """
        arrival=2017-09-15  # 入住日期，采用ISO 8601格式（YYYY-MM-DD）
        departure=2017-09-17  # 退房日期
        currency=USD      # 货币类型 ISO 4217格式
        language=en-US    # 语言
        country_code=US  # 客户所在国家代码
        occupancy=2  # 入住人员信息  2名成人，1名9岁和1名4岁儿童将代表occupancy=2-9,4
        property_id={{property_id}}  # 酒店属性id
        sales_channel=website  # 显示费率的销售渠道
        sales_environment={{sales_environment}}  # 提供销售价格的销售环境
        sort_type=preferred
        """
        room_info = self.task.ticket_info.get("room_info", [{"room_count": 1, "occ": 2}])
        self.user_datas["occ"] = room_info[0]["occ"]
        self.user_datas["room_count"] = room_info[0]["room_count"]
        data = {}
        city_id, hotel_code, check_in, check_out = self.content_parser(content)
        self.user_datas["city_id"] = city_id
        data["arrival"] = check_in
        data["departure"] = check_out
        data["currency"] = "CNY"
        self.user_datas["currency"] = data["currency"]
        data["language"] = "zh-CN"
        data["country_code"] = "CN"
        data["occupancy"] = str(self.user_datas["occ"])
        if self.user_datas["room_count"] > 1:
            for i in range(self.user_datas["room_count"] - 1):
                data["occupancy"] += "&occupancy=" + str(self.user_datas["occ"])
        data["property_id"] = hotel_code
        data["sales_channel"] = "website"
        data["sales_environment"] = "hotel_only"
        data["sort_type"] = "preferred"
        return data

    def content_parser(self, content):
        content_list = content.split("&")
        city_id = content_list[0]
        hotel_code = content_list[1]
        night = int(content_list[2])
        self.user_datas["night"] = night
        checkin = datetime.datetime.strptime(content_list[3], "%Y%m%d")
        checkout = checkin + datetime.timedelta(days=night)
        check_in = checkin.strftime("%Y-%m-%d")
        self.user_datas["check_in"] = check_in
        check_out = checkout.strftime("%Y-%m-%d")
        self.user_datas["check_out"] = check_out
        return city_id, hotel_code, check_in, check_out

    def get_authHeaderValue(self, api_key, secret):
        import hashlib
        apiKey = api_key
        secret = secret
        timestamp = str(int(time.time()))
        authHeaderValue = "EAN APIkey=" + apiKey + ",Signature=" + hashlib.sha512(
            apiKey + secret + timestamp).hexdigest() + ",timestamp=" + timestamp
        return authHeaderValue

    def response_error(self, req, resp, error):
        if resp.status_code == 400:
            raise parser_except.ParserException(121, '请求参数有误')
        elif resp.status_code == 401:
            raise parser_except.ParserException(122, '认证信息错误')
        elif resp.status_code == 403:
            raise parser_except.ParserException(122, '认证信息错误')
        elif resp.status_code == 404:
            raise parser_except.ParserException(29, '源无房型')
        elif resp.status_code in [426, 500, 503]:
            raise parser_except.ParserException(89, '服务出错')

    def _parse_room(self, data, room_index):
        room = Room()
        room.city = self.user_datas["city_id"]
        room.source = "eanApi"
        room.source_hotelid = data[0]["property_id"]
        room.source_roomid = data[0]["rooms"][room_index]["id"]
        room.real_source = room.source
        room.room_type = data[0]["rooms"][room_index]["room_name"]
        room.occupancy = self.user_datas['occ']
        room.check_in = self.user_datas["check_in"]
        room.check_out = self.user_datas["check_out"]
        room.rest = data[0]["rooms"][room_index]["rates"][0].get("available_rooms", -1)
        room.price = float(
            data[0]["rooms"][room_index]["rates"][0]["occupancies"].get(str(self.user_datas["occ"]))["totals"][
                "exclusive"]["request_currency"]["value"])
        room.tax = float(
            data[0]["rooms"][room_index]["rates"][0]["occupancies"].get(str(self.user_datas["occ"]))["totals"][
                "inclusive"]["request_currency"]["value"]) - room.price
        room.tax = round(room.tax, 2)
        room.currency = self.user_datas["currency"]
        room.pay_method = "mioji"
        room.has_breakfast = "No"
        room.is_breakfast_free = "No"
        room.room_desc = "NULL"

        # 退改信息
        room.is_cancel_free = "NULL"
        refundable = data[0]["rooms"][room_index]["rates"][0]["refundable"]
        if refundable:
            cancel_penalties = data[0]["rooms"][room_index]["rates"][0]["cancel_penalties"][0]
            return_params = dict()
            return_params["start"] = cancel_penalties["start"]
            return_params["end"] = cancel_penalties["end"]
            currency = cancel_penalties["currency"]
            room.return_rule = """免费取消截止日期：{start}<br/>从{start}至{end}扣取<br/>""".format(**return_params)
            nights = cancel_penalties.get("nights", "")
            amount = cancel_penalties.get("amount", "")
            percent = cancel_penalties.get("percent", "")
            if nights:
                room.return_rule += "{nights}晚的费用<br/>".format(nights=nights)
            if amount:
                room.return_rule += "共扣取{amount}{currency}<br/>".format(amount=amount, currency=currency)
            if percent:
                room.return_rule += "占总金额的百分比为：{percent}%".format(percent=percent)
        else:
            room.return_rule = "订单不可取消"

        comments = {}
        # todo  早餐
        amenities = data[0]["rooms"][room_index]["rates"][0].get("amenities", None)
        breakfast_title = ""
        if amenities:
            room.room_desc = list()
            for amenitie in amenities:
                if "早餐" in amenitie["name"]:
                    room.has_breakfast = "NULL"
                    room.is_breakfast_free = "NULL"
                    breakfast_title = amenitie["name"]
                else:
                    room.room_desc.append(amenitie["name"])
            room.room_desc = "|".join(room.room_desc)

        extra = {'breakfast': breakfast_title,
                 'payment': '',
                 'return_rule': room.return_rule,
                 'occ_des': ''}
        comments["extra"] = extra

        pay_key = {
            "redis_key": self.redis_key,
            "id": room_index,
            "price_check_href": data[0]["rooms"][room_index]["rates"][0]["bed_groups"][0]["links"]["price_check"][
                "href"]
        }
        comments["paykey"] = pay_key
        comments["payKey"] = pay_key
        room.others_info = json.dumps(comments)

        roomtuple = (room.hotel_name, room.city, room.source, room.source_hotelid, room.source_roomid,
                     room.real_source, room.room_type, room.occupancy, room.bed_type, room.size, room.floor,
                     room.check_in, room.check_out, room.rest, room.price, room.tax, room.currency,
                     room.pay_method, room.is_extrabed, room.is_extrabed_free, room.has_breakfast,
                     room.is_breakfast_free, room.is_cancel_free, room.extrabed_rule, room.return_rule,
                     room.change_rule, room.room_desc, room.others_info, room.guest_info)
        return roomtuple

    def parse_room(self, req, data):
        """
        'http://oa.mioji.com/xwiki/bin/view/数据抓取/酒店数据文档'
        """
        data = json.loads(data)
        rooms = list()

        # todo 根据响应类型，对应处理数据
        if isinstance(data, types.ListType):
            room_type_len = len(data[0]["rooms"])
            for room_index in range(room_type_len):
                roomtuple = self._parse_room(data, room_index)
                rooms.append(roomtuple)

        return rooms


if __name__ == '__main__':
    from mioji.common.task_info import Task

    task = Task()
    task.content = "10009&9850572&2&20180310"
    task.source = "hotelbeds"

    auth = """{"apiKey": "2ipijb2099q707k3q72nhmvcmg", "secret": "5dqjshaqk267s", "url": "https://test.ean.com/2/"}"""

    # test
    task.ticket_info = {
        "room_info": [{"room_count": 2, "occ": 3}],
        "env_name": "offline",
        "auth": auth,
        'room_count': 2
    }

    ean_spider = EanSpider(task)
    # ean_spider.task = task
    ean_spider.crawl()
    result = ean_spider.result
    print result
