import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from db_manager_UST import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

myDB = db_manager_UST()
df = myDB.retrieve_as_of(datetime.datetime(2020,8,6))
df = df[df['type'].isin(['Note', 'Bond'])].copy()
df['ttm'] = (df['maturityDate'] - df['date']).dt.days / 365.0
df['term'] = (df['maturityDate'] - df['issueDate']).dt.days / 365.0
df['size'] = 2 * df['interestRate'] * 100 + 2


fig = px.scatter(df, x="ttm", y="endOfDay", color="term", size="size")

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
#    app.run_server(host="0.0.0.0",port=8050)
    app.run_server(debug=True)
#    import flask
#    server = flask.Flask(__name__)