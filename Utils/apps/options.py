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
                html.Span(
                    "Submit",
                    id="submit_new_option",
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
        [dcc.DatePickerRange(
            id="spot_price",
            start_date_placeholder_text='Choose your spot date',
            end_date_placeholder_text='Choose your strike date',
            display_format='MMM Do, YYYY',
            clearable=False, className="four columns"
        ),

         dcc.RadioItems(options=[
             {'label': 'Euroption Option', 'value': 'EurOption'},
            {'label': 'American Option', 'value': 'AmeOption'},
            {'label': 'Barrier Option', 'value': 'BarOption'}], value='EurOption',
            className='six columns',
            labelStyle={'display': 'inline-block', 'color': 'white', 'fontSize': '20px',
                    'margin-right': '20px'}),

            html.Div(html.Span(
                "Add New Underlying Asset",
                id="new_underlying",
                n_clicks=0,
                className="button button--primary add",
                style={"float": "right", 'width': 'auto'},
                ), className="two columns")],
        className="row",
        style={"marginBottom": "10", "padding-bottom": "10px"}),

    html.Div(
        [
            # dcc.Input(id="int_rate", placeholder='Risk-free Interest rate'),
                    # dcc.Input()
                    # dcc.Dropdown(id='')
            ],
    ),

    # add button


    # indicators row
    html.Div(
        [dcc.Dropdown(id='underlying_pool',
                      options=[{'label': 'Test', 'value': 'Test'},
                               {'label': 'Test2', 'value': 'Test2'}],
                      value=[],
                      placeholder='Your Underlying Pool', multi=True, className="ten columns"),
         html.Button(children='Clear All Stocks', id='clear', n_clicks=0,
                     className='two columns'),
         dcc.Input(id='clear_all', value=0, style={'display': 'None'}),
         ],
        className="row",
    ),
    html.Div([html.P('Correlation Structure', className='title'),
        html.Div(
            [
             dash_table.DataTable(
                id='corr_matrix',
                columns=[{'id': 'Ticker', 'name': ' Asset Name', 'editable': False},
                         {'id': 'Test', 'name': 'Test'}],
                data=[{'Ticker': 'Test', 'Test': 1.0}],
                editable=True,
            )], className='seven columns'
            ),
        html.Div([
            dcc.Graph(id= 'heat-map')
        ], className='five columns'
        )
    ], className='row'),
    # charts row div
    html.Div([
        html.P("Asset List", className='title'),
        dash_table.DataTable(
                id='asset_info',
                columns=[{'name': 'Name', 'id':'Name'},
                        {'name': 'Spot Price', 'id':'spot'},
                        {'name': 'Interest Rate', 'id':'int_rate'},
                        {'name': 'Volatiltiy', 'id':'volatility'},
                        {'name': 'Dividend', 'id':'dividend'}
                        ],
                row_deletable=True,
                data=[],
             )
    ], className='row'),

    html.Div(
        [html.P("The Fair Option Price", className='title'),
         dcc.Graph(id='oprice-graph', style={"height": "100vh", "width": "98%"},
                   className="ten columns"),
         ],
        className='row'),
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
            secret_df.sort_index(axis=0, inplace=True)
            secret_df.sort_index(axis=1, inplace=True)
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
            'x': [c['id'] for c in columns[1:]],
            'colorscale':'Viridis'
        }]
    }


@app.callback(
    [Output("option_modal_close", 'n_clicks'), Output('missing_warning', 'children'),
    Output('missing_warning', 'style'), Output('asset_info', 'data')],
    [Input("submit_new_option", "n_clicks")],
    [State('asset_name', 'value'),
    State('spot', 'value'), State('int_rate', 'value'),
    State('volatility', 'value'), State('dividend', 'value'), 
    State('missing_warning', 'style'),
    State('underlying_pool', 'options'), State('asset_info', 'data')]
)
def check_validity(n, name, spot, int_rate, vol, div, style, options, data):
    message = ''
    if not name:
        message = 'Enter asset name'
    elif name in [set(option.values()).pop() for option in options]:
        message = 'Asset with same name already exists. Try another one'
    elif not spot or spot < 0:
        message = 'Spot must not be empty or negative'
    elif vol < 0:
        message = f'{vol} is not valid. Volatility must be positive'
    elif div < 0 or div > 100:
        message = f'{div} is not valid. Dividend must be positive and smaller than 1'
    
    if message:
        style['display']='block'
        return 0, message, style, data
    else:
        data.append({'Name': name, 'spot': spot, 'int_rate': int_rate, 
                    'volatility': vol, 'dividend':div})
        return 1, message, style, data


@app.callback([Output('underlying_pool', 'value'), Output('underlying_pool', 'options'),
               Output('clear_all', 'value')],
              [Input('asset_info', 'data'), Input('clear', 'n_clicks')],
              [State('clear_all', 'value')])
def update_ticker(data, clear_btn, state):
    # new_ticker = str.upper("".join(new_ticker.split()))
    if int(clear_btn) != state:
        return [], [], int(clear_btn)
    else:
        nameLst = [row['Name'] for row in data]
        options = [{'label': name, 'value': name} for name in nameLst]
        return nameLst, options, state

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