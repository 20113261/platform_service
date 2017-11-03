#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/28 上午10:29
# @Author  : Hou Rong
# @Site    : 
# @File    : TestBrowser.py
# @Software: PyCharm
import unittest
from proj.my_lib.Common.Browser import MySession


class TestBrowser(unittest.TestCase):
    def test_running(self):
        try:
            with MySession() as session:
                session.get('http://www.baidu.com')
        except Exception:
            self.fail("Browser raised Exception")

    def test_exc(self):
        with self.assertRaises(Exception):
            with MySession() as session:
                session.get('https://www.google.com/generate_500')


if __name__ == '__main__':
    unittest.main()
