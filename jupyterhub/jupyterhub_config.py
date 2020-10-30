# launch with docker
c.JupyterHub.spawner_class = 'dockerspawner.SystemUserSpawner'

# we need the hub to listen on all ips when it is in a container
c.JupyterHub.hub_ip = '0.0.0.0'
# the hostname/ip that should be used to connect to the hub
# this is usually the hub container's name
c.JupyterHub.hub_connect_ip = 'jupyterhub_basic'

# pick a docker image. This should have the same version of jupyterhub
# in it as our Hub.
#c.SystemUserSpawner.image = 'phaustin/notebook:step1'
c.SystemUserSpawner.image = 'jupyter/datascience-notebook'
notebook_dir = "/home/jovyan/work"
c.SystemUserSpawner.notebook_dir = notebook_dir

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

#c.Authenticator.allowed_users = allowed = set()
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
    #check_call(['./examples/bootstrap-script/bootstrap.sh', username])

c.SystemUserSpawner.pre_spawn_hook = pre_spawn_hook

#def pre_spawn_start(user, spawner):
  # set user disk quota with soft limit of 1G and hard limit of 2G
  # and no limit on number of files
  # soft limit just means that user is allowed to have more than 1G for a week
  # and after that, they wouldn't be able to write anymore unless they delete
  # some files
  # TODO: have some notification for that...
  #subprocess.run(["setquota", "-u", user, "524288", "2097152", "0", "0", "/host_root/"])
#  setquota -u slemonide 262144 524288 0 0 /host_root/
#  print(user)

  # Caveats:
  # 524288 corresponds to 1GB (but it should to 0.5G)
  # I think it's because we mount the same files in two different locations
  #
  # If user runs out of disk space, they won't be able to start their notebook next time.
  # ... maybe that's a feature! They get automatically banned :)

#c.Authenticator.pre_spawn_start = pre_spawn_start
