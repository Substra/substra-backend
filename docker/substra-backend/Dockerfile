FROM ubuntu:24.04 AS build

ENV GRPC_POLL_STRATEGY=epoll1
ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && apt-get install --no-install-recommends -y --only-upgrade gnupg \
    && apt-get --no-install-recommends -y install software-properties-common python3-pip gcc python3-dev python3-watchdog celery python-is-python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY ./backend/requirements.txt /usr/src/app/.

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH" VIRTUAL_ENV="/venv"

RUN pip install --upgrade --no-cache-dir pip==24.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY ./backend/manage.py /usr/src/app/manage.py
COPY ./backend/libs /usr/src/app/libs
COPY ./backend/substrapp /usr/src/app/substrapp
COPY ./backend/backend /usr/src/app/backend
COPY ./backend/organization /usr/src/app/organization
COPY ./backend/organization_register /usr/src/app/organization_register
COPY ./backend/users /usr/src/app/users
COPY ./backend/orchestrator /usr/src/app/orchestrator
COPY ./backend/api /usr/src/app/api
COPY ./backend/builder /usr/src/app/builder
COPY ./backend/image_transfer /usr/src/app/image_transfer

FROM build AS arm64

RUN apt-get update && apt-get install -y --no-install-recommends \
    # libpq is a required dependency to build psycopg2 from source (support for arm64 platform)
    libpq-dev
RUN pip install --no-cache-dir psycopg2==2.9.9

ARG USER_ID=1001
ARG GROUP_ID=1001

RUN mkdir -p /var/substra/ /tmp/django_cache \
    && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app /var/substra/ /tmp/django_cache

USER ${USER_ID}:${GROUP_ID}

# only for `docker build --target dev`
FROM build AS dev

COPY ./backend/dev-requirements.txt /usr/src/app/.
RUN pip install --no-cache-dir -r dev-requirements.txt
COPY backend/dev-startup.sh .

FROM ubuntu:24.04

ARG VERSION
ENV BACKEND_VERSION=${VERSION:-dev}

ARG USER_ID=1001
ARG GROUP_ID=1001
ENV GRPC_POLL_STRATEGY=epoll1 PATH="/venv/bin:$PATH" VIRTUAL_ENV="/venv"

COPY --from=build /venv/ /venv/
COPY --from=build /usr/bin/ /usr/bin/
COPY --from=build /lib/ /lib/
COPY --from=build /usr/src/app /usr/src/app

RUN find /usr/src/app -type d -name tests -prune -exec rm -rf {} \;

WORKDIR /usr/src/app

RUN mkdir -p /var/substra/ /tmp/django_cache \
    && chown -R ${USER_ID}:${GROUP_ID} /usr/src/app /var/substra/ /tmp/django_cache \
    && rm -rf /usr/lib/python3/dist-packages

USER ${USER_ID}:${GROUP_ID}