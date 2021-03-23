import re
from typing import Collection

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server

poverty_data = pd.read_csv('../data/PovStatsData.csv')
poverty = pd.read_csv('../data/poverty.csv', low_memory=False)
series = pd.read_csv('../data/PovStatsSeries.csv')

gini = 'GINI index (World Bank estimate)'
gini_df = poverty[poverty[gini].notna()]


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

perc_pov_cols = poverty.filter(regex='Poverty gap').columns
perc_pov_df = poverty[poverty['is_country']].dropna(subset=perc_pov_cols)
perc_pov_years = sorted(set(perc_pov_df['year']))

cividis0 = px.colors.sequential.Cividis[0]

def make_empty_fig():
    fig = go.Figure()
    fig.layout.paper_bgcolor = '#E5ECF6'
    fig.layout.plot_bgcolor = '#E5ECF6'
    return fig


def multiline_indicator(indicator):
    final = []
    split = indicator.split()
    for i in range(0, len(split), 3):
        final.append(' '.join(split[i:i+3]))
    return '<br>'.join(final)


app.layout = html.Div([
    dbc.Col([
        html.Br(),
        html.H1('Poverty And Equity Database'),
        html.H2('The World Bank'),

    ], style={'textAlign': 'center'}),
    html.Br(),
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            dbc.Tabs([
                dbc.Tab([
                    html.Br(),
                    dcc.Dropdown(id='indicator_dropdown',
                                 value='GINI index (World Bank estimate)',
                                 options=[{'label': indicator,
                                 'value': indicator} 
                                 for indicator in poverty.columns[3:54]]),
                    dcc.Graph(id='indicator_map_chart'),
                    dcc.Markdown(id='indicator_map_details_md',
                                style={'backgroundColor': '#E5ECF6'})
                ], label='Explore Metrics'),
                dbc.Tab([
                    html.Br(),
                    dbc.Row([
                        dbc.Col(lg=1),
                        dbc.Col([
                            dbc.Label('Select the year:'),
                            dcc.Slider(id='year_cluster_slider',
                                    min=1974, max=2018, step=1, included=False,
                                    value=2018,
                                    marks={year: str(year)
                                            for year in range(1974, 2019, 5)})
                        ], lg=6, md=12),
                        dbc.Col([
                            dbc.Label('Select the number of clusters:'),
                            dcc.Slider(id='ncluster_cluster_slider',
                                    min=2, max=15, step=1, included=False,
                                    value=4,
                                    marks={n: str(n) for n in range(2, 16)}),
                        ], lg=4, md=12)
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(lg=1),
                        dbc.Col([
                            dbc.Label('Select Indicators:'),
                            dcc.Dropdown(id='cluster_indicator_dropdown',optionHeight=40,
                                        multi=True,
                                        value=['GINI index (World Bank estimate)'],
                                        options=[{'label': indicator, 'value': indicator}
                                                for indicator in poverty.columns[3:54]]),
                        ], lg=6),
                        dbc.Col([            
                            dbc.Label(''),html.Br(),
                            dbc.Button("Submit", id='clustering_submit_button'),
                        ]),
                    ]),
                    dcc.Loading([
                        dcc.Graph(id='clustered_map_chart')
                    ])
                ], label='Cluster Countries'),
            ]),
        ], lg=8)
    ]),
    html.Br(),
        html.Br(),
        html.Hr(),
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            dbc.Label('Indicator:'),
            dcc.Dropdown(id='hist_indicator_dropdown',optionHeight=40,
                         value='GINI index (World Bank estimate)',
                         options=[{'label': indicator, 'value': indicator}
                                  for indicator in poverty.columns[3:54]]),
        ], lg=5),
        dbc.Col([
            dbc.Label('Years:'),
            dcc.Dropdown(id='hist_multi_year_selector',
                         multi=True,
                         value=[2015],
                         placeholder='Select one or more years',
                         options=[{'label': year, 'value': year}
                                  for year in poverty['year'].drop_duplicates().sort_values()]),
        ], lg=3),
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            html.Br(),
            dbc.Label('Modify number of bins:'),
            dcc.Slider(id='hist_bins_slider', 
                       dots=True, min=0, max=100, step=5, included=False,
                       marks={x: str(x) for x in range(0, 105, 5)}),
            dcc.Graph(id='indicator_year_histogram',figure=make_empty_fig()),                       
        ], lg=8)
        
    ]),
    
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            html.Div(id='table_histogram_output'),
            html.Br(), html.Br(),
        ], lg=8)
    ]),

    html.H2('Gini Index - World Bank Data', style={'textAlign': 'center'}),
    html.Br(),
    dbc.Row([
        dbc.Col(lg=1),
        dbc.Col([
            dbc.Label('Year'),
            dcc.Dropdown(id='gini_year_dropdown',
                         placeholder='Select a year',
                         options=[{'label': year, 'value': year}
                                  for year in gini_df['year'].drop_duplicates().sort_values()]),
            html.Br(),
            dcc.Graph(id='gini_year_barchart',
                      figure=make_empty_fig())
        ], md=12, lg=5),
        dbc.Col([
            dbc.Label('Countries'),
            dcc.Dropdown(id='gini_country_dropdown',
                         placeholder='Select one or more countries',
                         multi=True,
                         options=[{'label': country, 'value': country}
                                  for country in gini_df['Country Name'].unique()]),
            html.Br(),
            dcc.Graph(id='gini_country_barchart',
                      figure=make_empty_fig())
        ], md=12, lg=5),
    ]),
    dbc.Row([
        dbc.Col(lg=2),
        dbc.Col([
            html.Br(),
            html.H2('Income Share Distribution', style={'textAlign': 'center'}),
            html.Br(),
            dbc.Label('Country'),
            dcc.Dropdown(id='income_share_country_dropdown', 
                         placeholder='Select a country',
                         options=[{'label': country, 'value': country}
                                  for country in income_share_df['Country Name'].unique()]),
            dcc.Graph(id='income_share_country_barchart',
                     figure=make_empty_fig())
        ], lg=8)
    ]),
    html.Br(),
    html.H2('Poverty Gap at $1.9, $3.2, and $5.5 (% of population)',
            style={'textAlign': 'center'}),
            html.Br(),html.Br(),

    dbc.Row([
        dbc.Col(lg=2),

    dbc.Col([
        dbc.Label('Select poverty level:'),
        dcc.Slider(id='perc_pov_indicator_slider', 
                   min=0,
                   max=2,
                   step=1,
                   included=False,
                   value=0,
                   marks={0:  {'label': '$1.9', 'style': {'color': cividis0, 'fontWeight': 'bold', 'fontSize': 15}}, 
                          1:  {'label': '$3.2', 'style': {'color': cividis0, 'fontWeight': 'bold', 'fontSize': 15}},
                          2:  {'label': '$5.5', 'style': {'color': cividis0, 'fontWeight': 'bold', 'fontSize': 15}}}),
        ], lg=2),
    dbc.Col([
        dbc.Label('Select year:'),
        dcc.Slider(id='perc_pov_year_slider',
                   min=perc_pov_years[0], 
                   max=perc_pov_years[-1],
                   step=1,
                   included=False,
                   value=2018,
                   marks={year: {'label': str(year), 
                                 'style': {'color': cividis0, 'fontSize': 14}} 
                          for year in perc_pov_years[::5]}),
        ], lg=5),
  ]),
    dbc.Row([
        dbc.Col(lg=1),
        dbc.Col([
            dcc.Graph(id='perc_pov_scatter_chart',
                      figure=make_empty_fig())
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
        ], label='Poject Info')
    ]),
], style={'backgroundColor': '#E5ECF6'})

