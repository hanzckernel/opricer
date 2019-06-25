# -*- coding: utf-8 -*-
import json
import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import numpy as np

import dash_table
import dash_table.FormatTemplate as FormatTemplate
from dash_table.Format import Format, Scheme, Sign, Symbol

from plotly import graph_objs as go
from datetime import datetime, date
from dash.exceptions import PreventUpdate
from ..app import app
import json
import pandas_datareader.data as web
import random
from opricer.model import models
from opricer.algo import pde, analytics, mc


def modal():
    return html.Div(
        html.Div([html.Div([
            # modal header
                html.Div(
                    [
                    html.Span(
                        "New Option",
                        style={
                            "color": "#506784",
                            "fontWeight": "bold",
                            "fontSize": "20",
                        },
                    ),
                    html.Span(
                        "x",
                        id="option_modal_close",
                        n_clicks=0,
                        style={
                            "float": "right",
                            "cursor": "pointer",
                            "marginTop": "0",
                            "marginBottom": "17",
                        },
                    ),
                ],
                    className="row",
                    style={"borderBottom": "1px solid #C8D4E3"},
                    ),


            # modal form
                html.Div([
                    html.P('Name of Asset'),

                    dcc.Input(id="asset_name", type='text',
                    placeholder='Asset Name'),

                    html.P("Spot Price"),

                    dcc.Input(id="spot", type='number',
                    step=10, min= 0,
                    placeholder='Spot Price'),

                    html.P("Risk-free interest rate (%)"),

                    dcc.Input(id="int_rate", type='number',
                    value = 0,
                    placeholder='Risk-free rate'),

                    html.P("Volatility (%)"),

                    dcc.Input(id="volatility", type='number',
                    step=0.5, min= 0,
                    placeholder='Volatility'),

                    html.P("Dividend (%)"),

                    dcc.Input(
                    id="dividend", type='number',
                    step=0.5, min= 0, value=0,
                    placeholder='Dividend',
                ),
                ],
                    className="row",
                    style={"paddingTop": "2%"},
                    ),

            # submit button
                html.Button(
                    "Submit",
                    id="submit_new_option",
                    type='submit',
                    n_clicks=0,
                    className="button button--primary add"
                    ),

                html.P(children = 'this is not fun', id='missing_warning', 
                    style={'display':'none', 'color':'red'})
            ],
            className="modal-content",
            style={"textAlign": "center"},
            )
            ],
            className="modal",
            ),
        id="option_modal",
        style={"display": "none"},
    )


