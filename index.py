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
        html.Div(
            [
                html.Section([
                    html.H1("Option Pricing Tool", className="title"),
                    html.H5("pricing UI powered by Numpy & Dash",
                            className="title")
                ],
                    className="container"
                ),

                # tabs
                html.Div([
                    dcc.Tabs(
                        id="tabs",
                        children=[
                            dcc.Tab(label="Stock Market",
                                    value="stock_tab"),
                            dcc.Tab(label="Option Pricing",
                                    value="option_tab"),
                        ],
                        value="option_tab",
                    )
                ],
                    className="tabs_div"
                ),

                # Tab content
                html.Div(id="tab_content", className="row"),
            ],
            style={"margin": "0%"},
        ),
    ], className="content-main"
)


@app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
def render_content(tab):
    if tab == "stock_tab":
        return stock.layout
    elif tab == "option_tab":
        return options.layout
    else:
        return stock.layout


if __name__ == "__main__":
    app.run_server(debug=True)
