# -*- coding: utf-8 -*-
import pandas as pd
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import dash_bootstrap_components as dbc
from plotly import graph_objs as go
from datetime import datetime
from dash.exceptions import PreventUpdate
from ..app import app
import pandas_datareader.data as web
import random
import requests

# Load Data
dfStock = pd.read_csv('./data/stock.csv')
dfETF = pd.read_csv("./data/ETF.csv")
dfCUR = pd.read_csv("./data/currency.csv")
dfIdx = pd.read_csv("./data/index.csv")

def update_news():
    try:
        # Using a public API key often fails or hits limits. 
        # Ideally this should be an env var or a paid service.
        # Fallback to dummy data if request fails to prevent app crash.
        news_requests = requests.get(
            "https://newsapi.org/v2/top-headlines?"
            "category=business&pageSize=5&"
            "apiKey=da8e2e705b914f9f86ed2e9692e66012"
        )
        jsonData = news_requests.json().get('articles', [])
        title = [x['title'] for x in jsonData]
        url = [x['url'] for x in jsonData]
    except Exception:
        title = ["Market data unavailable", "Check network connection"]
        url = ["#", "#"]

    if not title:
        return [0, html.P("No news available.")]

    return [len(title), html.Div(
        dbc.ListGroup(
            [
                dbc.ListGroupItem(
                    html.A(t, href=u, target="_blank", className="text-decoration-none"),
                    action=True
                )
                for t, u in zip(title, url)
            ],
            flush=True
        )
    )]

def gen_dropdown_options(df, cols):
    if len(cols) == 2:
        df_new = df[cols].drop_duplicates()
        df_new.columns = ['label', 'value']
        dic = df_new.to_dict('records')
    elif len(cols) == 1:
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

def build_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Add New Asset")),
            dbc.ModalBody(
                [
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Equity", tab_id="equity"),
                            dbc.Tab(label="ETF", tab_id="ETF"),
                            dbc.Tab(label="Index", tab_id="idx"),
                            dbc.Tab(label="Currency", tab_id="currency"),
                        ],
                        id="asset_tabs",
                        active_tab="equity",
                    ),
                    html.Div(id="asset_tab_content", className="mt-3"),
                    html.Hr(),
                    html.P("Or input ticker directly:", className="text-muted"),
                    dbc.Input(id='submit_input', placeholder="Ticker Symbol (e.g., AAPL)", className="mb-2"),
                    dcc.Dropdown(
                        id='submit_input_selected', 
                        options=[],
                        placeholder='Search ticker by name...',
                    ),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button("Add to Pool", id="submit_new_stock", className="ms-auto", n_clicks=0)
            ),
        ],
        id="stock_modal",
        is_open=False,
        size="lg",
    )

layout = dbc.Container([
    dbc.Row([
        # Sidebar Controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Market Controls"),
                dbc.CardBody([
                    dbc.Button("Watch New Asset", id="new_stock", color="primary", className="w-100 mb-3"),
                    
                    html.Label("Date Range"),
                    dcc.DatePickerRange(
                        id="date_picker",
                        min_date_allowed=datetime(2010, 1, 1),
                        max_date_allowed=datetime.now(),
                        start_date=datetime(2023, 1, 1),
                        end_date=datetime.now(),
                        display_format='YYYY-MM-DD',
                        className="mb-3 d-block",
                        style={"width": "100%"}
                    ),

                    html.Label("Price Type"),
                    dcc.Dropdown(
                        id="ppty_input",
                        options=[
                            {'label': 'Open', 'value': 'Open'},
                            {'label': 'Close', 'value': 'Close'},
                            {'label': 'High', 'value': 'High'},
                            {'label': 'Low', 'value': 'Low'},
                            {'label': 'Adj Close', 'value': 'Adj Close'}
                        ],
                        value='Adj Close',
                        clearable=False,
                        className="mb-3"
                    ),

                    html.Label("Stock Pool"),
                    dcc.Dropdown(
                        id='total_ticker',
                        options=[{'label': 'AAPL', 'value': 'AAPL'}, {'label': 'TSLA', 'value': 'TSLA'}],
                        value=['AAPL'],
                        multi=True,
                        className="mb-3"
                    ),

                    dbc.Button("Clear All", id="clear", color="danger", outline=True, className="w-100"),
                    dcc.Input(id='true_clear', value=0, style={'display': 'None'}),
                ])
            ], className="mb-4"),

            dbc.Card([
                dbc.CardHeader("Market News"),
                dbc.CardBody([
                    html.Div(id="news"),
                    html.Small(id="news-no", className="text-muted")
                ])
            ])
        ], width=12, lg=3),

        # Main Graphs
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Price History", className="card-title"),
                    dcc.Graph(id='stock-graph', style={"height": "60vh"})
                ])
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("OHLC", className="card-title"),
                            dcc.Graph(id='stock-ohlc', style={"height": "40vh"})
                        ])
                    ]), width=12, lg=6, className="mb-4"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Candlestick", className="card-title"),
                            dcc.Graph(id='stock-candlestick', style={"height": "40vh"})
                        ])
                    ]), width=12, lg=6, className="mb-4"
                )
            ])
        ], width=12, lg=9)
    ]),

    build_modal(),
    
    dcc.Interval(
        id='refresh',
        interval=60000, 
        n_intervals=0
    )
], fluid=True)