layout = [
    # top controls
    html.Div(
        [html.Div(
            [dcc.DatePickerRange(
                id="spot_date",
                start_date_placeholder_text='Choose your spot date',
                end_date_placeholder_text='Choose your strike date',
                display_format='MMM Do, YYYY',
                clearable=False, className="row",
                start_date='2015-1-1',
                end_date='2016-1-1',
            ),

                dcc.RadioItems(id='ocate', options=[
                    {'label': 'Euroption Option', 'value': 'EurOption'},
                    {'label': 'American Option', 'value': 'AmeOption'},
                    {'label': 'Barrier Option', 'value': 'BarOption'}], value='EurOption',
                className="row",
                labelStyle={'display': 'inline-block', 'color': 'white', 'fontSize': '20px',
                            'margin-right': '20px'}),
                dcc.RadioItems(id='otype', options=[
                    {'label': 'Call Option', 'value':'call'},
                    {'label': 'Put Option', 'value':'put'}
                    ], value='call', className="row",
                labelStyle={'display': 'inline-block', 'color': 'white', 'fontSize': '20px',
                            'margin-right': '20px'},
                ),
                dcc.Input(id='strike', value=100, type='number'),

                ],
            className="six columns",
            style={"marginBottom": "10", "padding-bottom": "10px"}),

         html.Div(
            [
                html.Div(html.Span(
                    "Add New Underlying Asset",
                    id="new_underlying",
                    n_clicks=0,
                    className="button button--primary add",
                    style={"float": "right", 'width': 'auto'},
                ), className="row"),
                dcc.Dropdown(id='underlying_pool',
                             options=[],
                             value=[],
                             placeholder='Your Underlying Pool', multi=True, className="row"),
                html.Button('Clear All Stocks', id='option-clear', n_clicks=0,
                            className="row"),
                dcc.Input(id='clear_all', value=0, style={'display': 'none'}),
            ], className='six columns'
        ),

         ], className="row"
    ),

    # add button


    # indicators row
    html.Div([
        html.Div([
            html.P("Asset List", className='title'),
                    dash_table.DataTable(
                        id='asset_info',
                        columns=[{'name': 'Name', 'id': 'Name', 'editable': False},
                                 {'name': 'Spot Price', 'id': 'spot', 'type': 'numeric',
                                "format":FormatTemplate.money(2)},
                                 {'name': 'Interest Rate', 'id': 'int_rate', 'type': 'numeric',
                                "format":FormatTemplate.percentage(2)},
                                 {'name': 'Volatiltiy', 'id': 'volatility', 'type': 'numeric',
                                 "format":FormatTemplate.percentage(2)},
                                 {'name': 'Dividend', 'id': 'dividend', 'type': 'numeric',
                                 "format":FormatTemplate.percentage(2)}
                                 ],
                        style_table={'maxHeight': '200px', 'overflowY': 'scroll',
                        'height':'200px'},
                        row_deletable=True,
                        editable=True,
                        data=[],
                    ),
            html.P('Correlation Structure', className='title'),
            html.Div(
                [
                    dash_table.DataTable(
                        id='corr_matrix',
                        columns=[{'id': 'Ticker', 'name': ' Asset Name', 'editable': False},
                                 {'id': 'Test', 'name': 'Test'}],
                        data=[{'Ticker': 'Test', 'Test': 1.0}],
                        editable=True,
                        style_table={'maxHeight': '200px', 'overflowY': 'scroll',
                        'height': '200px'},
                    ),
                ], className="row", style={"row-gap": "200px"}
            )
        ],
            className='six columns'
        ),
        html.Div([
            html.P('Correlation Heatmap', className='title'),
            dcc.Graph(id='heat-map'),
        ],
            className='six columns'),
    ], className="row"),
    # charts row div
    html.Button('confirm', id='confirm', n_clicks=0, className="row", style={}),
    html.Div(
        [html.P("The Fair Option Price", className='title'),
         dcc.Graph(id='opricer_graph', style={"height": "100vh", "width": "98%"}),
        html.Div('this is test', id='test',),
         ],
        className="row"),
    html.Div([html.Div([
        html.P('Your OHLC Diagram'),
        dcc.Graph(id='stock-ohlc', style={"height": "90vh", "width": "98%"}),
    ], className='six columns'),
        html.Div([
            html.P('Your Candlestick Diagram'),
            dcc.Graph(id='stock-candlestick', style={"height": "90vh", "width": "98%"})
        ], className='six columns')], className="row"),
    # tables row div
    html.Div(
        [modal()],
        className="row",
        style={"marginTop": "5px", "max height": "200px"},
    ),
]


@app.callback([Output('corr_matrix', 'columns'),
               Output('corr_matrix', 'data')],
              [Input('underlying_pool', 'value'),
               Input('corr_matrix', 'data_timestamp')],
              [State('corr_matrix', 'data'),
     State('corr_matrix', 'data_previous')])
def update_corr_matrix(tickers, timestamp, data, data_prev):
    '''
    Inspired by https://stackoverflow.com/questions/26033301/
    Workaround here is very nasty. Any elegant solution is welcome.
    '''
    # check if there is a change in columns:
    try:
        secret_df = pd.DataFrame(data).set_index('Ticker')
        if set(tickers) != set(secret_df.columns):
            # secret_df.sort_index(axis=0, inplace=True)
            # secret_df.sort_index(axis=1, inplace=True)
            if set(secret_df.columns) - set(tickers):  # if remove tickers
                secret_df = secret_df.loc[tickers, tickers]
            elif set(tickers) - set(secret_df.columns):  # if add tickers
                new_ticker = (set(tickers) - set(secret_df.columns)).pop()
                secret_df.loc[new_ticker, new_ticker] = 1.0
        elif data != data_prev and data_prev:
            changed, unchanged = [[x, y] for x,y in zip(data, data_prev) if x != y][0]
            item_changed = (set(changed.items()) - \
                            set(unchanged.items())).pop()
            item_changed[1]
            i, j = changed['Ticker'], item_changed[0]
            if i == j:
                secret_df.at[i, j] = 1.0
            else:
                try:
                    if float(item_changed[1]) > 1 or float(item_changed[1]) < -1:
                        secret_df.at[i, j] = secret_df.at[j, i]
                    else:
                        secret_df.at[j, i] = secret_df.at[i, j]
                except ValueError:
                    secret_df.at[i, j] = secret_df.at[j, i]

            
    except KeyError:
        secret_df = pd.DataFrame(1, index=tickers, columns= tickers)
        secret_df.index.name = 'Ticker'
    finally:
        secret_df.sort_index(axis=0, inplace=True)
        secret_df.sort_index(axis=1, inplace=True)
        secret_df.reset_index(inplace=True)
        columns = [{'label': ticker, 'id': ticker} for ticker in secret_df.columns]
        columns[0]['editable'] = False
        data = secret_df.to_dict('records')
    return columns, data

@app.callback(
    Output('heat-map', 'figure'),
    [Input('corr_matrix', 'data'),
     Input('corr_matrix', 'columns')])
