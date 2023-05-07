import dash_renderjson
import plotly.express as px
from datetime import timedelta
from datetime import datetime as dt
from datetime import timezone
import pytz
import plotly.graph_objs as go
from dash import dash_table
from dash import dcc, html
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
from Parsing.parseFunctions import timestamp_from_utc, gen_dict_extract
from dateutil import parser


def update_timeline(sensors, sensor_times):
    tz = pytz.timezone('UTC')


    # use scid to fix up times
    # find all start and end times.
    parameters = []
    start_times = []
    stop_times = []
    for i in range(0, len(sensors)):
        parameters.append(sensors[i]["name"])
        start_times.append(dt.fromtimestamp(round(sensor_times[i]["statistics"]["min"], 2)))
        stop_times.append(dt.fromtimestamp(round(sensor_times[i]["statistics"]["max"], 2)))

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
                symbol=["arrow-bar-right", "arrow-bar-left"],
                size=16,
                line_color=["green", "red"],
                line_width=2
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
            symbol="arrow-bar-right",
            size=16,
            line_color="green",
            line_width=2,
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
            symbol="arrow-bar-left",
            size=16,
            line_color="red",
            line_width=2
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
        legend=dict(  # title_text='Start and Stop Times for Parameter Recording\t',
            yanchor="bottom", y=1.4,
            xanchor="left", x=0,
            orientation="h")
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
    children = []
    # try plotting errors (limit|amplitude) per minute over the whole flight

    # create scatter plot for each parameter on the time axis. plot out of limit as red. Out of amplitude as blue
    ssb = shm.get("single sensor behaviour")
    fig = go.Figure()

    parameter_errors = {}

    # plot each error
    for error in ssb.keys():
        # transform data into dictionary of times and entries of variables
        time_dict = {}
        for parameter, value in ssb[error].items():
            # this is inefficient af
            for time in list(value["occurences"].keys()):
                time_dict.setdefault(parser.parse(time), []).append(parameter)
            # also create a dictionary for n_errors
            # check if key is existent. if it is existent. add number of errors if not create and assign number of errors
            if parameter_errors.get(parameter) is None:
                parameter_errors[parameter] = len(value["occurences"].keys())
            else:
                parameter_errors[parameter] = parameter_errors[parameter] + len(value["occurences"].keys())

        """ # optimization strategy?
        inv_map = {}
        for k, v in ssb[error].items():
            inv_map[v] = inv_map.setdefault(list(v["occurences"].keys()), []).append(k)
        """
        # Get smallest and largest times
        start = min(time_dict.keys())
        end = max(time_dict.keys())
        delta = timedelta(seconds=1)
        # fill in empty values with 0.
        # Iterate over datetime range and fill in missing keys with empty lists
        while start <= end:
            if start not in time_dict:
                time_dict[start] = []
            start += delta

        # sort
        time_dict = {k: time_dict[k] for k in sorted(time_dict)}

        # isolate data for x-axis:time and y-axis
        fig.add_trace(go.Scatter(x=list(time_dict.keys()),
                                 y=[len(element) for element in time_dict.values()],
                                 mode="lines",
                                 text=["<br>".join(dot) for dot in list(time_dict.values())],
                                 name=error,
                                 showlegend=True
                                 ))
    # sort parameter errors
    parameter_errors = {k: parameter_errors[k] for k in
                        sorted(parameter_errors, key=lambda i: int(parameter_errors[i]))}

    if len(ssb) > 0:
        # add parameters to plot for represents=[height] on a second axis
        # represents["height"]

        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="Detected Errors")
        # get collective errors per second
        fig.update_layout(legend=dict(yanchor="bottom",
                                      xanchor="right"),
                          title="Errors over recording period")
        children.append(dcc.Graph(figure=fig,
                                  config=dict(responsive=True),
                                  style={"width": "60%", "height": "100%"},
                                  ))

        ## sensor ranking
        x_data = list(parameter_errors.values())
        y_data = list(parameter_errors.keys())
        # show logarithmic hbars for each sensor with cumulative error sorting. Show top 5 sensors only.
        bar = go.Bar(y=y_data,
                     x=x_data,
                     orientation='h',
                     text=y_data,
                     textposition="auto",
                     )

        right_graph = html.Div(children=[dcc.Graph(figure=go.Figure(data=bar,
                                                                    layout=go.Layout(title="Sensor Ranking by Faults",
                                                                                     xaxis_side='top',
                                                                                     xaxis_type="log",
                                                                                     yaxis={"tickvals": []},
                                                                                     height=len(y_data) * 50,
                                                                                     margin=dict(l=10, r=10),
                                                                                     dragmode=False,
                                                                                     )
                                                                    ),
                                                   config=dict(responsive=False, displayModeBar=False),
                                                   )
                                         ],
                               style={
                                   "width": "40%", "height": "30vh",
                                   "overflowY": "scroll"}
                               )
        children.append(right_graph)
    return children


def update_level3(shm, sensors, sensor_times):
    children = []

    # find sensors with shm
    shm3 = {}
    for sensor in sensors:
        if sensor["user_tags"].get("SHM") is not None:
            shm3.update({sensor["user_tags"]["Name"]: sensor["user_tags"]["SHM"]})

    # create dash columns for number of
    print("test")

    for component, comp_content in shm.get("level 3").items():
        # create children in x direction for windows description, graph, offset
        # descriptor 30%, graph 40%, offset 30%

        descriptor_table = dash_renderjson.DashRenderjson(id="input", data=comp_content["tags"], max_depth=-1)
        descriptor = html.Div(children=[descriptor_table], style=dict(width="30%"))

        #########
        # get comp_content["data"] and plot with +- checking range.

        x_data = [dt.fromtimestamp(timestamp, tz=timezone.utc) for timestamp in comp_content["data"][0]]
        y_data = comp_content["data"][1]
        fig = go.Figure(go.Scatter(x=x_data, y=y_data))

        graph = html.Div(children=[dcc.Graph(figure=fig,
                                             config=dict(responsive=True))],
                         style={"width": "39%"})

        ############
        # then get all parameters with according tags and calculate occurences per second

        offset = html.Div(style={"width": "30%"})
        # plot 1d all parameter offsets that are with the same tags
        component_box = html.Div(children=[descriptor, graph, offset],
                                 className="level3-box", #style={"display":"flex", "flex-direction":"column"}
                                 )
        children.append(component_box)

    return children
