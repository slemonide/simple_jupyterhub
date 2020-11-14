FROM jupyterhub/jupyterhub:master

# quota to set disk quotas
RUN apt-get update \
 && apt-get install -yq --no-install-recommends \
    quota \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN /usr/bin/python3 -m pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache -r /tmp/requirements.txt

# development
COPY packages/cdsdashboards/ /tmp/packages/cdsdashboards/
RUN pip install /tmp/packages/cdsdashboards/

COPY packages/dockerspawner/ /tmp/packages/dockerspawner/
RUN pip install /tmp/packages/dockerspawner/

COPY packages/jhsingle-native-proxy/ /tmp/packages/jhsingle-native-proxy/
RUN pip install /tmp/packages/jhsingle-native-proxy/

COPY userlist /srv/jupyterhub/userlist
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

