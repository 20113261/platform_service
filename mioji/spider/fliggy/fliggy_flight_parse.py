#coding=utf-8
import re
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_miojilight
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'经济舱','B':'商务舱','F':'头等舱','P':'超级经济舱'}

class Fliggy_flight_parse(object):
    def get_flight_items(self, result):
        flight_items = result['data']['flightItems']
        return flight_items

    def get_nonzero_no(self, flight_no, time):
        if time == 'second_request':
            flight_no = re.sub(r'([a-zA-Z]*)(0*)([1-9]*)(\d*)', r'\1\3\4', flight_no)
        return flight_no

    def parse_one_way(self, result, setype):
        all_ticket = []
        flight_items = self.get_flight_items(result)
        for flight in flight_items:
            mflight = MFlight(MFlight.OD_ONE_WAY)
            self.process_mflight(mflight, flight, setype, 'second_request')
            all_ticket.append(mflight.convert_to_mioji_flight().to_tuple())
        return all_ticket

    def parse_multi_flight(self, result, setype, mflight, way_type):
        all_ticket = []
        flight_items = result['data']['flightItems']
        flight_legs = []
        for leg in mflight.legs:
            flight_legs.append(leg)

        for flight in flight_items:
            next_mflight = MFlight(way_type)
            next_mflight.legs.extend(flight_legs)
            # print len(next_mflight.legs)
            self.process_mflight(next_mflight, flight, setype, 'second_request')
            # print 'next_mflight', len(next_mflight.legs)
            # for leg in next_mflight.legs:
            #     for seg in leg.segments:
            #         print seg.flight_no, seg.dept_id
            all_ticket.append(next_mflight.convert_to_mioji_flight().to_tuple())
        return all_ticket

    def parse_flight_no_dt(self, result, setype, flight_no_list):
        flight_location = 0
        flight_items = result['data']['flightItems']
        # print 'flight_no_list', flight_no_list, '-'*10
        for flight in flight_items:
            mflight = MFlight(MFlight.OD_ONE_WAY)
            self.process_mflight(mflight, flight, setype, 'first_request')
            flight_operating_no = []
            flight_numbers = []
            flight_no_compare_list = []
            for leg in mflight.legs:
                for seg in leg.segments:
                    flight_numbers.append(seg.flight_no)
                    non_zero_no = self.get_nonzero_no(seg.flight_no, 'second_request')
                    flight_no_compare_list.append(non_zero_no)
            # print 'flight_numbers', flight_numbers, '-'*10
            # print 'flight_no_compare_list', flight_no_compare_list, '-'*10
            exist = True
            for number in flight_no_list:
                print number, number in flight_no_compare_list
                if number not in flight_no_compare_list:
                    exist = False
            if exist:
                break
        if exist:
            dept_date = []
            for leg in mflight.legs:
                for seg in leg.segments:
                    dept_date.append(seg.dept_date)
                    seg.flight_no = self.get_nonzero_no(seg.flight_no, 'second_request')
                    flight_operating_no.append(seg.share_flight)
            flight_location = flight_items.index(flight)
        else:
            flight = flight_items[flight_location]
            mflight = MFlight(MFlight.OD_ONE_WAY)
            self.process_mflight(mflight, flight, setype, 'first_request')
            flight_numbers = []
            dept_date = []
            for leg in mflight.legs:
                for seg in leg.segments:
                    flight_numbers.append(seg.flight_no)
                    dept_date.append(seg.dept_date)
                    seg.flight_no = self.get_nonzero_no(seg.flight_no, 'second_request')
                    flight_operating_no.append(seg.share_flight)
        # print 'flight_location', flight_location
        return mflight, flight_numbers, flight_operating_no, dept_date

    def process_mflight(self, mflight, flight, setype, time):
        mflight.price = float(flight['cardAdultPrice']) / 100
        mflight.tax = float(flight['cardAdultTax']) / 100
        mflight.currency = 'CNY'
        mflight.source = 'fliggy'
        mflight.stopby = setype

        mflightleg = MFlightLeg()
        mflightleg.rest = flight.get('quantity', '')  # 单程和联程和往返的rest都在flightItems下提取quantity
        # 单程
        assert len(flight['flightInfo']) == 1
        flight_info = flight['flightInfo'][0]
        for seg in flight_info['flightSegments']:
            mfseg = MFlightSegment()
            flight_no = seg.get('marketingFlightNo', '')
            mfseg.flight_no = self.get_nonzero_no(flight_no, time)
            # mfseg.flight_no = re.sub(r'([a-zA-Z]*)(0*)([1-9]*)(\d*)', r'\1\3\4', flight_no)
            mfseg.dept_id = seg.get('depAirportCode', '')
            mfseg.dest_id = seg.get('arrAirportCode', '')
            mfseg.plane_type = seg.get('equipTypeCode', '')
            mfseg.flight_corp = str(seg.get('marketingAirlineCode', ''))
            mfseg.share_flight = seg.get('operatingFlightNo', '')
            dept_date = seg['depTimeStr']
            dept_date = dept_date.replace(' ', 'T')
            dest_date = seg['arrTimeStr']
            dest_date = dest_date.replace(' ', 'T')
            mfseg.set_dept_date(dept_date, FOR_FLIGHT_DATE)
            mfseg.set_dest_date(dest_date, FOR_FLIGHT_DATE)
            mfseg.seat_type = flight_info.get('cabinClassName', "经济舱")
            mfseg.real_class = flight_info.get('cabinClassName', "经济舱")
            mflightleg.append_seg(mfseg)
        mflight.append_leg(mflightleg)

    def parse_round_first(self, result, setype):
        first_flights = []
        flight_items = self.get_flight_items(result)
        for flight in flight_items:
            mflight = MFlight(MFlight.OD_ROUND)
            self.process_mflight(mflight, flight, setype, 'second_request')
            first_flights.append(mflight)
        return first_flights

    def parse_multi_first(self, result, setype):
        first_flights = []
        flight_items = self.get_flight_items(result)
        for flight in flight_items:
            mflight = MFlight(MFlight.OD_MULTI)
            self.process_mflight(mflight, flight, setype, 'second_request')
            first_flights.append(mflight)
        return first_flights



