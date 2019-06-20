import numpy as np
import pandas as pd
import os

def gen_dropdown_options(df, cols):
    if len(cols) == 2:
        df_new = df[cols].drop_duplicates()
        df_new.columns = ['label', 'value']
        dic = df_new.to_dict('record')
    elif len(cols) == 1:
        dic = [{'label': ticker, 'value': ticker}
               for ticker in df[cols[0]].unique()]
    else:
        raise ValueError('Dataframe using too many columns')
    return dic


df = pd.read_csv('../data/exchange.csv')
print(gen_dropdown_options(df, ['SE_Name']))
print(1)
