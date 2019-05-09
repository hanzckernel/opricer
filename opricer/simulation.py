# from data import models
# from algo import pde
# %%
from scipy.sparse import diags
import numpy as np
import datetime
from opricer.data import models
from opricer.algo import pde

a = models.EurOption("put", datetime.datetime(2011, 1, 1))
b = models.Underlying(datetime.datetime(2010, 1, 1), 100, dividend=0.0)
a.__dict__
a._attach_asset(100, b)
# %%
print(pde.option_price_begin(a))
