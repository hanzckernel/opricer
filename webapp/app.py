import dash
import dash_bootstrap_components as dbc
import flask

# Use a modern Bootstrap theme (FLATLY is clean and professional for finance)
external_stylesheets = [dbc.themes.FLATLY]

server = flask.Flask(__name__)

app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    title="Option Pricing Tool",
    update_title=None
)

# Expose server for WSGI
server = app.server