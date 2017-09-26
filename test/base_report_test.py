#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/26 上午9:55
# @Author  : Hou Rong
# @Site    : 
# @File    : base_report_test.py
# @Software: PyCharm
import unittest
from proj.my_lib.BaseTask import get_tag, get_source, get_type, get_report_key


class TestGetReport(unittest.TestCase):
    def test_ok(self):
        task_name = 'list_attr_daodao_20170925a'
        self.assertTupleEqual(get_report_key(task_name), ('Attr', 'Daodao', '20170925a'))


if __name__ == '__main__':
    unittest.main()
