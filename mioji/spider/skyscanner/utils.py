#!/usr/bin/python
# -*- coding: UTF-8 -*-

from mioji.common.class_common import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_multiflight
from mioji.common.class_common import RoundFlightLeg, convert_m_flight_to_roundflight
import urlparse

SRC_FORMAT = '%Y-%m-%dT%H:%M:%S'

# E经济舱、B商务舱、F头等舱、P超级经济舱
query_cabin_dict = {'E': 'economy', 'B': 'business', 'F': 'first', 'P': 'premiumeconomy'}


def seat_type_to_queryparam(seat_type):
    return query_cabin_dict.get(seat_type, 'economy')


def todict(src_list):
    d = {}
    for item in src_list:
        d[item['id']] = item
    return d


class FlightParser(object):  # for multiflight

    def __init__(self, result, task):
        self.query_cabin = task.ticket_info.get('v_seat_type', 'E')

        query_node = result['query']
        self.adults = query_node['adults']
        self.currency = query_node['currency'].encode('utf-8')

        self.legs = todict(result['legs'])
        self.segments = todict(result['segments'])
        self.carriers = todict(result['carriers'])
        self.places = todict(result['places'])
        self.itineraries = result['itineraries']

    def parse(self):
        flight_list = []
        for each_itinerarie in self.itineraries:
            leg_ids = each_itinerarie['leg_ids']
            mflight = MFlight()
            mflight.tax = -1
            # todo
            # mflight.rest
            # mflight.surcharge
            # mflight.promotion

            for leg_id in leg_ids:
                try:
                    mflight.append_leg(self.parse_leg(leg_id))
                except:
                    continue

            for price_op in each_itinerarie['pricing_options']:
                p_items = price_op.get('items', [])
                if p_items:
                    cabin = urlparse.parse_qs(p_items[0]['url'])['cabin_class'][0]
                    for leg in mflight.legs:
                        for seg in leg.segments:
                            seg.seat_type = cabin.lower().replace('_', '')
                            new_seat_type = cabin.lower().replace('_','')
                            for k, v in query_cabin_dict.items():
                                new_seat_type.replace(v, k)
                            seg.seat_type = new_seat_type

                mflight.currency = self.currency
                mflight.price = price_op['price']['amount'] / self.adults
                #print "mflight.price:",mflight.price,type(mflight.price)
                flight_list.append(convert_m_flight_to_multiflight(mflight).to_tuple())
        return flight_list

    def parse_leg(self, leg_id):
        leg_node = self.legs[leg_id]
        leg = MFlightLeg()
        leg.dur = leg_node['duration'] * 60
        leg.source = 'skyscanner'
        # todo
        # leg.return_rule
        # leg.change_rule
        # leg.ticket_type
        # leg.reimbursement

        for seg_id in leg_node['segment_ids']:
            leg.append_seg(self.parse_segment(seg_id))

        return leg

    def parse_segment(self, seg_id):
        seg_node = self.segments[seg_id]
        seg = MFlightSegment()

        carrier = self.carriers[seg_node['marketing_carrier_id']]
        seg.flight_no = carrier['display_code'] + seg_node['marketing_flight_number']
        seg.flight_corp = carrier['name']
        seg.set_dept_date(seg_node['departure'], SRC_FORMAT)
        seg.set_dest_date(seg_node['arrival'], SRC_FORMAT)

        from_node = self.places[seg_node['origin_place_id']]
        to_node = self.places[seg_node['destination_place_id']]

        seg.dept_id = from_node['alt_id']
        seg.dest_id = to_node['alt_id']

        seg.seat_type = self.query_cabin

        # todo
        # seg.plane_type
        # seg.real_class
        # seg.flight_meals
        # seg.flight_meals

        return seg


class RoundFlightParser(FlightParser):
    def parse_leg(self, leg_id):
        leg_node = self.legs[leg_id]
        leg = RoundFlightLeg()
        leg.dur = leg_node['duration'] * 60
        leg.source = 'skyscanner'
        # todo
        # leg.return_rule
        # leg.change_rule
        # leg.ticket_type
        # leg.reimbursement

        for seg_id in leg_node['segment_ids']:
            leg.append_seg(self.parse_segment(seg_id))
        return leg

    def parse(self):
        itineraries_list = []
        for itinerary in self.itineraries:
            leg_ids = itinerary['leg_ids']
            mflight = MFlight()
            mflight.tax = -1
            # todo
            # mflight.rest
            # mflight.surcharge
            # mflight.promotion

            try:
                for leg_id in leg_ids:
                    mflight.append_leg(self.parse_leg(leg_id))
            except:
                continue

            for price_op in itinerary['pricing_options']:
                p_items = price_op.get('items', [])
                if p_items:
                    cabin = urlparse.parse_qs(p_items[0]['url'])['cabin_class'][0]
                    for leg in mflight.legs:
                        leg.set_cabin(cabin.replace('_',''))

                mflight.currency = self.currency
                try:
                    mflight.price = price_op['price']['amount'] / self.adults
                except:  # 不带价格的不要
                    continue

                try:
                    itineraries_list.append(convert_m_flight_to_roundflight(mflight).to_tuple())
                except:
                    print 'parse error', itinerary['id'], itinerary['leg_ids']
        return itineraries_list


if __name__ == '__main__':
    import json
    from mioji.common.task_info import Task

    task = Task()
    with open('data') as fp:
        resp = json.load(fp)
        parse_obj = RoundFlightParser(resp, task)
        parse_obj.parse()
