import math

import pandas as pd
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dateutil.parser

# from sfManager import sf_Manager

import dash
import dash_html_components as html


class CustomDash(dash.Dash):
    def interpolate_index(self, **kwargs):
        # Inspect the arguments by printing them
        kwargs['app_entry'] = '''<div id="react-entry-point">
                                <div class="_dash-loading">
                                    <div class="progress">
                                        <div class="indeterminate"></div>
                                    </div>
                                </div>
                                </div>'''
        return '''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <meta http-equiv="X-UA-Compatible" content="ie=edge" />
                <title>Option Pricing Tool</title>
                <link rel="shortcut icon" type="image/png" href="src/assets/favicon.ico"/>
                {css}
            </head>
            <body id="bg-img">
                {app_entry}

                <footer class="page-footer">
                <div class="footer-copyright">
                <div class="container">
                &copy; 2019, Zhicheng Han. All Rights Reserved.
                <a class="grey-text text-lighten-4 right" 
                href="#!">Endenicher Allee 60, Bonn • MIT License • hanzc.kernel@gmail.com</a>
                </div>
                </div>
                </footer>

                {config}
                {scripts}
                {renderer}
            </body>

        </html>
        '''.format(
            css=kwargs['css'],
            app_entry=kwargs['app_entry'],
            config=kwargs['config'],
            scripts=kwargs['scripts'],
            renderer=kwargs['renderer'])


server = flask.Flask(__name__)
app = CustomDash(__name__, server=server,
                 assets_folder="./src", assets_ignore=".scss")
app.config.suppress_callback_exceptions = True


# sf_manager = sf_Manager()
