#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/20 下午8:01
# @Author  : Hou Rong
# @Site    : 
# @File    : poly_regression.py
# @Software: PyCharm

# 多项式回归
# 二次回归（Quadratic Regression）,y = α + β1x + β2x2,我们有一个解释变量，但是模型有三项，通过第三项（二次项）来实现曲线关系

# import numpy as np
# import matplotlib.pyplot as plt
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
#
# X_train = [[6], [8], [10], [14], [18]]
# y_train = [[7], [9], [13], [17.5], [18]]
# # X = [[10, ], [11, ], [12, ], [13, ], [14, ], [15, ], [16, ]]
# # y = [800, 900, 1000, 1200, 1400, 1420, 1435]
# xx = np.linspace(0, 26, 100)
# print(xx)
# quadratic_fearurizer = PolynomialFeatures(degree=2)
# X_train_quadratic = quadratic_fearurizer.fit_transform(X_train)
# regressor_quadratic = LinearRegression()
# regressor_quadratic.fit(X_train_quadratic, y_train)
# xx_quadratic = quadratic_fearurizer.transform(xx.reshape(xx.shape[0], 1))
# plt.plot(xx, regressor_quadratic.predict(xx_quadratic), 'r-')
# plt.show()


# import numpy as np
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
#
# # X_train = [[6], [8], [10], [14], [18]]
# # y_train = [[7], [9], [13], [17.5], [18]]
# x_train = [[1], [2], [3], [4], [5], [6], [7]]
# y_train = [[800], [900], [1000], [1200], [1400], [1420], [1435]]
# xx = np.linspace(0, 26, 100)
# quadratic_fearurizer = PolynomialFeatures(degree=2)
# X_train_quadratic = quadratic_fearurizer.fit_transform(x_train)
# regressor_quadratic = LinearRegression()
# regressor_quadratic.fit(X_train_quadratic, y_train)
# xx_quadratic = quadratic_fearurizer.transform(xx.reshape(xx.shape[0], 1))


# import numpy as np
# from sklearn.linear_model import LinearRegression
# from sklearn.preprocessing import PolynomialFeatures
#
#
# def next_key(values):
#     """
#     利用二次回归获取下一次的值
#     :param values: y 值的列表
#     :return:
#     """
#     y_train = [[v] for v in values]
#     x_train = [[i] for i in range(len(y_train))]
#     quadratic_fearurizer = PolynomialFeatures(degree=2)
#     X_train_quadratic = quadratic_fearurizer.fit_transform(x_train)
#     regressor_quadratic = LinearRegression()
#     regressor_quadratic.fit(X_train_quadratic, y_train)
#     _next_val = regressor_quadratic.predict(quadratic_fearurizer.transform([[len(y_train)]]))[0][0]
#     return _next_val
#
#
# if __name__ == '__main__':
#     values = [700, 800, 900, 1000, 1200, 1400, 1420, 1435, 1435, 1435, 1435]
#     next_key(values=values)

# import numpy as np
#
# from sklearn import linear_model
#
# values = [700, 800, 900, 1000, 1200, 1400, 1420, 1435, 1435, 1435, 1435]
# clf = linear_model.LogisticRegression(C=10000)
# y = [[v] for v in values]
# x = [[i] for i in np.linspace(min(values), max(values), len(values))]
# clf.fit(X=x, y=y)
# # xvals = np.linspace(min(values), max(values), len(values))
# x.extend([[1500], [1600]])
# predictions = clf.predict(X=x)
#
# # print(xvals)
# print(x)
# print(predictions)

#
# import numpy
# from scipy import log
# from scipy.optimize import curve_fit
#
#
# def func(x, a, b):
#     y = a * log(x) + b
#     return y
#
#
# def poly_fit(x, y, degree):
#     results = {}
#     popt, pcov = curve_fit(func, x, y)
#     results['polynomial'] = popt
#     yhat = func(x, popt[0], popt[1])
#     ybar = numpy.sum(y) / len(y)
#     ssreg = numpy.sum((yhat - ybar) ** 2)
#     sstot = numpy.sum((y - ybar) ** 2)
#     results['determination'] = ssreg / sstot
#
#     return results
#
#
# x = [1, 2, 3, 4, 5, 6]
# y = [2.5, 3.51, 4.45, 5.52, 6.47, 7.51]
# z1 = poly_fit(x, y, 2)
# print(z1)

import numpy as np
from math import exp, log10, pow
from sklearn.linear_model import LinearRegression

values = [700, 800, 900, 1000, 1200, 1400, 1420, 1435, 1435, 1435, 1435]

y = [[i] for i in values]
x = [[log10(i + 1)] for i in range(len(values))]

lr = LinearRegression()
lr.fit(X=x, y=y)

xx = np.linspace(0, 26, 100)
yy = [[v] for v in lr.predict(xx.reshape(xx.shape[0], 1))]