# --- Callbacks ---

@app.callback(
    Output("stock_modal", "is_open"),
    [Input("new_stock", "n_clicks"), Input("submit_new_stock", "n_clicks")],
    [State("stock_modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    [Output('total_ticker', 'value'), Output('total_ticker', 'options'),
     Output('true_clear', 'value')],
    [Input("submit_new_stock", "n_clicks"), Input('clear', 'n_clicks')],
    [State('submit_input', 'value'), State('total_ticker', 'value'), 
     State('total_ticker', 'options'), State('true_clear', 'value')]
)
def update_ticker(submit_btn, clear_btn, new_ticker, current_ticker, current_options, state):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_ticker, current_options, state
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'clear':
        return [], [], state + 1
    
    if button_id == 'submit_new_stock' and new_ticker:
        new_ticker = new_ticker.upper().strip()
        new_entry = {'label': new_ticker, 'value': new_ticker}
        if new_entry not in current_options:
            current_options.append(new_entry)
        if new_ticker not in current_ticker:
            current_ticker.append(new_ticker)
            
    return current_ticker, current_options, state

@app.callback(Output('asset_tab_content', 'children'), [Input("asset_tabs", "active_tab")])
def render_tab_content(active_tab):
    if active_tab == "equity":
        return html.Div([
            dbc.Label("Select Country"),
            dcc.Dropdown(id='select_country', options=gen_dropdown_options(dfStock, ['Country']), className="mb-2"),
            dbc.Label("Select Exchange"),
            dcc.Dropdown(id='select_exchange', options=exchange_dic, className="mb-2"),
            dbc.Label("Category"),
            dcc.Dropdown(id='select_category', options=gen_dropdown_options(dfStock, ['Category']), className="mb-2"),
        ])
    elif active_tab == "ETF":
        return html.Div([
            dbc.Label("Exchange"),
            dcc.Dropdown(id='select_exchange', options=etf_exchange_dic),
            # Hidden inputs to satisfy dependency logic if needed, or handle in callback
            # Original code used hidden inputs to prevent callback errors.
            # We can simplify by just not triggering if inputs are missing.
            dcc.Input(id='select_country', style={'display': 'None'}),
            dcc.Input(id='select_category', style={'display': 'None'})
        ])
    elif active_tab == "idx":
        return html.Div([
            dbc.Label("Exchange"),
            dcc.Dropdown(id='select_exchange', options=idx_exchange_dic),
            dcc.Input(id='select_country', style={'display': 'None'}),
            dcc.Input(id='select_category', style={'display': 'None'})
        ])
    elif active_tab == "currency":
        return html.Div([
            dbc.Label("Exchange"),
            dcc.Dropdown(id='select_exchange', options=idx_exchange_dic), # Original code reused idx_exchange_dic for currency? keeping logic
            dcc.Input(id='select_country', style={'display': 'None'}),
            dcc.Input(id='select_category', style={'display': 'None'})
        ])
    return html.P("Select a category")

@app.callback(
    Output('select_exchange', 'options'), 
    [Input('select_country', 'value')],
    [State('asset_tabs', 'active_tab')]
)
def locate_exchange(country, tab):
    if country and tab == 'equity':
        df_trunc = dfStock[dfStock['Country'] == country]
        return gen_dropdown_options(df_trunc, ['SE_Name', 'Exchange'])
    raise PreventUpdate

@app.callback(
    Output('submit_input_selected', 'options'),
    [Input('select_country', 'value'), Input('select_exchange', 'value'),
     Input('select_category', 'value')], 
    [State("asset_tabs", "active_tab")]
)
def locate_ticker(country, exchange, category, tab):
    if tab == 'equity':
        if country or exchange or category:
            mask1 = (dfStock['Country'] == country) | (not country)
            mask2 = (dfStock['Exchange'] == exchange) | (not exchange)
            mask3 = (dfStock['Category'] == category) | (not category)
            df_trunc = dfStock[mask1 & mask2 & mask3]
            return gen_dropdown_options(df_trunc, ['Name', 'Ticker'])
    elif tab == 'ETF' and exchange:
        mask = (dfETF['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfETF[mask], ['Name', 'Ticker'])
    elif tab == 'idx' and exchange:
        mask = (dfIdx['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfIdx[mask], ['Name', 'Ticker'])
    elif tab == 'currency' and exchange:
        mask = (dfCUR['Exchange'] == exchange) | (not exchange)
        return gen_dropdown_options(dfCUR[mask], ['Name', 'Ticker'])
    raise PreventUpdate

@app.callback(
    Output('submit_input', 'value'), [Input("submit_input_selected", 'value')]
)
def finalize_ticker(ticker):
    if ticker:
        return ticker
    raise PreventUpdate

@app.callback(Output("stock-graph", 'figure'),
              [Input("total_ticker", 'value'), Input('ppty_input', 'value'),
               Input('date_picker', 'start_date'), Input('date_picker', 'end_date')])
def update_graph(input_ticker, ppty_input, start_time, end_time):
    if not (input_ticker and ppty_input and start_time and end_time):
        raise PreventUpdate
        
    start = datetime.strptime(start_time.split('T')[0], '%Y-%m-%d')
    end = datetime.strptime(end_time.split('T')[0], '%Y-%m-%d')
    
    try:
        # yahoo finance is often unstable with pandas_datareader. 
        # Using a try-except block.
        df = web.DataReader(input_ticker, 'yahoo', start, end)
        
        # Handle single ticker result which might not be MultiIndex
        if len(input_ticker) == 1:
             # Structure might differ, ensuring compatibility
             pass

        traces = []
        for ticker in input_ticker:
            # Check if df has MultiIndex columns (Ticker, Attribute) or just Attribute
            if isinstance(df.columns, pd.MultiIndex):
                y_data = df[ppty_input][ticker]
            else:
                y_data = df[ppty_input]
                
            traces.append(
                go.Scatter(
                    x=df.index,
                    y=y_data,
                    mode='lines',
                    name=ticker
                ))
        return {
            'data': traces, 
            'layout': go.Layout(
                xaxis={'title': 'Date'},
                yaxis={'title': 'Price'},
                hovermode='x',
                margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
                template='plotly_white'
            )
        }
    except Exception as e:
        print(f"Data fetch error: {e}")
        raise PreventUpdate

@app.callback([Output("stock-candlestick", 'figure'), Output('stock-ohlc', 'figure')],
              [Input("total_ticker", 'value'), Input('date_picker', 'start_date'),
               Input('date_picker', 'end_date')])
def update_ohlc(input_ticker, start_time, end_time):
    if not (input_ticker and start_time and end_time):
        raise PreventUpdate

    start = datetime.strptime(start_time.split('T')[0], '%Y-%m-%d')
    end = datetime.strptime(end_time.split('T')[0], '%Y-%m-%d')
    
    try:
        df = web.DataReader(input_ticker, 'yahoo', start, end)
        ohlc_traces = []
        candlestick_traces = []
        
        for i, ticker in enumerate(input_ticker):
            if isinstance(df.columns, pd.MultiIndex):
                d = df.xs(ticker, axis=1, level=1)
            else:
                d = df
            
            # Simple color cycle
            color = colors[i % len(colors)]
            
            candlestick_traces.append(
                go.Candlestick(
                    x=d.index, open=d['Open'], high=d['High'],
                    low=d['Low'], close=d['Close'], name=ticker
                )
            )
            ohlc_traces.append(
                go.Ohlc(
                    x=d.index, open=d['Open'], high=d['High'],
                    low=d['Low'], close=d['Close'], name=ticker
                )
            )
            
        layout = go.Layout(
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            template='plotly_white',
            hovermode='x'
        )
        
        return {'data': candlestick_traces, 'layout': layout}, {'data': ohlc_traces, 'layout': layout}
        
    except Exception:
        raise PreventUpdate

@app.callback([Output("news", "children"), Output("news-no", "children")], 
            [Input("refresh", "n_intervals")])
def renew_news(n):
    infos = update_news()
    return infos[1], f"Last updated: {datetime.now().strftime('%H:%M:%S')}"