#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/10 上午10:02
# @Author  : Hou Rong
# @Site    : 
# @File    : test_memory_and_load_average.py
# @Software: PyCharm
import psutil
import os

if __name__ == '__main__':
    memory_obj = psutil.virtual_memory()
    memory_percent = memory_obj.percent
    load_average = os.getloadavg()[0]
    print(load_average)
