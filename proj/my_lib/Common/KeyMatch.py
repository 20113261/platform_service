#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 上午12:03
# @Author  : Hou Rong
# @Site    : 
# @File    : KeyMatch.py
# @Software: PyCharm


def key_is_legal(s):
    if s:
        if isinstance(s, str):
            if s.strip():
                if s.lower() != 'null':
                    return True
        elif isinstance(s, int):
            if s > -1:
                return True

        elif isinstance(s, float):
            if s > -1.0:
                return True
    return False