@app.callback(Output('indicator_map_chart', 'figure'),
              Output('indicator_map_details_md', 'children'),
              Input('indicator_dropdown', 'value'))
def display_generic_map_chart(indicator):
    if indicator is None:
        raise PreventUpdate
    df = poverty[poverty['is_country']]
    fig = px.choropleth(df, locations='Country Code', 
                        color=indicator,
                        title=indicator,
                        hover_name='Country Name',
                        color_continuous_scale='cividis',
                        animation_frame='year', height=650)
    fig.layout.geo.showframe = False
    fig.layout.geo.showcountries = True
    fig.layout.geo.projection.type = 'natural earth'
    fig.layout.geo.lataxis.range = [-53, 76]
    fig.layout.geo.lonaxis.range = [-138, 167]
    fig.layout.geo.landcolor = 'white'
    fig.layout.geo.bgcolor = '#E5ECF6'
    fig.layout.paper_bgcolor = '#E5ECF6'
    fig.layout.geo.countrycolor = 'gray'
    fig.layout.geo.coastlinecolor = 'gray'
    fig.layout.coloraxis.colorbar.title = multiline_indicator(indicator)
    
    series_df = series[series['Indicator Name'].eq(indicator)]
    if series_df.empty:
        markdown = "No details available on this indicator"
    else:
        limitations = series_df['Limitations and exceptions'].fillna('N/A').str.replace('\n\n', ' ').values[0]

        markdown = f"""
        ## {series_df['Indicator Name'].values[0]}  
        
        {series_df['Long definition'].values[0]}  
        
        * **Unit of measure** {series_df['Unit of measure'].fillna('count').values[0]}
        * **Periodicity** {series_df['Periodicity'].fillna('N/A').values[0]}
        * **Source** {series_df['Source'].values[0]}
        
        ### Limitations and exceptions:  
        
        {limitations}  

        """
    return fig, markdown


