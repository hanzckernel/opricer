# %%
import abc
import datetime
import numpy as np
from scipy.sparse import diags
from opricer.model import models
from opricer.tools.mathtool import force_broadcast, back_quad
from functools import partial
import analytics


class EurSolver(analytics.AnalyticSolver):

    def __call__(self, model, greeks = ['price']):
        total_output = self.get_price(model)
        dS = (self.high_val - self.low_val) * model.spot_price / (self.asset_no-1)
        dt = model.time_to_maturity / (self.time_no-1)
        return [{
            'price': partial(lambda arr: arr[0]),
            'Delta': partial(lambda arr: np.gradient(arr, float(dS), axis = 1)[0]),
            'Theta': partial(lambda arr: np.gradient(arr, float(dt), axis = 0)[0]),
            'Gamma': partial(lambda arr: np.gradient(np.gradient(arr, dS,
                            axis =1), dS, axis= 1)),}[greek](total_output) for greek in greeks
        ]

    @staticmethod
    def _gen_pde_coeff(model):
        try:
            @force_broadcast
            def coef2(asset, t):
                return (model._vol[0](asset, t) * asset) ** 2 / 2

            @force_broadcast
            def coef1(asset, t):
                return (model.int_rate(t) - model.div[0](t)) * asset

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
        self.high_val = self.high_val/model.spot_price
        self.low_val = self.low_val/model.spot_price
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
                mat_left, (mat_right @ out).ravel() + extra_vec).reshape(-1, 1)
            total_output.append(out)
        total_output.reverse() 

        return total_output







