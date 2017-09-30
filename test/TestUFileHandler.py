#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/30 下午5:39
# @Author  : Hou Rong
# @Site    : 
# @File    : TestUFileHandler.py
# @Software: PyCharm
import unittest
import zlib
import pickle
from proj.my_lib.Common.UFileHandler import get_ufile_and_info


class TestUfileHandler(unittest.TestCase):
    def test_download(self):
        case = ['service_platform_117c514806200f46c730f0a0d1bd1a02']
        results = [u'http://hotels.ctrip.com/international/6225236.html']
        for each, res in zip(case, results):
            result = get_ufile_and_info(each)
            if result:
                resp, file_info = result
                obj = pickle.loads(zlib.decompress(resp))
                self.assertEqual(obj.url, res)


if __name__ == '__main__':
    unittest.main()
