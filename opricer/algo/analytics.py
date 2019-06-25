#!/usr/bin/env python
# coding: utf-8
# %%
from opricer.model import models
import abc
import datetime
import numpy as np
from scipy.stats import norm
import pandas as pd
np.seterr(divide='ignore')


class GenericSolver(abc.ABC):

    @abc.abstractmethod
    def get_price(self, model):
        pass

    @classmethod
    def _gen_grid(cls, low_val, high_val, start_time, end_time, time_no, asset_no):
        cls.time_samples = np.linspace(start_time, end_time, int(time_no))
        cls.asset_samples = np.linspace(low_val, high_val, int(asset_no))


class AnalyticSolver(GenericSolver):

    def __call__(self, model, to_df=True):
        # if to_df:
        #     start = pd.Timestamp(model._time[0])
        #     end = pd.Timestamp(model.expiry)
        #     idx = pd.to_datetime(np.linspace(
        #         start.value, end.value, self.time_no))
        #     df = self.get_price(model).T
        #     df = pd.DataFrame(df,
        #                       index=idx, columns=self.asset_samples.flatten())
        #     df.index.name = 'Date'
        #     df.columns.name = 'Spot_price'
        #     return df
        # else:
        return self.get_price(model)

    def __init__(self, time_no=50, asset_no=20, low_val=0, high_val=5):
        self.time_no = time_no
        self.asset_no = asset_no
        self.low_val = low_val
        self.high_val = high_val

    def get_price(self, model):
        spot_price = np.array(model.spot_price)
        self._gen_grid(self.low_val * spot_price, self.high_val * spot_price, 0,
                       model.time_to_maturity, self.time_no, self.asset_no)
        K, T = model.strike, self.time_samples
        r, D, vol = model.int_rate(T), model.div[0](K), model._vol[0](K, T)
        moneyness = np.log(self.asset_samples / K)
        d1 = (moneyness + (r-D + vol**2/2)*T)/(vol * np.sqrt(T))
        d2 = d1 - vol * np.sqrt(T)
        strike_disc = model.strike * np.exp(-r*T)
        if model.otype.lower() == 'call':
            return self.asset_samples * np.exp(-D*T) * norm.cdf(d1) - strike_disc * norm.cdf(d2)
        if model.otype.lower() == 'put':
            return strike_disc * norm.cdf(-d2) - self.asset_samples * np.exp(-D*T) * norm.cdf(-d1)


# a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
# a1 = models.Underlying(datetime.datetime(2010, 1, 1), 200)
# b = models.EurOption(datetime.datetime(2011, 1, 1), 'call')
# b._attach_asset(100, a)
# solver = AnalyticSolver(high_val=2, low_val=0)
# %%
