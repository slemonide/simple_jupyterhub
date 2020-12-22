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

def start_external_containers(projects):
  docker_client = docker.from_env()

  for project_label in projects['projects']:
    project = projects['projects'][project_label]
    for service_label in project['services']:
      service = project['services'][service_label]
      
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

        # JUPYTERHUB_SERVICE_PREFIX
        environment = {
          "JUPYTERHUB_SERVICE_PREFIX":
              "/services/external/" + project_label + "/" + service_label + "/"
        }

        #["JUPYTERHUB_SERVICE_PREFIX=/services/external/eoas-341/three-signals/"]
        labels = {}# {"com.centurylinklabs.watchtower.scope": "jhub-external"}

        volumes = get_volumes(service, project_label, service_label)

        command = get_service_prop(service, "command", [])
      
        if "image" in service:
          image = service["image"]
        elif "build" in service:
          (image, logs) = docker_client.images.build(path=service["build"])
        else:
          sys.exit('Need an image or a build path/url for ' + name)

        container = docker_client.containers.run(image, detach=True,
          name=name, network="net_basic", environment=environment,
          labels=labels, volumes=volumes, command=command)

        setup_proxy_routes(service, project_label, service_label, name)

def setup_proxy_routes(service, project_label, service_label, name):
  if "ports" in service:
    port_labels = service["ports"]
    for port_label in port_labels:
      port_label_split = port_label.split(" ")

      path = port_label_split[0]
      port = port_label_split[1]

      proxy_add_route(project_label, service_label, name, path, port)
  else:
    # add default port "8000" to default route "/"
    proxy_add_route(project_label, service_label, name, "/", 8000)

def proxy_add_route(project_label, service_label, name, url_path, port):
  proxy_api_url = 'http://jupyterhub-proxy:8001/api'
  proxy_api_token = os.environ['CONFIGPROXY_AUTH_TOKEN']

  url_full_path = proxy_api_url + '/routes/services%2Fexternal%2F' +\
                  project_label + "%2F" + service_label + "%2F" +\
                  tornado.escape.url_escape(url_path)
  r = requests.post(url_full_path,
    headers = {
      'Authorization': 'token %s' % proxy_api_token,
      'Content-Type': 'application/json',
      'accept': 'application/json'
    },
    json = {
      'target': "http://" + name + ":" + str(port),
    }
  )
  r.raise_for_status()

def get_service_prop(service, prop, default):
  if prop in service:
    return service[prop]
  else:
    return default

def get_volumes(service, project_label, service_label):
  # TODO: make sure people can't escape path with something like ../../../
  volumes_list = get_service_prop(service, "volumes", [])

  volumes_pre = os.path.join("/data/jupyterhub/projects",
                             project_label, "services",
                             service_label)

  volumes = {}
  for volume in volumes_list:
    volume_mount = {"bind": "/" + volume, "mode": "rw"}
    volumes[os.path.join(volumes_pre, volume)] = volume_mount

  return volumes

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
    http_server.listen(10101, "*")

    IOLoop.current().start()


if __name__ == '__main__':
    main()
