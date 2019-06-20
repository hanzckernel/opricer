#!/usr/bin/env python
# coding: utf-8

import json
import pandas as pd
from urllib.request import Request, urlopen


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


def scrap_website():
    # Creating a ticker list by forcing it
    req = Request('https://www.stockmarketclock.com/exchanges',
                  headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()
    exchange_dict = pd.read_html(webpage)[0]

    # Drop first x in MIC, and rename labels
    exchange_dict['MIC'].loc[exchange_dict['MIC'].str[0]
                             == 'X'] = exchange_dict['MIC'].str[1:]
    exchange_dict.rename(index=str, columns={
                         "MIC": "Exchange", 'Name': "SE_Name"}, inplace=True)

    # Creating dataframes using downloaded xlsx

    xls = pd.ExcelFile('./data/yahoo_data.xlsx')

    stock_df = pd.read_excel(xls, 'Stock', header=3)
    ETF_df = pd.read_excel(xls, 'ETF', header=3)
    idx_df = pd.read_excel(xls, 'Index', header=3)
    currency_df = pd.read_excel(xls, 'Currency', header=3)

    # drop nan for those tickers which do not have name

    stock_df.dropna(axis=0, subset=['Name'], inplace=True)
    ETF_df.dropna(axis=0, subset=['Name'], inplace=True)
    idx_df.dropna(axis=0, subset=['Name'], inplace=True)
    currency_df.dropna(axis=0, subset=['Name'], inplace=True)

    # Further dropping tickers with outdated stock exchanges
    stock_df.drop(stock_df.columns[-3:], axis=1, inplace=True)
    stock_df.rename(columns={"Category Name": 'Category'}, inplace=True)
    stock_df = stock_df.merge(
        exchange_dict[['Exchange', 'SE_Name']], on='Exchange', how='inner')

    for df in [stock_df, currency_df, idx_df, ETF_df]:
        df.fillna(value={'Exchange': 'Unknown',
                         'Category': 'Others'}, inplace=True)
    #     df.replace('N/A', 'Unknown', inplace=True)

    ETF_df.to_csv('./data/ETF.csv', index=False)
    idx_df.to_csv('./data/index.csv', index=False)
    currency_df.to_csv('./data/currency.csv', index=False)
    stock_df.to_csv('./data/stock.csv', index=False)

    dic1 = gen_dropdown_options(stock_df, ['Name', 'Ticker'])
    dic2 = gen_dropdown_options(ETF_df, ['Name', 'Ticker'])
    dic3 = gen_dropdown_options(currency_df, ['Name', 'Ticker'])
    dic4 = gen_dropdown_options(idx_df, ['Name', 'Ticker'])

    dic = dic1 + dic2 + dic3 + dic4
    with open('ticker.json', 'w') as fp:
        json.dump(dic, fp)


# with open("ticker.json", "r") as read_file:
#     ticker = json.load(read_file)
