#!/usr/bin/python
# -*- coding: UTF-8 -*-
from mioji.common.mioji_struct import MFlightSegment, MFlightLeg, MFlight, convert_m_flight_to_miojilight
FOR_FLIGHT_DAY = '%Y-%m-%d'
FOR_FLIGHT_DATE = FOR_FLIGHT_DAY + 'T%H:%M:%S'
cabin = {'E':'经济舱','B':'商务舱','F':'头等舱','P':'超级经济舱'}

class Flight_moblie_parse(object):

    def parse_mo_flight(self, result, setype):
        result_flight = result['fltitem']
        all_ticket = []
        for flight in result_flight:
            mflight = MFlight(MFlight.OD_ONE_WAY)
            priceinfo = flight['policyinfo'][0]['priceinfo'][0]
            mflight.currency = 'CNY'
            mflight.source = 'ctrip::ctrip'
            mflight.surcharge = 0
            mflight.price = priceinfo['price']
            mflight.tax = priceinfo['tax']
            mflightleg = MFlightLeg()
            mflightleg.rest = priceinfo['ticket']
            for seg in flight['mutilstn']:
                mfseg = MFlightSegment()
                mfseg.flight_no = seg['basinfo']['flgno']
                mfseg.dept_id = seg['dportinfo']['aport']
                mfseg.dest_id = seg['aportinfo']['aport']
                mfseg.plane_type = seg['craftinfo']['craft']
                flight_corp = seg['basinfo']['airsname'].decode("unicode-escape")
                mfseg.flight_corp = flight_corp.encode('utf8')
                dept_date = seg['dateinfo']['ddate']
                dept_date = dept_date.replace(' ', 'T')
                dest_date = seg['dateinfo']['adate']
                dest_date = dest_date.replace(' ', 'T')
                mfseg.set_dept_date(dept_date, FOR_FLIGHT_DATE)
                mfseg.set_dest_date(dest_date, FOR_FLIGHT_DATE)
                mfseg.seat_type = cabin[setype]
                mfseg.real_class = cabin[setype]
                mflightleg.append_seg(mfseg)
            mflight.append_leg(mflightleg)
            all_ticket.append(mflight.convert_to_mioji_flight().to_tuple())
        return all_ticket


if __name__ == "__main__":
    fl = Flight_moblie_parse()

