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
import dash_bootstrap_components as dbc


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
                               annotations=[{"text": "show",
                                             "hovertext": missing_string,
                                             "showarrow": False,
                                             "align": "left",
                                             "height": 1000}],
                               margin=dict(l=40, r=40),
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
    # create scatter plot for each parameter on the time axis. plot out of limit as red. Out of amplitude as blue
    ssb = shm.get("single sensor behaviour")
    fig = go.Figure()

    parameter_errors = {}
    # plot each error
    for error in ssb.keys():
        if len(ssb[error]) > 0 :
            time_dict = get_error_occurence_sum(ssb[error])

            for parameter, value in ssb[error].items():
                # create a dictionary counting the number of errors per parameter over all error types
                # check if key is existent. if it is existent. add number of errors if not create and assign number of errors
                if parameter_errors.get(parameter) is None:
                    parameter_errors[parameter] = len(value["occurences"].keys())
                else:
                    parameter_errors[parameter] = parameter_errors[parameter] + len(value["occurences"].keys())

            # isolate data for x-axis:time and y-axis
            fig.add_trace(go.Scatter(x=list(time_dict.keys()),
                                     y=[len(element) for element in time_dict.values()],
                                     mode="lines",
                                     text=["<br>".join(dot) for dot in list(time_dict.values())],
                                     name=error,
                                     showlegend=True,
                                     opacity=0.7,
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
                     #text=y_data, # not necessary since it is already shown. Possible to define additional data here later
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

    # create dash columns for number of parameters
    for component, comp_content in shm.get("level 3").items():
        # create children in x direction for windows description, graph, offset
        # descriptor 30%, graph 40%, offset 30%
        # ignore properties attribute
        edges = get_edge_lists({k: v for k, v in comp_content.items() if k not in ["properties"]}, component)
        # wrap edge names at 25 characters using the underscore _ as natural separator
        for n, edge in enumerate(edges[1]):
            edges[1][n] = fold_string(edge, 25, "_", "<br>")

        treefig = go.Figure(data=go.Treemap(
            parents=edges[0],
            labels=edges[1],
        ), layout=go.Layout(margin=dict(l=10, r=10), ))
        descriptor = html.Div(children=[dcc.Graph(figure=treefig, config=dict(responsive=True))],
                              style={"width": "25%", "height": "100%"})
        #########
        # get comp_content["data"] and plot with +- checking range.
        x_data = [dt.fromtimestamp(timestamp, tz=timezone.utc) for timestamp in comp_content["properties"]["data"][0]]
        y_data = comp_content["properties"]["data"][1]
        y_upper = [value + float(comp_content["properties"]["checking_range"]) for value in y_data]
        y_lower = [value - float(comp_content["properties"]["checking_range"]) for value in y_data]

        fig = go.Figure(data=go.Scatter(
            x=x_data + x_data[::-1],
            y=y_upper + y_lower[::-1],
            fill='toself',
            fillcolor='#B5B0FF',
            line_color='rgba(255,255,255,0)',
            showlegend=False,
            name='Ideal',
            yaxis="y1",
        ))

        fig.add_trace(go.Scatter(
            x=x_data, y=y_data,
            line_color='#3024FF',
            name=component + " +- allowed deviation",
            yaxis="y1",
        ))
        # add trace for error occurences.
        # get parameter for component
        parameter_list = [parameter for tag in comp_content["properties"]["tags"].keys()
                          for parameter in comp_content["properties"]["tags"][tag]]
        # get error dictionary based on the component-parameter_list
        error_dict = {key: {"occurences": value["suspicious values"]} for key, value in shm3.items() if
                      key in parameter_list}
        # transpose error list into dict of time
        time_dict = get_error_occurence_sum(error_dict)
        # isolate data for x-axis:time and y-axis
        fig.add_trace(go.Scatter(
            x=list(time_dict.keys()),
            y=[len(element) for element in time_dict.values()],
            line_color="orange",
            mode="lines",
            text=["<br>".join(dot) for dot in list(time_dict.values())],
            name="number errors",
            showlegend=True,
            yaxis="y2",
            opacity=0.5,
        ))

        fig.update_layout(
            # title='',
            hovermode='closest',
            xaxis=dict(
                domain=[0.3, 1]
            ),
            yaxis=dict(title=component),
            yaxis2=dict(title='number errors',
                        titlefont=dict(color="orange"),
                        tickfont=dict(color="orange"),
                        anchor="free",
                        overlaying='y',
                        side='left',
                        position=0.15,
                        rangemode="tozero",
                        autorange=True,
                        ),
            # plot_bgcolor='white',
            legend=dict(yanchor="bottom",
                        xanchor="right",
                        ))

        graph = html.Div(children=[dcc.Graph(figure=fig,
                                             config=dict(responsive=True))],
                         style={"width": "65%", "height": "100%"})
        ############
        # then get all parameters with according tags and calculate occurences per second
        # TODO: plot offset in percentage of allowed deviation.
        # TODO: find way to remark NONe/nan values

        traces = []
        for parameter, value in shm3.items():
            if parameter in parameter_list:
                parameter = fold_string(parameter, 25, "_", "<br>")
                traces.append(go.Scatter(
                    x=[0],
                    y=[float(value["offset"])],
                    text=parameter,
                    name=parameter,
                    # line_color="white",
                    marker=dict(
                        symbol=["line-ew-open"],
                        size=16,
                        # line_color=["blue"],
                        line_width=2
                    ),
                ))

        layout = go.Layout(
            # title='Start and Stop Times for Parameter Recording',
            yaxis=dict(title='Offset', showgrid=False),
            xaxis=dict(showgrid=False,
                       zeroline=True, zerolinecolor='black', zerolinewidth=3,
                       showticklabels=False),
            hovermode='closest',
            plot_bgcolor='white',
            showlegend=False,
            # legend=dict(  # title_text='Start and Stop Times for Parameter Recording\t',
            # yanchor="bottom", #y=1.4,
            # xanchor="left", #x=0,
            # orientation="h"
            # )
        )

        offset = html.Div(children=[
            dcc.Graph(
                figure=go.Figure(data=traces, layout=layout),
                config=dict(responsive=True),
            )],
            style={"width": "10%", "height": "100%"})

        ### plot 1d all parameter offsets that are with the same tags
        component_box = html.Div([html.Div(children=[descriptor, graph, offset],
                                           style={"display": "flex",
                                                  "flex-direction": "row",
                                                  "width": "100%",
                                                  }
                                           )], style=dict(padding="10px 0px"))
        children.append(component_box)

    return children


def fold_string(string, max_line_length=25, separator=" ", linebreak="\n"):
    """
    this is a function for generating a folded line based on the maximum allowed line length and splits the string before the line is exceeded.

    a separator can be given to indicate the string separators.
    :param string:
    :type string:
    :param max_line_length:
    :type max_line_length:
    :param separator:
    :type separator:
    :return:
    :rtype:
    """

    # check if string is longer than linebreak
    if len(string) > max_line_length:
        chunks = string.split(separator)
        new_string = ""
        char_counter = 0
        for n, chunk in enumerate(chunks):
            # check if adding strings would be greater than line length
            if char_counter + len(chunk) > max_line_length:
                # add linebreak and then add
                new_string += linebreak + chunk
                char_counter = len(linebreak + chunk)
            else:
                if n > 0:
                    string_addon = separator + chunk
                else:
                    string_addon = chunk
                new_string += string_addon
                char_counter += len(string_addon)
    else:
        new_string = string
    return new_string


def get_edge_lists(d, m="root"):
    edges = get_edges(d, m)
    # transpose nested lists
    edges_tp = list(map(lambda *x: list(x), *edges))
    return edges_tp


def get_edges(d, m="root"):
    """
    :param d: system description: hierarchical data dict, no lists allowed. Allows processing of str
    :type d: dictionary
    :param m: name of the root parameter
    :type m: str
    :return: list linking parameters for treemap usage
    :rtype: list of lists
    """
    edges = []
    for key, value in d.items():
        edges.append([m, key])
        if type(value) is dict:
            edges.extend(get_edges(value, key))
        elif type(value) is str:
            edges.append([key, value])
        else:
            print("Invalid data type in " + key)
    return edges


def get_error_occurence_sum(error_dict):
    """
    get sensors and their error occurences by time and permute into a dictionary of times

    :param error_dict: sensor(time(value))
    :type error_dict: dict(dict(str))
    :return: time(parameters)
    :rtype: dict(list)
    """
    time_dict = {}

    # transform data into dictionary of times and entries of variables
    for parameter, value in error_dict.items():
        # this is inefficient af
        for time in list(value["occurences"].keys()):
            time_dict.setdefault(parser.parse(time), []).append(parameter)

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
    return time_dict
