# -*- coding: utf-8 -*-

# Run this app with `python app3.py` and
# visit http://127.0.0.1:8050/ in your web browser.
# documentation at https://dash.plotly.com/ 

# based on app3.py and ideas at "Dash App With Multiple Inputs" in https://dash.plotly.com/basic-callbacks
# plotly express line parameters via https://plotly.com/python-api-reference/generated/plotly.express.line.html#plotly.express.line
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import numpy as np
from numpy import random
import math #needed for definition of pi
from os import environ
from flask import Flask

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = Flask(__name__)
app = dash.Dash(
    server=server,
    url_base_pathname=environ.get('JUPYTERHUB_SERVICE_PREFIX', '/'),
    external_stylesheets=external_stylesheets
)

app.layout = html.Div([
    dcc.Markdown('''
### Noisy sine wave on a linear trend

#### Purpose

Demonstrate a synthetic signal consisting of _data + random noise + a linear trend_. Also show effect of smoothing the noisy signal. Signal is sine wave with adjustable samples/cycle and smoothing is an adjustable N-pt moving avg. (i.e. a N-pt boxcar convolution). Sine wave is plotted as points while smoothed is plotted as lines.

#### Instructions

Explore the dashboard and its controls. Note that figure-viewing controls in the figure's top-right corner only appear when your mouse is within the figure. 

----------
'''),

# slider details at https://dash.plotly.com/dash-core-components/slider 
    html.Div([
        dcc.Markdown('''
        **Select signal components**
        '''),
        dcc.Checklist(
            id='Sigs',
            options=[
                {'label': 'SineWave', 'value': 'sine'},
                {'label': 'Noise', 'value': 'noise'},
                {'label': 'Trend', 'value': 'trend'},                
            ],
            value=['sine', 'noise']
        ),
        dcc.Markdown('''
        **Check to show smoothed**
        '''),
        dcc.Checklist(
            id='Smooth_on',
            options=[
                {'label': 'Smoothed', 'value': 'smooth'}
            ],
            value=[]
        )
    ], style={'width': '48%', 'display': 'inline-block'}),

    html.Div([
        # html.P('Set signal parameters'),
        dcc.Markdown(''' _No. cycles:_ '''),
        dcc.Slider(id='ncycles', min=2, max=10, value=3, step=0.5,
            marks={2:'2', 4:'4', 6:'6', 8:'8', 10:'10'}
            # tooltip={'always_visible':True, 'placement':'topLeft'}
        ),
        dcc.Markdown(''' _Noise level:_ '''),
        dcc.Slider(id='noiselevel', min=0.0, max=5.0, value=1.0, step=0.25,
            marks={0:'0', 1:'1', 2:'2', 3:'3', 4:'4', 5:'5'}
            # tooltip={'always_visible':True, 'placement':'topLeft'}
        ),
        dcc.Markdown(''' _N-pt smoothing:_ '''),
        dcc.Slider(id='smoothwin', min=1.0, max=15.0, value=5.0, step=2.0,
            marks={1:'1', 3:'3', 5:'5', 7:'7', 9:'9', 11:'11', 13:'13', 15:'15'}
        )
    ], style={'width': '48%', 'display': 'inline-block'}
    ),

    dcc.Graph(id='indicator-graphic'),

    dcc.Markdown('''
        ----
        
        ### Questions students could consider

        These are examples of questions to drive teaching discussions or learning assignments. Questions are not necessarily well-posed. Also, most are judgement calls - which is part of the point!
        
        1. How much noise does it take to obscure the fact that the signal is a nice sinewave?
        2. "Smoothing" is a simple "boxcar", or 5-point moving average. How much MORE noise can be managed before the smoothed signal begins to loose its useful character?
        3. If there are only 2 or 3 cycles of signal, can you tell there is a trend? What are the implications for the "length" of your data set or series of measurements? 
        4. Does noise obscure the fact that there is a superimposed linear trend? 
        5. How much data (i.e. how long do you have to take measurments) before the trend is observed? 
        6. Does this necessary length for measuring the phenomenon vary if there is more noise? 
        7. Pose your own question AND answer it.  
        ''')
], style={'width': '900px'}
)

def moving_avg(x, w):
    y = np.convolve(x, np.ones(w), 'valid') / w
    
    # applying "roll" is necessary so the timeseries are aligned over the correct x-axis values. 
    # this is probably easier using data frames when x-axis will be the index frame.
    z = np.roll(y, int(w/2))
    
    # roll wraps end points back to first points, so set these to zero; a cludge, but works for now.
    wrap = int((w)/2)
    z[:wrap] = 0
    return z

#@app.callback(
#    Output('indicator-graphic', 'figure'),
#    Input('ncycles', 'value'),
#    Input('noiselevel', 'value'),
#    Input('smoothwin', 'value'),
#    Input('Sigs', 'value'),
#    Input('Smooth_on', 'value')  
#    )    
def update_graph(ncycles, noiselevel, smoothwin, Sigs, Smooth_on):
    # make a noisy sine wave on a linear trend
    # build the X-axis first, then the three time series: 
    xpoints = np.arange(0, ncycles, 0.05)
    N=len(xpoints)   # this may not be the most sophisticated approach 
    ypoints = np.sin(xpoints*2*math.pi)
    randpoints = noiselevel * (random.rand(N)-.5)
    trendpoints = 0.4*xpoints + 0.5

    if Sigs == ['sine']:
         sumpoints = ypoints
    elif Sigs == ['noise']:
        sumpoints = randpoints
    elif Sigs == ['trend']:
        sumpoints = trendpoints
    elif Sigs == ['sine', 'noise']:
         sumpoints = ypoints + randpoints
    elif Sigs == ['sine', 'trend']:
         sumpoints = ypoints + trendpoints
    elif Sigs == ['trend', 'noise']:
         sumpoints = trendpoints + randpoints
    else:
        sumpoints = ypoints + randpoints + trendpoints

    if Smooth_on == ['smooth']:
        smoothpoints = moving_avg(sumpoints,smoothwin)
    else:
        smoothpoints = []

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xpoints, y=sumpoints,
                    mode='lines',
                    name='signal'))
    fig.add_trace(go.Scatter(x=xpoints, y=smoothpoints,
                    mode='lines',
                    name='smoothed'))

    fig.update_layout(xaxis_title='Time', yaxis_title='Value')
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[-2, 7])

#    fig = px.line(x=xpoints, y=sumpoints, labels={'x':'t', 'y':'sin(t)'}, range_x=(0,10), range_y=(-2,7))

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
