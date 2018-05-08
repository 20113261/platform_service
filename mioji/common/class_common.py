#!/usr/bin/env python
# coding=UTF8
'''
这个文件里面定义了需要使用的类
'''

import sys, datetime

reload(sys)

FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'

def calsecond(hms):
    hms_list = hms.split(':')
    dur = int(hms_list[0]) * 3600 + int(hms_list[1]) * 60 + int(hms_list[2])
    return dur


def cal_day_diff(time_list):
    day_diff = ''
    temp_list = time_list.split('|')

    for each in temp_list:

        each_list = each.split('_')
        each_list_0 = each_list[0].split('T')
        each_list_1 = each_list[1].split('T')
        if each_list_0[0] == each_list_1[0]:
            if calsecond(each_list_0[1]) >= calsecond(each_list_1[1]):
                day_diff += '1_'
            else:
                day_diff += '0_'
        else:
            day_diff += '1_'
    return day_diff[:-1]


class Flight:
    def __init__(self):
        self.flight_no = 'NULL'
        self.plane_no = 'NULL'
        self.airline = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.real_class = 'NULL'
        self.package = 'NULL'
        self.stop_airport = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.stop_dur = 'NULL'
        self.daydiff = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop_cost = 'NULL'
        self.stop = -1
        self.plane_type = 'NULL'
        self.plane_corp = 'NULL'
        self.flight_corp = 'NULL'
        self.change_rule = 'NULL'
        self.share_flight = 'NULL'
        self.stopby = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.others_info = 'NULL'
        self.ticket_type = 'NULL'

        self.key_list = ['flight_no', 'plane_type', 'flight_corp', 'dept_id',
                        'dest_id', 'dept_day', 'dept_time', 'dest_time', 'dur',
                        'rest', 'price', 'tax', 'surcharge', 'promotion', 'currency',
                        'seat_type', 'real_class', 'package', 'stop_id', 'stop_time',
                        'daydiff', 'source', 'return_rule', 'change_rule', 'stop',
                        'share_flight', 'stopby', 'baggage', 'transit_visa',
                        'reimbursement', 'flight_meals', 'ticket_type', 'others_info']

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results

    def get_day_diff(self):
        return cal_day_diff(self.stop_time)

    def get_airline(self):
        ret = []
        for flight_no in self.flight_no.split('_'):
            if flight_no == 'NULL':
                ret.append('NULL')
            else:
                ret.append(flight_no[:2])
        return '_'.join(ret)

    def to_tuple(self):
        return (self.flight_no, self.plane_type, self.flight_corp, self.dept_id,
                self.dest_id, self.dept_day, self.dept_time, self.dest_time, self.dur,
                self.rest, self.price, self.tax, self.surcharge, self.promotion, self.currency,
                self.seat_type, self.real_class, self.package, self.stop_id, self.stop_time,
                self.daydiff, self.source, self.return_rule, self.change_rule, self.stop,
                self.share_flight, self.stopby, self.baggage, self.transit_visa,
                self.reimbursement, self.flight_meals, self.ticket_type, self.others_info)

    def human_friendly_dump(self):
        for key in self.key_list:
            print key, ':', self.__dict__[key]


class MultiFlight:
    def __init__(self):
        self.flight_no = 'NULL'
        self.plane_no = 'NULL'
        self.airline = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.real_class = 'NULL'
        self.package = 'NULL'
        self.stop_airport = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.stop_dur = 'NULL'
        self.daydiff = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop_cost = 'NULL'
        self.stop = -1
        self.plane_type = 'NULL'
        self.plane_corp = 'NULL'
        self.flight_corp = 'NULL'
        self.change_rule = 'NULL'
        self.share_flight = 'NULL'
        self.stopby = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.others_info = 'NULL'
        self.ticket_type = 'NULL'

        self.key_list = [
            'flight_no', 'plane_type', 'flight_corp', 'dept_id',
            'dest_id', 'dept_day', 'dept_time', 'dest_time', 'dur',
            'rest', 'price', 'tax', 'surcharge', 'promotion', 'currency',
            'seat_type', 'real_class', 'package', 'stop_id', 'stop_time',
            'daydiff', 'source', 'return_rule', 'change_rule', 'stop',
            'share_flight', 'stopby', 'baggage', 'transit_visa',
            'reimbursement', 'flight_meals', 'ticket_type', 'others_info'
        ]

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results

    def to_tuple(self):
        return (self.flight_no, self.plane_type, self.flight_corp, self.dept_id,
                self.dest_id, self.dept_day, self.dept_time, self.dest_time, self.dur,
                self.rest, self.price, self.tax, self.surcharge, self.promotion, self.currency,
                self.seat_type, self.real_class, self.package, self.stop_id, self.stop_time,
                self.daydiff, self.source, self.return_rule, self.change_rule, self.stop,
                self.share_flight, self.stopby, self.baggage, self.transit_visa,
                self.reimbursement, self.flight_meals, self.ticket_type, self.others_info)

    def human_friendly_dump(self):
        for key in self.key_list:
            print key, ':', self.__dict__[key]


