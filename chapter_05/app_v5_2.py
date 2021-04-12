import re

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

poverty_data = pd.read_csv('../data/PovStatsData.csv')
poverty = pd.read_csv('../data/poverty.csv', low_memory=False)
gini = 'GINI index (World Bank estimate)'

regions = ['East Asia & Pacific', 'Europe & Central Asia',
           'Fragile and conflict affected situations', 'High income',
           'IDA countries classified as fragile situations', 'IDA total',
           'Latin America & Caribbean', 'Low & middle income', 'Low income',
           'Lower middle income', 'Middle East & North Africa',
           'Middle income', 'South Asia', 'Sub-Saharan Africa',
           'Upper middle income', 'World']

population_df = poverty_data[~poverty_data['Country Name'].isin(regions) &
                             (poverty_data['Indicator Name']== 'Population, total')]

income_share_df = poverty.filter(regex='Country Name|^year$|Income share.*?20').dropna()
income_share_df = income_share_df.rename(columns={
    'Income share held by lowest 20%': '1 Income share held by lowest 20%',
    'Income share held by second 20%': '2 Income share held by second 20%',
    'Income share held by third 20%': '3 Income share held by third 20%',
    'Income share held by fourth 20%': '4 Income share held by fourth 20%',
    'Income share held by highest 20%': '5 Income share held by highest 20%'
}).sort_index(axis=1)

income_share_df.columns = [re.sub('\d Income share held by ', '', col).title()
                           for col in income_share_df.columns]
income_share_cols = income_share_df.columns[:-2]

app.layout = html.Div([
    html.H1('Poverty And Equity Database'),
    html.H2('The World Bank'),
    dcc.Dropdown(id='country',
                 options=[{'label': country, 'value': country}
                          for country in poverty_data['Country Name'].unique()]),
    html.Br(),
    html.Div(id='report'),
    html.Br(),
    dcc.Dropdown(id='year_dropdown',
                 value='2010',
                 options=[{'label': year, 'value': str(year)}
                          for year in range(1974, 2019)]),
    dcc.Graph(id='population_chart'),
    html.Br(),
    html.H2('Gini Index - World Bank Data', style={'textAlign': 'center'}),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='gini_year_dropdown',
                         options=[{'label': year, 'value': year}
                                  for year in poverty['year'].unique()]),
            html.Br(),
            dcc.Graph(id='gini_year_barchart')
        ]),
        dbc.Col([
            dcc.Dropdown(id='gini_country_dropdown',
            options=[{'label': country, 'value': country}
                     for country in poverty['Country Name'].unique()]),
            html.Br(),
            dcc.Graph(id='gini_country_barchart')
        ]),
    ]),
    dbc.Row([
        dbc.Col(lg=1),
        dbc.Col([
            html.H2('Income Share Distribution', style={'textAlign': 'center'}),
            html.Br(),
            dcc.Dropdown(id='income_share_country_dropdown', 
                         options=[{'label': country, 'value': country}
                                  for country in income_share_df['Country Name'].unique()]),
            dcc.Graph(id='income_share_country_barchart')
        ], lg=10)

    ]),

    dbc.Tabs([
       dbc.Tab([
           html.Ul([
               html.Br(),
               html.Li('Number of Economies: 170'),
               html.Li('Temporal Coverage: 1974 - 2019'),
               html.Li('Update Frequency: Quarterly'),
               html.Li('Last Updated: March 18, 2020'),
               html.Li([
                   'Source: ',
                   html.A('https://datacatalog.worldbank.org/dataset/poverty-and-equity-database',
                          href='https://datacatalog.worldbank.org/dataset/poverty-and-equity-database')
               ])
           ])

       ], label='Key Facts'),
        dbc.Tab([
            html.Ul([
                html.Br(),
                html.Li('Book title: Interactive Dashboards and Data Apps with Plotly and Dash'),
                html.Li(['GitHub repo: ',
                         html.A('https://github.com/PacktPublishing/Interactive-Dashboards-and-Data-Apps-with-Plotly-and-Dash',
                                href='https://github.com/PacktPublishing/Interactive-Dashboards-and-Data-Apps-with-Plotly-and-Dash')
                         ])
            ])
        ], label='Project Info')
    ]),

])


@app.callback(Output('report', 'children'),
              Input('country', 'value'))
def display_country_report(country):
    if country is None:
        return ''

    filtered_df = poverty_data[(poverty_data['Country Name']==country) &
                               (poverty_data['Indicator Name']=='Population, total')]
    population = filtered_df.loc[:, '2010'].values[0]

    return [html.H3(country),
            f'The population of {country} in 2010 was {population:,.0f}.']


@app.callback(Output('population_chart', 'figure'),
              Input('year_dropdown', 'value'))
def plot_countries_by_population(year):
    fig = go.Figure()
    year_df = population_df[['Country Name', year]].sort_values(year, ascending=False)[:20]
    fig.add_bar(x=year_df['Country Name'],
                y=year_df[year])
    fig.layout.title = f'Top twenty countries by population - {year}'
    return fig


@app.callback(Output('gini_year_barchart', 'figure'),
              Input('gini_year_dropdown', 'value'))
def plot_gini_year_barchart(year):
    if not year:
        raise PreventUpdate
    df = poverty[poverty['year'].eq(year)].sort_values(gini).dropna(subset=[gini])
    n_countries = len(df['Country Name'])
    fig = px.bar(df,
                 x=gini,
                 y='Country Name', 
                 orientation='h',
                 height=200 + (n_countries*20), 
                 width=650,
                 title=gini + ' ' + str(year))
    return fig


@app.callback(Output('gini_country_barchart', 'figure'), Input('gini_country_dropdown', 'value'))
def plot_gini_country_barchart(country):
    if not country:
        raise PreventUpdate
    df = poverty[poverty['Country Name']==country].dropna(subset=[gini])
    fig = px.bar(df,
                 x='year',
                 y=gini, 
                 title=' - '.join([gini, country]))
    return fig


@app.callback(Output('income_share_country_barchart', 'figure'), Input('income_share_country_dropdown', 'value'))
def plot_income_share_barchart(country):
    if country is None:
        raise PreventUpdate
    fig = px.bar(income_share_df[income_share_df['Country Name']==country].dropna(), 
                 x=income_share_cols,
                 y='Year',
                 barmode='stack',
                 height=600, 
                 hover_name='Country Name',
                 title=f'Income Share Quintiles - {country}',
                 orientation='h',
                 )
    fig.layout.legend.title = None
    fig.layout.legend.orientation = 'h'
    fig.layout.legend.x = 0.2
    fig.layout.xaxis.title = None
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
