#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/27 上午9:55
# @Author  : Hou Rong
# @Site    : 
# @File    : ServiceStandardError.py
# @Software: PyCharm
import unittest
from proj.my_lib.Common.Utils import get_full_stack


class ServiceStandardError(Exception):
    TASK_ERROR = 12
    PROXY_NONE = 21
    PROXY_INVALID = 22
    PROXY_FORBIDDEN = 23
    REQ_ERROR = 2
    DATA_FORMAT_ERROR = 3

    PARSE_ERROR = 27
    DATA_NONE = 24
    UNKNOWN_ERROR = 25
    EMPTY_TICKET = 29

    STORAGE_ERROR = 31
    STORAGE_UNKNOWN_ERROR = 32
    RABBITMQ_ERROR = 33
    MYSQL_ERROR = 34
    RABBITMQ_MYSQL_ERROR = 35

    FLIP_WARRING = 36

    API_ERROR = 89
    API_NOT_ALLOWED = 90
    API_EMPTY_DATA = 92

    KEY_WORDS_FILTER = 102
    PAGE_SAVE_ERROR = 104

    IMG_INCOMPLETE = 105
    IMG_TOO_LARGE = 106
    IMG_SIZE_FILTER = 107
    IMG_UPLOAD_ERROR = 108

    TARGET_CLOSED = 109

    def __init__(self, error_code=103, msg="未返回错误码", *args, **kwargs):
        self.error_code = error_code
        self.msg = msg

        if 'wrapped_exception' in kwargs:
            self.wrapped_exception = kwargs['wrapped_exception']
            try:
                self.wrapped_exception_info = get_full_stack()
            except Exception:
                self.wrapped_exception_info = None


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
