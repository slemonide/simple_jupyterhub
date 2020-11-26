from os import environ
from argparse import ArgumentParser
from dash import Dash
import dash_html_components as tag

parser = ArgumentParser()
parser.add_argument('-p', '--port', default=10104)
args = parser.parse_args()

app = Dash(
    __name__,
    url_base_pathname=environ.get('JUPYTERHUB_SERVICE_PREFIX', '/')
)
app.layout = tag.Div('Hello, World!')

if __name__ == '__main__':
    app.run_server(port=args.port)