class RoundFlight:
    def __init__(self):
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_day = 'NULL'
        self.dest_day = 'NULL'
        self.price = -1.0
        self.tax = -1.0
        self.surcharge = -1.0
        self.promotion = 'NULL'
        self.currency = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.flight_no_A = 'NULL'
        self.airline_A = 'NULL'
        self.plane_no_A = 'NULL'
        self.dept_time_A = 'NULL'
        self.dest_time_A = 'NULL'
        self.dur_A = -1
        self.seat_type_A = 'NULL'
        self.real_class_A = 'NULL'
        self.stop_id_A = 'NULL'
        self.stop_time_A = 'NULL'
        self.daydiff_A = 'NULL'
        self.stop_A = -1
        self.flight_no_B = 'NULL'
        self.airline_B = 'NULL'
        self.plane_no_B = 'NULL'
        self.dept_time_B = 'NULL'
        self.dest_time_B = 'NULL'
        self.dur_B = -1
        self.seat_type_B = 'NULL'
        self.real_class_B = 'NULL'
        self.stop_id_B = 'NULL'
        self.stop_time_B = 'NULL'
        self.daydiff_B = 'NULL'
        self.stop_B = -1
        self.change_rule = 'NULL'
        self.share_flight_A = 'NULL'
        self.share_flight_B = 'NULL'
        self.stopby_A = 'NULL'
        self.stopby_B = 'NULL'
        self.baggage = 'NULL'
        self.transit_visa = 'NULL'
        self.reimbursement = 'NULL'
        self.flight_meals = 'NULL'
        self.ticket_type = 'NULL'
        self.others_info = 'NULL'
        self.rest = -1

        self.key_list = [
            'dept_id', 'dest_id', 'dept_day', 'dest_day', 'price', 'tax', 'surcharge',
            'promotion', 'currency', 'source', 'return_rule', 'flight_no_A', 'airline_A',
            'plane_no_A', 'dept_time_A', 'dest_time_A', 'dur_A', 'seat_type_A',
            'real_class_A', 'stop_id_A', 'stop_time_A', 'daydiff_A', 'stop_A', 'flight_no_B',
            'airline_B', 'plane_no_B', 'dept_time_B', 'dest_time_B', 'dur_B', 'seat_type_B',
            'real_class_B', 'stop_id_B', 'stop_time_B', 'daydiff_B', 'stop_B', 'change_rule',
            'share_flight_A', 'share_flight_B', 'stopby_A', 'stopby_B', 'baggage',
            'transit_visa', 'reimbursement', 'flight_meals', 'ticket_type', 'others_info',
            'rest'
        ]

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('UTF-8')))
        return results

    def to_tuple(self):
        return (
            self.dept_id, self.dest_id, self.dept_day, self.dest_day, self.price, self.tax, self.surcharge,
            self.promotion, self.currency, self.source, self.return_rule, self.flight_no_A, self.airline_A,
            self.plane_no_A, self.dept_time_A, self.dest_time_A, self.dur_A, self.seat_type_A,
            self.real_class_A, self.stop_id_A, self.stop_time_A, self.daydiff_A, self.stop_A, self.flight_no_B,
            self.airline_B, self.plane_no_B, self.dept_time_B, self.dest_time_B, self.dur_B, self.seat_type_B,
            self.real_class_B, self.stop_id_B, self.stop_time_B, self.daydiff_B, self.stop_B, self.change_rule,
            self.share_flight_A, self.share_flight_B, self.stopby_A, self.stopby_B, self.baggage,
            self.transit_visa, self.reimbursement, self.flight_meals, self.ticket_type, self.others_info,
            self.rest)

    def human_friendly_dump(self):
        for key in self.key_list:
            print key, ':', self.__dict__[key]

