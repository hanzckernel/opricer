# %%
import abc
import datetime
import numpy as np
from scipy.sparse import diags
from scipy import integrate
from opricer.data import models
from opricer.tools.mathtool import force_broadcast


class GenericSolver(abc.ABC):

    @abc.abstractmethod
    def get_price(model):
        pass

    @classmethod
    def _gen_grid(cls, low_val, high_val, start_time, end_time, time_no, asset_no):
        cls.time_samples = np.linspace(start_time, end_time, time_no)
        cls.asset_samples = np.linspace(low_val, high_val, asset_no)


class EurSolver(GenericSolver):
    def __init__(self, time_no=1000, asset_no=100, low_val=0, high_val=5):
        self.time_no = time_no
        self.asset_no = asset_no
        self.low_val = low_val
        self.high_val = high_val

    def __call__(self, model):
        return self.get_price(model)[0]

    @staticmethod
    def _gen_pde_coeff(model):
        try:
            @force_broadcast
            def coef2(asset, t):
                # TODO: This needs further redress
                return (model._vol[0](asset, t) * asset) ** 2 / 2

            @force_broadcast
            def coef1(asset, t):
                return (model.int_rate(t) - model.div) * asset

            @force_broadcast
            def coef0(asset, t):
                return - model.int_rate(t)
            return coef2, coef1, coef0
        except AttributeError:
            raise('Underlying not attached')

    def _load_sim(self, model):
        coef2, coef1, coef0 = self._gen_pde_coeff(model)
        spot_price = np.array(model.spot_price)
        self.low_val *= spot_price
        self.high_val *= spot_price
        self._gen_grid(self.low_val, self.high_val, 0,
                       model.time_to_maturity, self.time_no, self.asset_no)
        self.dS = dS = (self.high_val - self.low_val) / self.asset_no
        dt = model.time_to_maturity / self.time_no
        v1, v2 = dt / (dS ** 2), dt / dS
        X, Y = np.meshgrid(self.asset_samples, self.time_samples)
        self.A = (v1 * coef2(X, Y) / 2 - v2 * coef1(X, Y) / 4).T
        self.B = (-v1 * coef2(X, Y) + dt * coef0(X, Y) / 2).T
        self.C = (v1 * coef2(X, Y) / 2 + v2 * coef1(X, Y) / 4).T

    def _prepare_matrix(self, model):
        self.C[0] += self.A[0]
        self.A[-1] += self.C[-1]
        matrix_left = [diags((-self.A[:, i], 1-self.B[:, i], -self.C[:, i]), offsets=[0, 1, 2],
                             shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        matrix_right = [diags((self.A[:, i], 1+self.B[:, i], self.C[:, i]), offsets=[0, 1, 2],
                              shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        if model.otype.lower() == "call":
            lower_bdd, upper_bdd = 0, self.dS
        elif model.otype.lower() == "put":
            lower_bdd, upper_bdd = -self.dS, 0
        else:
            raise Exception('Invalid model type')
        lower_bdd = lower_bdd * self.A[0]
        upper_bdd = upper_bdd * self.C[-1]
        return matrix_left, matrix_right, lower_bdd, upper_bdd

    def get_price(self, model):
        """
        Prepare coefficient now. For convience we follow convention of Wilmott.
        """
        self._load_sim(model)
        matrix_left, matrix_right, lower_bdd, upper_bdd = self._prepare_matrix(
            model)
        del (self.A, self.B, self.C, self.dS)
        """
        Prepare 3D tensor (time-list of sparse diagonal matrix) for simulation.
        Later only expand one slice to full matrix so as to save storage.
        """
        out = model.payoff(self.asset_samples)
        total_output = [out]

        for time in range(1, self.time_no):
            mat_left = matrix_left[-time - 1].A
            mat_right = matrix_right[-time].A
            mat_left, mat_right = mat_left[:, 1:-1], mat_right[:, 1:-1]
            extra_vec = np.zeros(self.asset_no)
            extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                upper_bdd[-time] + upper_bdd[-time - 1]
            out = np.linalg.solve(
                mat_left, (mat_right @ out).ravel() + extra_vec)
            total_output.append(out)
        total_output.reverse()
        return total_output


class BarSolver(EurSolver):

    def _prepare_matrix(self, model):
        matrix_left, matrix_right = super()._prepare_matrix(model)[0:2]
        lower_bdd, upper_bdd = [np.full(self.time_no, lvl)
                                for lvl in model.barrier]
        to_endtime = model.time_to_maturity - self.time_samples
        if model.otype == 'call':
            upper_bdd = np.minimum(upper_bdd,
                                   self.high_val * np.exp(-model.div * (to_endtime)) -
                                   model.strike * np.exp(-model.int_rate(self.time_samples) * (to_endtime)))
        # TODO: hard-coded. need to changed
        elif model.otype == 'put':
            lower_bdd = np.minimum(lower_bdd,
                                   -self.low_val * np.exp(-model.int_rate(self.time_samples) * (to_endtime)) +
                                   model.strike * np.exp(-model.div * (to_endtime)))
        else:
            raise ValueError('Unknown option type')
        return matrix_left, matrix_right, lower_bdd, upper_bdd

    def get_price(self, model):
        self._load_sim(model)
        matrix_left, matrix_right, lower_bdd, upper_bdd = self._prepare_matrix(
            model)
        lower_bdd = lower_bdd * self.A[1]
        upper_bdd = upper_bdd * self.C[-2]
        del (self.A, self.B, self.C, self.dS)
        lower_bar, higher_bar = model.barrier
        out = model.payoff(self.asset_samples)
        damp_layer = np.where((self.asset_samples <= lower_bar)
                              | (self.asset_samples >= higher_bar))
        out[damp_layer] = model.rebate
        total_output = [out]
        for time in range(1, self.time_no):
            mat_left, mat_right = matrix_left[-time -
                                              1].A, matrix_right[-time].A
            mat_left, mat_right = mat_left[1:-1, 2:-2], mat_right[1:-1, 2:-2]
            extra_vec = np.zeros(self.asset_no-2)
            extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                upper_bdd[-time] + upper_bdd[-time - 1]
            out[1:-1] = np.linalg.solve(mat_left,
                                        (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
            out[damp_layer] = model.rebate
            total_output.append(out)
        total_output.reverse()
        return total_output
