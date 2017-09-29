#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 下午8:31
# @Author  : Hou Rong
# @Site    : 
# @File    : TestHotels.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.new_hotel_parser.agoda_parser import agoda_parser
from mioji.common.ufile_handler import download_file


def test_agoda_parser(page):
    return agoda_parser(page,
                        url='',
                        other_info={'source_id': 'test', 'city_id': 'test'}
                        )


class TestAgoda(unittest.TestCase):
    def test_img(self):
        cases = ['c7c953f5f9e393306412dfb3e0e06a3b']
        results = ['http://aff.bstatic.com/images/hotel/840x460/991/99181998.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100565919.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100549525.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100550550.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100566312.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100566039.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100551886.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100551968.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100550859.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100550005.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100549700.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100551104.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100552101.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100549524.jpg|http://aff.bstatic.com/images/hotel/840x460/991/99181990.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100038760.jpg|http://aff.bstatic.com/images/hotel/840x460/991/99182001.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100046019.jpg|http://aff.bstatic.com/images/hotel/840x460/991/99181993.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100549524.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100551104.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100550859.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100550859.jpg|http://aff.bstatic.com/images/hotel/840x460/100/100551968.jpg']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_agoda_parser(j_data['data'])
            self.assertEqual(result.img_items, res)

    def test_check_IN_OUT(self):
        cases = ['64a59248435c4906180887a3c33c00bc']
        results = [('14:00','12:00')]
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_agoda_parser(j_data['data'])
            self.assertEqual((result.check_in_time,result.check_out_time), res)

    def test_service(self):
        cases = ['e0238c984978dfb51c0339e12db88c6e',]
        results = [u'冰箱|厨具|电风扇|电视|隔音设施|唤醒服务|咖啡/茶冲泡器具|淋浴设施|小厨房|休息区|阳台/露台']
        for case, res in zip(cases, results):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_agoda_pagit(j_data['data'])
            self.assertEqual(result.service, res)

            # def test_desc(self):
            #     cases = ['83ba683f30f00298c4808a0b7b79bcc6', '2d46474aa51e51ca70e134e17d9efcbc',
            #              '8d3b32c6f9b824466344e600958c3684', 'a042d06f6147dd44c38fc24e4f0d266e']
            #
            #     results = [u'艾西拉的公寓，設有廚房和露台', u'4 星酒店，設有室外泳池，鄰近巴達霍斯大教堂',
            #                u'海濱酒店，位於馬塔薩瓦島，設有餐廳、酒吧/酒廊', u'基耶斯特的山區公寓，設有露台']
            #
            #     for case, res in zip(cases, results):
            #         page = download_file(case)
            #         j_data = json.loads(page)
            #         result = test_hotels_parser(j_data['data'])
            #         self.assertEqual(result.description, res)


if __name__ == '__main__':
    unittest.main()
