#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/29 下午8:49
# @Author  : Hou Rong
# @Site    : 
# @File    : TestDaodaoAttr.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.rest_parser import parse
from mioji.common.ufile_handler import download_file


def test_parser(page):
    return parse(page,
                 url='https://www.tripadvisor.cn/Attraction_Review-g1006203-d3529862-Reviews-Norsk_Skogmuseum-Elverum_Elverum_Municipality_Hedmark_Eastern_Norway.html',
                 city_id='',
                 debug=True
                 )


class TestDaodaoRest(unittest.TestCase):
    def test_name(self):
        name_cases = ['3f9b04594307a160e800dfdbe21b1c30']
        name_result = [('', 'The Coffee Club - Jungceylon')]
        for case, res in zip(name_cases, name_result):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_parser(j_data['data'])
            self.assertTupleEqual((result['name'], result['name_en']), res)

    def test_ranking(self):
        name_cases = ['3f9b04594307a160e800dfdbe21b1c30']
        name_result = ['33']
        for case, res in zip(name_cases, name_result):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_parser(j_data['data'])
            self.assertEqual(result['ranking'], res)


if __name__ == '__main__':
    unittest.main()
