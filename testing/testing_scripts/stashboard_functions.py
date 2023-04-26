import plotly.express as px
from datetime import datetime
import pytz
import plotly.graph_objs as go
from dash import dash_table
from dash import dcc, html
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
from Parsing.parseFunctions import timestamp_from_utc
from dateutil import parser


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

    # create dummy traces for legend
    trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        name="Start",
        marker=dict(
            color=['green'],
            symbol="x",
            size=8,
        ),
        showlegend=True
    )
    data.append(trace)
    trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        name="Stop",
        marker=dict(
            color=['red'],
            symbol="x",
            size=8,
        ),
        showlegend=True
    )
    data.append(trace)

    # Define layout
    layout = go.Layout(
        title='Start and Stop Times for Parameter Recording',
        xaxis=dict(title='Time', showgrid=False),
        yaxis=dict(showgrid=False,
                   zeroline=True, zerolinecolor='black', zerolinewidth=3,
                   showticklabels=False),
        hovermode='closest',
        height=200,
        plot_bgcolor='white',
        legend=dict(yanchor="bottom", y=1.2,
                    xanchor="right", x=0.99)
    )

    # Create a figure
    figure = go.Figure(data=data, layout=layout)

    return figure


def update_level_1(shm, sensors):
    children = []
    # children = [html.P("Level 1")]

    sensors_missing = shm.get("missing parameters")
    speedo = level1_speedo(sensors_missing, sensors)
    children.append(speedo)
    return children


def level1_speedo(missing_sensors, present_sensors):
    working = len(present_sensors)
    missing_string = "<br>".join(missing_sensors)
    param_min = 0
    param_max = len(present_sensors) + len(missing_sensors)
    param_1std = int((param_max - param_min) * 0.68 + param_min)
    param_2std = int((param_max - param_min) * 0.95 + param_min)
    figure = dcc.Graph(id="speedometer",
                       config=dict(displayModeBar=False, responsive=True),
                       style={"width": "100%", "height": "100%"},
                       figure=go.Figure(
                           layout=go.Layout(
                               title={"text": "Parameter Availability"},
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
                                   'axis': {'range': [param_min, param_max],
                                            # 'tickvals': [ent_min, ent_tick_60, ent_tick_90, ent_max]
                                            },
                                   'steps': [
                                       {'range': [param_min, param_1std], 'color': "red"},
                                       {'range': [param_1std, param_2std], 'color': "yellow"},
                                   ],
                               },
                               number={'suffix': "/" + str(param_max)},
                           )
                       )
                       )
    return figure


def update_level2(shm, sensors, times):
    # try plotting errors (limit|amplitude) per minute over the whole flight

    # create scatter plot for each parameter on the time axis. plot out of limit as red. Out of amplitude as blue
    ssb = shm.get("single sensor behaviour")
    fig = go.Figure()

    # plot each error
    for error in ssb.keys():
        # transform data into dictionary of times and entries of variables
        time_dict = {}
        for parameter, value in ssb[error].items():
            # this is inefficient af
            for time in list(value["occurences"].keys()):
                time_dict.setdefault(parser.parse(time), []).append(parameter)
        """ # optimization strategy?
        inv_map = {}
        for k, v in ssb[error].items():
            inv_map[v] = inv_map.setdefault(list(v["occurences"].keys()), []).append(k)
        """

        # sort
        time_dict = {k: time_dict[k] for k in sorted(time_dict)}

        # fill in empty values with 0.

        # isolate data for x-axis:time and y-axis
        fig.add_trace(go.Scatter(x=list(time_dict.keys()),
                                 y=[len(element) for element in time_dict.values()],
                                 mode="lines",
                                 text=["<br>".join(dot) for dot in list(time_dict.values())],
                                 name=error,
                                 showlegend=True))

    # add parameters to plot for represents=[height] on a second axis
    # represents["height"]

    # Define layout
    layout = go.Layout(
        title='Parameter Errors',
        xaxis=dict(title='Time'),
        yaxis=dict(title="Detected Errors"),
    )
    fig.update_layout(layout)
    # get collective errors per second
    # show logarithmic hbars for each sensor with cumulative error sorting. Show top 5 sensors only.

    figure = dcc.Graph(figure=fig,
                       config=dict(responsive=True),
                       style={"maxWidth": "100%", "maxHeight": "100%"},
                       )

    return figure


def update_level3(shm, sensors, sensor_times):
    # find sensors with shm
    shm3 = {}
    for sensor in sensors:
        if sensor["user_tags"].get("SHM") is not None:
            shm3.update({sensor["user_tags"]["Name"]:sensor["user_tags"]["SHM"]})

    pass
