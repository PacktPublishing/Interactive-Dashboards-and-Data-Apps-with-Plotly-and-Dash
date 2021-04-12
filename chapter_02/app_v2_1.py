import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
import pandas as pd

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

poverty_data = pd.read_csv('../data/PovStatsData.csv')

app.layout = html.Div([
    html.H1('Poverty And Equity Database'),
    html.H2('The World Bank'),
    dcc.Dropdown(id='country',
                 options=[{'label': country, 'value': country}
                          for country in poverty_data['Country Name'].unique()]),
    html.Br(),
    html.Div(id='report'),
    html.Br(),
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


if __name__ == '__main__':
    app.run_server(debug=True)