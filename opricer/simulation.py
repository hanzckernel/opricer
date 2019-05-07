# from data import models
# from algo import pde
from scipy.sparse import diags
import numpy as np
import datetime
from opricer.data import models
from opricer.algo import pde

a = models.BarOption("call", datetime.datetime(2011, 1, 1), rebate=12)
b = models.Underlying(datetime.datetime(2010, 1, 1), 100, dividend=0.0)

a.__dict__
a._attach_asset([80, None], 100, b)
a.otype
# %%
pde.option_price_begin(a)
