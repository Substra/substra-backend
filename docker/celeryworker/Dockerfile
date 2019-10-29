FROM nvidia/cuda:9.2-base-ubuntu18.04

RUN apt-get update
RUN apt-get install -y python3.6 python3-pip python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev
RUN apt-get install -y git curl netcat

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt

COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/users /usr/src/app/users
