#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/21 上午11:21
# @Author  : Hou Rong
# @Site    : 
# @File    : test_subclass_name.py
# @Software: PyCharm


class BaseClass(object):
    def __init__(self):
        print("Now Load: {}".format(self.__class__.__name__))


class SubClass(BaseClass):
    pass


if __name__ == '__main__':
    s = SubClass()
