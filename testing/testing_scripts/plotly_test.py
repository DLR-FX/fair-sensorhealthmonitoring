import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# Create a list of parameters
params = ['Temperature', 'Pressure', 'Humidity']

# Define start and stop times for each parameter
start_times = [0, 2, 4]
stop_times = [1, 3, 5]

# Create a list of scatter traces for each parameter
data = []
for i in range(len(params)):
    trace = go.Scatter(
        x=[start_times[i], stop_times[i]],
        y=[0,0],
        mode='markers',
        name=params[i],
        text=['Parameter: {}, Start time: {}, Stop time: {}'.format(params[i], start_times[i], stop_times[i])],
        marker=dict(
            color=['green', 'red'],
            size=10,
            line=dict(width=1, color='black')
        )
    )
    data.append(trace)

# Define layout
layout = go.Layout(
    title='Start and Stop Times for Different Parameters',
    xaxis=dict(title='Time'),
    yaxis=dict(title='Parameter')
)

# Create a figure
fig = go.Figure(data=data, layout=layout)

# Create the Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div(children=[
    html.H1(children='Start and Stop Times for Different Parameters'),

    dcc.Graph(
        id='start-stop-times-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
