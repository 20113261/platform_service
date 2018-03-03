#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/20 上午11:38
# @Author  : Hou Rong
# @Site    : 
# @File    : Utils.py
# @Software: PyCharm
import unittest
import re
import functools
import types
from urlparse import urlparse
from my_logger import get_logger

logger = get_logger("utils")


def is_legal(s):
    if s:
        if isinstance(s, types.StringTypes):
            if s.strip():
                if s.lower() != 'null':
                    return True
        elif isinstance(s, types.IntType):
            if s > -1:
                return True

        elif isinstance(s, types.FloatType):
            if s > -1.0:
                return True
    return False


def modify_url(raw_url):
    if not bool(re.match(r'^https?:/{2}\w.+$', raw_url or '')):
        return ''

    parsed_obj = urlparse(raw_url.strip())

    parsed_link_prefix = '{0}://{1}{2}'.format(
        parsed_obj.scheme.strip(),
        parsed_obj.netloc.strip(),
        parsed_obj.path.strip(),
    )
    if parsed_obj.query:
        parsed_link = "{0}?{1}".format(parsed_link_prefix, parsed_obj.query.strip())
    else:
        parsed_link = parsed_link_prefix
    return parsed_link


class UtilTest(unittest.TestCase):
    def test_is_legal_false(self):
        self.assertEqual(is_legal(None), False)

    def test_is_legal_true(self):
        self.assertEqual(is_legal('test'), True)

    def test_modify_url(self):
        self.assertEqual(
            modify_url(
                'https://ihg.scene7.com/is/image/ihg/transparent_1440?fmt=png-alpha&wid=668&hei=385#asdfasdf#123123'),
            'https://ihg.scene7.com/is/image/ihg/transparent_1440?fmt=png-alpha&wid=668&hei=385')

    def test_modify_url_2(self):
        self.assertEqual(
            modify_url('asdfasdfasdfasdf'), ''
        )


def retry(times=3, raise_exc=True):
    def wrapper(func):
        @functools.wraps(func)
        def f(*args, **kwargs):
            _exc = None
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    _exc = exc
                    logger.exception(msg="[retry exception][func: {}][count: {}]".format(func.__name__, i),
                                     exc_info=exc)
            if _exc and raise_exc:
                raise _exc

        return f

    return wrapper


if __name__ == '__main__':
    unittest.main()
