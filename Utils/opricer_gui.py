import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import flask
import plotly.plotly as py
from plotly import graph_objs as go
from apps import option
from dash.exceptions import PreventUpdate
import datetime


app = dash.Dash(__name__)

app.layout = html.Div(
    [html.Div([
        html.Div([
            html.H1("Option Pricing Tool"),
            html.P('option pricing powered by numpy & dash')],
            className='app-title col-75'),
        html.Div(
            [html.Img(src=app.get_asset_url('markt.png'), height="100%")],
            className='app-title col-25'),
    ],
        className="row header"
    ),

        html.Div(className='container', children=[
            html.Label('Option Type', className='col-25'),
            dcc.RadioItems(id='otype', options=[
                {'label': 'Call Option', 'value': 'call'},
                {'label': 'Put Option', 'value': 'put'},
                {'label': 'Barrier Option', 'value': 'barrier'},
            ], value='call', labelStyle={'display': 'inline-block'},
                className='col-75'),
            html.Label('Spot Date', className='col-25'),
            dcc.DatePickerSingle(
                id='expiry', date=datetime.datetime.today(),
                className='col-75')
        ]),
        html.Div(className='container', children=[
            html.Label('Expiry Date', className='col-25'),
            dcc.DatePickerSingle(id='date', placeholder='Enter spot date',
                                 className='col-75'),
            html.Label('Strike Price', className='col-25'),
            dcc.Input(id='strike', placeholder='strike',
                      type='number', debounce=True, className='col-75'),
            html.Label('Spot Price', className='col-25'),
            dcc.Input(id='spot', placeholder='spot price',
                      type='number', debounce=True, className='col-75'),
            html.Label('Volatility', className='col-25'),
            dcc.Input(id='vol', placeholder='volatility',
                      type='number', debounce=True, className='col-75'),
        ]
    ),
        html.Button('Submit', id='button'),

        html.Link(href="https://fonts.googleapis.com/css?family=Dosis",
                  rel="stylesheet"),
        html.Link(href="https://fonts.googleapis.com/css?family=Open+Sans",
                  rel="stylesheet"),
        html.Link(href="https://fonts.googleapis.com/css?family=Ubuntu",
                  rel="stylesheet"), ],
    className="row",
    style={"display": "flex",
           "flex-direction": "column"},)


if __name__ == '__main__':
    app.run_server(debug=True, port=2019)