class AmeSolver(EurSolver):

    def _load_sim(self, model):
        super()._load_sim(model)
        if model.otype.lower() == 'call':
            h_row, l_row = [1-self.B[1]], []
            for i in range(2, self.asset_no-1):
                l_addrow = -self.A[i]/h_row[i-2]
                h_addrow = 1 - self.B[i] + l_addrow * self.C[i-1]
                h_row.append(h_addrow)
                l_row.append(l_addrow)

        elif model.otype.lower() == 'put':
            h_row, l_row = [1-self.B[-2]], []
            for i in range(2, self.asset_no-1):
                l_addrow = -self.A[-i]/h_row[i-2]
                h_addrow = 1 - self.B[-i-1] + l_addrow * self.C[-i-1]
                h_row.append(h_addrow)
                l_row.append(l_addrow)
            h_row.reverse(), l_row.reverse()
        else:
            raise ValueError('Not Applicable')
        self.H, self.L = np.array(h_row), np.array(l_row)

    def _prepare_matrix(self, model):
        matrix_right = [diags((self.A[:, i], 1+self.B[:, i], self.C[:, i]), offsets=[0, 1, 2],
                              shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        matrix_left = [diags((-self.A[:, i], 1-self.B[:, i], -self.C[:, i]), offsets=[0, 1, 2],
                             shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        matrix_Lleft = [diags(
            [self.L[:, i], 1], [-1, 0], shape=(self.asset_no-2, self.asset_no-2)) for i in range(self.time_no)]
        matrix_Uleft = [diags([self.H[:, i], -self.C[1:-1, i]], offsets=[0, 1],
                              shape=(self.asset_no-2, self.asset_no-2)) for i in range(self.time_no)]
        # to_endtime = model.time_to_maturity - self.time_samples
        if model.otype == 'call':
            upper_bdd = np.maximum(self.high_val - model.strike,
                                   self.high_val * np.exp(-back_quad(model.div[0], self.time_samples)) -
                                   model.strike * np.exp(-back_quad(model.int_rate, self.time_samples)))
            lower_bdd = 0
        elif model.otype == 'put':
            lower_bdd = np.minimum(model.strike - self.low_val,
                                   -self.low_val * np.exp(-back_quad(model.int_rate, self.time_samples)) +
                                   model.strike * np.exp(-back_quad(model.div[0], self.time_samples)))
            upper_bdd = 0
        else:
            raise ValueError('Unknown option type')
        return matrix_right, matrix_Lleft, matrix_Uleft, lower_bdd, upper_bdd

    def get_price(self, model, beautify=True):
        self._load_sim(model)
        matrix_right, matrix_Lleft, matrix_Uleft, lower_bdd, upper_bdd = self._prepare_matrix(
            model)

        lower_bdd = lower_bdd * self.A[1]
        upper_bdd = upper_bdd * self.C[-2]
        del (self.A, self.B)
        out = model.payoff(self.asset_samples)
        out[[0, -1]] = 0  # this is for the convience of looping.
        begin = out.copy()
        total_output = [begin]
        if model.otype.lower() == 'call':
            for time in range(1, self.time_no):
                mat_Lleft, mat_Uleft = matrix_Lleft[-time -
                                                    1].A,  matrix_Uleft[-time-1].A
                mat_right = matrix_right[-time].A[1:-1, 2:-2]
                extra_vec = np.zeros(self.asset_no-2)
                extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                    upper_bdd[-time] + upper_bdd[-time - 1]
                out[1:-1] = np.linalg.solve(
                    mat_Lleft, (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
                # for i in np.nditer(out[-2:0:-1], op_flags = ['readwrite']):
                for i in range(2, self.asset_no):
                    out[-i] = max((out[-i] + self.C[-i, time]
                                   * out[1-i])/self.H[1-i, time], begin[-i])
                total_output.append(out)
        if model.otype.lower() == 'put':
            for time in range(1, self.time_no):
                mat_Lleft, mat_Uleft = matrix_Lleft[-time -
                                                    1].A,  matrix_Uleft[-time-1].A
                mat_right = matrix_right[-time].A[1:-1, 2:-2]
                extra_vec = np.zeros(self.asset_no-2)
                extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                    upper_bdd[-time] + upper_bdd[-time - 1]
                out[1:-1] = np.linalg.solve(
                    mat_Uleft, (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
                # use trick here out[0] = 0
                for i in range(1, self.asset_no - 1):
                    out[i] = max(
                        (out[i] - self.L[i - 2, time] * out[i-1]), begin[i])
                total_output.append(out)
        total_output.reverse()
        del (self.L, self.H, self.C, self.dS)
        self.low_val = self.low_val/model.spot_price
        self.high_val = self.high_val/model.spot_price
        if beautify:
            total_output = np.array(total_output)
            total_output[:, [0, -1]] = 2 * \
                total_output[:, [1, -2]] - total_output[:, [2, -3]]
        return total_output

class BarSolver(EurSolver):

    def _prepare_matrix(self, model):
        matrix_left, matrix_right = super()._prepare_matrix(model)[0:2]
        lower_bdd, upper_bdd = model.barrier
        # lower_bdd, upper_bdd = [np.full(self.time_no, lvl)
                                # for lvl in model.barrier]
        to_endtime = model.time_to_maturity - self.time_samples
        if model.otype == 'call':
            upper_bdd = np.minimum(upper_bdd,
                                   self.high_val * np.exp(-back_quad(model.div[0], self.time_samples)) -
                                   model.strike * np.exp(-back_quad(model.int_rate, self.time_samples)))
        elif model.otype == 'put':
            lower_bdd = np.minimum(lower_bdd,
                                   -self.low_val * np.exp(-back_quad(model.int_rate, self.time_samples)) +
                                   model.strike * np.exp(-back_quad(model.div[0], self.time_samples)))
        else:
            raise ValueError('Unknown option type')
        return matrix_left, matrix_right, lower_bdd, upper_bdd

    def get_price(self, model):
        self._load_sim(model)
        matrix_left, matrix_right, lower_bdd, upper_bdd = self._prepare_matrix(
            model)
        lower_bdd = lower_bdd * self.A[1] if np.isfinite(lower_bdd).all() else np.zeros(self.time_no)
        upper_bdd = upper_bdd * self.C[-2] if np.isfinite(upper_bdd).all() else np.zeros(self.time_no)
        del (self.A, self.B, self.C, self.dS)
        lower_bar, higher_bar = model.barrier
        out = model.payoff(self.asset_samples)
        damp_layer = np.where((self.asset_samples <= lower_bar)
                              | (self.asset_samples >= higher_bar))
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
        self.high_val = self.high_val/ model.spot_price
        self.low_val = self.low_val/ model.spot_price
        total_output.reverse()
        return total_output


# a = models.Underlying(datetime.datetime(2010, 1, 1), 100)
# b = models.EurOption(datetime.datetime(2011, 1, 1), 'call')
# c = models.AmeOption(datetime.datetime(2011, 1, 1), 'call')
# b._attach_asset(100, a)
# c._attach_asset(100, a)
# solver1 = EurSolver()
# solver2 = AmeSolver()

# print(solver1(b)[0].flatten())
# print(solver2(c)[0].flatten())