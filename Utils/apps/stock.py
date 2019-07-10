# -*- coding: utf-8 -*-
import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from plotly import graph_objs as go
from datetime import datetime, date
from dash.exceptions import PreventUpdate
from ..app import app
import pandas_datareader.data as web
import random
import requests

# import plotly.plotly as py
# import json
# with open("./data/ticker.json", "r") as read_file:
#     labelFull = json.load(read_file)

dfStock = pd.read_csv('./data/stock.csv')
dfETF = pd.read_csv("./data/ETF.csv")
dfCUR = pd.read_csv("./data/currency.csv")
dfIdx = pd.read_csv("./data/index.csv")


def update_news():
    news_requests = requests.get(
    "https://newsapi.org/v2/top-headlines?"
    "category=business&pageSize=100&"
    # "sources=australian-financial-review,bloomberg,fortune,wirtschafts-woche,handelsblatt&"
    "apiKey=da8e2e705b914f9f86ed2e9692e66012"
    )

    jsonData = news_requests.json()['articles']
    title, url = [x['title'] for x in jsonData], [x['url'] for x in jsonData]

    return [len(title), html.Div(html.Table(
            html.Tbody(
                children=[
                    html.Tr(
                            html.Td(
                                    html.A(title[i],
                                        href=url[i],
                                        target="_blank",
                                    )
                            )
                    )
                    for i in range(min(len(title), len(url))) # might mismatch.
                ],
            ), className="striped centered"), className="custom-table")]

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

colors = [f"hsl({x}, 100%, 40%)" for y in zip(
    range(0, 180, 30), range(180, 360, 30)) for x in y]

def modal():
    return html.Div(
        html.Div([html.Div([
            # modal header
            html.Div(
                [
                    html.Span("New Asset"),
                    html.Span(
                        "X",
                        id="stock_modal_close",
                        n_clicks=0,
                        style={
                            "float": "right",
                            "cursor": "pointer",
                            "marginTop": "0",
                            "marginBottom": "17",
                        },
                    ),
                    html.Div(className="divider")
                ],
                className="caption",
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
                    html.Span("Enter your ticker here directly",
                              className="rmk"),
                    html.Div([
                        dcc.Input(id='submit_input', value='',
                                  className='validate'),
                        html.Label("Input Ticker", htmlFor='submit_input'),
                    ], className="input-field row"),
                    html.Span('..Or choose from the following category',
                              className="rmk"),

                    # TODO: Find out better way for loading large data
                    html.Div(id='asset_tab_content'),

                    html.P('Choose your ticker'),
                    dcc.Dropdown(id='submit_input_selected', options=[],
                                 placeholder='Search your ticker by name here', value=''),
                ], className="container")
            ], className="row", style={"paddingTop": "2%"},
            ),

            # TODO: Check validate field !!!!
            # submit button
            html.Div([
                html.Button(
                    "Submit",
                    id="submit_new_stock",
                    n_clicks=0,
                    className="btn waves-effect",

                )], className="modal-footer")
        ],
            className="row",
            style={"textAlign": "center"},
        )
        ],
            className="modal-content",
        ),
        id="stock_modal",
        className="custom-modal",
        style={"display":"none"},
    )


