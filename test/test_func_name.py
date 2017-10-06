#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/6 下午2:53
# @Author  : Hou Rong
# @Site    : 
# @File    : test_func_name.py
# @Software: PyCharm
if __name__ == '__main__':
    from proj.my_lib.logger import get_logger
    from proj.my_lib.logger import get_logger as test_logger2
    from poi_list import poi_list_task

    print(get_logger)
