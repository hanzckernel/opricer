# %%
import numpy as np
from opricer.data import models
from datetime import datetime
import random
import abc
from numpy.random import randn
from math import sqrt

a = models.EurOption(datetime(2011, 1, 1), 'call')
b = models.Underlying(datetime(2010, 1, 1), 100)
a._attach_asset(100, b)


class GenericMCSolver(abc.ABC):
    def get_price(model):
        pass

    @classmethod
    def _gen_path(cls, model, low_val, high_val, asset_no, time_no, path_no,
                  start_time, end_time, include_all=False):
        cls.dt = (end_time - start_time)/time_no
        cls.dS = (high_val - low_val)/asset_no
        cls.time_samples = np.arange(start_time, end_time, cls.dt)
        cls.asset_samples = np.arange(low_val, high_val, cls.dt)
        cls.sqrt_dt = sqrt(cls.dt)
        paths = np.tile(cls.asset_samples, (path_no, asset_no))
        for time in cls.time_samples:
            add = paths * model.int_rate(time) * cls.dt + \
                model.vol(paths, time) * cls.sqrt_dt * randn(time_no)
            if include_all:
                paths.append(add)
            else:
                paths = add
        return paths


class EurMCSolver(abc.ABC):
    def __init__(self, asset_no=100, time_no=100, path_no=1000, high_val=5, low_val=0):
        self.time_no = time_no
        self.path_no = path_no

    def get_price(self, model):
        low_val, high_val = model.strike * (low_val, high_val)
        paths = self._gen_path(model, low_val, high_val, self.time_no, self.path_no,
                               0, model.time_to_maturity)
        return paths
