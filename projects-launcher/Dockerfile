FROM jupyterhub/jupyterhub:master

RUN /usr/bin/python3 -m pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache -r /tmp/requirements.txt

COPY src /srv/jupyterhub/src
COPY projects.yaml /srv/jupyterhub/projects.yaml

CMD [ "python3", "./src/launcher.py"]
