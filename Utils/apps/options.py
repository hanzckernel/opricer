# -*- coding: utf-8 -*-
import json
import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_daq as daq
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
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup

from scipy.linalg import cholesky


# memoization of scraping data
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache'
})


def func_check(string):
    pass
    


def parse_table(tag):
    page = requests.get(f"https://www.global-rates.com/interest-rates/libor/{tag}/2019.aspx")
    soup = BeautifulSoup(page.content, 'lxml')
    page = soup.find('tr', 'tableheader').parent

#   prepocessing the data

    df = pd.read_html(str(page))[0]
    df.set_index(df.columns[0], inplace=True)
    df.columns = df.iloc[0]
    df = df[1:]
    df.replace('-', float('nan'), inplace=True)
    df.dropna(how='all', axis=0, inplace=True)
    df.index.name = 'Time'
    df.replace(r'\xa0%', '', regex=True, inplace=True)
    df = df.astype(float)/100
    df.reset_index(inplace=True)
    # return df.to_dict('records')
    return df


@cache.memoize(timeout=36000)
def scrape_libor():
    currency_list = ['japanese-yen', 'american-dollar',
                     'british-pound-sterling', 'european-euro', "swiss-franc"]
    dfs = {tag: parse_table(tag) for tag in currency_list}
    return dfs


def modal():
    return html.Div(
        html.Div([html.Div([
            # modal header
            html.Div(
                [
                html.Span("New Option"),
                html.Span(
                    "X",
                    id="option_modal_close",
                    n_clicks=0,
                    style={
                        "float": "right",
                        "cursor": "pointer",
                        "marginTop": "0",
                        "marginBottom": "17",
                    },
                ),
                html.Div(className="divider hide-on-med-and-down")
            ], className="caption",
                ),


            # modal form
            html.Div([
                html.Div(
                [html.P(['Supports mathematical function inputs. For details see:  ',
                 html.A('HERE', href="https://docs.python.org/3/library/math.html")]),
                html.P('Example: lambda x, y: np.sin(x) **2  + np.arctan(y)')], 
                style={'display':'none'}, 
                className='col s8', id='func_tip'),
                html.Div(daq.ToggleSwitch(id='func_off', label=['Input Function Type', 'Input Constant Type'],
                         value=True, color='rosybrown'), className='col s4 right'),
            ], className='row'),
            html.Div(
                html.Div([
                html.Div([
                    dcc.Input(id='asset_name', type='text', 
                    # placeholder="input asset name",
                                className='validate'),
                    html.Label("Name of Asset", htmlFor='asset_name'),
                ], className="input-field col s12 m6"),

                html.Div([
                    dcc.Input(id='spot', type='number', step=0.01,
                        # placeholder="choose spot price",
                            min=0.01,
                                className='validate'),
                    html.Label("Spot Price", htmlFor='spot'),
                ], className="input-field col s12 m6"),


                html.Div([
                    dcc.Input(id='volatility', type='number', step=0.001,
                        min = 0, 
                        # placeholder="input volatility of asset",
                        className='validate'),
                    html.Label("Volatility (%)", htmlFor='volatility'),
                ], className="input-field col s12 m6"),

                html.Div([
                    dcc.Input(id='dividend', type='number', step=0.001,
                        min = 0, placeholder="input dividend of asset",
                        value = 0, className='validate'),
                    html.Label("Dividend (%)", htmlFor='dividend'),
                ], className="input-field col s12 m6"),
            ], className='container'),
            className='row'
            ),

            # submit button
                

            html.Div(
                [
                html.Button(
                "Submit",
                id="submit_new_option",
                type='submit',
                n_clicks=0,
                className="btn waves-effect waves-light center-align"
                ),
                html.Span(id='missing_warning', style={'display':'none', 'color':'red'})
                ], className='modal-footer'
            )], className="modal-content center-align",
            )
            ],
            className="custom-modal",
            ),
        id="option_modal",
        style={"display": "none"},
    )


