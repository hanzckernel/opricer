#!/usr/bin/env python
# coding: utf-8
from opricer.data import models
from opricer.algo import pde, mc
import datetime
import numpy as np


# def test_BS_call(asset, t, T, vol, r, D, K):
#     moneyness = np.log(asset / K)
#     d1 = (moneyness + (r-D + vol**2/2)*T)/(vol * np.sqrt(T))
#     d2 = d1 - vol * np.sqrt(T)
#     return asset * np.exp(-D*T)*norm.cdf(d1) - K * np.exp(-r*T)*norm.cdf(d2)


def test_first():
    assert models.Option('call', datetime.datetime(2011, 1, 1)).otype == 'call'
