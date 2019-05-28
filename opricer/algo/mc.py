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
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


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
    def __init__(self, path_no=3000, asset_no=10, time_no=150, high_val=2, low_val=0):
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

    def _gen_parameter(self, model, asset_no, time_no):
        """
        We use asset_no and time_no as parameters so that we can make it sparser
        when running LS.
        """
        low_val, high_val = model.strike * self.low_val, model.strike * self.high_val
        self._gen_grid(model, low_val, high_val, asset_no, time_no,
                       0, model.time_to_maturity)

    def _gen_path(self, model):
        self._gen_parameter(model, self.asset_no, self.time_no)
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.time_no, self.path_no)
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
        self._gen_parameter(model)
        # Note the difference in order for this special one
        random_set = randn(self.path_no, self.time_no)
        increment = 1 + np.sum(coef_dt(self.time_samples)) * self.dt + self.sqrt_dt * \
            random_set @ coef_dW(self.time_samples)
        return np.outer(increment, self.asset_samples)


class BarMCSolver(EurMCSolver):

    def _gen_path(self, model):
        self._gen_parameter(model)
        lower_bar, higher_bar = model.barrier
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.time_no, self.path_no)
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


class AmeMCSolver(EurMCSolver):
    '''
    Longstaff-Schwartz
    '''

    def _gen_exercise_time(self, model):
        """
        We just use one price to simulate, as this is more difficult.
        """
        self.BiasPath_no = int(self.path_no/5)
        self.BiasTime_no = int(self.time_no/3)
        coef_dW, coef_dt = self._gen_coeff(model)
        # Note here time_samples are sparse
        self._gen_parameter(model, asset_no=self.asset_no,
                            time_no=self.BiasTime_no)
        random_set = randn(self.time_no-1, self.BiasPath_no)
        cum_intrate = back_quad(model.int_rate, self.time_samples)
        disc_factor = np.exp(cum_intrate)
        asset = np.tile(self.asset_samples, (self.BiasPath_no, 1))
        lst = [asset.copy()]
        # end_time = np.full(
        #     (self.BiasPath_no, self.asset_no), model.time_to_maturity)
        poly = PolynomialFeatures()
        reg_model = LinearRegression()
        for idx, time in zip(range(self.BiasTime_no-1), self.time_samples[1:]):
            asset += (coef_dt(asset, time) * self.dt + self.sqrt_dt *
                      coef_dW(asset, time) * random_set[idx].reshape(-1, 1))
            lst.append(asset.copy())
        '''lst.shape = (self.BTime_no, self.BPath_no, self.asset_no)'''
        lst = np.array(lst)[..., int(self.asset_no/1.75)]
        lst_payoff = model.payoff(lst)
        stopping_idx = -np.ones(self.BiasPath_no, dtype=int)
        stopping_val = [lst_payoff[-1], stopping_idx]
        for time_idx in range(-2, -self.BiasTime_no - 1, -1):
            asset_left, asset_right = lst[time_idx], stopping_val[0]
            non_zero_idx = np.nonzero(lst_payoff[time_idx])
            X_axis = asset_left[non_zero_idx]
            Y_axis = (np.exp(cum_intrate[- stopping_val[1] - 1] - cum_intrate[-time_idx - 1]) *
                      stopping_val[0])[non_zero_idx]
            if X_axis.size != 0:
                X_poly, total_poly = [np.array(
                    [x, x ** 2, x ** 3]).T for x in [X_axis, asset_left]]
                '''total_poly.shape = (3, self.BPath_no, self.asset_no)'''
                reg_model.fit(X_poly, Y_axis)
                Y_pred = total_poly @ reg_model.coef_ + reg_model.intercept_
                Y_pred = np.clip(Y_pred, 0, None)
                X_payoff = lst_payoff[time_idx]
                # print(X_payoff > Y_pred)
                exercise_now = np.argwhere(X_payoff > Y_pred)
                # print(exercise_now)
                # hold_on = np.argwhere(X_payoff < Y_pred)
                stopping_val[1][exercise_now] = time_idx
                stopping_val[0][exercise_now] = X_payoff[exercise_now]
                # print(stopping_val)
            else:
                break
        fair_price = np.dot(stopping_val[0], np.exp(
            cum_intrate[-stopping_val[1] - 1])-cum_intrate[-1])/self.BiasPath_no
        # first_nonzero = np.argwhere(stopping_val[0] == 0)[1]
        return fair_price, stopping_val

    def _gen_path(self, model):
        lower_bar, higher_bar = model.barrier
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = self._gen_parameter(model)

    def get_price(self, model):
        pass


a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
c = models.AmeOption(datetime.datetime(2011, 1, 1), 'put')
c._attach_asset(100, a)
Amesolver = AmeMCSolver()
print(Amesolver._gen_exercise_time(c),
      AmeMCSolver.asset_samples[int(Amesolver.asset_no/1.75)])


# %%
