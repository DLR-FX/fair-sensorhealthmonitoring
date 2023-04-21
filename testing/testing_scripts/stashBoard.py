# TODO: app to fetch stash projects of instance and display projects as well as flights
import pandas as pd
from dash import Dash, Input, Output, State, dcc, html, dash_table
import stashclient
from stashclient.client import Client
import plotly.graph_objects as go
import dash_daq as daq
import plotly.express as px
from readFunctions.readSensorInformation import read_istar_excel
import dash_bootstrap_components as dbc
from datetime import datetime
import pytz

# first: instance
instances = {"Production": "prod", "Development": "dev"}

# second: projects
client = Client.from_instance_name("prod")
projects = {project["id"]: project["name"] for project in client.search({"type": "project"})}
# third: flights
flights = {}

"""
# fourth: istar config excel
istar_config = read_istar_excel(r"D:\working_dir\Programmieren\laufende Projekte\sensorhealthmonitoring\readFunctions\AllParameters_ASCBD_V2.xlsx")
config_df = pd.DataFrame(index=istar_config.keys(), data=istar_config.values())
config_df = config_df[config_df['sheet'].notna()]
"""

app = Dash(__name__)
app.title = "stashboard: the stash's FTI dashboard"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children=[html.Img(src=app.get_asset_url("DigECat_stash.png"),
                                          style={'height': '10%', 'width': '10%'})],
                       className="header-emoji"),
                html.H1(
                    children="STASHBOARD", className="header-title",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(children=[
                    html.Div(children="instances", className="menu-title"),
                    dcc.Dropdown(
                        id="instance-drop",
                        options=[{"label": instance_key, "value": instance_value}
                                 for instance_key, instance_value in instances.items()],
                        value="dev",
                        clearable=False,
                        className="dropdown",
                    )
                ]),
                html.Div(children=[
                    html.Div(children="projects", className="menu-title"),
                    dcc.Dropdown(
                        id="project-drop",
                        options=[{"label": project_value, "value": project_key}
                                 for project_key, project_value in projects.items()],
                        className="dropdown",
                        clearable=False,
                    )
                ]),
                html.Div(children=[
                    html.Div(children="flights", className="menu-title"),
                    dcc.Dropdown(
                        id="flight-drop",
                        options=[{"label": value, "value": stash_id}
                                 for stash_id, value in flights.items()],
                        placeholder="Please select Project",
                        className="dropdown",
                    )
                ]),
            ],
            className="menu",
        ),
        html.Div([html.P("Timeline"),
                  dcc.Graph(
                      id='graph-timeline',
                  )
                  ],
                 id="div-timeline"
                 ),
        html.Div(
            children=[
                html.Div(children=[
                    html.P("Level 1"),
                    dcc.Graph(figure=px.pie(None), style={"width": "28vh", "height": "28vw"}, id="parameter-pie")
                ], id="level1",
                    className="level1"
                ),
                html.Div(children=[
                    html.P("Level 2"),
                    # dash_table.DataTable(id="level2-table")
                ],
                    className="level2",
                    id="level2"
                ),
                html.Div(children=[
                    html.P("level 3")
                ], id="level3", className="level3"),
            ],
            className="wrapper12",
            id="shm-div",
        )
    ],
)


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
        title='Start and Stop Times for Different Parameters',
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


@app.callback(
    Output("graph-timeline", "figure"),
    Output("parameter-pie", "figure"),
    Input("flight-drop", "value"),
    State("instance-drop", "value"),
)
def update_shm(flight_id, instance_name):
    client = Client.from_instance_name(instance_name)
    # pie = go.Figure(data=go.Pie(None))
    lvl1_pie = px.pie(None)
    timeline = {}
    if flight_id:
        shm = client.search({"id": flight_id})[0]["user_tags"].get("SHM")
        sensors = client.search({"parent": flight_id, "type": "series", "is_basis_series": False})
        sensor_times = client.search({"parent": flight_id, "type": "series", "is_basis_series": True})
        # transform sensor_times into dict of series connector id
        sensor_times_scid = {sensor["series_connector_id"]: sensor for sensor in sensor_times}
        sensor_times = [sensor_times_scid[sensor["series_connector_id"]] for sensor in sensors]

        # plot start and stop data by using x's. Green for start. Red for start. upon hovering show tooltip name
        timeline = update_timeline(sensors, sensor_times)

        if shm:
            sensors_missing = shm.get("Missing parameters")
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

            """
            dict_sensors = {element["name"]: "sensor present" for element in sensors}
            dict_sensors_missing = {element: "sensor missing" for element in shm.get("Missing parameters")}
            dict_sensors.update(dict_sensors_missing)
            sensor_df = pd.DataFrame(index=dict_sensors.keys(),
                                     data=dict_sensors.values())
            pie = px.pie(sensor_df, names=0, title="Missing parameters", color=0,
                         color_discrete_map={"sensor present": "green",
                                             "sensor missing": "red"})


            pie.update_traces(hoverinfo='label+percent', textinfo='value')
            """
            # and list missing sensors
            # level 2

        else:  # make shm disappear and show flight stats maybe?
            pass
    return timeline, lvl1_pie


@app.callback(
    Output("project-drop", "options"),
    Input("instance-drop", "value")
)
def update_projects(instance_name):
    client = Client.from_instance_name(instance_name)
    projects = {project["id"]: project["name"] for project in client.search({"type": "project"})}
    return projects


@app.callback(
    Output("flight-drop", "options"),
    Output("flight-drop", "placeholder"),
    Input("project-drop", "value"),
    State("instance-drop", "value")
)
def update_flights(project_id, instance_name):
    client = Client.from_instance_name(instance_name)
    flight_list = client.search({"type": "collection", "parent": project_id})
    flights = {flight["id"]: flight["name"] for flight in flight_list}
    return flights, "Select.."


if __name__ == "__main__":
    app.run_server(debug=True)
