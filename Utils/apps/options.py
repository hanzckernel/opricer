# -*- coding: utf-8 -*-
import json
import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import dash_table
from plotly import graph_objs as go
from datetime import datetime, date
from dash.exceptions import PreventUpdate
from ..app import app
import json
import pandas_datareader.data as web
import random


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
                dcc.Tabs(
                    id="option_tabs",
                    style={"height": "20",
                           "verticalAlign": "middle"},
                    children=[
                        dcc.Tab(label="European Option",
                                value="EurOption"),
                        dcc.Tab(label="American Option", value="AmeOption"),
                        dcc.Tab(label='Barrier Option', value="BarOption"),
                    ],
                    value="EurOption",
                ),
                html.Div(id='option_tab_content')],
                className="row",
                style={"paddingTop": "2%"},
            ),

            # submit button
            html.Span(
                "Submit",
                id="submit_new_option",
                n_clicks=0,
                className="button button--primary add"
            ),
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
        [
            html.Div(
                dcc.DatePickerSingle(
                    id="date_picker",
                    placeholder='Choose Your Spot Date',
                    display_format='MMM Do, YYYY',
                    # value="D",
                    clearable=False,
                ),
                className="four columns"
            ),
            html.Div(
                dcc.Dropdown(id="ppty_input",
                             options=[{'label': 'Open Price', 'value': 'Open'},
                                      {'label': 'Close Price', 'value': 'Close'},
                                      {'label': 'Daily High', 'value': 'High'},
                                      {'label': 'Daily Low', 'value': 'Low'},
                                      {'label': 'Adjoint Close', 'value': 'Adj Close'}],
                             value='Adj Close',
                             clearable=False),
                className="two columns",
            ),

            # add button
            html.Div(
                html.Span(
                    "Watch New Asset",
                    id="new_stock",
                    n_clicks=0,
                    className="button button--primary add"
                ),
                className="two columns",
                style={"float": "right", 'width': 'auto'},
            ),
        ],
        className="row",
        style={"marginBottom": "10", "padding-bottom": "10px"},
    ),

    # indicators row
    html.Div(
        [dcc.Dropdown(id='total_ticker',
                      options=[{'label': 'AAPL', 'value': 'AAPL'},
                               {'label': 'TSLA', 'value': 'TSLA'}],
                      value=['AAPL'],
                      placeholder='Enter a stock ticker', multi=True, className="ten columns"),
         html.Button(children='Clear All Stocks', id='clear', n_clicks=0,
                     className='two columns'),
         dcc.Input(id='true_clear', value=0, style={'display': 'None'}),
         ],
        className="row",
    ),
    html.Div([html.P('The Correlation Matrix'),
            dash_table.DataTable(
            id='corr_matrix',
            columns=[],
            data=[],
            editable=True,
    )]),
    # charts row div
    html.Div(
        [html.P("Your asset price"),
         dcc.Graph(id='stock-graph', style={"height": "100vh", "width": "98%"},
                   className="ten columns"),
         ]
    ),
    html.Div([html.Div([
        html.P('Your OHLC Diagram'),
        dcc.Graph(id='stock-ohlc', style={"height": "90vh", "width": "98%"},
                  className="ten columns"),
    ], className='six columns'),
        html.Div([
            html.P('Your Candlestick Diagram'),
            dcc.Graph(id='stock-candlestick', style={"height": "90vh", "width": "98%"},
                      className="ten columns")
        ], className='six columns')], className='row'),
    # tables row div
    html.Div(
        [modal()],
        className="row",
        style={"marginTop": "5px", "max height": "200px"},
    ),
]


# @app.callback([Output('total_ticker', 'value'), Output('total_ticker', 'options'),
#                Output('true_clear', 'value')],
#               [Input("submit_new_option", "n_clicks"),
#                Input('clear', 'n_clicks')],
#               [State('submit_input', 'value'),
#                State('total_ticker', 'value'), State(
#                    'total_ticker', 'options'),
#                State('true_clear', 'value')])
# def update_ticker(submit_btn, clear_btn, new_ticker, current_ticker, current_options, state):
#     new_ticker = str.upper("".join(new_ticker.split())
#                            )  # preprocessing the ticker
#     new_entry = {'label': new_ticker, 'value': new_ticker}
#     if int(clear_btn) != state:
#         current_options.clear()
#         state = int(clear_btn)
#     elif submit_btn > 0 and new_ticker:
#         if new_entry not in current_options:
#             current_options.append(new_entry)
#         if new_ticker not in current_ticker:
#             current_ticker += [new_ticker]
#     else:
#         pass
#     return current_ticker, current_options, state


@app.callback([Output('corr_matrix', 'columns'), Output('corr_matrix', 'data')])
@app.callback([Output('option_tab_content', 'children')], [Input("option_tabs", "value")])
def render_content(tab):
    if tab == "EurOption":
        return [html.Div([
            dcc.DatePickerSingle(id='strikeDate'),
            dcc.Dropdown(id='otype',
            options=[{'label': 'Call Option', 'value': 'call'},
            {'label': 'Put Option', 'value': 'put'}]),
            dcc.Input(id='strike', type='number', placeholder='Strike pls')
        ])]
    elif tab == "AmeOption":
        return [html.Div([
            dcc.DatePickerSingle(id='strikeDate'),
            dcc.Dropdown(id='otype',
            options=[{'label': 'Call Option', 'value': 'call'},
            {'label': 'Put Option', 'value': 'put'}]),
            dcc.Input(id='strike', type='number', placeholder='Strike pls'),
            dcc.Input(id='coupon', type='number',
                      placeholder='Coupon structure pls')
        ])]
    elif tab == "BarOption":
        return [html.Div(
            [dcc.DatePickerSingle(id='strikeDate'),
            dcc.Dropdown(id='otype',
            options=[{'label': 'Call Option', 'value': 'call'},
            {'label': 'Put Option', 'value': 'put'}]),
            dcc.Input(id='strike', type='number', placeholder='Strike pls'),
            dcc.Input(id='rebate', type='number', placeholder='Rebate pls')]
        )]
    else:
        raise ValueError("Not working")

# @app.callback(
#     Output('submit_input', 'value'), [Input("submit_input_selected", 'value')]
# )
# def finalize_ticker(ticker):
#     if not ticker:
#         raise PreventUpdate
#     else:
#         return ticker


# @app.callback(
#     Output("option_modal", "style"), [Input("new_stock", "n_clicks")]
# )
# def display_stock_modal_callback(n):
#     if n > 0:
#         return {"display": "block"}
#     return {"display": "none"}


# reset to 0 add button n_clicks property
# @app.callback(
#     Output("new_stock", "n_clicks"),
#     [
#         Input("option_modal_close", "n_clicks"),
#         Input("submit_new_option", "n_clicks"),
#     ],
# )
# def close_modal_callback(n, n2):
#     return 0
