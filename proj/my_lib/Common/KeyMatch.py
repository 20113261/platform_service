#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 上午12:03
# @Author  : Hou Rong
# @Site    : 
# @File    : KeyMatch.py
# @Software: PyCharm
import types


def key_is_legal(s):
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


if __name__ == '__main__':
    print key_is_legal(u'asdfasdf')
    print key_is_legal(None)
    print key_is_legal(u'NULL')
    print key_is_legal(u'')
    print key_is_legal(b'NULL')
    print not (key_is_legal(None) and key_is_legal('NULL'))
