
# In[1]:


# from data import models


from scipy.sparse import diags
from scipy import integrate

syspath


# %%


# %%

X, Y = np.meshgrid(asset_samples, time_samples)


#        time_samples = np.arange(start_time, end_time+dt, dt)
#        asset_samples = np.arange(S_low+dS, S_high, dS)
#        time_no = time_samples.size
#        step_no = asset_samples.size


# In[2]:


v1 = dt / (dS ** 2)
v2 = dt / dS

v1, v2


# In[3]:


a, b, c = second_order_coeff(X, Y).T, first_order_coeff(X, Y).T, zero_order_coeff(X, Y).T
A = v1 * a/2 - v2 * b/4
B = -v1 * a + dt * c/2
C = v1 * a/2 + v2 * b/4

# all these start from S_1, 0 and end at S_{M-1} , T

'''This is a test block'''
A_first, C_last = A[0], C[-1]

lower = np.zeros(time_no)
upper = S_high - strike_price * np.exp(- 0.05 * (end_time-time_samples))
# lower_bdd and Upper_bdd
lower_bdd = lower * A_first
upper_bdd = upper * C_last
'''This is a test block'''


# In[4]:


def pricing_operator(t, bdd='Dirichlet'):
    time_loc = round((t - start_time)/dt)
    base_matrix = diags([A[:, time_loc], B[:, time_loc], C[:, time_loc]],
                        [0, 1, 2], shape=(step_no, step_no+2))
    off_diag = diags([1], [1], shape=(step_no, step_no+2))
    if bdd == 'Dirichlet':
        matrix_left = -base_matrix + off_diag
        matrix_right = base_matrix + off_diag
    elif bdd == 'Neumann':
        pass
    else:
        raise Exception('Unknown boundary condition')
    return matrix_left.A, matrix_right.A


def option_price(asset):
    outlayer = payoff(asset)
    total_output = outlayer
    """the following is not fully optimised.
    But as that is not related to linear system, we can ignore it (partially)"""
    for time_pt in range(1, time_no):
        time = end_time - time_pt * dt  # time stands for the time TO BE CALCULATED
        matrix_left, matrix_right = pricing_operator(time)[0], pricing_operator(time+dt)[1]
        mat_left, mat_right = matrix_left[:, 1:-1], matrix_right[:, 1:-1]
        """Note here extra_vec is subject to Z_2-error"""
        extra_vec = np.zeros(step_no)
        extra_vec[[0, -1]] = lower_bdd[-time_pt] + \
            lower_bdd[-time_pt - 1], upper_bdd[-time_pt] + upper_bdd[-time_pt-1]
        outlayer = np.linalg.solve(mat_left, mat_right @ outlayer + extra_vec)
        total_output = np.vstack((total_output, outlayer))
    return total_output


def option_price_begin(asset):
    return option_price(asset)[-1]


# In[ ]:


'''all the boundary_condition will be initiated after testing'''


def boundary(option='call', barrier=False):
    if barrier and option == 'call':
        lower_bdd = np.zeros(time_no)
        upper_bdd = -strike_price * \
            np.exp(-back_quad(int_rate, time_samples)) + S_high * \
            np.exp(-back_quad(div_rate, time_samples))
    if barrier and option == 'put':
        lower_bdd = -S_low * np.exp(-back_quad(div_rate, time_samples)) + \
            strike_price * np.exp(-back_quad(int_rate, time_samples))
        upper_bdd = np.zeros(time_no)
    else:
        raise Exception('Unknown option type')
