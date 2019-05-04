from models import EurOption, AmeOption, Underlying
from datetime import datetime


# %%
a = EurOption("A", datetime(2010, 1, 1))
b = Underlying('A', datetime(2009, 1, 1), 100)
a._attach_asset(100, b)

# gen_coeff(a)
