#############
# LIBRERIAS #
#############

# Required libraries
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from scipy.interpolate import interp1d

# Pyomo Output Functions
from src import output_data


# ======================= #
# PACKAGING RESOURCE PATH #
# ======================= #

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Path a la carpeta de imagenes
DATA_PATH = resource_path('data/tmp/output')



##################
# CARGA DE DATOS #
##################

# Data Loader
def load_data(path):
    # Loading Pyomo Output Data from Pyomo
    d_vars = output_data.vars_csv_to_dict(path)

    # Investment Costs
    df_inv_costs = d_vars['vInvCost']
    df_inv_costs['sYear'] = df_inv_costs["sYear"].str.replace("y","").astype(int)
    df_inv_costs = df_inv_costs.sort_values(by=["vInvCost", "sYear"], ascending=False)
    
    # Operational Costs
    df_op_costs = d_vars['vOpCost']
    df_op_costs['sYear'] = df_op_costs["sYear"].str.replace("y","").astype(int)

    # Total Emissions
    df_total_emissions = d_vars['vEmiTot']
    df_total_emissions['sYear'] = df_total_emissions["sYear"].str.replace("y","").astype(int)
    return df_inv_costs, df_op_costs, df_total_emissions

# Loading the data
df_inv_costs, df_op_costs, df_total_emissions = load_data(DATA_PATH)

# Years
min_year = df_inv_costs.copy()['sYear'].min()
max_year = df_inv_costs.copy()['sYear'].max()

# Energy Sources
inv_energy_sources = df_inv_costs["sCE"].unique()

#############
# FUNCIONES #
#############

def filter_energy_sources(df, selected_sources):
    """
    This function filters the dataframe by Energy Source
    
    """
    # Filtered Dataframe
    return df[df['sCE'].isin(selected_sources)]
#-----

def filter_years(df, selected_years):
    return df.copy()[(df['sYear'] >= int(selected_years[0])) & (df['sYear'] <= int(selected_years[1]))]
#-----

def plotInvestmentCosts(df):
    """
    This function plots a stacked barplot showing the investment costs by energy source and year
    """
    fig = px.bar(df, x="sYear", y="vInvCost", color="sCE", barmode="stack", title="Investment Costs")

    min_year = df['sYear'].min()
    max_year = df['sYear'].max()

    if not pd.isna(min_year):
        tickvals = list(range(min_year, max_year+5, 5))
        ticktext = [str(year) for year in tickvals]
    else:
        tickvals, ticktext = [], []

    fig.update_layout(xaxis=dict(tickmode='array',
                                tickvals=tickvals,
                                ticktext=ticktext))
    return fig
#-----

def plotOperationalCosts(df):
    """
    This functions plots a Time Series with the operation costs over the years
    """
    fig = px.line(df, x="sYear", y="vOpCost", title= "Operational Costs")
    return fig
#-----

def plotTotalStackedEmissions(df, emmissions_limit):
    """
    This functions plots the aggregated total emissions over the year
   
     """
    # Cumulative Emissions
    cum_emissions = df['vEmiTot'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        name = "Yearly Emissions",
        x = df['sYear'].values,
        y = df['vEmiTot'].values,
    ))
    fig.add_trace(go.Scatter(
        name = "Cumulative Emissions",
        x = df['sYear'].values,
        y = cum_emissions,
        fill='tozeroy',
        mode = "none"
    )),
    fig.add_hline(y=emmissions_limit, line_dash="dash", line_color="green")
    
    if emmissions_limit >= cum_emissions.min() and emmissions_limit <= cum_emissions.max():
        # Find the x-value of the intersection point
        intersection_y = emmissions_limit
        f = interp1d(cum_emissions, df['sYear'].values)
        intersection_x = f(intersection_y)
        
        # Add the intersection point to the chart
        fig.add_scatter(x=[intersection_x], y=[intersection_y],
                    mode="markers", marker=dict(size=10, color="red"),
                    text=[f"Intersection ({intersection_x:.2f}, {intersection_y:.2f})"],
                    textposition="bottom center", showlegend=False),

    return fig
#-----

def update_figures(df_inv_costs, df_op_costs, df_total_emissions,selected_sources, selected_years, emissions_limit):
    # Filter Energy Source
    df_filtered_inv = filter_energy_sources(df_inv_costs, selected_sources)
    # Filter Year
    df_filtered_inv = filter_years(df_filtered_inv, selected_years)

    # Stacked Bar Plot Figure
    investment_cost_figure = plotInvestmentCosts(df_filtered_inv)

    # Filter Year for Operational Costs
    df_filtered_op = filter_years(df_op_costs, selected_years)

    # Stacked Bar Plot Figure for Operational Costs
    operational_cost_figure = plotOperationalCosts(df_filtered_op)

    # Total Emissions Plot
    total_emissions_figure = plotTotalStackedEmissions(df_total_emissions, emissions_limit)

    return investment_cost_figure, operational_cost_figure, total_emissions_figure


