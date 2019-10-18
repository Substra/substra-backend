FROM python:3.6

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev g++ gcc gfortran musl-dev postgresql-contrib
RUN apt-get install -y git curl netcat

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./substrabackend/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt

COPY ./substrabackend/manage.py /usr/src/app/manage.py
COPY ./substrabackend/libs /usr/src/app/libs
COPY ./substrabackend/substrapp /usr/src/app/substrapp
COPY ./substrabackend/events /usr/src/app/events
COPY ./substrabackend/substrabackend /usr/src/app/substrabackend
COPY ./substrabackend/node /usr/src/app/node
COPY ./substrabackend/node-register /usr/src/app/node-register
