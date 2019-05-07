import datetime
import numpy as np
from scipy.sparse import diags
from scipy import integrate
from opricer.data import models

a = models.EurOption('call', datetime.datetime(2011, 1, 1))
b = models.Underlying(datetime.datetime(2010, 1, 1), 100)
a._attach_asset(100, b)

# %%


def gen_grid(low_val, high_val, end_time, start_time=0, dt=0.01, dS=10):
    time_samples = np.arange(start_time, end_time + dt, dt)
    asset_samples = np.arange(low_val, high_val + dS, dS)
    X, Y = np.meshgrid(asset_samples, time_samples)
    return X, Y


def load_sim(model):
    end_time, [coef2, coef1, coef0] = model.gen_pde_coeff()
    spot_price = sum(model.spot_price)  # TODO: Change this part when vectorize
    X, Y = gen_grid(0, 5 * spot_price, end_time)
    # TODO: This price range can later be scaled up to paramters.
    time_no = X.shape[0]
    step_no = X.shape[1]
    dS, dt = X[0, 1] - X[0, 0], Y[1, 0] - Y[0, 0]
    v1, v2 = dt / (dS ** 2), dt / dS
    A = (v1 * coef2(X, Y) / 2 - v2 * coef1(X, Y) / 4).T
    B = (-v1 * coef2(X, Y) + dt * coef0(X, Y) / 2).T
    C = (v1 * coef2(X, Y) / 2 + v2 * coef1(X, Y) / 4).T
    return A, B, C, X, Y, time_no, step_no, spot_price


def boundary_condition(model):
    """
    This part accounts for boundary condition. By default we use Dirichlet
    boundary condition for barrier option. If it's not barrier option, then for
    vanilla option we switch to Neumann boundary condition.

    WARNING: To make sure this boundary_condition function properly, we need to
    make the simulation range large enough.
    """
    A, B, C, X, Y, time_no, step_no, spot_price = load_sim(model)
    try:  # use Dirchlet boundary condition
        lower_lvl, upper_lvl = model.barrier
        lower = np.full(time_no, float(lower_lvl or 0))  # change None to 0
        upper = np.full(time_no, float(upper_lvl or 0))
        if model.otype == 'call':
            lower = np.maximum(np.zeros(time_no), lower)
            upper = np.minimum(upper,
                               X[-1, -1] * np.exp(-model.div * (Y[-1, -1] - Y[:, 0])) -
                               model.strike * np.exp(-model.int_rate(Y[:, 0]) * (Y[-1, -1] - Y[:, 0])))
        # TODO: hard-coded. need to changed
        elif model.otype == 'put':
            upper = np.maximum(np.zeros(time_no), upper)
            lower = np.minimum(lower,
                               -X[0, 0] * np.exp(-model.int_rate(Y[:, 0]) * (Y[-1, -1] - Y[:, 0])) +
                               model.strike * np.exp(-model.div * (Y[-1, -1] - Y[:, 0])))
        else:  # use Neumann Boundary condition
            raise ValueError('Unknown option type')
    except AttributeError:  # use von Neumann boundary condition
        if model.otype == "call":
            lower = 0
            upper = X[0, 1] - X[0, 0]
        if model.otype == "put":
            lower = X[0, 0] - X[0, 1]  # only a concise notation of previous
            upper = 0
    except:
        raise Exception('Invalid model type')
    finally:
        return lower, upper


def option_price_all(model):
    """
    Prepare coefficient now. For convience we follow convention of Wilmott.
    """
    A, B, C, X, Y, time_no, step_no, spot_price = load_sim(model)
    lower, upper = boundary_condition(model)
    """
    Prepare 3D tensor (time-list of sparse diagonal matrix) for simulation.
    Later only expand one slice to full matrix so as to save storage.
    """
    matrix_left = [diags((-A[:, i], 1-B[:, i], -C[:, i]), offsets=[0, 1, 2],
                         shape=(step_no, step_no + 2)) for i in range(time_no)]
    matrix_right = [diags((A[:, i], 1+B[:, i], C[:, i]), offsets=[0, 1, 2],
                          shape=(step_no, step_no + 2)) for i in range(time_no)]

    """the following is not fully optimised.
    But as that is not related to linear system, we can ignore it (partially)"""
    try:  # for barrier option case, use Dirchlet.
        lower_bar, higher_bar = model.barrier
        outlayer = model.payoff(X[0][1:-1])
        total_output = [outlayer]
        lower_bdd = lower * A[1]
        upper_bdd = upper * C[-2]
        for time_pt in range(1, time_no):
            mat_left, mat_right = matrix_left[-time_pt - 1].A, matrix_right[-time_pt].A
            mat_left, mat_right = mat_left[1:-1, 2:-2], mat_right[1:-1, 2:-2]
            extra_vec = np.zeros(step_no-2)
            extra_vec[[0, -1]] = lower_bdd[-time_pt] + lower_bdd[-time_pt - 1], \
                upper_bdd[-time_pt] + upper_bdd[-time_pt - 1]
            outlayer = np.linalg.solve(mat_left, mat_right @ outlayer + extra_vec)
            outlayer = np.clip(outlayer, lower_bar, higher_bar)
            outlayer[outlayer == lower_bar] = model.rebate
            outlayer[outlayer == higher_bar] = model.rebate
            total_output.append(outlayer)
    except AttributeError:  # For vanilla option case, use von Neumann
        outlayer = model.payoff(X[0])
        total_output = [outlayer]
        lower_bdd = lower * A[0]
        upper_bdd = upper * C[-2]
        for time_pt in range(1, time_no):
            mat_left, mat_right = matrix_left[-time_pt - 1].A, matrix_right[-time_pt].A
            mat_left[:, [2, -3]] += mat_left[:, [0, -1]]
            mat_right[:, [2, -3]] += mat_right[:, [0, -1]]
            mat_left, mat_right = mat_left[:, 1:-1], mat_right[:, 1:-1]
            extra_vec = np.zeros(step_no)
            extra_vec[[0, -1]] = lower_bdd[-time_pt] + lower_bdd[-time_pt - 1],
            upper_bdd[-time_pt] + upper_bdd[-time_pt - 1]
            outlayer = np.linalg.solve(mat_left, mat_right @ outlayer + extra_vec)
            total_output.append(outlayer)
    return total_output


def option_price_begin(model):
    return option_price_all(model)[-1]

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