# 这个弃用了吧
class EachFlight:
    def __init__(self):
        self.flight_key = 'NULL'
        self.flight_no = 'NULL'
        self.airline = 'NULL'
        self.plane_no = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.daydiff = -1
        self.stop = -1
        self.cost = -1
        self.schedule = 'NULL'
        self.source = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('UTF-8')))

        return results


class Hotel:
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
        self.postal_code = 'NULL'
        self.star = -1.0
        self.grade = 'NULL'
        self.review_num = -1
        self.has_wifi = 'NULL'
        self.is_wifi_free = 'NULL'
        self.has_parking = 'NULL'
        self.is_parking_free = 'NULL'
        self.service = 'NULL'
        self.img_items = 'NULL'
        self.description = 'NULL'
        self.accepted_cards = 'NULL'
        self.check_in_time = 'NULL'
        self.check_out_time = 'NULL'
        self.hotel_url = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Room:
    def __init__(self):
        self.hotel_name = 'NULL'
        self.city = 'NULL'
        self.source = 'NULL'
        self.source_hotelid = 'NULL'
        self.source_roomid = 'NULL'
        self.room_type = 'NULL'
        self.real_source = 'NULL'
        self.occupancy = -1
        self.bed_type = 'NULL'
        self.size = -1.0
        self.floor = -1
        self.check_in = 'NULL'
        self.check_out = 'NULL'
        self.rest = -1
        self.price = -1.0
        self.tax = -1.0
        self.currency = 'NULL'
        self.is_extrabed = 'NULL'
        self.is_extrabed_free = 'NULL'
        self.has_breakfast = 'NULL'
        self.is_breakfast_free = 'NULL'
        self.is_cancel_free = 'NULL'
        self.room_desc = 'NULL'
        self.return_rule = 'NULL'
        self.pay_method = 'NULL'
        self.extrabed_rule = 'NULL'
        self.change_rule = 'NULL'
        self.others_info = 'NULL'
        self.guest_info = 'NULL'
        self.hotel_url = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Comment:
    def __init__(self):
        self.hotel_name = 'NULL'
        self.city = 'NULL'
        self.source_hotelid = 'NULL'
        self.comment = 'NULL'
        self.comment_user = 'NULL'
        self.source = 'NULL'
        self.title = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class Attraction:
    def __init__(self):
        self.name = 'NULL'
        self.name_en = 'NULL'
        self.grade = 'NULL'
        self.city_id = 'NULL'
        self.map_info = 'NULL'
        self.address = 'NULL'
        self.phone = 'NULL'
        self.website = 'NULL'
        self.open = 'NULL'
        self.close = 'NULL'
        self.ticket = 'NULL'
        self.description = 'NULL'
        self.image = 'NULL'
        self.rcmd_visit_time = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Train:
    def __init__(self):
        self.train_no = 'NULL'
        self.train_type = 'NULL'
        self.train_corp = 'NULL'
        self.dept_city = 'NULL'
        self.dept_station = 'NULL'
        self.dest_city = 'NULL'
        self.dest_station = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.price = -1.0
        self.tax = -1.0
        self.currency = 'NULL'
        self.seat_type = 'NULL'
        self.source = 'NULL'
        self.return_rule = 'NULL'
        self.stop = -1
        self.stop_station = 'NULL'
        self.dept_day = 'NULL'
        self.real_class = 'NULL'
        self.stopid = 'NULL'
        self.stoptime = 'NULL'
        self.daydiff = 'NULL'
        self.dept_id = 'NULL'
        self.dest_id = 'NULL'
        self.change_rule = 'NULL'
        self.train_facilities = 'NULL'
        self.ticket_info = 'NULL'
        self.electric_ticket = 'NULL'
        self.promotion = 'NULL'
        self.others_info = 'NULL'
        self.change_rule = 'NULL'
        self.facilities = 'NULL'
        self.ticket_type = 'NULL'
        self.rest = -1

    def to_tuple(self):
        return (self.train_no, self.train_type,
                self.train_corp, self.dept_city, self.dept_id,
                self.dest_city, self.dest_id, self.dept_day,
                self.dept_time, self.dest_time, self.dur,
                self.price, self.tax, self.currency, self.seat_type,
                self.real_class, self.promotion, self.source,
                self.return_rule, self.change_rule, self.stopid,
                self.stoptime, self.daydiff, self.stop,
                self.train_facilities, self.ticket_type,
                self.electric_ticket, self.others_info, self.rest)

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class EachTrain:
    def __init__(self):
        self.train_key = 'NULL'
        self.train_no = 'NULL'
        self.train_corp = 'NULL'
        self.train_type = 'NULL'
        self.dept_station = 'NULL'
        self.dest_station = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))

        return results


