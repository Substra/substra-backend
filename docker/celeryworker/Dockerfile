FROM nvidia/cuda:9.2-base-ubuntu18.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3-dev python3-pip python3-setuptools python3-wheel build-essential git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/doc/*

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt

COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/users /usr/src/app/users