@app.callback(Output('gini_year_barchart', 'figure'),
              Input('gini_year_dropdown', 'value'))
def plot_gini_year_barchart(year):
    if not year:
        raise PreventUpdate
    df = gini_df[gini_df['year'].eq(year)].sort_values(gini).dropna(subset=[gini])
    n_countries = len(df['Country Name'])
    fig = px.bar(df,
                 x=gini,
                 y='Country Name', 
                 orientation='h',
                 height=200 + (n_countries*20), 
                 width=650,
                 title=gini + ' ' + str(year))
    fig.layout.paper_bgcolor = '#E5ECF6'                 
    return fig


@app.callback(Output('gini_country_barchart', 'figure'), Input('gini_country_dropdown', 'value'))
def plot_gini_country_barchart(countries):
    if not countries:
        raise PreventUpdate
    df = gini_df[gini_df['Country Name'].isin(countries)].dropna(subset=[gini])
    fig = px.bar(df,
                 x='year',
                 y=gini,
                 height=100 + (250*len(countries)),
                 facet_row='Country Name',
                 color='Country Name',
                 labels={gini: 'Gini Index'},
                 title=''.join([gini, '<br><b>', ', '.join(countries), '</b>']))
    fig.layout.paper_bgcolor = '#E5ECF6'                 
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
                 orientation='h')
    fig.layout.legend.title = None
    fig.layout.legend.orientation = 'h'
    fig.layout.legend.x = 0.2
    fig.layout.legend.y = -0.15
    fig.layout.xaxis.title = 'Percent of Total Income'
    fig.layout.paper_bgcolor = '#E5ECF6'
    fig.layout.plot_bgcolor = '#E5ECF6'
    return fig

@app.callback(Output('perc_pov_scatter_chart', 'figure'),
              Input('perc_pov_year_slider', 'value'),
              Input('perc_pov_indicator_slider', 'value'))
def plot_perc_pov_chart(year, indicator):
    indicator = perc_pov_cols[indicator]
    df = (perc_pov_df
          [perc_pov_df['year'].eq(year)]
          .dropna(subset=[indicator])
          .sort_values(indicator))
    if df.empty:
        raise PreventUpdate

    fig = px.scatter(df,
                     x=indicator, 
                     y='Country Name',
                     color='Population, total', 
                     size=[30]*len(df),
                     size_max=15,
                     hover_name='Country Name',
                     height=250 +(20*len(df)),
                     color_continuous_scale='cividis',
                     title=indicator + '<b>: ' + f'{year}' +'</b>')
    fig.layout.paper_bgcolor = '#E5ECF6'
    fig.layout.xaxis.ticksuffix = '%'
    return fig

