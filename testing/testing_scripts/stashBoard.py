# TODO: app to fetch stash projects of instance and display projects as well as flights
from dash import Dash, Input, Output, State, dcc, html
from stashclient.client import Client
import plotly.express as px

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
        html.Div(
            children=[
                html.Div(children=[
                    html.Div(children=[
                        html.P("Level 1"),
                        dcc.Graph(figure=px.pie(None),
                                  id="parameter-pie")
                    ], id="level1", className="wrapper"),

                    html.Div(children=[
                        html.P("Level 2"),
                        #dash_table.DataTable(id="level2-table")
                    ], id="level2", className="card")
                ],
                    id="level1,2",
                    className="level12"
                ),
                html.Div(children=[], id="level3", className="card"),
            ],
            style={'display': 'flex', 'flex-direction': 'row'},
            #id="shm-div",
        )
    ],
)


@app.callback(
    Output("parameter-pie", "figure"),
    Input("flight-drop", "value"),
    State("instance-drop", "value"),
)
def update_shm(flight_id, instance_name):
    client = Client.from_instance_name(instance_name)
    # pie = go.Figure(data=go.Pie(None))
    fig = px.pie(None)
    if flight_id:
        shm = client.search({"id": flight_id})[0]["user_tags"].get("SHM")
        sensors = client.search({"parent": flight_id, "type": "series", "is_basis_series": False})
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

            fig = px.sunburst(
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
    return fig


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
