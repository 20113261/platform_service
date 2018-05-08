#!/usr/bin/env python
# coding:utf-8
from mioji.common.utils import setdefaultencoding_utf8

setdefaultencoding_utf8()


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


if __name__ == '__main__':
    getdur = GetDaydiff()
    res = getdur.GetDaydiff(
        '2015-06-25T00:30:00_2015-06-25T06:25:00|2015-06-26T02:10:00_2015-06-26T06:35:00|2015-06-26T19:25:00_2015-06-26T20:10:00')
    print res
