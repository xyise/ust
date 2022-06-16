import numpy as np
import dash
from dash.dependencies import Input, Output
from dash import dcc
#import dash_core_components as dcc
from dash import html
#import dash_html_components as html
import plotly.express as px
import pandas as pd
from db_manager_UST import *
from bond_analytics import *
import re


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

myDB = db_manager_UST()

available_dates = np.array([r['Date'] for r in myDB.db[myDB.col_confirmed_date_name].find({})])
available_dates = np.sort(available_dates)

df_empty = pd.DataFrame({'x':[0], 'y':[0]})

app.layout = html.Div(children=[

    html.H1(children='US Treasury Securities'),

    html.Div([

        html.Label('Select Date'), 
        
        dcc.DatePickerSingle(
            id='my-date-picker', 
            min_date_allowed=available_dates[0], 
            max_date_allowed=available_dates[-1], 
            initial_visible_month=available_dates[-1],
            date=available_dates[-1], 
            first_day_of_week=1
        ),

        dcc.Markdown(children=
    '''
        [Google Cloud Compute Engine](http://https://console.cloud.google.com/compute), 
        [Treasury Direct](https://www.treasurydirect.gov/GA-FI/FedInvest/selectSecurityPriceDate.htm)
    ''')]),

    dcc.Graph(
        id='example-graph',
        figure=px.scatter(df_empty)
    )
])

@app.callback(
    Output('example-graph','figure'),
    [Input('my-date-picker', 'date')]
)
def update_fig(date):

    if date is None:
        return px.scatter(df_empty)


    dt = datetime.datetime.strptime(re.split('T| ', date)[0], '%Y-%m-%d')
    df = myDB.retrieve_as_of(dt)

    if df is None:
        return px.scatter(df_empty)

    df = df[df['type'].isin(['Note', 'Bond'])].copy()

    df['Time-to-maturity'] = (df['maturityDate'] - df['date']).dt.days / 365.0
    df['Term'] = (df['maturityDate'] - df['issueDate']).dt.days / 365.0
    df['Coupon'] = [str(r * 100) + '\%' for r in df['interestRate'].values]
    df['Price'] = df['endOfDay']

    def find_yield(ds):
        bond = USConventional(ds['type'], ds['issueDate'], 
        ds['maturityDate'], ds['interestRate'])
        price = ds['endOfDay'] 
        if price > 0.01:
            y = bond.get_yield(dt, ds['endOfDay'])
        else:
            y = np.nan
        return y

    df['Yield'] = df.apply(find_yield, axis = 1)


    symbol_size = [(r * 100) + 1 for r in df['interestRate']]

    fig = px.scatter(df, 
        x="Time-to-maturity", y="Yield", color="Term", size=symbol_size, 
        hover_name="cusip")

    return fig

if __name__ == '__main__':
#    app.run_server(host="0.0.0.0",port=8050)
    app.run_server(debug=True)
#    import flask
#    server = flask.Flask(__name__)