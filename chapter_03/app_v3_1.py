import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

poverty_data = pd.read_csv('../data/PovStatsData.csv')

regions = ['East Asia & Pacific', 'Europe & Central Asia',
           'Fragile and conflict affected situations', 'High income',
           'IDA countries classified as fragile situations', 'IDA total',
           'Latin America & Caribbean', 'Low & middle income', 'Low income',
           'Lower middle income', 'Middle East & North Africa',
           'Middle income', 'South Asia', 'Sub-Saharan Africa',
           'Upper middle income', 'World']

population_df = poverty_data[~poverty_data['Country Name'].isin(regions) &
                             (poverty_data['Indicator Name']== 'Population, total')]

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


if __name__ == '__main__':
    app.run_server(debug=True)