layout = [
    #first row 

    html.Div(
        [
        html.Div(
        [
            html.H3("Underlyings", className='title'),
            html.Div(html.Button(
                    "Add New Underlying Asset",
                    id="new_underlying",
                    n_clicks=0,
                    className="waves-effect waves-light btn",
                ), className="col s12"),
            html.Div(className='divider col s12 hide-on-med-and-down', style={"margin": "1.5rem 0"}),
            html.P("Dates of Speculation", className="title"),
                dcc.DatePickerRange(
                id="spot_date",
                start_date_placeholder_text='Choose your spot date',
                end_date_placeholder_text='Choose your strike date',
                display_format='MMM Do, YYYY',
                clearable=True,
                start_date='2015-1-1',
                end_date='2016-1-1',
                show_outside_days=True,
                ),
            html.Div([
                html.P("Type of Option", className='title'),
                dcc.RadioItems(id='ocate', options=[
                    {'label': 'European Option', 'value': 'EurOption'},
                    {'label': 'American Option', 'value': 'AmeOption'},
                    {'label': 'Barrier Option', 'value': 'BarOption'}], value='EurOption',
                    style={"flex-direction":'column'}, className="custom-gap custom-radio", 
                    ),
            ], className="col s12"),
            
            html.Div([
                html.P("Choice of Call / Put", className='title'),
                dcc.RadioItems(id='otype', options=[
                {'label': 'Call Option', 'value':'call'},
                {'label': 'Put Option', 'value':'put'}
                ], value='call', style={"flex-direction":'column'},
                className="custom-gap custom-radio", 
                ), 
            ], className="col s12"),
        ], className="col s12 m12 l3 center-align"
    ),
    # top controls
    html.Div(
        [
        html.Div(
            [
            html.P('Correlation Heatmap', className='title'),
            dcc.Graph(id='heat-map', figure={'layout': go.Layout(
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            paper_bgcolor='rgba(255, 255, 255, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin={'t':40},
            )}, style={"height":"80vh"}
            )], 
            className = "col s12 m12 l6"
        ),
        html.Div([
        html.P("Watched Correlation Structure", className='title'),
        dcc.Dropdown(id='underlying_pool',
                             options=[],
                             value=[],
                             placeholder='Your Underlying Pool', multi=True,
                            className="col s12",
                            style={"margin-bottom": "1rem"}),
        html.Button('Clear All Stocks', id='option-clear', n_clicks=0,
                    className="btn waves-effect blue waves-light"),
        dcc.Input(id='clear_all', value=0, style={'display': 'none'}),
        html.P("Correlation Structure", className='title'),
        dash_table.DataTable(
                        id='corr_matrix',
                        columns=[{'id': 'Ticker', 'name': ' Asset Name', 'editable': False},
                                 {'id': 'Test', 'name': 'Test'}],
                        data=[{'Ticker': 'Test', 'Test': 1.0}],
                        editable=True,
                        style_table={'maxHeight': '25vh', 'overflowY': 'scroll',
                                    'height':'25vh', 'padding':'0 1rem'},
                        style_cell={"maxWidth":"1rem", 'fontFamily': 'Arial',
                        "fontWeight":"300", "filter": "brightness(125%)",
                        'backgroundColor':'rgba(255, 255, 255, 0.2)'},
                        css=[{"selector": "tr", "rule": 'background-color:rgba(255, 255, 255, 0.2)'}]
                    ),
        html.P("Asset List", className='title'),
        dash_table.DataTable(
            id='asset_info',
            columns=[{'name': 'Name', 'id': 'Name', 'editable': False},
                        {'name': 'Spot Price', 'id': 'spot', 'type': 'numeric',
                    "format":FormatTemplate.money(2)},
                    #     {'name': 'Interest Rate', 'id': 'int_rate', 'type': 'numeric',
                    # "format":FormatTemplate.percentage(2)},
                        {'name': 'Volatiltiy', 'id': 'volatility', 'type': 'numeric',
                        "format":FormatTemplate.percentage(2)},
                        {'name': 'Dividend', 'id': 'dividend', 'type': 'numeric',
                        "format":FormatTemplate.percentage(2)}
                        ],
            style_table={'maxHeight': '25vh', 'overflowY': 'scroll', "height":"20vh",
                        'padding':'0 1rem'},
            style_cell={"maxWidth":"1rem", 'fontFamily': 'Arial',
                    "fontWeight":"300", "filter": "brightness(125%)",
                    'backgroundColor':'rgba(255, 255, 255, 0.2)'},
            css=[{"selector": "tr", "rule": 'background-color:rgba(255, 255, 255, 0.2)'}],
            row_deletable=True,
            editable=True,
            data=[],
        ),
            
        ], 
        className="col s12 m12 l6"
        ),
         ], className="col s12 m12 l9 center-align"
    ),
        ], className='row'
    ),
    html.Div(className='divider row hide-on-med-and-down', style={'margin-top':'1rem'}),

    #second row

    html.Div([
        
        html.Div([
        html.H3("World Data", className='title'),
        html.Div([
            dcc.Input(id='risk_free_rate', type='number', step=0.001,
                      # placeholder="choose risk-free rate of asset",
                      className='validate', disabled=True, style={'color':'white'}),
            html.Label("Risk-free interest rate (%)", htmlFor='risk_free_rate'),
        ], className="input-field col s12 m4", style={'color':'white'}),
        html.Div([daq.ToggleSwitch(id='libor_on', label=['Use customized rates', 'Use LIBOR rates'],
                         value=True, color='skyblue', size=80)], 
                         className='col s12 m4', style={'margin-top':'1rem'}),
        # html.P('Choose Libor-based currency', className='title', style={'margin-top':'1rem'}),
        dcc.Dropdown(id='choose_currency', placeholder='Choose Libor based-currency',
                    className='col s12 m4', style={'margin-top':'1rem'},
                     options=[{"label": tag.replace('-', ' ').title(), "value": tag}
                      for tag in scrape_libor().keys()]),
        # html.Div(id='int_rate'),
        dcc.Store(id='int_rate'),
    ], className='col s12 center-align'),
    html.Div([
        dash_table.DataTable(
            id='libor_table',
            style_cell={'fontFamily': 'Arial',
                        "fontWeight": "300", "filter": "brightness(125%)",
                        'backgroundColor': 'rgba(255, 255, 255, 0.2)'},
            css=[{"selector": "tr", "rule": 'background-color:rgba(255, 255, 255, 0.2)'}]),
        
        dcc.ConfirmDialog(id='true-confirm'),
            ],
             className='col s12 center-align'),
    html.Div([
                    dcc.Input(id='strike', type='number', step=0.001, min = 0.01,
                    className='validate', style={"color":"white"}),
                    html.Label("Strike Price", htmlFor='strike'),
                ], className="input-field col s12"),
    html.Div([
        html.Button('Compute Price!', id='confirm', n_clicks=0, 
        className="btn btn-large red waves-effect waves-light"),
    ], className='col s12 center-align', style={'margin-bottom':'1rem'}),


    html.Div(className='divider col s12 hide-on-med-and-down'),
    ], className='col s12'),

    #third row
    # html.Div([
        html.Div([
    html.H3("The Fair Option Price", className='title'),
    daq.ToggleSwitch(id='as3d', label=['2D', '3D'], value=True, color='skyblue',
            style={"float":'right'})],className="col s12", style={"margin-bottom":"1rem"}),
    html.Div([dcc.Graph(
        figure={
            "layout":go.Layout(
            hovermode='closest',
            paper_bgcolor='rgba(255, 255, 255, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin={'t':20, 'l':20, 'b':20, 'r':20},
            )
        },
        id='opricer_graph', style={"height": "70vh", 'width':"95vw"}),
    ], className="col s12"),
    html.Div([dcc.Graph(id='2d_graph', style={"display":'none', "height":"70vh", 'width':"95vw"})], 
    className='col s12'),
    # ], className="row center-align"
    # ),

    html.Div(id='test'),

    # modal div
    html.Div(modal()),
]

