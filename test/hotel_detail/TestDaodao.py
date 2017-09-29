#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/29 下午8:49
# @Author  : Hou Rong
# @Site    : 
# @File    : TestDaodao.py
# @Software: PyCharm
import unittest
import json
from proj.my_lib.attr_parser import parse
from mioji.common.ufile_handler import download_file


def test_parser(page):
    return parse(page,
                 url='https://www.tripadvisor.cn/Attraction_Review-g1006203-d3529862-Reviews-Norsk_Skogmuseum-Elverum_Elverum_Municipality_Hedmark_Eastern_Norway.html',
                 city_id='',
                 debug=True
                 )


class TestDaodao(unittest.TestCase):
    def test_name(self):
        name_cases = ['299895401f7d7a3ee20a5bfe3bfebbc7']
        name_result = [(u'奥赛美术馆', "Musee d'Orsay")]
        for case, res in zip(name_cases, name_result):
            page = download_file(case)
            j_data = json.loads(page)
            result = test_parser(j_data['data'])
            self.assertTupleEqual((result['name'], result['name_en']), res)


if __name__ == '__main__':
    unittest.main()