layout = [

    html.Div([
        
    # top controls
    html.Div(
        [html.H3("Property Block", className="title col s12 center-align"),

        html.Div(
                [
                html.Span(
                    "Watch New Asset",
                    id="new_stock",
                    n_clicks=0,
                    className="btn waves-effect waves-light"
                )],
                className="col s12 center-align",
            ),
                html.Div(
                [
                html.P("Dates of Speculation"),
                dcc.DatePickerRange(
                    id="date_picker",
                    min_date_allowed=datetime(2010, 1, 1),
                    max_date_allowed=datetime.now(),
                    start_date_placeholder_text='Start Date',
                    end_date_placeholder_text='End Date',
                    display_format='MMM Do, YYYY',
                    # value="D",
                    clearable=False,
                    show_outside_days=True,
                    style={"width": "100%"}
                )],
                className="col s12 center-align"
            ),

            html.Div(
                [
                html.P("Type of Price", className="center-align"),
                dcc.Dropdown(id="ppty_input",
                             options=[{'label': 'Open Price', 'value': 'Open'},
                                      {'label': 'Close Price', 'value': 'Close'},
                                      {'label': 'Daily High', 'value': 'High'},
                                      {'label': 'Daily Low', 'value': 'Low'},
                                      {'label': 'Adjoint Close', 'value': 'Adj Close'}],
                             value='Adj Close',
                             clearable=False,
                             style={"position":"relative"})],
                className="col s12",
            ),

            # add button

        html.Div([
            html.P("Your Stock Pool", className="center-align"),
            dcc.Dropdown(id='total_ticker',
                      options=[{'label': 'AAPL', 'value': 'AAPL'},
                               {'label': 'TSLA', 'value': 'TSLA'}],
                      value=['AAPL'],
                      placeholder='Enter a stock ticker', multi=True, 
                      ),
        ], className="col s12"),
        
        html.Div(
            [
            html.Button(children='Clear All Stocks', id='clear', n_clicks=0,
                     className='btn waves-effect waves-red')], 
            className="col s12 center-align", style={"margin-top":"2rem"}
        ),
         
         dcc.Input(id='true_clear', value=0, style={'display': 'None'}),


        # News Headline 

        html.Div(
        children=[
            html.H3("Headlines", className="title center-align"),
            html.Span(f"{update_news()[0]} pieces of news has updated", id='news-no'),
            html.Span("Last update : "
                + datetime.now().strftime("%H:%M:%S"),
                className="right"
            )
        ], className="col s12"
    ),
        html.Div([update_news()[1]], id='news')
        ],
        className="col s12 m12 l4",
        style={}
    ),

    # charts side
    html.Div(
        [
            # html.H3("Graph Block", className="caption col s12"),
        html.H3("Asset price", className='title header'),
         dcc.Graph(
            figure={'layout': go.Layout(
            paper_bgcolor='rgba(255, 255, 255, 0.7)',
            plot_bgcolor='rgba(0,0,0,0)'
            )},
            id='stock-graph',
            style={"height": "70vh"},
            className="row"),

        html.H3('OHLC Diagram', className='title header'),
        dcc.Graph(
            figure={'layout': go.Layout(
            paper_bgcolor='rgba(255, 255, 255, 0.7)',
            plot_bgcolor='rgba(0,0,0,0)'
            )},
            id='stock-ohlc', style={"height": "70vh"},
                  className="row"),

        html.H3('Candlestick Diagram', className='title row'),
            dcc.Graph(
            figure={'layout': go.Layout(
            paper_bgcolor='rgba(255, 255, 255, 0.7)',
            plot_bgcolor='rgba(0,0,0,0)'
            )},
            id='stock-candlestick', style={"height": "70vh"},
            className="row"),

        ], className="col s12 m12 l8 center-align"),

        dcc.Interval(
            id='refresh',
            interval=1*60000, # in milliseconds
            n_intervals=0
        ),
    # tables row div
    html.Div(
        modal(),
        # style={"marginTop": "5px", "max height": "200px"},
    ),
    ], className="row")
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
            html.Div([
                html.P("Select Country"),
                dcc.Dropdown(id='select_country',
                             options=gen_dropdown_options(
                                 dfStock, ['Country']),
                            className="custom-input")
            ]),


            html.Div([
                html.P("Select Stock Exchange"),
                dcc.Dropdown(id='select_exchange',
                             options=exchange_dic),
            ]),

            html.Div([
                html.P("Choose Category of Business"),
                dcc.Dropdown(id='select_category',
                             options=gen_dropdown_options(dfStock, ['Category'])),
            ]),
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
                colorway=colors,
                paper_bgcolor='rgba(255,255,255,0.7)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin={'t':40},
                xaxis={'title': 'Dates'},
                yaxis={'title': 'Price'},
            # can change hovermode to "closest"
                hovermode='x'
            )
            for ticker in input_ticker:
                traces.append(
                    go.Scatter(
                        x=df.index,
                        y=df[ppty_input][ticker],
                        opacity=0.95,
                        mode='lines',
                        # marker={'size': 5,'line': {'width': 0.5, 'color': 'white'}},
                        name=ticker
                    ))
            figure = {
                'data': traces, 'layout': graph_layout,
            }
            return figure
        except (KeyError, TypeError, web._utils.RemoteDataError):
            raise PreventUpdate
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
                paper_bgcolor='rgba(255, 255, 255, 0.7)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin={'t':40},
                xaxis={'title': 'Dates'},
                yaxis={'title': 'OHLC'},
                hovermode='x',
                # legend=dict(orientation="h")
            )
            candlestick_layout = go.Layout(
                paper_bgcolor='rgba(255, 255, 255, 0.7)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin={'t':40},
                xaxis={'title': 'Dates'},
                yaxis={'title': 'candlestick'},
                hovermode='x',
                # legend=dict(orientation="h")
            )
            for idx, ticker in enumerate(input_ticker):
                rand1 = random.random()
                rand2 = 1-rand1
                inc_color = 'rgb' + \
                    str((rand1*0, rand2*0, 200))
                dec_color = 'rgb' + \
                    str((rand2*0, rand1*0, 100))
                candlestick_traces.append(
                    go.Candlestick(x=df.index,
                                   open=df['Open'][ticker],
                                   high=df['High'][ticker],
                                   low=df['Low'][ticker],
                                   close=df['Close'][ticker],
                                   increasing=dict(line=dict(color=colors[(idx * 2) % 12])),
                                   decreasing=dict(line=dict(color=colors[(idx * 2+1) % 12])),
                                   name=ticker,
                                   ))
                ohlc_traces.append(
                    go.Ohlc(x=df.index,
                            open=df['Open'][ticker],
                            high=df['High'][ticker],
                            low=df['Low'][ticker],
                            close=df['Close'][ticker],
                            increasing=dict(line=dict(color=colors[(idx * 2) % 12])),
                            decreasing=dict(line=dict(color=colors[(idx * 2+1) % 12])),
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
        except (KeyError, TypeError, web._utils.RemoteDataError):
            pass
    else:
        raise PreventUpdate


@app.callback([Output("news", "children"), Output("news-id", "children")], 
            [Input("refresh", "n-intervals")])
def renew_news(n):
    infos = update_news()
    return infos[0], f"{infos[0]} pieces of news has updated"
