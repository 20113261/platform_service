#!/usr/bin/env python
# coding=UTF8
'''
正常思维的结构体
'''

import sys, datetime, class_common

FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'


class MFlight(object):
    # 单程
    OD_ONE_WAY = 1
    # 联程
    OD_MULTI = 2
    # 往返
    OD_ROUND = 3
    """
    结构：
      leg(OD) - list, 单程、往返程、缺口程,中的一程
        segment  - list, 航段，经停、中转中的一段
    适用现有的飞机类型：单程、联程、往返
    """

    def __init__(self, od_type):
        """
        :param od_type: MFlight.OD_ONE_WAY, MFlight.OD_MULTI, MFlight.OD_ROUND
        """
        '''必填字段'''
        self.price = -1
        self.tax = -1
        self.currency = None
        self.source = None
        # 请求的舱位等级 E|P|B|F
        self.stopby = None
        self.legs = []
        self.od_type = od_type
        '''选填字段'''

        self.surcharge = -1
        self.package = None

    @property
    def rest(self):
        return min([leg.rest for leg in self.legs])

    def append_leg(self, leg):
        self.legs.append(leg)

    def convert_to_mioji_flight(self):
        if self.od_type == MFlight.OD_ROUND:
            return convert_m_flight_to_roundflight(self)
        else:
            return convert_m_flight_to_miojilight(self)


class MFlightLeg(object):
    """
    leg(OD):单程、联程、
    """

    def __init__(self):
        # 必填字段
        self.segments = []
        # 选填字段
        self.rest = -1
        self.ticket_type = None  # varchar   NULL&NULL   Y   儿童票&NULL    票的类型 如果是成人票为默认值 NULL 如果为儿童票或老年票则为实际类型
        self.baggage = None  # 托运行李规则托运行李规则
        self.return_rule = None
        self.change_rule = None
        self.others_info = None

    def append_seg(self, seg):
        self.segments.append(seg)

    @property
    def stop(self):
        return len(self.segments) - 1


class MFlightSegment(object):
    def __init__(self):
        # 必填字段
        self.flight_no = None  # MU3800
        self.dept_id = None
        self.dest_id = None
        self.seat_type = None
        # 辅助变量
        self._dept_date = None  # 输出 dept_day detp_time
        self._dest_date = None
        # 选填字段
        self.plane_type = None
        self.flight_corp = None
        self.real_class = None
        self.share_flight = None

    @property
    def dept_date(self):
        return self._dept_date

    @property
    def dest_date(self):
        return self._dest_date

    def set_dept_date(self, date_str, src_format):
        """
        :param date_str: 时间字符串 
        :param src_format: 时间格式
        :return: 
        """
        self._dept_date = datetime.datetime.strptime(date_str, src_format)

    def set_dest_date(self, date_str, src_format):
        self._dest_date = datetime.datetime.strptime(date_str, src_format)


# utils
def safe_value(src, default='NULL'):
    return src if src is not None else default


def safe_join(delimiter, elements, default='', none_default='NULL'):
    if not elements:
        return default
    for i in xrange(len(elements)):
        elements[i] = str(safe_value(elements[i], none_default))

    return delimiter.join(elements)


def convert_m_flight_to_miojilight(mflight):
    """
    结构飞机票，转换mioji单程、联程
      ps:单程 为 联程中的 len(legs) == 1,输出结果也一样
    :param mflight: 
    :return: 
    """
    flight = class_common.MultiFlight()
    flight.rest = mflight.rest
    flight.price = mflight.price
    flight.tax = mflight.tax
    flight.surcharge = mflight.surcharge
    flight.promotion = 'NULL'
    flight.currency = mflight.currency
    flight.stopby = mflight.stopby

    # todo 后续可以通过dict等方式优化代码结构, __setattr__ 等
    dept_segs = []
    dest_segs = []

    package = []
    return_rule = []
    change_rule = []
    stop = []
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

        package.append(None)
        return_rule.append(leg.return_rule)
        change_rule.append(leg.change_rule)
        stop.append(leg.stop)
        baggage.append(leg.baggage)
        transit_visa.append(None)
        reimbursement.append(None)
        ticket_type.append(leg.ticket_type)
        source.append(mflight.source)
        dur.append(None)
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
            leg_daydiff.append(0)
            leg_share_flight.append(seg.share_flight)
            leg_flight_meals.append(None)

            leg_stop_id.append(safe_join('_', [seg.dept_id, seg.dest_id]))
            leg_stop_time.append(
                safe_join('_', [seg.dept_date.strftime(FOR_FLIGHT_DATE), seg.dest_date.strftime(FOR_FLIGHT_DATE)]))

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
    flight.baggage = safe_join('&', baggage)
    flight.transit_visa = safe_join('&', transit_visa)
    flight.reimbursement = safe_join('&', reimbursement)
    flight.ticket_type = safe_join('&', ticket_type)
    flight.source = safe_join('::', source)
    flight.others_info = safe_join('&', others_info)
    flight.dur = safe_join('&', dur)
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

    flight.dept_day = safe_join('&', [s.dept_date.strftime(FOR_FLIGHT_DAY) for s in dept_segs])

    flight.dept_id = safe_join('&', [s.dept_id for s in dept_segs])
    flight.dept_time = safe_join('&', [s.dept_date.strftime(FOR_FLIGHT_DATE) for s in dept_segs])

    flight.dest_id = safe_join('&', [s.dest_id for s in dest_segs])
    flight.dest_time = safe_join('&', [s.dest_date.strftime(FOR_FLIGHT_DATE) for s in dest_segs])

    return flight


