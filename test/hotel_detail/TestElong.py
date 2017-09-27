#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午8:21
# @Author  : Hou Rong
# @Site    : 
# @File    : TestElong.py
# @Software: PyCharm
# 342781aef5b8304572841c549e321d3e
import unittest
import json
from proj.my_lib.new_hotel_parser.elong_parser import elong_parser
from mioji.common.ufile_handler import download_file


def test_elong_parser(page):
    return elong_parser(page,
                        url='',
                        other_info={'source_id': 'test', 'city_id': 'test'}
                        )


class TestElong(unittest.TestCase):
    def test_name(self):
        cases = ['342781aef5b8304572841c549e321d3e']
        results = [('NULL', 'Torre Mar Galapagos')]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_elong_parser(j_data['data'])
            self.assertTupleEqual((result.hotel_name, result.hotel_name_en), res)

    def test_address(self):
        cases = ['342781aef5b8304572841c549e321d3e']
        results = ['San Cristobal y General Rodriguez Lara']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_elong_parser(j_data['data'])
            self.assertEqual(result.address, res)


if __name__ == '__main__':
    unittest.main()