class Car:
    def __init__(self):
        self.source = 'NULL'
        self.company = 'NULL'
        self.car_type = 'NULL'
        self.car_desc = 'NULL'
        self.car_image = 'NULL'
        self.price = -1.0
        self.list_price = -1.0
        self.rest = -1
        self.currency = 'NULL'
        self.rent_city = 'NULL'
        self.return_city = 'NULL'
        self.rent_store = 'NULL'
        self.return_store = 'NULL'
        self.rent_time = 'NULL'
        self.return_time = 'NULL'
        self.store_name = 'NULL'
        self.store_addr = 'NULL'
        self.return_store_name = 'NULL'
        self.return_store_addr = 'NULL'
        self.take_time = 'NULL'
        self.return_time = 'NULL'
        self.rent_time = 'NULL'
        self.rent_area = 'NULL'
        self.return_area = 'NULL'
        self.is_automatic = 'NULL'
        self.baggages = 'NULL'
        self.passengers = -1
        self.pay_method = 'NULL'
        self.insurance = 'NULL'
        self.fuel_strategy = 'NULL'
        self.promotion = 'NULL'
        self.license = 'NULL'
        self.diff_location_fee = -1.0
        self.door_num = -1
        self.mile_limit = 'NULL'
        self.extra_driver = 'NULL'
        self.zone_desc = 'NULL'
        self.package = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode("UTF-8")))
        return results