# Modal controlling

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

# Choose modal input type
@app.callback([Output('func_tip', 'style'), Output('volatility', 'type'),
             Output('dividend', 'type')],
             [Input('func_off', 'value')], [State('func_tip', 'style')])
def turnoff_func_input(func_off, style):
    if func_off:
        style['display']='none'
        return style, 'number', 'number'
    else:
        style['display']='inline-block'
        return style, 'text', 'text'




# First Row Correlation Matrix Controlling

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
                    if float(item_changed[1]) >= 1 or float(item_changed[1]) <= -1:
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


# Correlation Matrix => Heat Map

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
            'colorscale':'Viridis',
            'opacity':0.9,
            "hovertemplate":'%{y} and %{x} are %{z}-correlated',
        }],

        'layout': go.Layout(
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            paper_bgcolor='rgba(255, 255, 255, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin={'t':40},
            )
    }


@app.callback(
    [Output("option_modal_close", 'n_clicks'), Output('missing_warning', 'children'),
    Output('missing_warning', 'style'), Output('asset_info', 'data'),
    Output('clear_all', 'value')],
    [Input("submit_new_option", "n_clicks"), Input('option-clear', 'n_clicks')],
    [State('asset_name', 'value'),State('spot', 'value'), 
    # State('int_rate', 'value'),
    State('volatility', 'value'), State('dividend', 'value'), 
    State('missing_warning', 'style'),
    State('underlying_pool', 'options'), State('asset_info', 'data'),
     State('clear_all', 'value')]
)
def check_validity(n, clear_btn, name, spot, 
                 vol, div, style, options, data, clear_state):
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
            message = 'Spot price must not be empty nor negative'
        elif not vol or vol < 0:
            message = f'Volatility must not be empty nor negative'
        elif div < 0 or div > 100:
            message = f'{div} is not valid. Dividend must be positive and smaller than 1'
    
    if message:
        style['display']='block'
        return 0, message, style, data, clear_state
    else:
        data.append({'Name': name, 'spot': spot, 
                # 'int_rate': float(int_rate)/100, 
                    'volatility': float(vol)/100, 'dividend':float(div)/100})
        return 1, message, style, data, clear_state


