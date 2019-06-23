# -*- coding: utf-8 -*-
import json
import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
from plotly import graph_objs as go
from datetime import datetime, date
from dash.exceptions import PreventUpdate
from ..app import app
import json
import pandas_datareader.data as web
import random

# with open("./data/ticker.json", "r") as read_file:
#     labelFull = json.load(read_file)

dfStock = pd.read_csv('./data/stock.csv')
dfETF = pd.read_csv("./data/ETF.csv")
dfCUR = pd.read_csv("./data/currency.csv")
dfIdx = pd.read_csv("./data/index.csv")


def gen_dropdown_options(df, cols):
    if len(cols) == 2:
        df_new = df[cols].drop_duplicates()
        df_new.columns = ['label', 'value']
        dic = df_new.to_dict('record')
    elif len(cols) == 1:  # TODO: maybe use pd.unique
        dic = [{'label': ticker, 'value': ticker}
               for ticker in pd.unique(df[cols[0]])]
    else:
        raise ValueError('Dataframe using too many columns')
    return dic


exchange_dic = gen_dropdown_options(dfStock, ['SE_Name', 'Exchange'])
etf_exchange_dic = gen_dropdown_options(dfETF, ['Exchange'])
cur_exchange_dic = gen_dropdown_options(dfCUR, ['Exchange'])
idx_exchange_dic = gen_dropdown_options(dfIdx, ['Exchange'])


# returns modal (hidden by default)