class CarStore:
    def __init__(self):
        self.store_id = 'NULL'
        self.company = 'NULL'
        self.store_code = 'NULL'
        self.store_name = 'NULL'
        self.open_time = 'NULL'
        self.close_time = 'NULL'
        self.address = 'NULL'
        self.area = 'NULL'
        self.area_code = 'NULL'
        self.telephone = 'NULL'
        self.map_info = 'NULL'
        self.city_id = 'NULL'

    def items(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Bus:
    def __init__(self):
        self.dept_city = 'NULL'
        self.dest_city = 'NULL'
        self.dept_station = 'NULL'
        self.dest_station = 'NULL'
        self.dept_day = 'NULL'
        self.dept_time = 'NULL'
        self.dest_time = 'NULL'
        self.dur = -1
        self.price = -1.0
        self.currency = 'NULL'
        self.source = 'NULL'
        self.corp = 'NULL'
        self.tax = -1.0
        self.return_rule = 'NULL'
        self.daydiff = 'NULL'
        self.rest = -1
        self.change_rule = 'NULL'
        self.ticket_type = 'NULL'
        self.bus_type = 'NULL'
        self.insurance = -1.0
        self.service_fee = -1.0
        self.stop = -1
        self.bus_no = 'NULL'
        self.stop_id = 'NULL'
        self.stop_time = 'NULL'
        self.transfer_interval = 'NULL'
        self.has_wifi = 'NULL'
        self.has_charge = 'NULL'
        self.has_extended_seat = 'NULL'
        self.free_baggage_num = 'NULL'
        self.free_baggage_weight = 'NULL'
        self.has_meals = 'NULL'
        self.has_wc = 'NULL'
        self.arrive_gate = 'NULL'

    def item(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class Pickup:
    def __init__(self):
        self.source = 'NULL'
        self.pattren_type = 'NULL'
        self.airport_code = 'NULL'

        self.dept_addr = 'NULL'
        self.dept_lat = 'NULL'
        self.dept_lng = 'NULL'
        self.dest_addr = 'NULL'
        self.dest_lat = 'NULL'
        self.dest_lng = 'NULL'

        self.use_time = 'NULL'

        self.car_type_id = 'NULL'
        self.car_title = 'NULL'
        self.car_desc = 'NULL'
        self.car_seat_num = -1
        self.car_luggage_num = -1

        self.price = -1.0
        self.currency = 'NULL'
        self.price_mark = 'NULL'

        self.is_support_card = 'NULL'
        self.card_fee = -1.0
        self.is_support_child_seat = 'NULL'
        self.child_seat_fee = -1.0
        self.is_has_car_wifi = 'NULL'
        self.car_wifi_fee = -1.0

        self.is_must_child_seat = 'NULL'
        self.is_support_chinese = 'NULL'

    def item(self):
        results = []
        for k, v in self.__dict__.items():
            results.append((k, str(v).decode('utf-8')))
        return results


class MFlight(object):

    def __init__(self):
        self.rest = -1
        self.price = -1
        self.tax = -1
        self.surcharge = -1
        self.promotion = 'NULL'
        self.currency = None
        self.legs = []

    def append_leg(self, leg):
        self.legs.append(leg)

    def to_flight(self):
        assert len(self.legs) == 1, '好像不是单程'
        leg = self.legs[0]
        flight = Flight()
        if not isinstance(leg, RoundFlightLeg):
            raise Exception('不支持这个类型')
        default_val = '_'.join(['NULL'] * leg.segment_count)

        flight.flight_no = leg.flight_no
        flight.plane_type = leg.plane_no
        flight.flight_corp = leg.airline
        flight.dept_id = leg.dept_id
        flight.dest_id = leg.dest_id
        flight.dept_day = leg.dept_day
        flight.dept_time = leg.dept_time
        flight.dest_time = leg.dest_time
        flight.dur = leg.dur
        # 没rest
        flight.price = self.price
        flight.tax = self.tax
        flight.surcharge = self.surcharge
        flight.promotion = self.promotion
        flight.currency = self.currency
        flight.seat_type = leg.seat_type
        flight.real_class = leg.real_class
        flight.stop_id = leg.stop_id
        flight.stop_time = leg.stop_time
        flight.daydiff = leg.day_diff
        flight.stop = leg.stop

        flight.source = flight.return_rule = flight.change_rule =\
        flight.share_flight = flight.package = flight.stopby =\
        flight.baggage = flight.transit_visa = flight.reimbursement=\
        flight.flight_meals = flight.ticket_type = flight.others_info = default_val
        return flight

    def to_round_flight(self):
        return convert_m_flight_to_roundflight(self)

    def to_multi_flight(self):
        return convert_m_flight_to_multiflight(self)

    
class MFlightLeg(object):

    def __init__(self):
        # 票价套餐，一般为廉价航空的 Basic Fare/ Excellence Fare 等
        self.package = None
        self.return_rule = None
        self.change_rule = None
        # 转机次数 varchar	NULL&NULL	Y	1件,每件23公斤&NULL
        # 经停 (类似中转，但是航班号相同)
        self.stopby = None
        # 托运行李规则托运行李规则
        self.baggage = None
        # varchar	NULL&NULL	Y	NULL&NULL	过境签
        self.transit_visa = None
        # varchar	NULL&NULL	Y	NULL&NULL	报销凭证
        self.reimbursement = None
        # varchar	NULL&NULL	Y	儿童票&NULL	票的类型 如果是成人票为默认值 NULL 如果为儿童票或老年票则为实际类型
        self.ticket_type = None
        self.others_info = None
        self._dur = -1
        self.segments = []
        self.source = None
        # string
        self.others_info = None

    def append_seg(self, seg):
        self.segments.append(seg)

    @property
    def stop(self):
        return len(self.segments) - 1

    @property
    def dur(self):
        return self._dur if self._dur != -1 else (self.segments[0].dest_date - self.segments[-1].dept_date).seconds

    @dur.setter
    def dur(self, value):
        self._dur = value


def datetime_to_str(date, FMT=FOR_FLIGHT_DATE):
    # datetime object, str ->   formated data string
    return date.strftime(FMT)


class RoundFlightLeg(MFlightLeg):
    '''
    this object represents a leg of a round trip or multi trip
    '''
    def __init__(self):
        super(RoundFlightLeg, self).__init__()

        self.segments = []
        # attribute for stash segment attribute
        self.flight_no_list = []
        self.airline_list = []
        self.plane_no_list = []
        self.dept_time_list = []
        self.dest_time_list = []
        self.seat_type_list = []
        self.real_class_list = []
        self.dept_airports = []
        self.dest_airports = []
        self.day_diff_list = []

    def append_seg(self, segment):
        self.segments.append(segment)
        # 把每个seg的数据加入到对应的list里面
        self.flight_no_list.append(segment.flight_no)
        self.airline_list.append(segment.flight_corp)
        self.plane_no_list.append(segment.plane_type)
        # datetime to str
        self.dept_time_list.append(datetime_to_str(segment.dept_date))
        self.dest_time_list.append(datetime_to_str(segment.dest_date))

        # set seat_type, real_class = seat_type
        self.seat_type_list.append(segment.seat_type)
        self.real_class_list.append(segment.real_class if segment.real_class else segment.seat_type)

        self.dept_airports.append(segment.dept_id)
        self.dest_airports.append(segment.dest_id)
        self.day_diff_list.append(segment.daydiff)

    @property
    def segment_count(self):
        return len(self.segments)

    @property
    def dept_id(self):
        if len(self.dept_airports) < 1:
            raise Exception('empty departure airport')
        return self.dept_airports[0]

    @property
    def dept_day(self):
        if len(self.segments) < 1:
            raise Exception('Empty Segment')
        return datetime_to_str(self.segments[0].dept_date, FOR_FLIGHT_DAY)

    @property
    def dest_day(self):
        if len(self.segments) < 1:
            raise Exception('Empty Segment')
        return datetime_to_str(self.segments[-1].dest_date, FOR_FLIGHT_DAY)
    @property
    def dest_id(self):
        if len(self.dest_airports) < 1:
            raise Exception('Empty arrival airport')
        return self.dest_airports[-1]

    @property
    def flight_no(self):
        return safe_join('_', self.flight_no_list)

    @property
    def airline(self):
        return safe_join('_', self.airline_list)

    @property
    def plane_no(self):
        return safe_join('_', self.plane_no_list)

    @property
    def dept_time(self):
        if len(self.dept_time_list) < 1:
            raise Exception('Empty departure time')
        return self.dept_time_list[0]

    @property
    def dest_time(self):
        if len(self.dest_time_list) < 1:
            raise Exception('Empty arrival time')
        return self.dest_time_list[-1]

    @property
    def seat_type(self):
        if len(self.seat_type_list) < 1:
            raise Exception('Empty seat type')
        return safe_join('_', self.seat_type_list)

    @property
    def real_class(self):
        return self.seat_type

    @property
    def stop_id(self):
        return safe_join('|', map(lambda x: x[0]+'_'+ x[1], zip(self.dept_airports, self.dest_airports)))

    @property
    def stop_time(self):
        return safe_join('|', map(lambda x: x[0]+'_'+x[1], zip(self.dept_time_list, self.dest_time_list)))

    @property
    def day_diff(self):
        return safe_join('_', self.day_diff_list)

    def set_cabin(self, cabin):
        for i in range(len(self.seat_type_list)):
            self.seat_type_list[i] = cabin


class MFlightSegment(object):

    def __init__(self):
        self.flight_no = None
        self.plane_type = None
        self.flight_corp = None
        self.dept_id = None
        self._dept_date = None
        self._dept_day = None
        self.dest_id = None
        self._dest_date = None
        self._dest_day = None
        self.seat_type = None
        self.real_class = None
        self.share_flight = None
        self.flight_meals = None

    @property
    def daydiff(self):
        return (self._dest_day - self._dept_day).days

    @property
    def dept_date(self):
        return self._dept_date

    @property
    def dest_date(self):
        return self._dest_date

    def set_dept_date(self, date_str, src_format):
        self._dept_date = datetime.datetime.strptime(date_str, src_format)
        self._dept_day = datetime.datetime.strptime(self._dept_date.strftime(FOR_FLIGHT_DAY), FOR_FLIGHT_DAY)

    def set_dest_date(self, date_str, src_format):
        self._dest_date = datetime.datetime.strptime(date_str, src_format)
        self._dest_day = datetime.datetime.strptime(self._dest_date.strftime(FOR_FLIGHT_DAY), FOR_FLIGHT_DAY)


def safe_value(src, default='NULL'):
    return src if src is not None else default


def safe_join(delimiter, elements, default='', none_default='NULL'):
    if not elements:
        return default
    for i in xrange(len(elements)):
        elements[i] = str(safe_value(elements[i], none_default))

    return delimiter.join(elements)


def convert_m_flight_to_multiflight(mflight):
    flight = MultiFlight()
    flight.rest = mflight.rest
    flight.price = mflight.price
    flight.tax = mflight.tax
    flight.surcharge = mflight.surcharge
    flight.promotion = mflight.promotion
    flight.currency = mflight.currency

    # todo 后续可以通过dict等方式优化代码结构, __setattr__ 等
    dept_segs = []
    dest_segs = []

    package = []
    return_rule = []
    change_rule = []
    stop = []
    stopby = []
    baggage = []
    transit_visa = []
    reimbursement = []
    ticket_type = []
    source = []
    dur = []
    others_info = []

    flight_no = []
    plane_type = []
    flight_corp = []
    seat_type = []
    real_class = []
    daydiff = []
    share_flight = []
    flight_meals = []

    stop_id = []
    stop_time = []

    for leg in mflight.legs:
        dept_segs.append(leg.segments[0])
        dest_segs.append(leg.segments[-1])

        package.append(leg.package)
        return_rule.append(leg.return_rule)
        change_rule.append(leg.change_rule)
        stop.append(leg.stop)
        stopby.append(leg.stopby)
        baggage.append(leg.baggage)
        transit_visa.append(leg.transit_visa)
        reimbursement.append(leg.reimbursement)
        ticket_type.append(leg.ticket_type)
        source.append(leg.source)
        dur.append(leg.dur)
        others_info.append(leg.others_info)

        leg_flight_no = []
        leg_plane_type = []
        leg_flight_corp = []
        leg_seat_type = []
        leg_real_class = []
        leg_daydiff = []
        leg_share_flight = []
        leg_flight_meals = []

        leg_stop_id = []
        leg_stop_time = []

        for seg in leg.segments:
            leg_flight_no.append(seg.flight_no)
            leg_plane_type.append(seg.plane_type)
            leg_flight_corp.append(seg.flight_corp)
            leg_seat_type.append(seg.seat_type)
            leg_real_class.append(seg.real_class)
            leg_daydiff.append(seg.daydiff)
            leg_share_flight.append(seg.share_flight)
            leg_flight_meals.append(seg.flight_meals)

            leg_stop_id.append(safe_join('_', [seg.dept_id, seg.dest_id]))
            leg_stop_time.append(safe_join('_', [seg.dept_date.strftime(FOR_FLIGHT_DATE), seg.dest_date.strftime(FOR_FLIGHT_DATE)]))

        flight_no.append(safe_join('_', leg_flight_no))
        flight_corp.append(safe_join('_', leg_flight_corp))
        plane_type.append(safe_join('_', leg_plane_type))
        seat_type.append(safe_join('_', leg_seat_type))
        real_class.append(safe_join('_', leg_real_class))
        daydiff.append(safe_join('_', leg_daydiff))
        share_flight.append(safe_join('_', leg_share_flight))
        flight_meals.append(safe_join('_', leg_flight_meals))

        stop_id.append(safe_join('|', leg_stop_id))
        stop_time.append(safe_join('|', leg_stop_time))

    flight.package = safe_join('&', package)
    flight.return_rule = safe_join('&', return_rule)
    flight.change_rule = safe_join('&', change_rule)
    flight.stop = safe_join('&', stop)
    flight.stopby = safe_join('&', stopby)
    flight.baggage = safe_join('&', baggage)
    flight.transit_visa = safe_join('&', transit_visa)
    flight.reimbursement = safe_join('&', reimbursement)
    flight.ticket_type = safe_join('&', ticket_type)
    flight.source = safe_join('::', source)
    flight.others_info = safe_join('&', others_info)

    flight.flight_no = safe_join('&', flight_no)
    flight.flight_corp = safe_join('&', flight_corp)
    flight.plane_type = safe_join('&', plane_type)
    flight.seat_type = safe_join('&', seat_type)
    flight.real_class = safe_join('&', real_class)
    flight.daydiff = safe_join('&', daydiff)
    flight.share_flight = safe_join('&', share_flight)
    flight.flight_meals = safe_join('&', flight_meals)

    flight.stop_id = safe_join('&', stop_id)
    flight.stop_time = safe_join('&', stop_time)

    flight.dept_id = safe_join('&', [s.dept_id for s in dept_segs])
    flight.dest_id = safe_join('&', [s.dest_id for s in dest_segs])
    flight.dept_day = safe_join('&', [s.dept_date.strftime(FOR_FLIGHT_DAY) for s in dept_segs])
    flight.dept_time = safe_join('&', [s.dept_date.strftime(FOR_FLIGHT_DATE) for s in dept_segs])
    flight.dest_time = safe_join('&', [s.dest_date.strftime(FOR_FLIGHT_DATE) for s in dept_segs])

    return flight


def convert_m_flight_to_roundflight(mflight):
    assert len(mflight.legs) == 2, "Wrong leg nums, len(leg) = %s" % len(mflight.legs)
    rf = RoundFlight()
    leg_outbound, leg_inbound = mflight.legs[0], mflight.legs[1]
    rf.dept_id = leg_outbound.dept_id
    rf.dest_id = leg_outbound.dest_id
    rf.dept_day = leg_outbound.dept_day
    rf.dest_day = leg_inbound.dept_day
    rf.rest = mflight.rest
    rf.price = mflight.price
    rf.tax = mflight.tax
    rf.surcharge = mflight.surcharge
    rf.promotion = mflight.promotion
    rf.currency = mflight.currency
    rf.source = safe_join("::", [leg_outbound.source, leg_inbound.source])
    rf.return_rule = safe_join("&", [leg_outbound.return_rule, leg_inbound.return_rule])

    rf.flight_no_A = leg_outbound.flight_no
    rf.flight_no_B = leg_inbound.flight_no
    rf.airline_A = leg_outbound.airline
    rf.airline_B = leg_inbound.airline
    rf.plane_no_A = leg_outbound.plane_no
    rf.plane_no_B = leg_inbound.plane_no
    rf.dept_time_A = leg_outbound.dept_time
    rf.dept_time_B = leg_inbound.dept_time
    rf.dest_time_A = leg_outbound.dest_time
    rf.dest_time_B = leg_inbound.dest_time
    rf.dur_A = leg_outbound.dur
    rf.dur_B = leg_inbound.dur
    rf.seat_type_A = leg_outbound.seat_type
    rf.seat_type_B = leg_inbound.seat_type
    rf.real_class_A = leg_outbound.seat_type
    rf.real_class_B = leg_inbound.seat_type
    rf.stop_id_A = leg_outbound.stop_id
    rf.stop_id_B = leg_inbound.stop_id
    rf.stop_A = leg_outbound.stop
    rf.stop_B = leg_inbound.stop
    rf.stop_time_A = leg_outbound.stop_time
    rf.stop_time_B = leg_inbound.stop_time
    rf.daydiff_A = leg_outbound.day_diff
    rf.daydiff_B = leg_inbound.day_diff

    return rf


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


if __name__ == '__main__':

    mflight = MFlight()
    leg = MFlightLeg()
    seg = MFlightSegment()
    seg.set_dept_date('2017-07-26T16:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-07-26T19:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)
    seg = MFlightSegment()
    seg.set_dept_date('2017-07-26T20:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-07-27T00:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)

    mflight.append_leg(leg)
    mflight.append_leg(leg)
    print convert_m_flight_to_multiflight(mflight).to_tuple()

    print leg.dur
    print seg.daydiff

    suggets_url = 'https://www.skyscanner.net/dataservices/geo/v2.0/autosuggest/UK/en-GB/{0}?' \
                  'isDestination=false&ccy=GBP&limit_taxonomy=City,Airport'
    print suggets_url