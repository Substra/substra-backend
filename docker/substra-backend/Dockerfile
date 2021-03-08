FROM python:3.6-slim AS build

ENV GRPC_POLL_STRATEGY=epoll1
RUN apt-get update && apt-get install gcc -y && apt-get clean

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.
RUN pip3 install --upgrade pip && pip3 install --prefix /usr/local -r requirements.txt

COPY ./backend/manage.py /usr/src/app/manage.py
COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/events /usr/src/app/events
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/node-register /usr/src/app/node-register
COPY ./backend/users /usr/src/app/users

FROM python:3.6-slim

ARG USER_ID=1001
ARG GROUP_ID=1001
ENV GRPC_POLL_STRATEGY=epoll1

COPY --from=build /usr/local/lib/python3.6/ /usr/local/lib/python3.6/
COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/src/app /usr/src/app

WORKDIR /usr/src/app
RUN chown -R ${USER_ID}:${GROUP_ID} /usr/src/app

RUN mkdir -p /var/substra/
RUN mkdir -p /tmp/django_cache
RUN chown -R ${USER_ID}:${GROUP_ID} /var/substra/ /tmp/django_cache

USER ${USER_ID}:${GROUP_ID}
