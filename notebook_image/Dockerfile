FROM phaustin/base-image:sep05

USER ${NB_USER}

RUN mkdir -p ${HOME}/work

RUN echo "conda activate ${CONDA_ENV}" >> ${HOME}/.bashrc
COPY jupyter_notebook_config.py /etc/jupyter/

WORKDIR ${HOME}/work

CMD ["jupyterhub-singleuser"]