### Add Ticker. Similar Function as Stock tab, except more complicated ###

@app.callback([Output('underlying_pool', 'value'), Output('underlying_pool', 'options')],
              [Input('asset_info', 'data')])
def update_ticker(data):
    # new_ticker = str.upper("".join(new_ticker.split()))
    nameLst = [row['Name'] for row in data]
    options = [{'label': name, 'value': name} for name in nameLst]
    return nameLst, options

#################################################
#  Switch between Libor and custom rates`       #
#################################################

@app.callback([Output('risk_free_rate', 'disabled'), Output('choose_currency', 'disabled')],
              [Input('libor_on', 'value'), ])
def turnon_libor(on):
    if on:    
        return True, False
    else:
        return False, True

@app.callback([Output('libor_table', 'columns'), Output('libor_table', 'data')],
                [Input('choose_currency', 'value')])
def choose_libor_currency(currency):
    if currency:
        dfs = scrape_libor()[currency]
        cols = [{'id': dfs.columns[0], 'name': dfs.columns[0]}] + [
            {'id': col, 'name': col.title(), 'type': 'numeric',
             "format": FormatTemplate.percentage(4)} for col in dfs.columns[1:]]
        return cols, dfs.to_dict('records')
    else:
        return [], []

# Send interest rat
@app.callback(Output('int_rate', 'data'),
    [Input('risk_free_rate', 'value'), Input('libor_table', 'data'), Input('libor_on', 'value')])
def store_int_rate(custom_rate, libor_table, libor_on):
    if libor_on and libor_table:
        return libor_table[-1]['average']
    elif not libor_on and custom_rate is not None:
        return custom_rate/100
    else:
        raise PreventUpdate


    

###########################################
#### Here begins the Option Pricing!!! ####
###########################################
@app.callback(
            [Output('opricer_graph', 'style'),
            Output('2d_graph', 'figure'),Output('2d_graph', 'style')],
            [Input('as3d', 'value')],
            [State('opricer_graph', 'figure'), State('opricer_graph', 'style'),
            State('2d_graph', 'style')])
def change2d(as3d, fig3d, style3d, style2d):
    if as3d:
        style2d['display']='none'
        style3d['display']="block"
        return style3d, {}, style2d
    else:
        try:
        
            scatter = fig3d['data'][0]
            x = scatter['x']
            y = scatter['z'][0]
            figure= {
                "data": [go.Scatter(x=x, y=y, mode='lines')],
                "layout": go.Layout(
                xaxis={'title':'Spot Price at End Time'},
                yaxis={'title':"Option Price"},
                hovermode='closest',
                paper_bgcolor='rgba(255, 255, 255, 0.5)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin={'t':30},
                )
            }
            style3d['display']="none"
            style2d['display']='block'
            return style3d, figure, style2d
        except KeyError:
            raise PreventUpdate

# @app.callback([Output('as3d', 'disabled'), Output('as3d', 'value')],
#                 [Input('ocate', 'value')])
# def disable3d(ocate):
#     if ocate == 'AmeOption':
#         return True, False
#     else:
#         return False, True