def display_output(rows, columns):
    return {
        'data': [{
            'type': 'heatmap',
            'z': [[row.get(c['id'], None) for c in columns[1:]] for row in rows],
            'y': [c['id'] for c in columns[1:]],
            'x': [c['id'] for c in columns[1:]],
            'colorscale':'Viridis'
        }]
    }


@app.callback(
    [Output("option_modal_close", 'n_clicks'), Output('missing_warning', 'children'),
    Output('missing_warning', 'style'), Output('asset_info', 'data'),
    Output('clear_all', 'value')],
    [Input("submit_new_option", "n_clicks"), Input('option-clear', 'n_clicks')],
    [State('asset_name', 'value'),
    State('spot', 'value'), State('int_rate', 'value'),
    State('volatility', 'value'), State('dividend', 'value'), 
    State('missing_warning', 'style'),
    State('underlying_pool', 'options'), State('asset_info', 'data'),
     State('clear_all', 'value')]
)
def check_validity(n, clear_btn, name, spot, 
                int_rate, vol, div, style, options, data, clear_state):
    message = ''
    if clear_btn and clear_btn !=0:
        if int(clear_btn) != clear_state:
            return 1, message, style, [], int(clear_btn)
    else:
        if not name:
            message = 'Enter asset name'
        elif name in [set(option.values()).pop() for option in options]:
            message = 'Asset with same name already exists. Try another one'
        elif not spot or spot < 0:
            message = 'Spot price must not be empty or negative'
        elif vol < 0:
            message = f'{vol} is not valid. Volatility must be positive'
        elif div < 0 or div > 100:
            message = f'{div} is not valid. Dividend must be positive and smaller than 1'
    
    if message:
        style['display']='block'
        return 0, message, style, data, clear_state
    else:
        data.append({'Name': name, 'spot': spot, 'int_rate': float(int_rate)/100, 
                    'volatility': float(vol)/100, 'dividend':float(div)/100})
        return 1, message, style, data, clear_state

@app.callback([Output('underlying_pool', 'value'), Output('underlying_pool', 'options')],
              [Input('asset_info', 'data')])
def update_ticker(data):
    # new_ticker = str.upper("".join(new_ticker.split()))
    nameLst = [row['Name'] for row in data]
    options = [{'label': name, 'value': name} for name in nameLst]
    return nameLst, options

# reset to 0 add button n_clicks property
@app.callback(
    Output("new_underlying", "n_clicks"),
    [Input("option_modal_close", "n_clicks")],
)
def close_modal_callback(n):
    if n > 0:
        return 0

@app.callback(
    Output("option_modal", "style"), [Input("new_underlying", "n_clicks")]
)
def display_stock_modal_callback(n):
    try:
        if n > 0:
            return {"display": "block"}
        else:
            return {"display": "none"}
    except TypeError:
        raise PreventUpdate

# Input("submit_new_option", "n_clicks")

#### Here begins the Option Pricing!!! ####
@app.callback(
    Output('opricer_graph', 'figure'),
    [Input('confirm', 'n_clicks')],
    [State('asset_info', 'data'), State('ocate', 'value'), State('otype', 'value'),
    State('spot_date', 'start_date'), State('spot_date', 'end_date'), State('strike', 'value')
    ]
)
def plot_graph(n_clicks, data, ocate, otype, spot_date, strike_date, strike):
    if data:
        we_use = data[0]
        start = datetime.strptime(spot_date, '%Y-%m-%d')
        end = datetime.strptime(strike_date, '%Y-%m-%d')
        asset = models.Underlying(start, we_use['spot'])
        option = getattr(models, ocate)(end, otype)
        option._attach_asset(strike, asset)
        solver = analytics.AnalyticSolver(high_val=2, low_val=0)
        price = solver(option)
        traces= []
        traces.append(
            go.Surface(
                        x=solver.asset_samples.flatten(),
                        y=solver.time_samples,
                        z=price,
                        opacity=0.7,
                        # mode='lines',
                        # marker={'size': 5,'line': {'width': 0.5, 'color': 'white'}},
                        name='Analytic Solver',
                        colorscale='Viridis'
                    )
            # go.Scatter(x=solver.asset_samples.flatten(),
            #             # y=solver.time_samples,
            #             y=price[:, -1],
            #             opacity=0.7,
            #             mode='lines',
            #             # marker={'size': 5,'line': {'width': 0.5, 'color': 'white'}},
            #             name='Analytic Solver',
            #             )
                    )

        graph_layout = go.Layout(
                xaxis={'title': 'Asset'},
                yaxis={'title': 'Price'},
                hovermode='closest',

            )
        figure = {
                'data': traces, 'layout': graph_layout
            }
        return figure
    else:
        raise PreventUpdate
