import dash
import dash_html_components as html

app = dash.Dash(__name__)

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
            html.A(children='https://datacatalog.worldbank.org/dataset/poverty-and-equity-database',
                   href='https://datacatalog.worldbank.org/dataset/poverty-and-equity-database')
        ])
    ])
])


if __name__ == '__main__':
    app.run_server(debug=True)

from jupyter_dash import JupyterDash
import dash_html_components as html
app = JupyterDash(__name__)

app.layout = html.Div([
    html.H1('Blah Blah Blah BlahBlah BlahBlah BlahBlah BlahBlah Blah')
])

if __name__ == '__main__':
    app.run_server(mode='inline', port=1234, width=100)
from dash.dependencies import Output, Input

Input()