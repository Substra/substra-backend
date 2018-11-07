FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get update; apt-get install -y git python3 python3-pip \
    python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev curl netcat

COPY ./substrabac/requirements.txt /usr/src/app/.
RUN pip3 install -r requirements.txt

COPY ./substrabac /usr/src/app

RUN sed -i 's/localhost/rabbit/g' /usr/src/app/substrabac/celery.py