########
# TABS #
########
emissions_tab = dbc.Container(
    [
        dbc.Row([
                dbc.Col([
                    html.H1("Energy Generation Emissions",  
                        style={
                            "margin-left": "0.5%",
                            "margin-top":"0.5%",
                            "margin-bottom":"0.5%",
                            "textAlign": "left",
                        }
                    )
                ],
                lg = 12)
            ],
            style={
                "margin": "auto",
                "textAlign": "center",
            }
        ),

        html.Hr(),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label("Emissions Limit: "),
                        dcc.Input(
                            id='tot_emissions_limit',
                            type='number',
                            value=2000,
                            min=0,
                            max=10000,
                            step=100
                        )
                    ]
                )
            ]
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph
                        (
                            id="total_emissions_fig",
                            style={
                                "display": "block"
                            },
                        ),     
                    ],
                    lg = 12
                )
            ]
        )

    ]
)
#------

costs_tab = dbc.Container(
    [
        dbc.Row([
                dbc.Col([
                    html.H1("Energy Generation Costs",  
                        style={
                            "margin-left": "0.5%",
                            "margin-top":"0.5%",
                            "margin-bottom":"0.5%",
                            "textAlign": "left",
                        }
                    )
                ],
                lg = 12)
            ],
            style={
                "margin": "auto",
                "textAlign": "center",
            }
        ),

        html.Hr(),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.DropdownMenu(
                            label="Select Energy Sources",
                            children=[
                                dbc.Button("Select/Deselect All", id="select-deselect-all", color = "Light", className="me-1"),
                                dbc.Checklist(
                                    options=[
                                        {"label": energy_source, "value": energy_source}
                                        for energy_source in inv_energy_sources
                                    ],
                                    value=inv_energy_sources,
                                    id="eng_source_checklist"
                                )
                            ],
                            color="primary",
                            className="mb-3",
                        )
                    ],
                ),
                dbc.Col(
                    [
                        dbc.Label("sYear"), 
                        dcc.RangeSlider(
                            id="year-slider",
                            min=min_year,
                            max=max_year,
                            step=5,
                            value=[min_year, max_year],
                            marks={year: str(year) for year in range(min_year, max_year+1, 5)})
                    ]
                                        
                )
            ]
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph
                        (
                            id="inv_costs_fig",
                            style={
                                "display": "block"
                            },
                        ),     
                    ],
                    lg = 6
                ),

                dbc.Col(
                    [
                        dcc.Graph
                        (
                            id="op_costs_fig",
                            style={
                                "display": "block"
                            },
                        ),     
                    ],
                    lg = 6
                )
            ]
        )

    ]
)
#------

scenarios_tab = dbc.Container(
    [
        dbc.Row([
                dbc.Col([
                    html.H1("Scenarios",  
                        style={
                            "margin-left": "0.5%",
                            "margin-top":"0.5%",
                            "margin-bottom":"0.5%",
                            "textAlign": "left",
                        }
                    )
                ],
                lg = 12)
            ],
            style={
                "margin": "auto",
                "textAlign": "center",
            }
        ),

        html.Hr(),

        dbc.Row(
            [
                dbc.Label("Scenario"),
                dcc.Dropdown(
                            id = "dropdown-scenario",
                            options = [
                                "SC01",
                                "SC02",
                            ],
                            value = "SC01",
                            style = {})
            ],
        )
    ]
)

########
# DASH #
########

# Initializing a Plotly Dashboard
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.LUX]
)

# APP Title
app.title = "openMASTER"

# Defining the APP Layout
app.layout = dbc.Tabs(
    [
        dbc.Tab(scenarios_tab, label='Scenario'),
        dbc.Tab(costs_tab, label='Costs'),
        dbc.Tab(emissions_tab, label='Emissions'),
    ]
)

# Server
server = app.server


#############
# CALLBACKS #
#############
# Callback for select-deselect-all
@app.callback(
    Output("eng_source_checklist", "value"),
    Input("select-deselect-all", "n_clicks"),
    State("eng_source_checklist", "value")
)
def select_deselect_all(n_clicks, current_value):
    if n_clicks is None:
        return current_value
    return inv_energy_sources if len(current_value) != len(inv_energy_sources) else []

# Callback for updating figures
@app.callback(
    [Output('inv_costs_fig', 'figure'),
     Output('op_costs_fig', 'figure'),
     Output('total_emissions_fig', 'figure')],
    [Input('eng_source_checklist', 'value'),
     Input('year-slider', 'value'),
     Input('tot_emissions_limit', 'value')]
)
def update_figures_callback(selected_sources, selected_years, emissions_limit):
    return update_figures(df_inv_costs, df_op_costs, df_total_emissions, selected_sources, selected_years, emissions_limit)


########
# MAIN #
########

# Arrancamos el servidor
if __name__ == "__main__":
    app.run_server(debug=True)
