import dash
import dash_html_components as html
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = html.Div([
    html.H1('Poverty And Equity Database',
            style={'color': 'blue',
                   'fontSize': '40px'}),
    html.H2('The World Bank'),
    html.P('Key Facts:'),
    html.Ul([
        html.Li('Number of Economies: 170'),
        html.Li('Temporal Coverage: 1974 - 2019'),
        html.Li('Update Frequency: Quarterly'),
        html.Li('Last Updated: March 18, 2020'),
        html.Li([
            'Source: ',
            html.A('https://datacatalog.worldbank.org/dataset/poverty-and-equity-database',
                   href='https://datacatalog.worldbank.org/dataset/poverty-and-equity-database')
        ])
    ]),
    html.P('external_stylesheets=[dbc.themes.DARKLY]')
])


if __name__ == '__main__':
    app.run_server(debug=True)
