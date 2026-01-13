from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from webapp.app import app
from webapp.apps import stock, options

# Define the Navigation Bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Stock Market", href="/stock", id="stock-link")),
        dbc.NavItem(dbc.NavLink("Option Pricing", href="/options", id="options-link")),
    ],
    brand="Option Pricing Tool",
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True,
)

# Define the main layout
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        dbc.Container(id="page-content", fluid=True, className="mt-4"),
    ]
)

# Callback to handle routing
@app.callback(
    [Output("page-content", "children"), Output("stock-link", "active"), Output("options-link", "active")],
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/" or pathname == "/stock":
        return stock.layout, True, False
    elif pathname == "/options":
        return options.layout, False, True
    return dbc.Alert("404: Page not found", color="danger"), False, False

if __name__ == "__main__":
    app.run(debug=True)