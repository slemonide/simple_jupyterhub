import sys
import os

# launch with docker
from cdsdashboards.hubextension.spawners.variabledocker import VariableSystemUserSpawner

c.JupyterHub.spawner_class = 'cdsdashboards.hubextension.spawners.variabledocker.VariableSystemUserSpawner'

# Use our launcher instead of /hub/spawn and /hub/home
c.JupyterHub.default_url = "/services/launcher"

c.SystemUserSpawner.remove = True
c.JupyterHub.cleanup_servers = False
c.ConfigurableHTTPProxy.should_start = False
c.ConfigurableHTTPProxy.auth_token = os.environ['CONFIGPROXY_AUTH_TOKEN']
c.ConfigurableHTTPProxy.api_url = 'http://jupyterhub-proxy:8001'


c.JupyterHub.services = [
    {
        'name': 'launcher',
        'url': 'http://jupyterhub_basic:10101',
        'admin': True, # allow launching user containers
        'command': [sys.executable, './services/launcher/launcher.py'],
    },
]

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
c.SystemUserSpawner.image = 'ideonate/containds-allr-datascience'
c.VariableSystemUserSpawner.allowed_images = [
  'ideonate/containds-allr-datascience',
  'jupyter/datascience-notebook',
  'phaustin/notebook:step1',
  'jh-code-server'
]

# tell the user containers to connect to our docker network
c.SystemUserSpawner.network_name = 'net_basic'

# Github OAuth
from oauthenticator.github import LocalGitHubOAuthenticator
c.JupyterHub.authenticator_class = LocalGitHubOAuthenticator
c.LocalGitHubOAuthenticator.create_system_users = True

# Load users from access list

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

# Database
c.JupyterHub.db_url = 'postgresql://postgres:{password}@{host}/{db}'.format(
    host=os.environ['POSTGRES_HOST'],
    password=os.environ['POSTGRES_PASSWORD'],
    db=os.environ['POSTGRES_DB'],
)
