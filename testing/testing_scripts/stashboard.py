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
from testing.testing_scripts.stashboard_functions import update_timeline, update_level2, update_level_1, update_level3

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
    Output("level3", "children"),
    Output("stash-link", "hidden"),
    Input("flight-drop", "value"),
    Input("instance-drop", "value"),
)
def update_shm(flight_id, instance_name):
    client = Client.from_instance_name(instance_name)
    timeline = {}
    lvl1_html = {}
    lvl2_html = {}
    lvl3_html = {}
    link_disabled = True
    if flight_id:
        link_disabled = False
        shm = client.search({"id": flight_id})[0]["user_tags"].get("SHM")

        sensors = client.search({"parent": flight_id, "type": "series", "is_basis_series": False})
        sensor_times = client.search({"parent": flight_id, "type": "series", "is_basis_series": True})
        # transform sensor_times into dict of series connector id
        sensor_times_scid = {sensor["series_connector_id"]: sensor for sensor in sensor_times}
        sensor_times = [sensor_times_scid[sensor["series_connector_id"]] for sensor in sensors]

        # plot start and stop data by using x's. Green for start. Red for stop. upon hovering show tooltip name
        timeline = update_timeline(sensors, sensor_times)

        if shm:
            # and list missing sensors
            if shm.get("missing parameters") is not None:
                lvl1_html = update_level_1(shm, sensors)
            # level 2
            if shm.get("single sensor behaviour") is not None:
                lvl2_html = update_level2(shm, sensors, sensor_times)
            lvl3_html = update_level3(shm, sensors, sensor_times)
        else:  # make shm disappear and show flight stats maybe?
            pass
    return timeline, lvl1_html, lvl2_html, lvl3_html, link_disabled


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


@app.callback(
    Output("stash-link", "href"),
    Input("stash-link", "hidden"),
    State("instance-drop", "value"),
    State("project-drop", "value"),
    State("flight-drop", "value"),
)
def update_link(hidden, instance, project_id, flight_id):
    flightlink = ""
    if instance is not None and project_id is not None and flight_id is not None:
        flightlink = r"https://" + instance + r".stash.dlr.de/projects/" + project_id + r"/collections/" + flight_id
    return flightlink


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
