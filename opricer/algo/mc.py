
import numpy as np
from opricer.model import models
import datetime
import random
import abc
from numpy.random import randn
from math import sqrt
from opricer.tools.mathtool import force_broadcast, back_quad, ArrFunc, poly_transform_
from scipy.linalg import cholesky
from scipy.integrate import quad
from sklearn.linear_model import LinearRegression
from typing import Callable, List, Optional, Tuple, Union, Any

class GenericMCSolver(abc.ABC):

    def __init__(self, path_no: int = 200, asset_no: int = 20, time_no: int = 100, 
                 high_val: float = 5.0, low_val: float = 0.0):
        self.asset_no = asset_no
        self.time_no = time_no
        self.path_no = path_no
        self.low_val = low_val
        self.high_val = high_val
        self.dt: float = 0.0
        self.time_samples: np.ndarray = np.array([])
        self.asset_samples: np.ndarray = np.array([])
        self.sqrt_dt: float = 0.0

    @abc.abstractmethod
    def get_price(self, model: Any) -> np.ndarray:
        pass

    def _gen_grid(self, model: Any, low_val: np.ndarray, high_val: np.ndarray, 
                  asset_no: int, time_no: int, start_time: float, end_time: float) -> None:
        self.dt = (end_time - start_time)/(time_no-1)
        self.time_samples = np.linspace(start_time, end_time, time_no)
        self.asset_samples = np.linspace(low_val, high_val, asset_no, axis=0) 
        self.sqrt_dt = sqrt(self.dt)

class EurMCSolver(GenericMCSolver):

    def __call__(self, model: Any) -> np.ndarray:
        return self.get_price(model)

    @staticmethod
    def _gen_coeff(model: Any) -> Tuple[Callable, Callable]:
        try:
            def coef_dt(asset: np.ndarray, t: float) -> np.ndarray:
                return asset * (model.int_rate(t) - ArrFunc(model.div, asset))

            def coef_dW(asset: np.ndarray, t: float) -> np.ndarray:
                return asset * ArrFunc(model._vol, asset, t)
            return coef_dW, coef_dt
        except AttributeError:
            raise ValueError('Underlying not attached')

    def _gen_parameter(self, model: Any, time_no: int) -> None:
        low_val = model.spot_price * self.low_val
        high_val = model.spot_price * self.high_val
        self._gen_grid(model, low_val, high_val, self.asset_no, time_no,
                       0.0, model.time_to_maturity)

    def _gen_path(self, model: Any) -> np.ndarray:
        self._gen_parameter(model, self.time_no)
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.path_no, self.time_no)
        asset = np.tile(self.asset_samples.reshape(-1, 1), (1, self.path_no))
        asset_lst = [asset.copy()]
        for idx, time in zip(range(1, self.time_no), self.time_samples[1:]):
            asset = asset + coef_dt(asset, time) * self.dt +                 coef_dW(asset, time) * self.sqrt_dt * random_set[:, idx]
            asset_lst.append(asset.copy())
        return np.array(asset_lst)

    def get_price(self, model: Any) -> np.ndarray:
        asset = self._gen_path(model)
        payoff = model.payoff(asset).transpose()
        disc = np.exp(-back_quad(model.int_rate, self.time_samples))

        disc_all = disc * payoff
        payoff = np.flip(np.mean(disc_all, axis=0), axis=1)
        return payoff.transpose()


class logMCSolver(EurMCSolver):
    # For fast calibration if the coeff are asset-independent. More inaccurate ATM.

    @staticmethod
    def _gen_coeff(model: Any) -> Tuple[Callable, Callable]:
        try:
            strike = model.strike
            @force_broadcast
            def coef_dt(t: float) -> float:
                return model.int_rate(t) - model.div[0](strike) - model._vol[0](strike, t) ** 2 / 2

            @force_broadcast
            def coef_dW(t: float) -> float:
                return model._vol[0](strike, t)
            return coef_dW, coef_dt
        except AttributeError:
            raise ValueError('Underlying not attached')

    def _gen_path(self, model: Any) -> np.ndarray:
        coef_dW, coef_dt = self._gen_coeff(model)
        self._gen_parameter(model, self.time_no)
        random_set = randn(self.path_no, self.time_no)
        increment = 1 + np.sum(coef_dt(self.time_samples)) * self.dt + self.sqrt_dt * \
            random_set @ coef_dW(self.time_samples.reshape(-1, 1))
        return np.outer(increment, self.asset_samples)

    def get_price(self, model: Any) -> np.ndarray:
        asset = self._gen_path(model)
        payoff = model.payoff(asset)
        cum_int = back_quad(model.int_rate, self.time_samples)
        disc_factor = np.exp(-cum_int[0])
        price = np.mean(payoff, axis=0) * disc_factor
        return price


