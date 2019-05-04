import datetime
import numpy as np
from scipy.sparse import diags
from scipy import integrate
from opricer.data import models


def gen_grid(low_val, high_val, end_time, start_time=0, dt=0.01, dS=10):
    time_samples = np.arange(start_time, end_time + dt, dt)
    asset_samples = np.arange(low_val + dS, high_val, dS)
    X, Y = np.meshgrid(asset_samples, time_samples)
    return X, Y

# time_samples = X[0], asset_samples =
# def gen_boundary_condition(model, otype = 'call'):
#     if otype == 'call':


def prepare_mat(model):
    '''
    def load_sim(model):
        """
        Currently writing all simulation part into one. Might consider split it
        when code-size increases.
        Generate paramteters
        """
    '''
    end_time, [coef2, coef1, coef0] = model.gen_pde_coeff()
    spot_price = sum(model.spot_price)  # TODO: Change this part when vectorize
    X, Y = gen_grid(0.3 * spot_price, 1.7 * spot_price, end_time)
    """
    Prepare coefficient now. For convience we follow convention of Wilmott.
    """
    time_no = X.shape[0]
    step_no = X.shape[1]
    dS, dt = X[0, 1] - X[0, 0], Y[1, 0] - Y[0, 0]
    v1, v2 = dt / (dS ** 2), dt / dS
    A = (v1 * coef2(X, Y)/2 - v2 * coef1(X, Y)/4).T
    B = (-v1 * coef2(X, Y) + dt * coef0(X, Y)/2).T
    C = (v1 * coef2(X, Y)/2 + v2 * coef1(X, Y)/4).T
    """
    This part accounts for boundary condition.
    """
    A_first, C_last = A[0], C[-1]
    lower = np.zeros(time_no)
    upper = 1.7 * spot_price - model.strike * np.exp(- 0.05 * (Y[-1, -1]-Y[:, 0]))
    # TODO: hard-coded. need to changed
    lower_bdd = lower * A_first
    upper_bdd = upper * C_last

    def pricing_operator(t, bdd='Dirichlet'):
        time_loc = int(round(t / dt))
        base_matrix = diags([A[:, time_loc], B[:, time_loc], C[:, time_loc]],
                            [0, 1, 2], shape=(step_no, step_no+2))
        off_diag = diags([1], [1], shape=(step_no, step_no+2))
        matrix_left = -base_matrix + off_diag
        matrix_right = base_matrix + off_diag
        return matrix_left.A, matrix_right.A

    outlayer = model.payoff(X[0])
    total_output = outlayer
    """the following is not fully optimised.
    But as that is not related to linear system, we can ignore it (partially)"""
    for time_pt in range(1, time_no):
        t = end_time - time_pt * dt  # time stands for the time TO BE CALCULATED
        matrix_left, matrix_right = pricing_operator(t)[0], pricing_operator(t+dt)[1]
        mat_left, mat_right = matrix_left[:, 1:-1], matrix_right[:, 1:-1]
        """Note here extra_vec is subject to Z_2-error"""
        extra_vec = np.zeros(step_no)
        extra_vec[[0, -1]] = lower_bdd[-time_pt] + \
            lower_bdd[-time_pt - 1], upper_bdd[-time_pt] + upper_bdd[-time_pt-1]
        outlayer = np.linalg.solve(mat_left, mat_right @ outlayer + extra_vec)
        total_output = np.vstack((total_output, outlayer))
    return total_output
# def option_price_all(model):


def option_price_begin(asset):
    return option_price_all(asset)[-1]

# In[ ]:


'''all the boundary_condition will be initiated after testing'''


def boundary(option='call', barrier=False):
    if barrier and option == 'call':
        lower_bdd = np.zeros(time_no)
        upper_bdd = -strike_price * \
            np.exp(-back_quad(int_rate, time_samples)) + high_val * \
            np.exp(-back_quad(div_rate, time_samples))
    if barrier and option == 'put':
        lower_bdd = -low_val * np.exp(-back_quad(div_rate, time_samples)) + \
            strike_price * np.exp(-back_quad(int_rate, time_samples))
        upper_bdd = np.zeros(time_no)
    else:
        raise Exception('Unknown option type')

 # %%


a = models.EurOption('A', datetime.datetime(2011, 1, 1))
b = models.Underlying('b', datetime.datetime(2010, 1, 1), 100)

a._attach_asset(100, b)
len(a._time)
a.payoff(np.array([1, 2, 3]))
# %%
prepare_mat(a)[-1]

# %%
