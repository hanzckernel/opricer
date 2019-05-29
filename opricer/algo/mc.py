# %%
import numpy as np
from opricer.data import models
import datetime
import random
import abc
from numpy.random import randn
from math import sqrt
from opricer.tools.mathtool import force_broadcast, back_quad
from scipy.integrate import quad
# from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression


class GenericMCSolver(abc.ABC):
    @abc.abstractmethod
    def get_price(model):
        pass

    @classmethod
    def _gen_grid(cls, model, low_val, high_val, asset_no, time_no,
                  start_time, end_time):
        cls.dt = (end_time - start_time)/(time_no-1)
        cls.dS = (high_val - low_val)/(asset_no-1)
        cls.time_samples = np.linspace(start_time, end_time, time_no)
        cls.asset_samples = np.linspace(low_val, high_val, asset_no)
        cls.sqrt_dt = sqrt(cls.dt)

    @abc.abstractmethod
    def get_price(self, model):
        pass


class EurMCSolver(GenericMCSolver):
    def __init__(self, path_no=1000, asset_no=5, time_no=101, high_val=2, low_val=0):
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

    def _gen_parameter(self, model, time_no):
        """
        We use asset_no and time_no as parameters so that we can make it sparser
        when running LS.
        """
        low_val, high_val = model.strike * self.low_val, model.strike * self.high_val
        self._gen_grid(model, low_val, high_val, self.asset_no, time_no,
                       0, model.time_to_maturity)

    def _gen_path(self, model):
        self._gen_parameter(model, self.time_no)
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.path_no, self.time_no)
        asset = np.tile(self.asset_samples.reshape(-1, 1), (1, self.path_no))
        for idx, time in zip(range(self.time_no), self.time_samples):
            asset = asset + coef_dt(asset, time) * self.dt + \
                coef_dW(asset, time) * self.sqrt_dt * random_set[:, idx]
        return asset

    def get_price(self, model):
        asset = self._gen_path(model)
        payoff = model.payoff(asset)
        disc = np.exp(-back_quad(model.int_rate, self.time_samples))

        # variance = np.var(asset, axis=0)
        payoff = np.mean(disc[-1] * payoff, axis=1)
        return payoff


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
        self._gen_parameter(model, self.time_no)
        # Note the difference in order for this special one
        random_set = randn(self.time_no, self.path_no)
        increment = 1 + np.sum(coef_dt(self.time_samples)) * self.dt + self.sqrt_dt * \
            random_set @ coef_dW(self.time_samples.reshape(-1, 1))
        return np.outer(increment, self.asset_samples)


class BarMCSolver(EurMCSolver):

    def _gen_path(self, model):
        self._gen_parameter(model, self.time_no)
        lower_bar, higher_bar = model.barrier
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.path_no, self.time_no)
        asset = np.tile(self.asset_samples.reshape(-1, 1), (1, self.path_no))
        for idx, time in zip(range(self.time_no), self.time_samples):
            asset = asset + coef_dt(asset, time) * self.dt + self.sqrt_dt * \
                coef_dW(asset, time) * random_set[idx]
        return asset

    def get_price(self, model):
        asset = self._gen_path(model)
        # disc = np.exp(-back_quad(model.int_rate, self.time_samples))
        asset = model.payoff(asset)
        # variance = np.var(asset, axis=0)
        asset = quad(model.int_rate, 0, model.time_to_maturity) * \
            np.mean(asset, axis=1)
        return asset


class AmeMCSolver(EurMCSolver):
    '''
    Longstaff-Schwartz
    '''

    def get_price(self, model):
        """
        We just use one price to simulate, as this is more difficult.
        """
        self.BiasPath_no = int(self.path_no)
        self.BiasTime_no = int(self.time_no)
        coef_dW, coef_dt = self._gen_coeff(model)
        # Note here time_samples are sparse
        self._gen_parameter(model, time_no=self.BiasTime_no)
        random_set = randn(self.BiasPath_no, self.BiasTime_no)
        cum_intrate = back_quad(model.int_rate, self.time_samples)
        disc_factor = np.exp(cum_intrate)
        asset = np.tile(self.asset_samples.reshape(-1, 1),
                        (1, self.BiasPath_no))
        lst = [asset.copy()]
        # end_time = np.full(
        #     (self.BiasPath_no, self.asset_no), model.time_to_maturity)
        reg_model = LinearRegression()
        for idx, time in zip(range(self.BiasTime_no), self.time_samples):
            asset = asset + (coef_dt(asset, time) * self.dt + self.sqrt_dt *
                             coef_dW(asset, time) * random_set[:, idx])
            lst.append(asset.copy())
        '''lst.shape = (self.BTime_no, self.asset_no, self.BPath_no)'''
        lst = np.array(lst)
        lst_payoff = model.payoff(lst)
        stopping_idx = -np.ones((self.asset_no, self.BiasPath_no), dtype=int)
        stopping_val = [lst_payoff[-1], stopping_idx]
        for time_idx in range(-2, -self.BiasTime_no - 1, -1):
            asset_left = lst[time_idx]
            non_zero_idx = np.nonzero(lst_payoff[time_idx])
            X_axis = asset_left[non_zero_idx]
            Y_axis = (np.exp(cum_intrate[- stopping_val[1] - 1] - cum_intrate[-time_idx - 1]) *
                      stopping_val[0])[non_zero_idx]
            if X_axis.size != 0:
                X_poly, total_poly = [np.array(
                    [x, x ** 2, x ** 3, x ** 4]).T for x in [X_axis, asset_left]]
                '''total_poly.shape = (4, self.BPath_no, self.asset_no)'''
                reg_model.fit(X_poly, Y_axis)
                Y_pred = (total_poly @ reg_model.coef_ +
                          reg_model.intercept_).T
                # print(reg_model.score(X_poly, Y_axis))
                Y_pred = np.clip(Y_pred, 0, None)
                X_payoff = lst_payoff[time_idx]
                # print(X_payoff > Y_pred)
                # print(exercise_now)
                # hold_on = np.argwhere(X_payoff < Y_pred)
                # print(f"before assignment:{X_payoff}\n \
                #     this is Y:{Y_pred}\n and payoff[-1]:{lst_payoff[-1]}")
                stopping_val[1][X_payoff > Y_pred] = time_idx
                stopping_val[0] = np.where(
                    X_payoff > Y_pred, X_payoff, stopping_val[0])
                # print('after assignment', stopping_val)
            else:
                break
        fair_price = (stopping_val[0] * (np.exp(
            cum_intrate[-stopping_val[1] - 1])-cum_intrate[-1])).sum(axis=1)/self.BiasPath_no
        # first_nonzero = np.argwhere(stopping_val[0] == 0)[1]
        return fair_price


# a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
# # b = models.EurOption(datetime.datetime(2011, 1, 1), 'call')
# c = models.AmeOption(datetime.datetime(2011, 1, 1), 'call')
# c._attach_asset(100, a)
# # b._attach_asset(100, a)
# AmeSolver = AmeMCSolver()
# # EurSolver = EurMCSolver()
# # # print(EurSolver._gen_path(b)[:, 20], EurSolver.asset_samples[20])
# print(AmeSolver(c))


# %%
