import json
import os
import sys
from urllib.parse import urlparse

import tornado.escape

import time
import yaml
import requests
import docker

def start_external_containers(projects):
  say("Starting containers")

  docker_client = docker.from_env()

  for project_label in projects['projects']:
    project = projects['projects'][project_label]
    for service_label in project['services']:
      service = project['services'][service_label]
      
      is_external = ("external" in service) and service["external"]
      if is_external:
        time.sleep(3) # don't ddos github
        name = project_label + "_" + service_label

        say("Working on " + name)

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
          image = docker_client.images.get(service["image"])
        elif "build" in service:
          (image, logs) = docker_client.images.build(path=service["build"])
        else:
          sys.exit('Need an image or a build path/url for ' + name)

        # stop & remove the container if it's already running
        try:
          container = docker_client.containers.get(name)

          # if image is
#          if isinstance(image, str):
          
          # if new image is different from the one currently running
          if (container.image.id != image.id):
            say("New image detected. Restarting container")
            container.stop()
            container.remove()
            launch_new_container = True
          else:
            launch_new_container = False
        except docker.errors.NotFound:
          launch_new_container = True
          say("Container wasn't running before. Starting it.")

        if launch_new_container:
          say("Launching container")
          container = docker_client.containers.run(image, detach=True,
            name=name, network="net_basic", environment=environment,
            labels=labels, volumes=volumes, command=command)

          say("Setting up proxy routes")
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

def load_configuration():
  say("")
  say("Loading configuration")
  with open(r'./projects.yaml') as file:
    projects = yaml.load(file, Loader=yaml.FullLoader)
    return projects

def say(msg):
  print(msg, flush=True)

def main():
  while True:
    projects = load_configuration()
    start_external_containers(projects)

if __name__ == '__main__':
    main()