def convert_m_flight_to_roundflight(mflight):
    """
    结构化飞机票，转换往返
    :param mflight: 
    :return: 
    """
    assert len(mflight.legs) == 2, "Wrong leg nums, len(leg) = %s" % len(mflight.legs)
    rf = class_common.RoundFlight()
    leg_outbound, leg_inbound = mflight.legs[0], mflight.legs[1]

    out_dept_seg = leg_outbound.segments[0]
    out_dest_seg = leg_outbound.segments[-1]
    in_dept_seg = leg_inbound.segments[0]
    in_dest_seg = leg_inbound.segments[-1]

    rf.dept_id = out_dept_seg.dept_id
    rf.dest_id = out_dest_seg.dest_id
    rf.dept_day = out_dept_seg.dept_date.strftime(FOR_FLIGHT_DAY)
    rf.dest_day = in_dept_seg.dept_date.strftime(FOR_FLIGHT_DAY)
    rf.rest = mflight.rest
    rf.price = mflight.price
    rf.tax = mflight.tax
    rf.surcharge = mflight.surcharge
    rf.promotion = 'NULL'
    rf.currency = mflight.currency
    rf.source = safe_join("::", [mflight.source, mflight.source])
    rf.return_rule = safe_join("&", [leg_outbound.return_rule, leg_inbound.return_rule])
    if mflight.source == 'hnair':
        rf.others_info = leg_outbound.others_info
    else:
        rf.others_info = safe_join("&", [leg_outbound.others_info, leg_inbound.others_info])

    def leg_join(leg):
        _flight_no = []
        _airline = []
        _plane_no = []
        _seat_type = []
        _real_class = []
        _stop_id = []
        _stop_time = []
        _daydiff = []
        for seg in leg.segments:
            _flight_no.append(seg.flight_no)
            _airline.append(seg.flight_corp)
            _plane_no.append(seg.plane_type)
            _seat_type.append(seg.seat_type)
            _real_class.append(seg.real_class)
            _stop_id.append(safe_join('_', [seg.dept_id, seg.dest_id]))
            _stop_time.append(safe_join('_', [seg.dept_date.strftime(FOR_FLIGHT_DATE),
                                              seg.dest_date.strftime(FOR_FLIGHT_DATE)]))
            _daydiff.append(0)
        a = [safe_join('_', _flight_no), safe_join('_', _airline), safe_join('_', _plane_no),
             safe_join('_', _seat_type), safe_join('_', _real_class), safe_join('|', _stop_id),
             safe_join('|', _stop_time), safe_join('_', _daydiff)]
        return a

    rf.flight_no_A, rf.airline_A, rf.plane_no_A, rf.seat_type_A, \
    rf.real_class_A, rf.stop_id_A, rf.stop_time_A, rf.daydiff_A = leg_join(leg_outbound)

    rf.flight_no_B, rf.airline_B, rf.plane_no_B, rf.seat_type_B, \
    rf.real_class_B, rf.stop_id_B, rf.stop_time_B, rf.daydiff_B = leg_join(leg_inbound)

    rf.dept_time_A = out_dept_seg.dept_date.strftime(FOR_FLIGHT_DATE)
    rf.dept_time_B = in_dept_seg.dept_date.strftime(FOR_FLIGHT_DATE)

    rf.dest_time_A = out_dest_seg.dest_date.strftime(FOR_FLIGHT_DATE)
    rf.dest_time_B = in_dest_seg.dest_date.strftime(FOR_FLIGHT_DATE)

    rf.dur_A = -1
    rf.dur_B = -1

    return rf


class HotelList:
    def __init__(self):
        self.qid = "NULL"
        self.source = "NULL"
        self.req_info = ""
        self.hotel_info_list = []
        self.page_num = ""

    def append_hotel_info_to_list(self, HotelListSegment):
        self.hotel_info_list.append({
            "hotel_name": HotelListSegment.hotel_name,
            "hotel_id": HotelListSegment.hotel_id,
            "price": float(HotelListSegment.price),
            "ccy": HotelListSegment.ccy,
            'hotel_url': HotelListSegment.hotel_url,
        })

    def return_hotel_info_all(self):
        return {
            "qid": self.qid,
            "source": self.source,
            "req_info": self.req_info,
            "hotel_list": self.hotel_info_list,
            "page_num": self.page_num
        }


class HotelListSegment:
    def __init__(self):
        self.hotel_name = "NULL"
        self.hotel_id = "NULL"
        self.price = -1
        self.ccy = "NULL"
        self.hotel_url = 'NULL'

if __name__ == '__main__':
    mflight = MFlight(MFlight.OD_MULTI)
    leg = MFlightLeg()
    seg = MFlightSegment()
    seg.set_dept_date('2017-07-26T16:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-07-27T19:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)
    seg = MFlightSegment()
    seg.set_dept_date('2017-07-28T20:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-07-29T00:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)

    print leg.segments[-1].dest_date
    mflight.append_leg(leg)

    leg = MFlightLeg()
    seg = MFlightSegment()
    seg.set_dept_date('2017-07-30T16:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-08-01T19:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)
    seg = MFlightSegment()
    seg.set_dept_date('2017-08-02T20:00:00', FOR_FLIGHT_DATE)
    seg.set_dest_date('2017-08-03T00:02:00', FOR_FLIGHT_DATE)
    leg.append_seg(seg)

    mflight.append_leg(leg)
    print mflight.convert_to_mioji_flight().to_tuple()

    suggets_url = 'https://www.skyscanner.net/dataservices/geo/v2.0/autosuggest/UK/en-GB/{0}?' \
                  'isDestination=false&ccy=GBP&limit_taxonomy=City,Airport'
    print suggets_url
