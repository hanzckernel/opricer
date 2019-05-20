# %%
import numpy as np
from opricer.data import models
from datetime import datetime


a = models.EurOption(datetime(2011, 1, 1), 'call')
b = models.Underlying(datetime(2010, 1, 1), 100)
a._attach_asset(100, b)
# a.payoff(np.arange(100.23, 123.4, 2.6))
a.__dict__

# %%
# X, Y = np.meshgrid(np.linspace(10, 100, 10), np.linspace(0, 1, 10))
# X[0]


def f(x=5, *y):
    return x, y


sum([f, f, f])(np.arange(0, 1, 0.1))
# %%