def modal():
    return html.Div(
        html.Div([html.Div([
            # modal header
            html.Div(
                [
                    html.Span(
                        "New Asset",
                        style={
                            "color": "#506784",
                            "fontWeight": "bold",
                            "fontSize": "20",
                        },
                    ),
                    html.Span(
                        "x",
                        id="stock_modal_close",
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
                    id="asset_tabs",
                    style={"height": "20",
                           "verticalAlign": "middle"},
                    children=[
                        dcc.Tab(label="Equity",
                                value="equity"),
                        dcc.Tab(label="ETF", value="ETF"),
                        dcc.Tab(label='Index', value='idx'),
                        dcc.Tab(label='Currency', value='currency'),
                    ],
                    value="ETF",
                ),

                html.Div(children=[
                    html.P("Enter your ticker here directly"),
                    dcc.Input(id='submit_input', value='',
                              placeholder='Enter Your Ticker'),
                    html.P(
                        html.Span('Or choose from the following category',
                        style={
                            'background':'#fff','padding':'0 10px',
                            'fontSize': '18px'
                        }),
                        style={'textAlign': 'center',
                               'borderBottom': '1px solid grey',
                               'lineHeight': '0.1em',
                               'width': '100%',
                               'margin': '30px 40px 30px 10px'
                               }),
                    # TODO: Find out better way for loading large data
                    html.Div(id='asset_tab_content'),
                    html.P('Choose your ticker'),
                    dcc.Dropdown(id='submit_input_selected', options=[],
                                 placeholder='Search your ticker by name here', value=''),
                ])],
                className="row",
                style={"paddingTop": "2%"},
            ),


            # submit button
            html.Span(
                "Submit",
                id="submit_new_stock",
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
        id="stock_modal",
        style={"display": "none"},
    )


layout = [
    # top controls
    html.Div(
        [
            html.Div(
                dcc.DatePickerRange(
                    id="date_picker",
                    min_date_allowed=datetime(2010, 1, 1),
                    max_date_allowed=datetime.now(),
                    start_date_placeholder_text='What are you looking at?',
                    end_date_placeholder_text='So I look then what?',
                    display_format='MMM Do, YYYY',
                    # value="D",
                    clearable=False,
                ),
                className="six columns"
            ),

            html.Div(
                dcc.Dropdown(
                    id="heatmap_dropdown",
                    options=[
                        {"label": "All stages", "value": "all_s"},
                        {"label": "Cold stages", "value": "cold"},
                        {"label": "Warm stages", "value": "warm"},
                        {"label": "Hot stages", "value": "hot"},
                    ],
                    value="all_s",
                    clearable=False,
                ),
                className="two columns",
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

    # charts row div
    html.Div(
        [html.P("Asset price", className='title'),
         dcc.Graph(id='stock-graph', 
                    style={"height": "100vh", "width": "98%"},
                   className="ten columns"),
         ]
    ),
    html.Div([html.Div([
        html.P('OHLC Diagram', className='title'),
        dcc.Graph(id='stock-ohlc', style={"height": "90vh", "width": "98%"},
                  className="ten columns"),
    ], className='six columns'),
        html.Div([
            html.P('Candlestick Diagram', className='title'),
            dcc.Graph(id='stock-candlestick', style={"height": "90vh", "width": "98%"},
                      className="ten columns")
        ], className='six columns')], className='row'),
    # tables row div
    html.Div(
        modal(),
        className="row",
        style={"marginTop": "5px", "max height": "200px"},
    ),
]


@app.callback([Output('total_ticker', 'value'), Output('total_ticker', 'options'),
               Output('true_clear', 'value')],
              [Input("submit_new_stock", "n_clicks"),
               Input('clear', 'n_clicks')],
              [State('submit_input', 'value'),
               State('total_ticker', 'value'), State(
                   'total_ticker', 'options'),
               State('true_clear', 'value')])
def update_ticker(submit_btn, clear_btn, new_ticker, current_ticker, current_options, state):
    new_ticker = str.upper("".join(new_ticker.split())
                           )  # preprocessing the ticker
    new_entry = {'label': new_ticker, 'value': new_ticker}
    if int(clear_btn) != state:
        current_options.clear()
        state = int(clear_btn)
    elif submit_btn > 0 and new_ticker:
        if new_entry not in current_options:
            current_options.append(new_entry)
        if new_ticker not in current_ticker:
            current_ticker += [new_ticker]
    else:
        pass
    return current_ticker, current_options, state


@app.callback([Output('asset_tab_content', 'children')], [Input("asset_tabs", "value")])
def render_content(tab):
    if tab == "equity":
        return [html.Div([
            html.P('Country'),
            dcc.Dropdown(id='select_country',
                         options=gen_dropdown_options(dfStock, ['Country'])),
            html.P('Stock Exchange'),
            dcc.Dropdown(id='select_exchange', options=exchange_dic),
            html.P('Category of Business'),
            dcc.Dropdown(id='select_category',
                         options=gen_dropdown_options(dfStock, ['Category']))
        ])]
    elif tab == "ETF":
        return [html.Div([
            html.P('Stock Exchange Ticker'),
            dcc.Dropdown(id='select_exchange', options=etf_exchange_dic),
            dcc.Input(id='select_country', style={'display': 'None'}),
            dcc.Input(id='select_category', style={'display': 'None'})])
        ]
    elif tab == "idx":
        return [html.Div(
            [
            html.P('Stock Exchange Ticker'),
            dcc.Dropdown(id='select_exchange', options=idx_exchange_dic),
             dcc.Input(id='select_country', style={'display': 'None'}),
             dcc.Input(id='select_category', style={'display': 'None'})]
        )]
    elif tab == "currency":
        return [html.Div(
            [
            html.P('Stock Exchange Ticker'),
            dcc.Dropdown(id='select_exchange', options=idx_exchange_dic),
             dcc.Input(id='select_exchange', style={'display': 'None'}),
             dcc.Input(id='select_category', style={'display': 'None'})]
        )]
    else:
        raise ValueError("Not working")

@app.callback(
    Output('select_exchange', 'options'), [Input('select_country', 'value')],
    [State('asset_tabs', 'value')]
)
def locate_exchange(country, tab):
    if country and tab == 'equity':
        df_trunc = dfStock[dfStock['Country'] == country]
        return gen_dropdown_options(df_trunc, ['SE_Name', 'Exchange'])
    else:
        raise PreventUpdate


@app.callback(
    Output('submit_input_selected', 'options'),
    [Input('select_country', 'value'), Input('select_exchange', 'value'),
     Input('select_category', 'value')], [State("asset_tabs", "value")]
)
def locate_ticker(country, exchange, category, tab):
    if tab == 'equity':
        if country or exchange or category:
            mask1 = (dfStock['Country'] == country) | (not country)
            mask2 = (dfStock['Exchange'] == exchange) | (not exchange)
            mask3 = (dfStock['Category'] == category) | (not category)
            df_trunc = dfStock[mask1 & mask2 & mask3]
            return gen_dropdown_options(df_trunc, ['Name', 'Ticker'])
        else:
            raise PreventUpdate
    elif tab == 'ETF' and exchange:
        mask = (dfETF['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfETF[mask], ['Name', 'Ticker'])
    elif tab == 'idx' and exchange:
        mask = (dfIdx['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfIdx[mask], ['Name', 'Ticker'])
    elif tab == 'currency' and exchange:
        mask = (dfCUR['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfCUR[mask], ['Name', 'Ticker'])
    else:
        raise PreventUpdate


@app.callback(
    Output('submit_input', 'value'), [Input("submit_input_selected", 'value')]
)
def finalize_ticker(ticker):
    if not ticker:
        raise PreventUpdate
    else:
        return ticker


@app.callback(
    Output("stock_modal", "style"), [Input("new_stock", "n_clicks")]
)
def display_stock_modal_callback(n):
    if n > 0:
        return {"display": "block"}
    return {"display": "none"}


# reset to 0 add button n_clicks property
@app.callback(
    Output("new_stock", "n_clicks"),
    [
        Input("stock_modal_close", "n_clicks"),
        Input("submit_new_stock", "n_clicks"),
    ],
)
def close_modal_callback(n, n2):
    return 0


@app.callback(Output("stock-graph", 'figure'),
              [Input("total_ticker", 'value'), Input('ppty_input', 'value'),
               Input('date_picker', 'start_date'), Input('date_picker', 'end_date')])
def update_graph(input_ticker, ppty_input, start_time, end_time):
    if all([input_ticker, ppty_input, start_time, end_time]):
        start = datetime.strptime(start_time, '%Y-%m-%d')
        end = datetime.strptime(end_time, '%Y-%m-%d')
        try:
            df = web.DataReader(input_ticker, 'yahoo', start, end)
            traces = []
            graph_layout = go.Layout(
                xaxis={'title': 'Dates'},
                yaxis={'title': 'Price'},
                hovermode='closest'
            )
            for ticker in input_ticker:
                traces.append(
                    go.Scatter(
                        x=df.index,
                        y=df[ppty_input][ticker],
                        opacity=0.7,
                        mode='lines',
                        # marker={'size': 5,'line': {'width': 0.5, 'color': 'white'}},
                        name=ticker
                    ))
            figure = {
                'data': traces, 'layout': graph_layout
            }
            return figure
        except (KeyError, TypeError):
            pass
    else:
        raise PreventUpdate


@app.callback([Output("stock-candlestick", 'figure'), Output('stock-ohlc', 'figure')],
              [Input("total_ticker", 'value'), Input('date_picker', 'start_date'),
               Input('date_picker', 'end_date')])
def update_Ohlc(input_ticker, start_time, end_time):
    if all([input_ticker, start_time, end_time]):
        start = datetime.strptime(start_time, '%Y-%m-%d')
        end = datetime.strptime(end_time, '%Y-%m-%d')
        try:
            df = web.DataReader(input_ticker, 'yahoo', start, end)
            ohlc_traces = []
            candlestick_traces = []
            ohlc_layout = go.Layout(
                xaxis={'title': 'Dates'},
                yaxis={'title': 'OHLC'},
                hovermode='closest',
                legend=dict(orientation="h")
            )
            candlestick_layout = go.Layout(
                xaxis={'title': 'Dates'},
                yaxis={'title': 'candlestick'},
                hovermode='x',
                legend=dict(orientation="h")
            )
            for idx, ticker in enumerate(input_ticker):
                rand1 = random.random()
                rand2 = 1-rand1
                inc_color = 'rgb' + \
                    str((rand1*255, rand2*255, 200))
                dec_color = 'rgb' + \
                    str((rand2*255, rand1*255, 100))
                candlestick_traces.append(
                    go.Candlestick(x=df.index,
                                   open=df['Open'][ticker],
                                   high=df['High'][ticker],
                                   low=df['Low'][ticker],
                                   close=df['Close'][ticker],
                                   increasing=dict(line=dict(color=inc_color)),
                                   decreasing=dict(line=dict(color=dec_color)),
                                   name=ticker,
                                   ))
                ohlc_traces.append(
                    go.Ohlc(x=df.index,
                            open=df['Open'][ticker],
                            high=df['High'][ticker],
                            low=df['Low'][ticker],
                            close=df['Close'][ticker],
                            increasing=dict(line=dict(color=inc_color)),
                            decreasing=dict(line=dict(color=dec_color)),
                            name=ticker,
                            )
                )
            candle_figure = {
                'data': candlestick_traces, 'layout': candlestick_layout
            }
            ohlc_figure = {
                'data': ohlc_traces, 'layout': ohlc_layout
            }
            return candle_figure, ohlc_figure
        except (KeyError, TypeError):
            pass
    else:
        raise PreventUpdate
