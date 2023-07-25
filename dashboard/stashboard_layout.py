from dash import dcc, html
from stashclient.client import Client


def get_layout(app):
    # first: instance
    instances = {"Production": "prod", "Development": "dev"}
    # second: projects
    client = Client.from_instance_name("prod")
    projects = {project["id"]: project["name"] for project in client.search({"type": "project"})}
    # third: flights
    flights = {}

    layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.P(children=[html.Img(src=app.get_asset_url("DigECat_stash.png"),
                                              style={'height': '10%', 'width': '10%'})],
                           className="header-emoji"),
                    html.H1(children="STASHBOARD", className="header-title"),
                ],
                className="header",
            ),
            html.Div(
                children=[
                    html.Div(children=[
                        html.Div(children="instance", className="menu-title"),
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
                        html.Div(children="project", className="menu-title"),
                        dcc.Dropdown(
                            id="project-drop",
                            options=[{"label": project_value, "value": project_key}
                                     for project_key, project_value in projects.items()],
                            className="dropdown",
                            clearable=False,
                        )
                    ]),
                    html.Div(children=[
                        html.Div(children="flight", className="menu-title"),
                        dcc.Dropdown(
                            id="flight-drop",
                            options=[{"label": value, "value": stash_id}
                                     for stash_id, value in flights.items()],
                            placeholder="Please select Project",
                            className="dropdown",
                        )
                    ]),
                    html.A(id="stash-link", children="View in skystash", hidden=True, target="_blank")
                ],
                className="menu",
            ),
            html.Div([
                      dcc.Graph(style={"height": "200px"},
                                id='graph-timeline'),
                      ],
                     id="div-timeline",
                     className="timeline"
                     ),
            html.Div(
                children=[
                    html.Div(children=[
                        html.P("Level 1"),
                    ],
                        id="level1",
                        className="level1"
                    ),
                    html.Div(children=[
                        html.P("Level 2"),
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

    return layout
