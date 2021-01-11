"""A simple launcher service that launches containers for users using a
project description from project.yaml file

This serves `/services/launcher/`, authenticated with the Hub.
"""
import json
import os
import sys
from urllib.parse import urlparse

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.web import authenticated
from tornado.web import RequestHandler

import tornado.escape

from jupyterhub.services.auth import HubAuthenticated

import yaml # to read config
import requests # to make requests to Hub API

class LauncherProjectsPageHandler(HubAuthenticated, RequestHandler):
    def initialize(self, projects):
        self.projects = projects

    @authenticated
    def get(self):
        user_model = self.get_current_user()

        self.render("projects_page.html",
            title = "Projects Launcher",
            projects = self.projects,
            username = user_model["name"])

class LauncherHandler(HubAuthenticated, RequestHandler):
    def initialize(self, projects):
        self.projects = projects

    @authenticated
    def get(self, project_name, project_service_name):
        user_model = self.get_current_user()

        projects = self.projects['projects']
     
        api_token = os.environ['JUPYTERHUB_API_TOKEN'] 
        api_url = 'http://jupyterhub_basic:8081/hub/api'

        # container_name
        container_name = project_name + "_" + project_service_name

        # check if user has this container launched already
        r = requests.get(api_url + '/users/' + user_model["name"],
          headers = {
            'Authorization': 'token %s' % api_token,
          }
        )
        r.raise_for_status()
        user = r.json()
        is_container_launched = (container_name in user['servers'])

        service = projects[project_name]['services'][project_service_name]

        is_external = ('external' in service) and service['external']

        if is_external:
          self.redirect("/services/external/" + project_name + "/" + project_service_name + "/")
        else:
          # get_project_service_container
          if (project_name in projects) and\
             (project_service_name in projects[project_name]['services']):
            project_service_container = \
              projects[project_name]['services'][project_service_name]['image']
          else:
            project_service_container = None
          # launch_container
          if not is_container_launched:
            r = requests.post(api_url + "/users/" + user_model["name"] + \
                                        "/servers/" + container_name,
              headers = {
                'Authorization': 'token %s' % api_token,
              },
              json = {
                "image": project_service_container
              }
            )
            r.raise_for_status()

          # See if there any additonal instructions to where to redirect to
          next_internal = self.get_argument('next_internal', '')

          # Redirect user to their container
          self.redirect("/user/" + user_model["name"] + "/" + container_name + "/" + next_internal)

def main():
    # load configuration
    with open(r'./projects.yaml') as file:
      projects = yaml.load(file, Loader=yaml.FullLoader)

    # start app
    app = Application(
        [
            (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + r"?", LauncherProjectsPageHandler, dict(projects = projects)),
            (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + r"([^/]+)/([^/]+)/?", LauncherHandler, dict(projects = projects)),
        ]
    )

    http_server = HTTPServer(app)
    http_server.listen(10101, "*")

    IOLoop.current().start()


if __name__ == '__main__':
    main()
