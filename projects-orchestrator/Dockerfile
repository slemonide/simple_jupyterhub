FROM python:3.8-slim-buster

RUN pip3 install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache -r /tmp/requirements.txt

RUN mkdir /wd
WORKDIR /wd/

COPY src /wd/src

CMD [ "python3", "./src/main.py"]
