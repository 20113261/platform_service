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