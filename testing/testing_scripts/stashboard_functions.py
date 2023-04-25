import plotly.express as px
from datetime import datetime
import pytz
import plotly.graph_objs as go
from dash import dash_table
from dash import dcc, html
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np


def update_timeline(sensors, sensor_times):
    tz = pytz.timezone('UTC')

    # find all start and end times.
    parameters = []
    start_times = []
    stop_times = []
    for i in range(0, len(sensors)):
        parameters.append(sensors[i]["name"])
        start_times.append(datetime.fromtimestamp(round(sensor_times[i]["statistics"]["min"], 2)))
        stop_times.append(datetime.fromtimestamp(round(sensor_times[i]["statistics"]["max"], 2)))

    # Create a list of scatter traces for each parameter
    data = []
    for i in range(len(parameters)):
        # generate string that gets shown on hover. index is :-4 to exclude irrelevant decimal places
        tooltip_string = 'Parameter: {}, <br> Start time: {}, Stop time: {}'.format(
            parameters[i],
            start_times[i].strftime("%H:%M:%S.%f")[:-4],
            stop_times[i].strftime("%H:%M:%S.%f")[:-4])

        trace = go.Scatter(
            x=[start_times[i], stop_times[i]],
            y=[0, 0],
            mode='markers',
            name=parameters[i],
            text=[tooltip_string, tooltip_string],  # display for both values
            marker=dict(
                color=['green', 'red'],
                symbol="x",
                size=8,
            ),
            showlegend=False
        )
        data.append(trace)

    # Define layout
    layout = go.Layout(
        title='Start and Stop Times for different Parameters',
        xaxis=dict(title='Time', showgrid=False),
        yaxis=dict(showgrid=False,
                   zeroline=True, zerolinecolor='black', zerolinewidth=3,
                   showticklabels=False),
        hovermode='closest',
        height=200,
        plot_bgcolor='white'
    )

    # Create a figure
    figure = go.Figure(data=data, layout=layout)

    return figure


def update_level_1(shm, sensors):
    children = []
    # children = [html.P("Level 1")]

    sensors_missing = shm.get("missing parameters")

    """
    # total number of sensors
    data = dict(
        character=["Sensors Missing", "Sensors Present"],
        parent=["", ""],
        value=[len(sensors_missing), len(sensors)])
    for element in sensors_missing:
        data["character"].append(element)
        data["parent"].append("Sensors Missing")
        data["value"].append(1)

    lvl1_pie = px.sunburst(
        data,
        names='character',
        parents='parent',
        values='value',
    )

    dict_sensors = {element["name"]: "sensor present" for element in sensors}
    dict_sensors_missing = {element: "sensor missing" for element in shm.get("missing parameters")}
    dict_sensors.update(dict_sensors_missing)
    sensor_df = pd.DataFrame(index=dict_sensors.keys(),
                             data=dict_sensors.values())
    pie = px.pie(sensor_df, names=0, title="missing parameters", color=0,
                 color_discrete_map={"sensor present": "green",
                                     "sensor missing": "red"})

    pie.update_traces(hoverinfo='label+percent', textinfo='value')
    # Define the list data as a dictionary of lists

    ratio = "Parameters available: " + str(len(sensors)) + "/" + str(len(sensors) + len(sensors_missing))
    #children.append(html.P(ratio))
    data = {
        'Item': ['Item 1', 'Item 2', 'Item 3'],
        'Description': ['Description 1', 'Description 2', 'Description 3'],
        'Quantity': [10, 20, 30]
    }

    # Display the list as a table
    table = dash_table.DataTable(
        columns=[{'name': col, 'id': col} for col in data.keys()],
        data=data,
        sort_action='native',
        filter_action='native',
        page_size=10
    )
    # program the pie or something here
    figure = {}
    """
    speedo = level1_speedo(sensors_missing, sensors)
    children.append(speedo)
    return children


