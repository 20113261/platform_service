#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/10 上午9:29
# @Author  : Hou Rong
# @Site    : 
# @File    : test_stop_3_for.py
# @Software: PyCharm

try:
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print(i, j, k)
                if i == 1 and j == 1 and k == 1:
                    raise StopIteration()
except StopIteration:
    print('It Stopped')
