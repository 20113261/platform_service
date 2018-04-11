#!/usr/bin/env python
# -*- coding: utf-8 -*-
from proj.my_lib.models.column import Column, String, Integer, Datetime, Text, Map, JSON
from proj.my_lib.models.base_model import BaseModel
import datetime


class HotelBase(BaseModel):
    hotel_name = Column(String(512), default='NULL')
    hotel_name_en = Column(String(512), default='NULL')
    source = Column(String(64), default='NULL')
    source_id = Column(String(128), default='NULL')
    source_city_id = Column(String(128), default='NULL')
    brand_name = Column(String(512), default='NULL')
    map_info = Column(String(512), default='NULL')
    address = Column(String(512), default='NULL')
    city = Column(String(512), default='NULL')
    country = Column(String(512), default='NULL')
    city_id = Column(String(11), default='NULL')
    postal_code = Column(String(512), default='NULL')
    star = Column(String(20), default='-1')
    grade = Column(String(256), default='-1.0')
    review_num = Column(String(20), default='-1')
    has_wifi = Column(String(20), default='NULL')
    is_wifi_free = Column(String(20), default='NULL')
    has_parking = Column(String(20), default='NULL')
    is_parking_free = Column(String(20), default='NULL')
    service = Column(Text(), default='NULL')
    img_items = Column(Text(), default='NULL')
    description = Column(Text(), default='NULL')
    accepted_cards = Column(String(512), default='NULL')
    check_in_time = Column(String(128), default='NULL')
    check_out_time = Column(String(128), default='NULL')
    hotel_url = Column(String(1024), default='NULL')
    # update_time = Column(Datetime(6), default=datetime.datetime.now)
    continent = Column(String(96), default='NULL')
    country_id = Column(String(512), default='NULL')
    others_info = Column(JSON(), default='{}')
    Img_first = Column(Text(), default='NULL')
    hotel_phone = Column(Text(), default='NULL')
    hotel_zip_code = Column(Text(), default='NULL')
    traffic = Column(Text(), default='NULL')
    chiled_bed_type = Column(Text(), default='NULL')
    pet_type = Column(Text(), default='NULL')
    facility = Column(Text(), default='NULL')
    feature = Column(Text(), default='NULL')