@app.callback(
    # Output('test', 'children'),
    Output('opricer_graph', 'figure'),
    [Input('true-confirm', 'submit_n_clicks')],
    [State('asset_info', 'data'), State('ocate', 'value'), State('otype', 'value'),
    State('spot_date', 'start_date'), State('spot_date', 'end_date'), State('strike', 'value'),
    State('int_rate', 'data'), State('corr_matrix', 'data')]
)
def plot_graph(n_clicks, data, ocate, otype, spot_date, strike_date, strike, int_rate, corr_matrix):
    '''
    We use Monte-Carlo Simulation here by default. At later phase one may consider optimize
    the plotting by using other PDESolver / AnalyticSolver for simpler case:
    '''
    if data and strike and int_rate:
        start = datetime.strptime(spot_date, '%Y-%m-%d')
        end = datetime.strptime(strike_date, '%Y-%m-%d')
        dic = {asset['Name']: models.Underlying(start, asset['spot'], dividend=asset['dividend']) 
                for asset in data}

        # Verify which solver and option object to be initialized
        if len(dic) == 1:
            option = getattr(models, ocate)(end, otype)
            option._attach_asset(strike, *dic.values())
            option.int_rate = lambda t: int_rate
            if ocate == 'EurOption':
                solver = pde.EurSolver()
            elif ocate == 'AmeOption':
                solver = pde.AmeSolver()
            elif ocate == 'BarOption':
                raise ValueError('currently not supported..')
                # solver = pde.BarSolver()
            price=solver(option)
            x_axis = solver.asset_samples.flatten()

        else:
            option = models.BasketOption(end, otype)
            option._attach_asset(strike, *dic.values())
            option.corr_mat = pd.DataFrame(corr_matrix).fillna(0).drop(
                            'Ticker', axis=1).values.astype('float')
            if ocate == 'EurOption':
                solver = mc.BasketMCSolver()
            elif ocate == 'AmeOption':
                solver = mc.BasketAmeSolver()
            elif ocate == 'BarOption':
                raise ValueError('currently not supported..')
                # solver = mc.BarMCSolver()
            else:
                raise ValueError('Unknown Option Type')
            price = solver(option)
            x_axis = solver.asset_samples.squeeze(1).sum(axis=-1)
            
        # hover_samples = np.tile([', '.join(row) for row in x_axis.astype(str)], (solver.time_no, 1)).T
        traces=[go.Surface(
                    x=x_axis,
                    y=pd.date_range(start, end, solver.time_no).strftime('%Y-%m-%d, %r'),
                    z=price,
                    # text= hover_samples,
                    opacity=0.9,
                    name=solver.__class__.__name__,
                    colorscale='Viridis',
                    # hoverinfo='text'
                    hovertemplate='''Average Spot Price: %{x}
                    <br>Time: %{y}<br>Estimated Option Worth: %{z}''',
                )]

        graph_layout = go.Layout(
            scene=dict(
            xaxis={'title': 'Asset', "tickvals":np.linspace(x_axis[0], x_axis[-1], 5),
             "ticktext": np.round(np.linspace(solver.asset_samples[0], solver.asset_samples[-1], 5), 5)},
            yaxis={'title': 'Date', 
            'showticklabels':False},
            zaxis={'title':'Fair Price'}),
            hovermode='closest',
            paper_bgcolor='rgba(255, 255, 255, 0.5)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin={'t':0, 'l':0, 'b':20, 'r':0, 'pad':0},
            )
        figure = {
                'data': traces, 'layout': graph_layout
            }
        del option, solver
        return figure
    else:
        raise PreventUpdate

### Confirm Computation Dialog ###

@app.callback([Output('true-confirm', 'displayed'),Output('true-confirm', 'message')],
            [Input('confirm', 'n_clicks')], [State('strike', 'value'), 
            State('int_rate', 'data'), State('asset_info', 'data')]
            )
def call_pop_up(n, strike, int_rate, data):
    if n:
        if not strike:
            return True, 'Have You forgot to input your strike price?'
        elif int_rate is None:
            return True, 'Have You forgot to get a valid interest rate?'
        elif not data:
            return True, 'Have you forgot to attach any underlying asset?'
        else:
            # if strike and int_rate is not None and not data:
            detail = f'''\nYou are about to compute an option with:\n 
                Strike Price of Option: {strike}\n
                Risk-free Interest Rate: {int_rate}\n
                Are you ready to compute the price? This might take a while..
                '''
            return True, detail
    return False, ''


