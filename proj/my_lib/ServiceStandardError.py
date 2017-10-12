#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午9:55
# @Author  : Hou Rong
# @Site    : 
# @File    : ServiceStandardError.py
# @Software: PyCharm
import unittest


class ServiceStandardError(Exception):
    def __init__(self, error_code=103, msg="未返回错误码", *args, **kwargs):
        self.error_code = error_code
        self.msg = msg

        if 'wrapped_exception' in kwargs:
            self.wrapped_exception = kwargs['wrapped_exception']


class TypeCheckError(ServiceStandardError):
    def __init__(self, *args, **kwargs):
        msg = None
        if args:
            if isinstance(args[0], (str, unicode)):
                msg = args[0]

        if not msg:
            msg = '关键字段被过滤'

        self.error_code = 102
        self.msg = msg


class TestStandardError(unittest.TestCase):
    def test_type_check_error(self):
        error_msg = "test error msg"
        try:
            raise TypeCheckError(error_msg)
        except ServiceStandardError as e:
            self.assertEqual(e.error_code, 102)
            self.assertEqual(e.msg, error_msg)

    def test_wrap_exception(self):
        test_exc = Exception()
        test_exc = ServiceStandardError(111, 'just a test', wrapped_exception=test_exc)
        self.assertEqual(test_exc.error_code, 111)


if __name__ == '__main__':
    unittest.main()
