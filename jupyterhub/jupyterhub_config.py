# launch with docker
#from cdsdashboards.hubextension.spawners.variabledocker import VariableSystemUserSpawner
#from dockerspawner import DockerSpawner

#class DemoFormSpawner(VariableSystemUserSpawner):
#    def _options_form_default(self):
#        default_stack = "ideonate/containds-allr-datascience"
#        return """
#        <label for="stack">Select your desired stack</label>
#        <select name="stack" size="1">
#        <option value="ideonate/containds-allr-datascience">ideonate/containds-allr-datascience</option>
#        <option value="jupyter/datascience-notebook">jupyter/datascience-notebook</option>
#        <option value="phaustin/notebook">phaustin/notebook</option>
#        </select>
#        """.format(stack=default_stack)

#    def options_from_form(self, formdata):
#        options = {}
#        options['stack'] = formdata['stack']
#        container_image = ''.join(formdata['stack'])
#        print("SPAWN: " + container_image + " IMAGE" )
#        self.container_image = container_image
#        return options

#c.JupyterHub.spawner_class = DemoFormSpawner

c.JupyterHub.spawner_class = 'cdsdashboards.hubextension.spawners.variabledocker.VariableSystemUserSpawner'

# More debug info
c.Spawner.debug = True

# Allow more than one jupyter notebook environment per user
# Needed for dashboards
c.JupyterHub.allow_named_servers = True
c.SystemUserSpawner.name_template = "{prefix}-{username}-{imagename}-{servername}"
#c.JupyterHub.internal_ssl = True

# Enable dashboards
from cdsdashboards.app import CDS_TEMPLATE_PATHS
from cdsdashboards.hubextension import cds_extra_handlers

c.JupyterHub.template_paths = CDS_TEMPLATE_PATHS
c.JupyterHub.extra_handlers = cds_extra_handlers

c.CDSDashboardsConfig.builder_class = 'cdsdashboards.builder.dockerbuilder.DockerBuilder'

#####

# we need the hub to listen on all ips when it is in a container
c.JupyterHub.hub_ip = '0.0.0.0'
# the hostname/ip that should be used to connect to the hub
# this is usually the hub container's name
c.JupyterHub.hub_connect_ip = 'jupyterhub_basic'

# pick a docker image. This should have the same version of jupyterhub
# in it as our Hub.
#c.SystemUserSpawner.image = 'phaustin/notebook:step1'
#c.SystemUserSpawner.image = 'jupyter/datascience-notebook'
c.SystemUserSpawner.image = 'ideonate/containds-allr-datascience'
c.VariableSystemUserSpawner.allowed_images = [
  'ideonate/containds-allr-datascience',
  'jupyter/datascience-notebook',
  'phaustin/notebook:step1'
]
#c.SystemUserSpawner.image = 'ideonate/containds-all-basic'
#notebook_dir = "/home/jovyan/work"
#c.SystemUserSpawner.notebook_dir = notebook_dir

# tell the user containers to connect to our docker network
c.SystemUserSpawner.network_name = 'net_basic'
# delete containers when the stop
c.SystemUserSpawner.remove = True

# Github OAuth
from oauthenticator.github import LocalGitHubOAuthenticator
c.JupyterHub.authenticator_class = LocalGitHubOAuthenticator
c.LocalGitHubOAuthenticator.create_system_users = True

# Load users from access list
import os

c.Authenticator.allowed_users = allowed = set()
c.Authenticator.admin_users = admin = set()
c.LocalGitHubOAuthenticator.uids = uids = dict()

c.SystemUserSpawner.host_homedir_format_string = '/data/jupyterhub/users/{username}'
c.Authenticator.add_user_cmd = ['adduser', '-q', '-gecos', '""', '-home', '/data/jupyterhub/users/USERNAME', '-disabled-password']

join = os.path.join
here = os.path.dirname(__file__)

with open(join(here, 'userlist')) as f:
    for line in f:
        if not line:
            continue
        parts = line.split()
        uid = int(parts[0]) + 300000

        # convert name to lower case to be compatible
        # with some linux tools...
        # not sure if github allows different users
        # with the same name, but different case
        name = parts[1].lower()

        uids[name] = uid

        allowed.add(name)
        if len(parts) > 2 and parts[2] == 'admin':
            admin.add(name)

# enable disk quotas
from subprocess import check_call
def pre_spawn_hook(spawner):
    user = spawner.user.name
    # 1G soft + 2G hard quota
    check_call(["setquota", "-u", user, "524288", "2097152", "0", "0", "/host_root/"])

c.SystemUserSpawner.pre_spawn_hook = pre_spawn_hook

