#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/20 下午8:43
# @Author  : Hou Rong
# @Site    : 
# @File    : test_next_value.py
# @Software: PyCharm
from proj.my_lib.Common.Utils import next_value

if __name__ == '__main__':
    values = [700, 800, 900, 1000, 1200, 1400, 1420, 1435, 1435, 1435, 1435]
    print(len(values), next_value(values))

    values = [300, 350, 370, 390]
    print(len(values), next_value(values=values))

    import numpy as np
    from math import exp, log10, pow
    from sklearn.linear_model import LinearRegression

    values = [300, 350, 370, 390, 400, 401, 402, 402, 402, 402, 402, 402]

    y = [[i] for i in values]
    x = [[log10(i + 1)] for i in range(len(values))]

    lr = LinearRegression()
    lr.fit(X=x, y=y)

    print(lr.predict([[log10(len(values) + 1)]]))

    values = [300, 50, 20, 20, 10, 5, 2, 1]

    print(len(values), next_value(values=values))


