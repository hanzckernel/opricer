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