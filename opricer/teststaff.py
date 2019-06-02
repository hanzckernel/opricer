# %%
import numpy as np
import matplotlib.pyplot as plt
from numpy.random import randn
from math import sqrt
from opricer.tools.mathtool import force_broadcast, poly_transform_
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from itertools import combinations_with_replacement


def f(x, y):
    return x ** 2 + x * y + y ** 2


x = np.arange(10)
y = np.arange(5)


# vol = 0.2
# int_rate = 0.15
# div = 0
# path_no = 1000
# asset_sample = np.array([0, 50, 100, 150, 200])
# strike = 100
# dt = 0.01


# def simulate(asset_sample):
#     random_set = randn(path_no, 100)
#     asset = np.tile(asset_sample.reshape(-1, 1), (1, path_no))
#     for t in range(100):
#         asset = asset + 0.01 * int_rate * asset + \
#             asset * vol * 0.1 * random_set[:, t]
#     # return asset
#     payoff = np.clip(asset - strike, 0, None)
#     disc_asset = np.exp(-0.15) * payoff
#     disc_asset = np.mean(disc_asset, axis=1)
#     return disc_asset


# %%


# %%
