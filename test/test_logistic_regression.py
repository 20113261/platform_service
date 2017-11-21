#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/20 下午6:27
# @Author  : Hou Rong
# @Site    : 
# @File    : test_logistic_regression.py
# @Software: PyCharm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression, LinearRegression

data = [['times', 'data_count'], [0, 800], [1, 900], [2, 1000], [3, 1200], [4, 1400], [5, 1420], [6, 1435]]

columns = data.pop(0)
df = pd.DataFrame(data=data, columns=columns)

lr = LogisticRegression()
lr.fit(X=df[['times']], y=df['data_count'])

xvals = np.arange(0, 14, 1)
predictions = lr.predict(X=xvals[:, np.newaxis])
probs = [y for [x, y] in predictions]

from sklearn import linear_model

clf = linear_model.LinearRegression()
X = [[0, ], [1, ], [2, ], [3, ], [4, ], [5, ], [6, ]]
y = [800, 900, 1000, 1200, 1400, 1420, 1435]
clf.fit(X=X, y=y)

import matplotlib.pyplot as plt
from sklearn import linear_model
from math import log10, pow

clf = linear_model.LogisticRegression()
X = [[10, ], [11, ], [12, ], [13, ], [14, ], [15, ], [16, ]]
y = [800, 900, 1000, 1200, 1400, 1420, 1435]
log_y = [log10(_i) for _i in y]
clf.fit(X=X, y=y)
xvals = np.arange(0, 14, 1)
predictions = clf.predict(X=xvals[:, np.newaxis])
predictions = [pow(10, _i) for _i in predictions]

# Plot the fitted model
plt.plot(xvals, probs)
plt.scatter(xvals, predictions)
plt.show()





import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
X_train = [[6], [8], [10], [14], [18]]
y_train = [[7], [9], [13], [17.5], [18]]
X_test = [[6], [8], [11], [16]]
y_test = [[8], [12], [15], [18]]
regressor = LinearRegression()
regressor.fit(X_train, y_train)
xx = np.linspace(0, 26, 100)
yy = regressor.predict(xx.reshape(xx.shape[0], 1))
plt.plot(X_train, y_train, 'k.')
plt.plot(xx, yy)
quadratic_featurizer = PolynomialFeatures(degree=2)
X_train_quadratic = quadratic_featurizer.fit_transform(X_train)
X_test_quadratic = quadratic_featurizer.transform(X_test)
regressor_quadratic = LinearRegression()
regressor_quadratic.fit(X_train_quadratic, y_train)
xx_quadratic = quadratic_featurizer.transform(xx.reshape(xx.shape[0], 1))
plt.plot(xx, regressor_quadratic.predict(xx_quadratic), 'r-')
plt.show()
print(X_train)
print(X_train_quadratic)
print(X_test)
print(X_test_quadratic)
print('一元线性回归 r-squared', regressor.score(X_test, y_test))
print('二次回归 r-squared', regressor_quadratic.score(X_test_quadratic, y_test))



X = [[10, ], [11, ], [12, ], [13, ], [14, ], [15, ], [16, ]]
y = [800, 900, 1000, 1200, 1400, 1420, 1435]

quadratic_featurizer = PolynomialFeatures(degree=2)
X_train_quadratic = quadratic_featurizer.fit_transform(X_train)
X_test_quadratic = quadratic_featurizer.transform(X_test)


from sklearn.preprocessing import PolynomialFeatures
import numpy as np
X = np.arange(6).reshape(3, 2)
poly = PolynomialFeatures(degree=2)
poly.fit_transform(X)
poly.transform(X = [[10, ], [11, ], [12, ], [13, ], [14, ], [15, ], [16, ]])

