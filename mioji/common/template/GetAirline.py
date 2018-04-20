#!/usr/bin/env python
# coding:utf-8
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()
import re
from mioji.common.airline_common import *


class GetAirline(object):
    def __init__(self):
        pass

    def GetAirline(self, flight_no):

        Aircorp = ''
        if flight_no.find('NULL') > -1:
            nullnum = flight_no.count('NULL')
            linenum = flight_no.count('_')
            if nullnum > linenum:
                Aircorp = flight_no + '_'
            else:
                airline_list = flight_no.split('_')
                for every in airline_list:
                    if every.find('NULL') > -1:
                        Aircorp += 'NULL_'
                    else:
                        try:
                            Aircorp += Airline[every[:2]] + '_'
                        except Exception, e:
                            Aircorp += 'NULL_'
        else:
            airline_list = flight_no.split('_')
            for every in airline_list:
                if every.find('NULL') > -1:
                    Aircorp += 'NULL_'
                else:
                    try:
                        Aircorp += Airline[every[:2]] + '_'
                    except Exception, e:
                        Aircorp += 'NULL_'

        return Aircorp[:-1]


if __name__ == '__main__':
    get = GetAirline()
    try:
        re = get.GetAirline('SU205_SU2584')
    except Exception, e:
        print e.message
    print re
