FROM python:3.9-slim AS build

ENV GRPC_POLL_STRATEGY=epoll1
ENV PYTHONUNBUFFERED=1

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
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
COPY ./backend/organization /usr/src/app/organization
COPY ./backend/organization_register /usr/src/app/organization_register
COPY ./backend/users /usr/src/app/users
COPY ./backend/orchestrator /usr/src/app/orchestrator
COPY ./backend/localrep /usr/src/app/localrep

FROM build AS arm64

RUN apt-get update && apt-get install -y --no-install-recommends \
    # libpq is a required dependency to build psycopg2 from source (support for arm64 platform)
    libpq-dev
RUN pip3 install --upgrade --no-cache-dir pip==21.3.1 \
    && pip3 install --prefix /usr/local --no-cache-dir psycopg2==2.9.3

ARG USER_ID=1001
ARG GROUP_ID=1001

RUN mkdir -p /var/substra/ /tmp/django_cache \
    && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app /var/substra/ /tmp/django_cache

USER ${USER_ID}:${GROUP_ID}

# only for `docker build --target dev`
FROM build AS dev

COPY ./backend/dev-requirements.txt /usr/src/app/.
RUN pip3 install --prefix /usr/local --no-cache-dir -r dev-requirements.txt
COPY backend/dev-startup.sh .

FROM python:3.9-slim

ARG BACKEND_VERSION
ENV BACKEND_VERSION=${BACKEND_VERSION:-dev}

ARG USER_ID=1001
ARG GROUP_ID=1001
ENV GRPC_POLL_STRATEGY=epoll1

COPY --from=build /usr/local/lib/python3.9/ /usr/local/lib/python3.9/
COPY --from=build /usr/local/bin/ /usr/local/bin/
COPY --from=build /usr/src/app /usr/src/app

RUN find /usr/src/app -type d -name tests -prune -exec rm -rf {} \;

WORKDIR /usr/src/app

RUN mkdir -p /var/substra/ /tmp/django_cache \
  && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app /var/substra/ /tmp/django_cache

USER ${USER_ID}:${GROUP_ID}