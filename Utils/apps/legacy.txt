dcc.RangeSlider(id='date-slider', min=0, max=100,
                marks={}, step=100, value=[0, 100])


@app.callback(
    [Output('date-slider', 'max'), Output('date-slider', 'marks'),
     Output('date-slider', 'steps')],
    [Input('date_picker', 'start_date'), Input('date_picker', 'end_date')]
)
def config_slider(start_date, end_date):
    if start_date and end_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        steps = (end - start).days
        timeLst = pd.timedelta_range(0, end - start, periods=steps)
        dateLst = (timeLst + start).strftime('%d, %b %Y')
        datedf = dict(zip(timeLst.days, dateLst))
        return steps, datedf, steps
    else:
        raise PreventUpdate


html.Div(
                [
                    html.P(
                        "Top Open stock",
                        style={
                            "color": "#2a3f5f",
                            "fontSize": "13px",
                            "textAlign": "center",
                            "marginBottom": "0",
                        },
                    ),
                    html.Div(
                        id="top_open_stock",
                        style={"padding": "0px 13px 5px 13px",
                               "marginBottom": "5"},
                    ),

                ],
                className="six columns",
                style={
                    "backgroundColor": "white",
                    "border": "1px solid #C8D4E3",
                    "borderRadius": "3px",
                    "height": "100%",
                    "overflowY": "scroll",
                },
            ),
            html.Div(
                [
                    html.P(
                        "Top Lost stock",
                        style={
                            "color": "#2a3f5f",
                            "fontSize": "13px",
                            "textAlign": "center",
                            "marginBottom": "0",
                        },
                    ),
                    html.Div(
                        id="top_lost_stock",
                        style={"padding": "0px 13px 5px 13px",
                               "marginBottom": "5"},
                    )
                ],
                className="six columns",
                style={
                    "backgroundColor": "white",
                    "border": "1px solid #C8D4E3",
                    "borderRadius": "3px",
                    "height": "100%",
                    "overflowY": "scroll",
                },
            ),html.Div(
                [
                    html.P(
                        "Top Open stock",
                        style={
                            "color": "#2a3f5f",
                            "fontSize": "13px",
                            "textAlign": "center",
                            "marginBottom": "0",
                        },
                    ),
                    html.Div(
                        id="top_open_stock",
                        style={"padding": "0px 13px 5px 13px",
                               "marginBottom": "5"},
                    ),

                ],
                className="six columns",
                style={
                    "backgroundColor": "white",
                    "border": "1px solid #C8D4E3",
                    "borderRadius": "3px",
                    "height": "100%",
                    "overflowY": "scroll",
                },
            ),
            html.Div(
                [
                    html.P(
                        "Top Lost stock",
                        style={
                            "color": "#2a3f5f",
                            "fontSize": "13px",
                            "textAlign": "center",
                            "marginBottom": "0",
                        },
                    ),
                    html.Div(
                        id="top_lost_stock",
                        style={"padding": "0px 13px 5px 13px",
                               "marginBottom": "5"},
                    )
                ],
                className="six columns",
                style={
                    "backgroundColor": "white",
                    "border": "1px solid #C8D4E3",
                    "borderRadius": "3px",
                    "height": "100%",
                    "overflowY": "scroll",
                },
            ),


def update_news():
    url = 'https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey=da8e2e705b914f9f86ed2e9692e66012'
    try:
        r = requests.get(url)
        json_data = r.json()["articles"]
        df = pd.DataFrame(json_data)
        df = pd.DataFrame(df[["title", "url"]])
    except Exception as e:
        data = {"title": ["news api not retrievable"], "url": [url]}
        df = pd.DataFrame(data=data, columns=["title", "url"])
    return generate_news_table(df)


layout = [

    # top controls
    html.Div(
        [
            html.Div(
                dcc.Dropdown(
                    id="converted_leads_dropdown",
                    options=[
                        {"label": "By day", "value": "D"},
                        {"label": "By week", "value": "W-MON"},
                        {"label": "By month", "value": "M"},
                    ],
                    value="D",
                    clearable=False,
                ),
                className="two columns",
            ),
            html.Div(
                dcc.Dropdown(
                    id="lead_source_dropdown",
                    options=[
                        {"label": "All status", "value": "all"},
                        {"label": "Open leads", "value": "open"},
                        {"label": "Converted leads", "value": "converted"},
                        {"label": "Lost leads", "value": "lost"},
                    ],
                    value="all",
                    clearable=False,
                ),
                className="two columns",
            ),

            # add button
            html.Div(
                html.Span(
                    "Add new",
                    id="new_option",
                    n_clicks=0,
                    className="button button--primary",
                    style={
                        "height": "34",
                        "background": "#119DFF",
                        "border": "1px solid #119DFF",
                        "color": "white",
                    },
                ),
                className="two columns",
                style={"float": "right"},
            ),
        ],
        className="row",
        style={"marginBottom": "10"},
    ),

    # indicators row div
    html.Div(
        [
            indicator(
                "#00cc96", "Converted Leads", "left_leads_indicator"
            ),
            indicator(
                "#119DFF", "Open Leads", "middle_leads_indicator"
            ),
            indicator(
                "#EF553B",
                "Conversion Rates",
                "right_leads_indicator",
            ),
        ],
        className="row",
    ),

    # charts row div
    html.Div(
        [
            html.Div(
                [
                    html.P("Leads count per state"),
                    dcc.Graph(
                        id="map",
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),
                ],
                className="four columns chart_div"
            ),

            html.Div(
                [
                    html.P("Leads by source"),
                    dcc.Graph(
                        id="lead_source",
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),
                ],
                className="four columns chart_div"
            ),

            html.Div(
                [
                    html.P("Converted Leads count"),
                    dcc.Graph(
                        id="converted_leads",
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),
                ],
                className="four columns chart_div"
            ),
        ],
        className="row",
        style={"marginTop": "5"},
    ),

    # table div
    html.Div(
        id="leads_table",
        className="row",
        style={
            "maxHeight": "350px",
            "overflowY": "scroll",
            "padding": "8",
            "marginTop": "5",
            "backgroundColor": "white",
            "border": "1px solid #C8D4E3",
            "borderRadius": "3px"
        },
    ),


    modal(),
]

if focus and focus['column'] != 0:
            i, j = secret_df.index[focus['row']], focus['column_id']
            if secret_df.at[i, j] != secret_df.at[j, i]:
                if float(secret_df.at[i, j]) > 1 or float(secret_df.at[i, j]) < -1:
                    secret_df.at[i, j] = secret_df.at[j, i]
                else:
                    secret_df.at[j, i] = secret_df.at[i, j]
        else:
            secret_df.sort_index(axis=0, inplace=True)
            secret_df.sort_index(axis=1, inplace=True)
            if set(secret_df.columns) - set(tickers): # if remove tickers
                secret_df = secret_df.loc[tickers, tickers]
            elif set(tickers) - set(secret_df.columns): # if add tickers
                new_ticker = (set(tickers) - set(secret_df.columns)).pop()
                secret_df.loc[new_ticker, new_ticker] = 1.0