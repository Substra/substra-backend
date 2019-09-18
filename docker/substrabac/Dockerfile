FROM python:3.6

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev g++ gcc gfortran musl-dev postgresql-contrib
RUN apt-get install -y git curl netcat

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./substrabac/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt

COPY ./substrabac/manage.py /usr/src/app/manage.py
COPY ./substrabac/libs /usr/src/app/libs
COPY ./substrabac/substrapp /usr/src/app/substrapp
COPY ./substrabac/events /usr/src/app/events
COPY ./substrabac/substrabac /usr/src/app/substrabac
COPY ./substrabac/node /usr/src/app/node
COPY ./substrabac/node-register /usr/src/app/node-register
COPY ./substrabac/user /usr/src/app/user