def level1_speedo(missing_sensors, present_sensors):
    working = len(present_sensors)
    missing_string = "<br>".join(missing_sensors)
    ent_min = 0
    ent_max = len(present_sensors) + len(missing_sensors)
    ent_tick_60 = int((ent_max - ent_min) * 0.6 + ent_min)
    ent_tick_90 = int((ent_max - ent_min) * 0.9 + ent_min)
    figure = dcc.Graph(id="speedometer",
                       config=dict(displayModeBar=False, responsive=True),
                       style={"width": "100%", "height": "100%"},

                       figure=go.Figure(
                           layout=go.Layout(
                               title={"text": "Parameter Status"},
                               annotations=[{"text": "             ",
                                             "hovertext": missing_string,
                                             "showarrow": False,
                                             "align": "left",
                                             "height": 1000}]
                           ),
                           data=go.Indicator(
                               mode="gauge+number",
                               value=working,
                               gauge={
                                   'axis': {'range': [ent_min, ent_max],
                                            'tickvals': [ent_min, ent_tick_60, ent_tick_90, ent_max]},
                                   'steps': [
                                       {'range': [ent_min, ent_tick_60], 'color': "red"},
                                       {'range': [ent_tick_60, ent_tick_90], 'color': "yellow"},
                                       # {'range': [ent_tick_90, ent_max], 'color': "green"}
                                   ],
                                   # 'threshold': {
                                   #    'line': {'color': "black", 'width': 4},
                                   #    'thickness': 0.75,
                                   #    'value': working
                                   # },
                                   # 'bar': {'color': "grey"}
                               },
                               number={'suffix': "/" + str(ent_max)},
                           )
                       )
                       )

    return figure


def update_level2(shm, sensors, times):
    # try plotting errors (limit|amplitude) per minute over the whole flight


    # create scatter plot for each parameter on the time axis. plot out of limit as red. Out of amplitude as blue
    ssb = shm.get("single sensor behaviour")
    fig = go.Figure()
    for error in ssb.keys():
        # isolate data for x-axis:time and y-axis
        fig.add_trace(go.Scatter(x=1, y=0, mode="lines", name=error))





    error_types = list(ssb.keys())

    # get collective errors per second

    #plot per single sensor behaviour. then collect amount of key entries

    # collect params
    params = []
    for error in error_types:
        params.extend(list(ssb[error].keys()))
    # delete duplicates
    params = list(dict.fromkeys(params))

    # Create a figure object with subplots
    fig = make_subplots(rows=len(params), cols=2, shared_xaxes=True)

    # Loop through each parameter and plot the timeline and accumulated errors
    for i, param in enumerate(params):
        for error in error_types:
            if ssb[error].get(param) is not None:
                occurence_dict = ssb[error][param]["occurences"]
                # Plot the timeline of parameter values
                fig.add_trace(
                    go.Scatter(
                        x=list(occurence_dict.keys()),
                        y=[i] * len(params),
                        mode='markers',
                        name=param,
                        marker=dict(size=10, color='black'),
                        showlegend=False
                    ),
                    row=i + 1,
                    col=1,
                )
                # create indicator for scalar number of errors in right subplot
                """
                # Plot the accumulated number of errors
                fig.add_trace(
                    go.Scatter(
                        x=list(occurence_dict.keys()),
                        y=np.cumsum(list(occurence_dict.keys())),
                        mode='lines',
                        name='Cumulative Errors',
                        line=dict(width=2)
                    ),
                    row=i + 1,
                    col=2
                )
                """

        # Add y-axis label for the timeline subplot
        fig.update_yaxes(
            title_text=param,
            row=i + 1,
            col=1
        )

    # Add x-axis label and title for the entire figure
    fig.update_xaxes(title_text='Timestamp', row=len(params), col=1)
    fig.update_layout(title='Timeline of Parameters and Accumulated Errors')

    figure = dcc.Graph(figure=fig,
                       config=dict(responsive=True),
                       style={"maxWidth": "100%", "maxHeight": "100%"},
                       )

    return figure
