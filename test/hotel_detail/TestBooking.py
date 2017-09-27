#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午6:03
# @Author  : Hou Rong
# @Site    : 
# @File    : TestBooking.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.new_hotel_parser.booking_parser import booking_parser
from mioji.common.ufile_handler import download_file


def test_booking_parser(page):
    return booking_parser(page,
                          url='',
                          other_info={'source_id': 'test', 'city_id': 'test'}
                          )


class TestBooking(unittest.TestCase):
    def test_name(self):
        name_cases = ['b36a1e904c0cf44784e36f29f3eba11e']
        name_result = [('', 'Penzi\xc3\xb3n Rogalo')]
        for case, res in zip(name_cases, name_result):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_booking_parser(j_data['data'])
            self.assertTupleEqual((result.hotel_name, result.hotel_name_en), res)


if __name__ == '__main__':
    unittest.main()
