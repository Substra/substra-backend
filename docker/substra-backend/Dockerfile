FROM python:3.8

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.

RUN pip3 install -r requirements.txt

COPY ./backend/manage.py /usr/src/app/manage.py
COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/events /usr/src/app/events
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/node-register /usr/src/app/node-register
COPY ./backend/users /usr/src/app/users
