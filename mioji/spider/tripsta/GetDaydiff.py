#!/usr/bin/env python
# coding:utf-8

import sys
import time
import re
from mioji.common.airline_common import Airline
reload(sys)
sys.setdefaultencoding('utf-8')


class GetDaydiff(object):
    def __init__(self):
        pass

    def __calsecond(self, hms):

        dur = 0
        hms_list = hms.split(':')
        dur = int(hms_list[0]) * 3600 + int(hms_list[1]) * 60 + int(hms_list[2])

        return dur

    def GetDaydiff(self, time_list):

        daydiff = ''
        temp_list = time_list.split('|')

        for each in temp_list:

            each_list = each.split('_')
            each_list_0 = each_list[0].split('T')
            each_list_1 = each_list[1].split('T')
            if each_list_0[0] == each_list_1[0]:
                if self.__calsecond(each_list_0[1]) >= self.__calsecond(each_list_1[1]):
                    daydiff += '1_'
                else:
                    daydiff += '0_'
            else:
                daydiff += '1_'

        return daydiff[:-1]


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