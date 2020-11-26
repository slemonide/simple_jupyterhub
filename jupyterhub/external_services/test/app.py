from os import environ
import dash
import dash_html_components as html

from flask import Flask

server = Flask(__name__)
app = dash.Dash(
    server=server,
    url_base_pathname=environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')
)

app.layout = html.Div("Hello world.")

if __name__ == '__main__':
    app.run_server()
