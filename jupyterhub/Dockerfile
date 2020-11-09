FROM jupyterhub/jupyterhub:master

# quota to set disk quotas
RUN apt-get update \
 && apt-get install -yq --no-install-recommends \
    quota \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN /usr/bin/python3 -m pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache -r /tmp/requirements.txt
COPY userlist /srv/jupyterhub/userlist
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

