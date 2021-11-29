FROM python:3.9-slim AS build

ENV GRPC_POLL_STRATEGY=epoll1
ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.
RUN pip3 install --upgrade --no-cache-dir pip==21.3.1 \
    && pip3 install --prefix /usr/local --no-cache-dir -r requirements.txt

COPY ./backend/manage.py /usr/src/app/manage.py
COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/events /usr/src/app/events
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/node /usr/src/app/node
COPY ./backend/node_register /usr/src/app/node_register
COPY ./backend/users /usr/src/app/users
COPY ./backend/orchestrator /usr/src/app/orchestrator

FROM python:3.9-slim

ARG BACKEND_VERSION
ENV BACKEND_VERSION=${BACKEND_VERSION:-dev}

ARG USER_ID=1001
ARG GROUP_ID=1001
ENV GRPC_POLL_STRATEGY=epoll1

COPY --from=build /usr/local/lib/python3.9/ /usr/local/lib/python3.9/
COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/src/app /usr/src/app

WORKDIR /usr/src/app

RUN mkdir -p /var/substra/ /tmp/django_cache \
  && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app /var/substra/ /tmp/django_cache

USER ${USER_ID}:${GROUP_ID}
