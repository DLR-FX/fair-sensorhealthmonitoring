import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load dataset into a pandas DataFrame
df = pd.read_csv('your_dataset.csv')

# Create a Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Two Time Series Plot'),
    dcc.Graph(id='time-series-graph')
])

# Define the callback function for the graph
@app.callback(
    Output('time-series-graph', 'figure'),
    [Input('time-series-graph', 'hoverData')]
)
def update_time_series(hoverData):
    # Check if hoverData is None or empty
    if not hoverData:
        series_name = 'Series 1'
    else:
        # Get the name of the series from hoverData
        series_name = hoverData['points'][0]['curveNumber']

    # Create the figure object
    fig = go.Figure()

    # Plot the first time series
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['series1'],
            mode='lines',
            name='Series 1',
            line=dict(width=2),
            hoverinfo='none'  # Hide hover info for this series
        )
    )

    # Plot the second time series
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['series2'],
            mode='lines',
            name='Series 2',
            line=dict(width=2),
            hovertemplate='%{x}<br>%{y}'  # Customize hover info for this series
        )
    )

    # Customize the layout of the figure
    fig.update_layout(
        title='Two Time Series Plot',
        xaxis_title='Timestamp',
        yaxis_title='Value',
        hovermode='x',  # Only show hover info for the x-axis
        legend=dict(
            title=None,
            orientation='h',
            y=1.1,
            yanchor='bottom',
            x=0.5,
            xanchor='center'
        )
    )

    # Highlight the selected series
    fig.data[series_name].line.color = 'red'

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
