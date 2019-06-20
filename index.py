# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import flask
import plotly.plotly as py
from plotly import graph_objs as go
import math
from Utils.app import app, server
# from app import sf_manager
from Utils.apps import stock, options
# from apps import cases

app.layout = html.Div(
    [
        # header
        html.Div([

            html.Span("Option Pricing Tool",
                      className='app-title ten columns'),
            html.Div(
                html.Img(src=app.get_asset_url('markt.png'), height="80%"),
                style={"float": "right", "height": "100%", "padding-top": '1%'},
                className='two columns'),
            html.P('pricing app powered by Numpy & Dash')
        ],
            className="row header"
        ),

        # tabs
        html.Div([

            dcc.Tabs(
                id="tabs",
                style={"height": "20", "verticalAlign": "middle"},
                children=[
                    dcc.Tab(label="Stock Market", value="stock_tab"),
                    dcc.Tab(label="Option Pricing", value="option_tab"),
                    # dcc.Tab(id="cases_tab", label="Cases", value="cases_tab"),
                ],
                value="stock_tab",
            )

        ],
            className="row tabs_div"
        ),


        # divs that save dataframe for each tab
        html.Div(
            # sf_manager.get_stock().to_json(orient="split"),  # stock df
            id="stock_df",
            style={"display": "none"},
        ),
        html.Div(
            # sf_manager.get_leads().to_json(orient="split"),
            id="leads_df", style={"display": "none"}),  # leads df
        # html.Div(
        # sf_manager.get_cases().to_json(orient="split"),
        # id="cases_df", style={"display": "none"}),  # cases df



        # Tab content
        html.Div(id="tab_content", className="row", style={"margin": "2% 3%"}),

        html.Footer(
            'Endenicher Allee 60, Bonn • MIT License • hanzc.kernel@gmail.com'),

        html.Link(
            href="https://use.fontawesome.com/releases/v5.2.0/css/all.css", rel="stylesheet"),
        # html.Link(href="https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css", rel="stylesheet"),
        html.Link(href="https://fonts.googleapis.com/css?family=Dosis",
                  rel="stylesheet"),
        html.Link(
            href="https://fonts.googleapis.com/css?family=Open+Sans", rel="stylesheet"),
        html.Link(
            href="https://fonts.googleapis.com/css?family=Ubuntu", rel="stylesheet"),
        # html.Link(href="https://cdn.rawgit.com/amadoukane96/8a8cfdac5d2cecad866952c52a70a50e/raw/cd5a9bf0b30856f4fc7e3812162c74bfc0ebe011/dash_crm.css", rel="stylesheet")
    ],
    className="row",
    style={"margin": "0%"},
)


@app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
def render_content(tab):
    if tab == "stock_tab":
        return stock.layout
    # elif tab == "cases_tab":
        # return cases.layout
    elif tab == "option_tab":
        return options.layout
    else:
        return stock.layout


if __name__ == "__main__":
    app.run_server(debug=True)
