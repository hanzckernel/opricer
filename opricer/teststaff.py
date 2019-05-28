# %%
import numpy as np
import numpy as np
import matplotlib.pyplot as plt
from numpy.random import randn
from math import sqrt
from opricer.tools.mathtool import force_broadcast
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures


# arr = np.empty((2000, 2000, 3000))
# print(arr[arr > 0])
# arr_out = 2 * arr ** 2 + 3 * arr + 20
# arr_poly = np.array([arr, arr ** 2]).T


# poly_model = LinearRegression()
# poly_model.fit(arr_poly, arr_out)
# print(poly_model.intercept_)


arr = np.arange(100)
idx = np.arange(20, 30, 1)
print(arr[[1, 1, 1]])
