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
    def _gen_grid(cls, model, low_val, high_val, asset_no, time_no, path_no,
                  start_time, end_time, include_all=False):
        cls.dt = (end_time - start_time)/time_no
        cls.dS = (high_val - low_val)/asset_no
        cls.time_samples = np.arange(start_time, end_time, cls.dt)
        cls.asset_samples = np.arange(low_val, high_val, cls.dS)
        cls.sqrt_dt = sqrt(cls.dt)

    @abc.abstractmethod
    def get_price(self, model):
        pass


class EurMCSolver(GenericMCSolver):
    def __init__(self, path_no=500, asset_no=200, time_no=100, high_val=5, low_val=0):
        self.asset_no = asset_no
        self.time_no = time_no
        self.path_no = path_no
        self.low_val = low_val
        self.high_val = high_val

    def __call__(self, model):
        return self.get_price(model)

    @staticmethod
    def _gen_coeff(model):
        try:
            def coef_dt(asset, t):
                return asset * (model.int_rate(t) - model.div(asset))

            def coef_dW(asset, t):
                return asset * model._vol[0](asset, t)
            return coef_dW, coef_dt
        except AttributeError:
            raise('Underlying not attached')

    def _gen_parameter(self, model):
        low_val, high_val = model.strike * self.low_val, model.strike * self.high_val
        random_set = randn(self.time_no, self.path_no)
        self._gen_grid(model, low_val, high_val, self.asset_no, self.time_no, self.path_no,
                       0, model.time_to_maturity)
        return random_set

    def _gen_path(self, model):
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = self._gen_parameter(model)
        asset = np.tile(self.asset_samples, (self.path_no, 1))
        for idx, time in zip(range(self.time_no), self.time_samples):
            asset += coef_dt(asset, time) * self.dt + self.sqrt_dt * \
                coef_dW(asset, time) * \
                random_set[idx].reshape(-1, 1)
        return asset

    def get_price(self, model):
        asset = self._gen_path(model)
        disc = np.exp(-back_quad(model.int_rate, self.time_samples))
        asset = model.payoff(asset)
        # variance = np.var(asset, axis=0)
        asset = disc[-1] * np.mean(asset, axis=0)
        return asset


class logMCSolver(EurMCSolver):
    '''
    For fast calibration if the coeff are asset-independent. More inaccurate ATM.
    '''

    @staticmethod
    def _gen_coeff(model):

        try:
            strike = model.strike
            @force_broadcast
            def coef_dt(t):
                return model.int_rate(t) - model.div(strike) - model._vol[0](strike, t) ** 2 / 2

            @force_broadcast
            def coef_dW(t):
                return model._vol[0](strike, t)
            return coef_dW, coef_dt
        except AttributeError:
            raise('Underlying not attached')

    def _gen_path(self, model):
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = self._gen_parameter(model).T
        increment = 1 + np.sum(coef_dt(self.time_samples)) * self.dt + self.sqrt_dt * \
            random_set @ coef_dW(self.time_samples)
        return np.outer(increment, self.asset_samples)


a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
b = models.EurOption(datetime.datetime(2011, 1, 1), 'put')
b._attach_asset(100, a)
solver = logMCSolver()
solver1 = EurMCSolver()
print(solver._gen_path(b), solver1._gen_path(b))

# %%
