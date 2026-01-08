from dash import dcc, html
from dash.dependencies import Input, Output
from dash.development.base_component import Component
from Utils.app import app
from Utils.apps import stock, options


app.layout = html.Div(
    [
        # header
        html.Div(
            [
                html.Section(
                    [
                        html.H1("Option Pricing Tool", className="title"),
                        html.H5(
                            "pricing UI powered by Numpy & Dash",
                            className="title",
                        ),
                    ],
                    className="container",
                ),
                # tabs
                html.Div(
                    [
                        dcc.Tabs(
                            id="tabs",
                            children=[
                                dcc.Tab(label="Stock Market", value="stock_tab"),
                                dcc.Tab(label="Option Pricing", value="option_tab"),
                            ],
                            value="option_tab",
                        )
                    ],
                    className="tabs_div",
                ),
                # Tab content
                html.Div(id="tab_content", className="row"),
            ],
            style={"margin": "0%"},
        ),
    ],
    className="content-main",
)


@app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
def render_content(tab: str) -> Component:
    if tab == "stock_tab":
        return stock.layout
    elif tab == "option_tab":
        return options.layout
    else:
        return stock.layout


if __name__ == "__main__":
    app.run_server(debug=True)
