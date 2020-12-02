"""A simple launcher service that launches containers for users using a
project description from project.yaml file

This serves `/services/launcher/`, authenticated with the Hub.
"""
import json
import os
from urllib.parse import urlparse

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.web import authenticated
from tornado.web import RequestHandler

from jupyterhub.services.auth import HubAuthenticated

import yaml # to read config
import requests # to make requests to Hub API

import docker # to start external services containers

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

        # get_project_service_container
        if (project_name in projects) and\
           (project_service_name in projects[project_name]['services']):
          project_service_container = \
            projects[project_name]['services'][project_service_name]['image']
        else:
          project_service_container = None
     
        api_token = os.environ['JUPYTERHUB_API_TOKEN'] 
        api_url = 'http://127.0.0.1:8081/hub/api'

        # container_name
        container_name = project_name + "_" + project_service_name

        # check if user has this container launched already
        r = requests.get(api_url + '/users/slemonide',
          headers = {
            'Authorization': 'token %s' % api_token,
          }
        )
        r.raise_for_status()
        user = r.json()
        is_container_launched = (container_name in user['servers'])
        
        # Debug
        proxy_api_url = 'http://jupyterhub-proxy:8001/api'
        proxy_api_token = "4a766d01cb5d0256c65ad75617995665e0ce6df75e1aae634950c55fd872426f"
        #proxy_api_token = os.environ['CONFIGPROXY_AUTH_TOKEN']
        r = requests.get(proxy_api_url + '/routes',
          headers = {
            'Authorization': 'token %s' % proxy_api_token,
          }
        )
        r.raise_for_status()
        proxy = r.json()

        self.set_header('content-type', 'application/json')
        self.write(json.dumps({
          "projects": self.projects,
          "container_image": project_service_container,
          "container_name": container_name,
          "proxy": proxy,
        }, indent=1, sort_keys=True))
        # End Debug

        # launch_container
        #if not is_container_launched:
        #  r = requests.post(api_url + "/users/" + user_model["name"] + \
        #                              "/servers/" + container_name,
        #    headers = {
        #      'Authorization': 'token %s' % api_token,
        #    },
        #    json = {
        #      "image": project_service_container
        #    }
        #  )
        #  r.raise_for_status()


        # Redirect user to their container
        #self.redirect("/user/" + user_model["name"] + "/" + container_name)

def start_external_containers(projects):
  docker_client = docker.from_env()

  for project_label in projects['projects']:
    project = projects['projects'][project_label]
    for service_label in project['services']:
      service = project['services'][service_label]
      image = service["image"]
      
      is_external = ("external" in service) and service["external"]
      if is_external:
        name = project_label + "_" + service_label

        # stop & remove the container if it's already running
        try:
          container = docker_client.containers.get(name)
          container.stop()
          container.remove()
        except docker.errors.NotFound:
          pass # it's not running or not defined

        container = docker_client.containers.run(image, detach=True, name=name)

def main():
    # load configuration
    with open(r'./projects.yaml') as file:
      projects = yaml.load(file, Loader=yaml.FullLoader)

    # start external containers
    start_external_containers(projects)

    # start app
    app = Application(
        [
            (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + r"?", LauncherProjectsPageHandler, dict(projects = projects)),
            (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + r"([^/]+)/([^/]+)/?", LauncherHandler, dict(projects = projects)),
        ]
    )

    http_server = HTTPServer(app)
    url = urlparse(os.environ['JUPYTERHUB_SERVICE_URL'])

    http_server.listen(url.port, url.hostname)

    IOLoop.current().start()


if __name__ == '__main__':
    main()
