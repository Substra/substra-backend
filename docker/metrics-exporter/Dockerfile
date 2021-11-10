FROM python:3.9-slim AS build

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ARG BACKEND_VERSION
ENV BACKEND_VERSION=${BACKEND_VERSION:-dev}

ARG USER_ID=1001
ARG GROUP_ID=1001

COPY ./metrics-exporter/requirements.txt /usr/src/app/.
RUN pip3 install --upgrade pip && pip3 install --prefix /usr/local -r requirements.txt

COPY ./metrics-exporter/* /usr/src/app/

RUN chown -R ${USER_ID}:${GROUP_ID} /usr/src/app

USER ${USER_ID}:${GROUP_ID}
