import dash
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import pandas_datareader.data as web
import datetime
from dash.exceptions import PreventUpdate
from collections import deque


app = dash.Dash()
ticker_lst = ['AAPL']

app.layout = html.Div(children=[
    html.H1(children="Option Pricing Tool"),
    html.Div(id="manual", children='''Dash: A platform for stock option pricing'''),
    dcc.Store(id='ticker_mem'),
    dcc.Input(id="ticker_input", placeholder='Enter Stock ticker',
              type="text", debounce=True),
    dcc.Dropdown(id='total_ticker', options=[], value=['AAPL', 'TSLA'],
                 placeholder='Enter a stock ticker', multi=True),
    html.Button(children='Clear All Stocks', id='clear', n_clicks=0,
                className='two columns'),
    dcc.Input(id='true_clear', value=0, style={'display': 'None'}),
    dcc.Dropdown(id="ppty_input",
                 options=[{'label': 'Open Price', 'value': 'Open'},
                          {'label': 'Close Price', 'value': 'Close'},
                          {'label': 'Daily High', 'value': 'High'},
                          {'label': 'Daily Low', 'value': 'Low'},
                          {'label': 'Adjoint Close', 'value': 'Adj Close'}],
                 placeholder='Choose a label to display'),
    dcc.Graph(id='output-graph'),
])


# @app.callback(Output('total_ticker', 'options'), [Input('ticker_input', 'value')],
#               [State('total_ticker', 'options')])
# def callback(new_value, current_options):
#     new_entry = {'label': new_value, 'value': new_value}
#     if not new_value or new_entry in current_options:
#         pass
#     else:
#         current_options.append(new_entry)
#     return current_options

# @app.callback([Output('test', 'children'), Output('true_clear', 'value')],
#               [Input('clear', 'n_clicks')], [State('true_clear', 'value')])
# def fire(click, state):
#     if click != state:
#         state = click
#         return f'''{state} Seven Hells''', state
#     else:
#         raise PreventUpdate

@app.callback([Output('total_ticker', 'value'), Output('total_ticker', 'options'),
               Output('true_clear', 'value')],
              [Input('ticker_input', 'value'), Input('clear', 'n_clicks')],
              [State('total_ticker', 'value'), State('total_ticker', 'options'),
               State('true_clear', 'value')])
def callback(new_value, btn, current_ticker, current_options, state):
    new_entry = {'label': new_value, 'value': new_value}
    if int(btn) != state:
        current_options.clear()
        state = int(btn)
    elif new_value:
        if new_entry not in current_options:
            current_options.append(new_entry)
        if new_value not in current_ticker:
            current_ticker += [new_value]
    else:
        pass
    return current_ticker, current_options, state

# @app.callback(Output('total_ticker', 'options'), [Input('clear', 'n_clicks')],
#               [State('total_ticker', 'options')])
# def clear_stock_pool(btn, options):
#     if btn > 0:
#         options.clear()
#         btn = 0
#     return options


@app.callback(Output("output-graph", 'figure'),
              [Input("total_ticker", 'value'), Input('ppty_input', 'value')]
              )
def update_graph(input_ticker, ppty_input):
    if not input_ticker or not ppty_input:
        raise PreventUpdate
    start = datetime.datetime(2015, 1, 1)
    end = datetime.datetime(2016, 1, 1)
    df = web.DataReader(input_ticker, 'yahoo', start, end)
    df.reset_index(inplace=True)
    df.set_index("Date", inplace=True)
    # df.drop("Symbol", axis=1, inplace=True)
    traces = []
    layout = go.Layout(
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
                # marker={
                #     'size': 5,
                #     'line': {'width': 0.5, 'color': 'white'}
                # },
                name=ticker
            )),
    figure = {
        'data': traces, 'layout': layout
    }
    return figure


if __name__ == '__main__':
    app.run_server(debug=True)

# print(update_value('AAPL'))
