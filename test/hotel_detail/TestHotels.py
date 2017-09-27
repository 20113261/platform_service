#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午8:31
# @Author  : Hou Rong
# @Site    : 
# @File    : TestHotels.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.new_hotel_parser.hotels_parser import hotels_parser
from mioji.common.ufile_handler import download_file


def test_hotels_parser(page):
    return hotels_parser(page,
                         url='',
                         other_info={'source_id': 'test', 'city_id': 'test'}
                         )


class TestHotels(unittest.TestCase):
    def test_name(self):
        cases = ['83ba683f30f00298c4808a0b7b79bcc6', '2d46474aa51e51ca70e134e17d9efcbc',
                 '8d3b32c6f9b824466344e600958c3684', 'a042d06f6147dd44c38fc24e4f0d266e']
        results = [('NULL', 'Appartement au complexe marina golf'), ('巴達霍斯中心酒店', 'Hotel Badajoz Center'),
                   ('NULL', 'Isa Lei Glampsite'), ('cApVerb 酒店', 'CapVerb')]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_hotels_parser(j_data['data'])
            self.assertTupleEqual((result.hotel_name, result.hotel_name_en), res)

    def test_desc(self):
        cases = ['83ba683f30f00298c4808a0b7b79bcc6', '2d46474aa51e51ca70e134e17d9efcbc',
                 '8d3b32c6f9b824466344e600958c3684', 'a042d06f6147dd44c38fc24e4f0d266e']

        results = [u'艾西拉的公寓，設有廚房和露台', u'4 星酒店，設有室外泳池，鄰近巴達霍斯大教堂',
                   u'海濱酒店，位於馬塔薩瓦島，設有餐廳、酒吧/酒廊', u'基耶斯特的山區公寓，設有露台']

        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_hotels_parser(j_data['data'])
            self.assertEqual(result.description, res)


if __name__ == '__main__':
    unittest.main()