@app.callback(Output('indicator_year_histogram', 'figure'),
              Output('table_histogram_output', 'children'),
              Input('hist_multi_year_selector', 'value'),
              Input('hist_indicator_dropdown', 'value'),
              Input('hist_bins_slider', 'value'))
def display_histogram(years, indicator, nbins):
    if (not years) or (not indicator):
        raise PreventUpdate
    df = poverty[poverty['year'].isin(years) & poverty['is_country']]
    fig = px.histogram(df, x=indicator, facet_col='year', color='year', 
                       title=indicator + ' Histogram',
                       nbins=nbins,
                       facet_col_wrap=4, height=700)
    fig.for_each_xaxis(lambda axis: axis.update(title=''))
    fig.add_annotation(text=indicator, x=0.5, y=-0.12, xref='paper', yref='paper', showarrow=False)
    fig.layout.paper_bgcolor = '#E5ECF6'

    table = DataTable(columns = [{'name': col, 'id': col} 
                                 for col in df[['Country Name', 'year', indicator]].columns],
                      data = df[['Country Name', 'year', indicator]].to_dict('records'),
                      style_header={'whiteSpace': 'normal'},
                      fixed_rows={'headers': True},
                      virtualization=True,
                      style_table={'height': '400px'},
                      sort_action='native',
                      filter_action='native',
                      export_format='csv',
                      style_cell={'minWidth': '150px'}),
    return fig, table


@app.callback(Output('clustered_map_chart', 'figure'),
              Input('clustering_submit_button', 'n_clicks'),
              State('year_cluster_slider', 'value'),
              State('ncluster_cluster_slider', 'value'),
              State('cluster_indicator_dropdown', 'value'))
def clustered_map(n_clicks, year, n_clusters, indicators):
    if not indicators:
        raise PreventUpdate
    imp = SimpleImputer(missing_values=np.nan, strategy='mean')
    scaler = StandardScaler()
    kmeans = KMeans(n_clusters=n_clusters)
    
    df = poverty[poverty['is_country'] & poverty['year'].eq(year)][indicators + ['Country Name', 'year']]
    data = df[indicators]
    if df.isna().all().any():
        return px.scatter(title='No available data for the selected combination of year/indicators.')
    data_no_na = imp.fit_transform(data)
    scaled_data = scaler.fit_transform(data_no_na)
    kmeans.fit(scaled_data)

    fig = px.choropleth(df,
                        locations='Country Name',
                        locationmode='country names',
                        color=[str(x) for x in  kmeans.labels_], 
                        labels={'color': 'Cluster'},
                        hover_data=indicators,
                        height=650,
                        title=f'Country clusters - {year}. Number of clusters: {n_clusters}<br>Inertia: {kmeans.inertia_:,.2f}',
                        color_discrete_sequence=px.colors.qualitative.T10)
    fig.add_annotation(x=-0.1, y=-0.15, 
                       xref='paper', yref='paper',
                       text='Indicators:<br>' + "<br>".join(indicators), 
                       showarrow=False)
    fig.layout.geo.showframe = False
    fig.layout.geo.showcountries = True
    fig.layout.geo.projection.type = 'natural earth'
    fig.layout.geo.lataxis.range = [-53, 76]
    fig.layout.geo.lonaxis.range = [-137, 168]
    fig.layout.geo.landcolor = 'white'
    fig.layout.geo.bgcolor = '#E5ECF6'
    fig.layout.paper_bgcolor = '#E5ECF6'
    fig.layout.geo.countrycolor = 'gray'
    fig.layout.geo.coastlinecolor = 'gray'
    return fig
    

if __name__ == '__main__':
    app.run_server(debug=True)