class HotelNewBase(BaseModel):
    hotel_name = Column(String(512), default='NULL')
    hotel_name_en = Column(String(512), default='NULL')
    source = Column(String(64), default='NULL')
    source_id = Column(String(128), default='NULL')
    brand_name = Column(String(512), default='NULL')
    map_info = Column(String(512), default='NULL')
    address = Column(String(512), default='NULL')
    city = Column(String(512), default='NULL')
    country = Column(String(512), default='NULL')
    city_id = Column(String(11), default='NULL')
    postal_code = Column(String(512), default='NULL')
    star = Column(String(20), default='-1')
    grade = Column(String(256), default='-1.0')
    review_num = Column(String(20), default='-1')
    service = Column(Text(), default='NULL')
    img_items = Column(Text(), default='NULL')
    description = Column(Text(), default='NULL')
    accepted_cards = Column(String(512), default='NULL')
    check_in_time = Column(String(128), default='NULL')
    check_out_time = Column(String(128), default='NULL')
    hotel_url = Column(String(1024), default='NULL')
    # update_time = Column(Datetime(6), default=datetime.datetime.now)
    continent = Column(String(96), default='NULL')
    others_info = Column(JSON(), default='{}')
    Img_first = Column(Text(), default='NULL')
    hotel_phone = Column(Text(), default='NULL')
    hotel_zip_code = Column(Text(), default='NULL')
    traffic = Column(Text(), default='NULL')
    chiled_bed_type = Column(Text(), default='NULL')
    pet_type = Column(Text(), default='NULL')
    facility = Column(Text(), default='NULL')
    feature = Column(Text(), default='NULL')

    feature_content = {
        "China_Friendly": "NULL",
        "Romantic_lovers": "NULL",
        "Parent_child": "NULL",
        "Beach_Scene": "NULL",
        "Hot_spring": "NULL",
        "Japanese_Hotel": "NULL",
        "Vacation": "NULL"
    }
    facility_content = {
        "Room_wifi": "NULL",
        "Room_wired": "NULL",
        "Public_wifi": "NULL",
        "Public_wired": 'NULL',
        "Parking": "NULL",
        "Airport_bus": "NULL",
        "Valet_Parking": "NULL",
        "Call_service": "NULL",
        "Rental_service": "NULL",
        "Swimming_Pool": "NULL",
        "gym": "NULL",
        'SPA': "NULL",
        "Bar": "NULL",
        "Coffee_house": "NULL",
        "Tennis_court": "NULL",
        "Golf_Course": "NULL",
        "Sauna": "NULL",
        "Mandara_Spa": "NULL",
        "Recreation": "NULL",
        "Business_Centre": "NULL",
        "Lounge": "NULL",
        "Wedding_hall": "NULL",
        "Restaurant": "NULL",
    }

    service_content = {
        "Luggage_Deposit": 'NULL',
        "front_desk": 'NULL',
        "Lobby_Manager": "NULL",
        "24Check_in": "NULL",
        "Security": "NULL",
        "Protocol": 'NULL',
        "wake": "NULL",
        "Chinese_front": "NULL",
        "Postal_Service": "NULL",
        "Fax_copy": 'NULL',
        "Laundry": "NULL",
        "polish_shoes": "NULL",
        "Frontdesk_safe": 'NULL',
        "fast_checkin": "NULL",
        "ATM": 'NULL',
        "child_care": 'NULL',
        "Food_delivery": 'NULL',
    }


    def facility_Num(self, key):
        facilities = {
            "Room_wifi": ("10001", u"客房wifi"),
            "Room_wired": ("10002", u"客房有线网络"),
            "Public_wifi": ("10003", u"公共区域WiFi"),
            "Public_wired": ('10004', u'公共区域有线网络'),
            "Parking": ("11001", u"停车场"),
            "Airport_bus": ("11002", u'机场班车'),
            "Valet_Parking": ("11003", u'代客泊车'),
            "Call_service": ("11004", u"叫车服务"),
            "Rental_service": ("11005", u'租车服务'),
            "Swimming_Pool": ("12001", u"游泳池"),
            "gym": ("12002", u'健身房'),
            'SPA': ("12003", u'SPA'),
            "Bar": ("12004", u'酒吧'),
            "Coffee_house": ("12005", u"咖啡厅"),
            "Tennis_court": ("12006", u"网球场"),
            "Golf_Course": ("12007", u"高尔夫球场"),
            "Sauna": ("12008", u"桑拿"),
            "Mandara_Spa": ("12009", u"水疗中心"),
            "Recreation": ("12010", u"儿童娱乐场"),
            "Business_Centre": ("13001", u"商务中心"),
            "Lounge": ("13002", u"行政酒廊"),
            "Wedding_hall": ("13003", u"婚礼礼堂"),
            "Restaurant": ("13004", u"餐厅"),
        }
        return facilities.get(key, None)


    def service_Num(self, key):
        service = {
            "Luggage_Deposit": ('20001', u"行李寄存"),
            "front_desk": ('20002', u"24小时前台"),
            "Lobby_Manager": ("20003", u"24小时大堂经理"),
            "24Check_in": ("20004", u"24小时办理入住"),
            "Security": ("20005", u"24小时安保"),
            "Protocol": ('20006', u"礼宾服务"),
            "wake": ("20007", u"叫醒服务"),
            "Chinese_front": ("20008", u"中文前台"),
            "Postal_Service": ("20009", u"邮政服务"),
            "Fax_copy": ('20010', u"传真/复印"),
            "Laundry": ("20011", u"洗衣服务"),
            "polish_shoes": ("20012", u"擦鞋服务"),
            "Frontdesk_safe": ('20013', u"前台保险柜"),
            "fast_checkin": ("20014", u"快速办理入住/退房"),
            "ATM": ('21001', u"自动柜员机(ATM)/银行服务"),
            "child_care": ('21002', u"儿童看护服务"),
            "Food_delivery": ('21003', u"送餐服务"),
        }
        return service.get(key, None)


    def feature_Num(self, key):
        feature = {
            "China_Friendly": ("30001", u"华人礼遇"),
            "Romantic_lovers": ("30002", u"浪漫情侣"),
            "Parent_child": ("30003", u"亲子酒店"),
            "Beach_Scene": ("30004", u"海滨风光"),
            "Hot_spring": ("30005", u"温泉酒店"),
            "Japanese_Hotel": ("30006", u"日式旅馆"),
            "Vacation": ("30007", u"休闲度假")
        }
        return feature.get(key, None)


    def to_dict(self):
        from json import dumps
        facility = {}
        service = {}
        feature = {}
        for key, value in self.facility_content.items():
            if value == "NULL":
                continue
            value_Num = self.facility_Num(key)
            if not value_Num:
                continue
            item = {"key": value_Num[1], "value": value}
            facility[value_Num[0]] = item
        for key, value in self.service_content.items():
            if value == "NULL":
                continue
            value_Num = self.service_Num(key)
            if not value_Num:
                continue
            item = {"key": value_Num[1], "value": value}
            service[value_Num[0]] = item
        for key, value in self.feature_content.items():
            if value == "NULL":
                continue
            value_Num = self.feature_Num(key)
            if not value_Num:
                continue
            item = {"key": value_Num[1], "value": value}
            feature[value_Num[0]] = item
        self.facility = str(facility) if facility != {} else 'NULL'
        self.feature = str(feature) if facility != {} else 'NULL'
        self.service = str(service) if facility != {} else 'NULL'
        return self




