#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/31 下午7:22
# @Author  : Hou Rong
# @Site    : 
# @File    : lang_convert.py
# @Software: PyCharm
from .langconv import *


def simple2tradition(line):
    # 将简体转换成繁体
    line = Converter('zh-hant').convert(line)
    line = line.encode('utf-8')
    return line


def tradition2simple(line):
    # 将繁体转换成简体
    line = Converter('zh-hans').convert(line)
    line = line.encode('utf-8')
    return line


if __name__ == '__main__':
    print(simple2tradition(
        '他们'
    ).decode())