class BarMCSolver(EurMCSolver):

    def _gen_path(self, model: Any) -> np.ndarray:
        self._gen_parameter(model, self.time_no)
        lower_bar, higher_bar = model.barrier
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.path_no, self.time_no)
        asset = np.tile(self.asset_samples.reshape(-1, 1), (1, self.path_no))
        asset_lst = [asset.copy()]
        for idx, time in zip(range(1, self.time_no), self.time_samples[1:]):
            asset = asset + coef_dt(asset, time) * self.dt + self.sqrt_dt *                 coef_dW(asset, time) * random_set[:, idx]
            damp_layer = np.where((asset <= lower_bar) | (asset >= higher_bar))
            asset[damp_layer] = np.nan
            asset_lst.append(asset.copy())
        
        asset_arr = np.array(asset_lst)
        asset_arr[np.isnan(asset_arr)] = model.rebate
        return asset_arr


class AmeMCSolver(EurMCSolver):
    # Longstaff-Schwartz

    def get_price(self, model: Any) -> np.ndarray:
        asset_lst = self._gen_path(model)
        reg_model = LinearRegression()
        cum_intrate = back_quad(model.int_rate, self.time_samples)
        lst_payoff = model.payoff(asset_lst)
        stopping_idx = -np.ones((self.asset_no, self.path_no), dtype=int)
        stopping_val = [lst_payoff[-1], stopping_idx]
        poly_axis = -1 if hasattr(model, 'AssetCount') else None
        
        for time_idx in range(-2, -self.time_no - 1, -1):
            asset_left = asset_lst[time_idx]
            non_zero_idx = np.nonzero(lst_payoff[time_idx])
            X_axis = asset_left[non_zero_idx]
            
            stop_idx_safe = -stopping_val[1] - 1
            curr_idx_safe = -time_idx - 1
            discount_factor = np.exp(cum_intrate[stop_idx_safe] - cum_intrate[curr_idx_safe])
            Y_axis = (discount_factor * stopping_val[0])[non_zero_idx]
            
            if X_axis.size != 0:
                X_poly, total_poly = [poly_transform_(x, axis=poly_axis, deg=3) for x in [
                    X_axis, asset_left]]
                reg_model.fit(X_poly, Y_axis)
                Y_pred = total_poly @ reg_model.coef_ + reg_model.intercept_
                Y_pred = np.clip(Y_pred, 0, None)
                X_payoff = lst_payoff[time_idx]
                
                update_mask = X_payoff > Y_pred
                stopping_val[1][update_mask] = time_idx
                stopping_val[0] = np.where(update_mask, X_payoff, stopping_val[0])
            else:
                break

        undiscounted = (
            stopping_val[0] * np.exp(cum_intrate[-stopping_val[1] - 1])).sum(axis=1)/self.path_no
        fair_price2 = np.outer(undiscounted, np.exp(-cum_intrate))
        return fair_price2


class BasketMCSolver(EurMCSolver):

    def _gen_path(self, model: Any) -> np.ndarray:
        self._gen_parameter(model, self.time_no)
        corr_sqrt = cholesky(model.corr_mat)
        coef_dW, coef_dt = self._gen_coeff(model)
        random_set = randn(self.path_no, self.time_no, model.AssetCount)
        random_set = np.dot(random_set, corr_sqrt.T)
        self.asset_samples = np.expand_dims(self.asset_samples, axis=1)
        asset = np.tile(self.asset_samples, (1, self.path_no, 1))
        asset_lst = [asset.copy()]
        for idx, time in zip(range(1, self.time_no), self.time_samples[1:]):
            asset = asset + coef_dt(asset, time) * self.dt +                 coef_dW(asset, time) * self.sqrt_dt * random_set[:, idx]
            asset_lst.append(asset.copy())
        return np.array(asset_lst)

    def get_price(self, model: Any) -> np.ndarray:
        return super().get_price(model)


class BasketAmeSolver(BasketMCSolver, AmeMCSolver):

    def get_price(self, model: Any) -> np.ndarray:
        return AmeMCSolver.get_price(self, model)
