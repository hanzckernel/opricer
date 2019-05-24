# %%
import numpy as np
from opricer.data import models
import datetime
import random
import abc
from numpy.random import randn
from math import sqrt
from opricer.tools.mathtool import force_broadcast, back_quad


class GenericMCSolver(abc.ABC):
    @abc.abstractmethod
    def get_price(model):
        pass

    @classmethod
    def _gen_path(cls, model, low_val, high_val, asset_no, time_no, path_no,
                  start_time, end_time, include_all=False):
        cls.dt = (end_time - start_time)/time_no
        cls.dS = (high_val - low_val)/asset_no
        cls.time_samples = np.arange(start_time, end_time, cls.dt)
        cls.asset_samples = np.arange(low_val, high_val, cls.dS)
        cls.sqrt_dt = sqrt(cls.dt)
        paths = np.tile(cls.asset_samples, (path_no, 1))
        for time in cls.time_samples:
            paths += paths * (model.int_rate(time) * cls.dt +
                              model._vol[0](paths, time) * cls.sqrt_dt *
                              randn(path_no, asset_no))
            # if include_all:
            #     paths.append(add)
            # else:
            #     paths = add
        return paths


class EurMCSolver(GenericMCSolver):
    def __init__(self, path_no=500, asset_no=100, time_no=100, high_val=5, low_val=0):
        self.asset_no = asset_no
        self.time_no = time_no
        self.path_no = path_no
        self.low_val = low_val
        self.high_val = high_val

    def __call__(self, model):
        return self.get_price(model)

    def get_price(self, model):
        low_val, high_val = model.strike * self.low_val, model.strike * self.high_val
        paths = self._gen_path(model, low_val, high_val, self.asset_no, self.time_no, self.path_no,
                               0, model.time_to_maturity)
        paths = np.exp(back_quad(model.int_rate, self.time_samples)[-1]
                       ) * model.payoff(paths)
        paths = np.mean(paths, axis=0)
        return paths


a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
b = models.EurOption(datetime.datetime(2011, 1, 1), 'put')
b._attach_asset(100, a)
solver = EurMCSolver()
solver(b)


# %%