class Hotel_New:
    def __init__(self):
        self.hotel_name = 'NULL'
        self.hotel_name_en = 'NULL'
        self.source = 'NULL'
        self.source_id = 'NULL'
        self.brand_name = 'NULL'
        self.map_info = 'NULL'
        self.address = 'NULL'
        self.city = 'NULL'
        self.country = 'NULL'
        self.city_id = 'NULL'
        self.postal_code = 'NULL'
        self.star = -1.0
        self.grade = 'NULL'
        self.review_num = -1
        self.Img_first = 'NULL'
        self.hotel_phone = 'NULL'
        self.hotel_zip_code = 'NULL'
        self.traffic = 'NULL'
        self.chiled_bed_type = 'NULL'
        self.pet_type = 'NULL'
        self.other_info = []
        self.img_items = 'NULL'
        self.description = 'NULl'
        self.accepted_cards = 'NULL'
        self.check_in_time = 'NULL'
        self.check_out_time = 'NULL'
        self.hotel_url = 'NULL'
        self.continent = 'NULL'
        self.feature = {
            "China_Friendly": "NULL",
            "Romantic_lovers": "NULL",
            "Parent_child": "NULL",
            "Beach_Scene": "NULL",
            "Hot_spring": "NULL",
            "Japanese_Hotel": "NULL",
            "Vacation": "NULL"
        }
        self.facility = {
            "Room_wifi": "NULL",
            "Room_wired": "NULL",
            "Public_wifi": "NULL",
            "Public_wired": 'NULL',
            "Parking": "NULL",
            "Airport_bus": "NULL",
            "Valet_Parking": "NULL",
            "Call_service": "NULL",
            "Rental_service": "NULL",
            "Swimming_Pool": "NULL",
            "gym": "NULL",
            'SPA': "NULL",
            "Bar": "NULL",
            "Coffee_house": "NULL",
            "Tennis_court": "NULL",
            "Golf_Course": "NULL",
            "Sauna": "NULL",
            "Mandara_Spa": "NULL",
            "Recreation": "NULL",
            "Business_Centre": "NULL",
            "Lounge": "NULL",
            "Wedding_hall": "NULL",
            "Restaurant": "NULL",
        }

        self.service = {
            "Luggage_Deposit": 'NULL',
            "front_desk": 'NULL',
            "Lobby_Manager": "NULL",
            "24Check_in": "NULL",
            "Security": "NULL",
            "Protocol": 'NULL',
            "wake": "NULL",
            "Chinese_front": "NULL",
            "Postal_Service": "NULL",
            "Fax_copy": 'NULL',
            "Laundry": "NULL",
            "polish_shoes": "NULL",
            "Frontdesk_safe": 'NULL',
            "fast_checkin": "NULL",
            "ATM": 'NULL',
            "child_care": 'NULL',
            "Food_delivery": 'NULL',
        }

    def facility_Num(self, key):
        facilities = {
            "Room_wifi": ("10001", u"客房wifi"),
            "Room_wired": ("10002", u"客房有线网络"),
            "Public_wifi": ("10003", u"公共区域WiFi"),
            "Public_wired": ('10004', u'公共区域有线网络'),
            "Parking": ("11001", u"停车场"),
            "Airport_bus": ("11002", u'机场班车'),
            "Valet_Parking": ("11003", u'代客泊车'),
            "Call_service": ("11004", u"叫车服务"),
            "Rental_service": ("11005", u'租车服务'),
            "Swimming_Pool": ("12001", u"游泳池"),
            "gym": ("12002", u'健身房'),
            'SPA': ("12003", u'SPA'),
            "Bar": ("12004", u'酒吧'),
            "Coffee_house": ("12005", u"咖啡厅"),
            "Tennis_court": ("12006", u"网球场"),
            "Golf_Course": ("12007", u"高尔夫球场"),
            "Sauna": ("12008", u"桑拿"),
            "Mandara_Spa": ("12009", u"水疗中心"),
            "Recreation": ("12010", u"儿童娱乐场"),
            "Business_Centre": ("13001", u"商务中心"),
            "Lounge": ("13002", u"行政酒廊"),
            "Wedding_hall":("13003", u"婚礼礼堂"),
            "Restaurant": ("13004", u"餐厅"),
        }
        return facilities.get(key, None)

    def service_Num(self,key):
        service = {
            "Luggage_Deposit": ('20001', u"行李寄存"),
            "front_desk": ('20002', u"24小时前台"),
            "Lobby_Manager": ("20003", u"24小时大堂经理"),
            "24Check_in": ("20004", u"24小时办理入住"),
            "Security": ("20005", u"24小时安保"),
            "Protocol": ('20006', u"礼宾服务"),
            "wake": ("20007", u"叫醒服务"),
            "Chinese_front": ("20008", u"中文前台"),
            "Postal_Service": ("20009", u"邮政服务"),
            "Fax_copy": ('20010', u"传真/复印"),
            "Laundry": ("20011", u"洗衣服务"),
            "polish_shoes": ("20012", u"擦鞋服务"),
            "Frontdesk_safe": ('20013', u"前台保险柜"),
            "fast_checkin": ("20014", u"快速办理入住/退房"),
            "ATM": ('21001', u"自动柜员机(ATM)/银行服务"),
            "child_care": ('21002', u"儿童看护服务"),
            "Food_delivery": ('21003', u"送餐服务"),
        }
        return service.get(key,None)

    def feature_Num(self,key):
        feature = {
            "China_Friendly": ("30001", u"华人礼遇"),
            "Romantic_lovers": ("30002", u"浪漫情侣"),
            "Parent_child": ("30003", u"亲子酒店"),
            "Beach_Scene": ("30004", u"海滨风光"),
            "Hot_spring": ("30005", u"温泉酒店"),
            "Japanese_Hotel": ("30006", u"日式旅馆"),
            "Vacation": ("30007", u"休闲度假")
        }
        return feature.get(key,None)

    def to_dict(self):
        from json import dumps
        facility = {}
        service = {}
        feature = {}
        for key,value in self.facility.items():
            if value == "NULL":
                continue
            value_Num = self.facility_Num(key)
            if not value_Num:
                continue
            item = {"key":value_Num[1],"value":value}
            facility[value_Num[0]] = item
        for key,value in self.service.items():
            if value == "NULL":
                continue
            value_Num = self.service_Num(key)
            if not value_Num:
                continue
            item = {"key":value_Num[1],"value":value}
            service[value_Num[0]] = item
        for key, value in self.feature.items():
            if value == "NULL":
                continue
            value_Num = self.feature_Num(key)
            if not value_Num:
                continue
            item = {"key":value_Num[1],"value":value}
            feature[value_Num[0]] = item
        result = self.__dict__
        result["facility"] = facility
        result["feature"] = feature
        result["service"] = service
        return dumps(result)


class BookingHotel(HotelBase):
    pass


class AgodaHotel(HotelBase):
    pass


class ExpediaHotel(HotelBase):
    pass


class HotelsHotel(HotelBase):
    pass


class ElongHotel(HotelBase):
    pass


class CtripHotel(HotelBase):
    pass

class CtripCNHotel(HotelBase):
    pass

class HiltonHotel(HotelBase):
    pass


class TripadvisorHotel(HotelBase):
    pass

class CommonHotel(HotelBase):
    pass