from dash import Dash, Input, Output, State
from stashclient.client import Client
import plotly.express as px
from readFunctions.readSensorInformation import read_istar_excel
import dash_bootstrap_components as dbc
from datetime import datetime
import pytz
import plotly.graph_objs as go
from dash import dash_table
from testing.testing_scripts.stashboard_layout import get_layout
from testing.testing_scripts.stashboard_functions import update_timeline, update_level2, update_level_1

# first: instance
instances = {"Production": "prod", "Development": "dev"}
# second: projects
client = Client.from_instance_name("prod")
projects = {project["id"]: project["name"] for project in client.search({"type": "project"})}
# third: flights
flights = {}

app = Dash(__name__)
app.title = "stashboard: the stash's FTI dashboard"
app.layout = get_layout(app)


@app.callback(
    Output("graph-timeline", "figure"),
    Output("level1", "children"),
    Output("level2", "children"),
    Input("flight-drop", "value"),
    State("instance-drop", "value"),
)
def update_shm(flight_id, instance_name):
    client = Client.from_instance_name(instance_name)
    lvl1_html = {}
    timeline = {}
    lvl2_html = {}
    if flight_id:
        shm = client.search({"id": flight_id})[0]["user_tags"].get("SHM")

        sensors = client.search({"parent": flight_id, "type": "series", "is_basis_series": False})
        sensor_times = client.search({"parent": flight_id, "type": "series", "is_basis_series": True})
        if len(sensors) > len(sensor_times):
            # transform sensor_times into dict of series connector id
            sensor_times_scid = {sensor["series_connector_id"]: sensor for sensor in sensor_times}
            sensor_times = [sensor_times_scid[sensor["series_connector_id"]] for sensor in sensors]

        # plot start and stop data by using x's. Green for start. Red for stop. upon hovering show tooltip name
        timeline = update_timeline(sensors, sensor_times)

        if shm:
            lvl1_html = update_level_1(shm, sensors)
            # and list missing sensors
            # level 2
            lvl2_html = update_level2(shm, sensors, sensor_times)

        else:  # make shm disappear and show flight stats maybe?
            pass
    return timeline, lvl1_html, lvl2_html


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
