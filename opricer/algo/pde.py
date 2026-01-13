# %%
import abc
import datetime
import numpy as np
from scipy.sparse import diags
from opricer.model import models
from opricer.tools.mathtool import force_broadcast, back_quad
from functools import partial
from . import analytics
from typing import List, Tuple, Any, Union, Callable

class EurSolver(analytics.AnalyticSolver):

    def __call__(self, model: Any, greeks: List[str] = ['price']) -> np.ndarray:
        total_output = self.get_price(model)
        return np.array(total_output).squeeze(axis=-1)

    @staticmethod
    def _gen_pde_coeff(model: Any) -> Tuple[Callable, Callable, Callable]:
        try:
            @force_broadcast
            def coef2(asset: np.ndarray, t: float) -> np.ndarray:
                # Volatility squared term
                return (model._vol[0](asset, t) * asset) ** 2 / 2

            @force_broadcast
            def coef1(asset: np.ndarray, t: float) -> np.ndarray:
                # Drift term
                return (model.int_rate(t) - model.div[0](t)) * asset

            @force_broadcast
            def coef0(asset: np.ndarray, t: float) -> np.ndarray:
                # Discount term
                return - model.int_rate(t)
            return coef2, coef1, coef0
        except AttributeError:
            raise ValueError('Underlying not attached')

    def _load_sim(self, model: Any) -> None:
        coef2, coef1, coef0 = self._gen_pde_coeff(model)
        spot_price = np.array(model.spot_price)
        # Scale grid by spot price
        # Note: This modifies instance attributes, which can be side-effect heavy if reused.
        # But for now we keep logic.
        self.low_val_scaled = self.low_val * spot_price
        self.high_val_scaled = self.high_val * spot_price
        
        self._gen_grid(self.low_val_scaled, self.high_val_scaled, 0,
                       model.time_to_maturity, self.time_no, self.asset_no)
                       
        self.dS = dS = (self.high_val_scaled - self.low_val_scaled) / self.asset_no
        dt = model.time_to_maturity / self.time_no
        
        # PDE Coeffs
        # v1 = dt / dS^2, v2 = dt / dS
        # But dS might be an array if spot_price is array? No, spot_price is scalar for 1 asset.
        
        v1, v2 = dt / (dS ** 2), dt / dS
        X, Y = np.meshgrid(self.asset_samples, self.time_samples)
        
        # Implicit scheme coefficients (Crank-Nicolson or Fully Implicit? Looks like Fully Implicit or similar)
        # A, B, C are diagonals for the tridiagonal matrix
        self.A = (v1 * coef2(X, Y) / 2 - v2 * coef1(X, Y) / 4).T
        self.B = (-v1 * coef2(X, Y) + dt * coef0(X, Y) / 2).T
        self.C = (v1 * coef2(X, Y) / 2 + v2 * coef1(X, Y) / 4).T

    def _prepare_matrix(self, model: Any) -> Tuple[List, List, np.ndarray, np.ndarray]:
        # Boundary conditions adjustment
        self.C[0] += self.A[0]
        self.A[-1] += self.C[-1]
        
        # Construct matrices
        # We create a list of sparse matrices for each time step
        matrix_left = [diags((-self.A[:, i], 1-self.B[:, i], -self.C[:, i]), offsets=[0, 1, 2],
                             shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        matrix_right = [diags((self.A[:, i], 1+self.B[:, i], self.C[:, i]), offsets=[0, 1, 2],
                              shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        
        if model.otype.lower() == "call":
            lower_bdd, upper_bdd = 0, self.dS
        elif model.otype.lower() == "put":
            lower_bdd, upper_bdd = -self.dS, 0
        else:
            raise ValueError('Invalid model type')
            
        lower_bdd = lower_bdd * self.A[0]
        upper_bdd = upper_bdd * self.C[-1]
        return matrix_left, matrix_right, lower_bdd, upper_bdd

    def get_price(self, model: Any) -> List[np.ndarray]:
        self._load_sim(model)
        matrix_left, matrix_right, lower_bdd, upper_bdd = self._prepare_matrix(model)
        
        # Clean up temporary large arrays
        del (self.A, self.B, self.C, self.dS)
        
        # Initial Condition (Payoff)
        out = model.payoff(self.asset_samples)
        total_output = [out]

        # Time stepping
        for time in range(1, self.time_no):
            mat_left = matrix_left[-time - 1].toarray()
            mat_right = matrix_right[-time].toarray()
            # Truncate to match inner points
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

    def _load_sim(self, model: Any) -> None:
        super()._load_sim(model)
        # SOR / LSOR pre-calculation for American options
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

    def _prepare_matrix(self, model: Any) -> Tuple[List, List, List, np.ndarray, np.ndarray]:
        # Using self.A, self.B, self.C from _load_sim
        
        matrix_right = [diags((self.A[:, i], 1+self.B[:, i], self.C[:, i]), offsets=[0, 1, 2],
                              shape=(self.asset_no, self.asset_no + 2)) for i in range(self.time_no)]
        
        # These seem unused in main loop? AmeSolver overrides get_price.
        # matrix_left is not used in AmeSolver get_price below, but L/U decomp matrices are.
        
        matrix_Lleft = [diags(
            [self.L[:, i], 1], [-1, 0], shape=(self.asset_no-2, self.asset_no-2)) for i in range(self.time_no)]
        matrix_Uleft = [diags([self.H[:, i], -self.C[1:-1, i]], offsets=[0, 1],
                              shape=(self.asset_no-2, self.asset_no-2)) for i in range(self.time_no)]
        
        if model.otype == 'call':
            upper_bdd = np.maximum(self.high_val_scaled - model.strike,
                                   self.high_val_scaled * np.exp(-back_quad(model.div[0], self.time_samples)) -
                                   model.strike * np.exp(-back_quad(model.int_rate, self.time_samples)))
            lower_bdd = 0.0 # scalar or array?
        elif model.otype == 'put':
            lower_bdd = np.minimum(model.strike - self.low_val_scaled,
                                   -self.low_val_scaled * np.exp(-back_quad(model.int_rate, self.time_samples)) +
                                   model.strike * np.exp(-back_quad(model.div[0], self.time_samples)))
            upper_bdd = 0.0
        else:
            raise ValueError('Unknown option type')
        return matrix_right, matrix_Lleft, matrix_Uleft, lower_bdd, upper_bdd

    def get_price(self, model: Any, beautify: bool = True) -> np.ndarray:
        self._load_sim(model)
        matrix_right, matrix_Lleft, matrix_Uleft, lower_bdd, upper_bdd = self._prepare_matrix(model)

        # Boundary adjustments
        # Ensure lower_bdd is array if 0
        if np.isscalar(lower_bdd): lower_bdd = np.zeros(self.time_no)
        if np.isscalar(upper_bdd): upper_bdd = np.zeros(self.time_no)

        lower_bdd = lower_bdd * self.A[1]
        upper_bdd = upper_bdd * self.C[-2]
        del (self.A, self.B)
        
        out = model.payoff(self.asset_samples)
        out[[0, -1]] = 0 
        begin = out.copy()
        total_output = [begin]
        
        if model.otype.lower() == 'call':
            for time in range(1, self.time_no):
                mat_Lleft = matrix_Lleft[-time - 1].toarray()
                # mat_Uleft is used? No, iterative method logic here
                # Wait, original code:
                # out[1:-1] = np.linalg.solve(mat_Lleft, (mat_right @ out[1:-1]).ravel() + extra_vec)
                # Then loop to update out[-i]
                
                mat_right = matrix_right[-time].toarray()[1:-1, 2:-2]
                extra_vec = np.zeros(self.asset_no-2)
                extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                    upper_bdd[-time] + upper_bdd[-time - 1]
                    
                # Forward sweep (using L)
                out[1:-1] = np.linalg.solve(
                    mat_Lleft, (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
                
                # Backward sweep (using U implicitly in loop?)
                for i in range(2, self.asset_no):
                    # Brennan-Schwartz algorithm / Projected SOR
                    out[-i] = max((out[-i] + self.C[-i, time] * out[1-i])/self.H[1-i, time], begin[-i])
                total_output.append(out.copy())
                
        if model.otype.lower() == 'put':
            for time in range(1, self.time_no):
                mat_Uleft = matrix_Uleft[-time-1].toarray()
                mat_right = matrix_right[-time].toarray()[1:-1, 2:-2]
                extra_vec = np.zeros(self.asset_no-2)
                extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                    upper_bdd[-time] + upper_bdd[-time - 1]
                
                # Backward sweep first?
                out[1:-1] = np.linalg.solve(
                    mat_Uleft, (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
                
                for i in range(1, self.asset_no - 1):
                    out[i] = max(
                        (out[i] - self.L[i - 2, time] * out[i-1]), begin[i])
                total_output.append(out.copy())
                
        total_output.reverse()
        del (self.L, self.H, self.C, self.dS)
        
        # Beautify result (smoothing boundaries)
        if beautify:
            total_output = np.array(total_output)
            total_output[:, [0, -1]] = 2 * total_output[:, [1, -2]] - total_output[:, [2, -3]]
            
        return total_output

class BarSolver(EurSolver):

    def _prepare_matrix(self, model: Any) -> Tuple[List, List, np.ndarray, np.ndarray]:
        matrix_left, matrix_right, _, _ = super()._prepare_matrix(model)
        lower_bdd_bar, upper_bdd_bar = model.barrier
        
        # If barrier is constant
        # Create array for time steps
        # This logic in original code was commented out or partial.
        # We need boundary conditions for the PDE solver at the grid boundaries, 
        # but for Barrier option, the grid boundaries ARE the barriers if we mesh it that way.
        # But here we use fixed grid (low_val, high_val) and check barrier?
        # "damp_layer = np.where..." in get_price suggests we enforce barrier on the grid.
        
        # The boundary conditions returned here are for the matrix solver (edges of grid).
        # For barrier option, usually we set value to rebate at barrier.
        
        lower_bdd = np.full(self.time_no, lower_bdd_bar)
        upper_bdd = np.full(self.time_no, upper_bdd_bar)
        
        # Override with rebates?
        # Actually, EurSolver uses lower_bdd/upper_bdd as Dirichlet conditions.
        # If the grid extends beyond barrier, we should be careful.
        # The original code seems to rely on enforcing it inside get_price via damp_layer.
        
        # Let's keep original logic for boundary conditions (Dirichlet at infinity/zero) but adjusted for barrier?
        # Original code:
        if model.otype == 'call':
             # Upper bound: Call value at very high price -> S - K*exp(-rT)
             # But if barrier is active (Knock-out), value is Rebate?
             # Assuming Knock-out.
             pass
        
        return matrix_left, matrix_right, lower_bdd, upper_bdd

    def get_price(self, model: Any) -> List[np.ndarray]:
        self._load_sim(model)
        matrix_left, matrix_right, lower_bdd, upper_bdd = self._prepare_matrix(model)
        
        # Handle non-finite boundaries (inf barrier)
        if np.isfinite(lower_bdd).all():
             lower_bdd = lower_bdd * self.A[1]
        else:
             lower_bdd = np.zeros(self.time_no)

        if np.isfinite(upper_bdd).all():
             upper_bdd = upper_bdd * self.C[-2]
        else:
             upper_bdd = np.zeros(self.time_no)

        del (self.A, self.B, self.C, self.dS)
        
        lower_bar, higher_bar = model.barrier
        out = model.payoff(self.asset_samples)
        
        # Apply barrier to initial condition
        damp_layer = np.where((self.asset_samples <= lower_bar)
                              | (self.asset_samples >= higher_bar))
        out[damp_layer] = model.rebate
        
        total_output = [out]
        
        for time in range(1, self.time_no):
            mat_left, mat_right = matrix_left[-time - 1].toarray(), matrix_right[-time].toarray()
            mat_left, mat_right = mat_left[1:-1, 2:-2], mat_right[1:-1, 2:-2]
            
            extra_vec = np.zeros(self.asset_no-2)
            extra_vec[[0, -1]] = lower_bdd[-time] + lower_bdd[-time - 1], \
                upper_bdd[-time] + upper_bdd[-time - 1]
                
            out[1:-1] = np.linalg.solve(mat_left,
                                        (mat_right @ out[1:-1]).ravel() + extra_vec).reshape(-1, 1)
            
            # Enforce barrier
            out[damp_layer] = model.rebate
            
            total_output.append(out.copy())
            
        total_output.reverse()
        return total_output
