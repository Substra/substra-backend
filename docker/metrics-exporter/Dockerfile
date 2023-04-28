FROM python:3.9-slim AS build

WORKDIR /usr/src/app

ARG VERSION
ENV BACKEND_VERSION=${VERSION:-dev}

ARG USER_ID=1001
ARG GROUP_ID=1001

COPY ./metrics-exporter/requirements.txt /usr/src/app/.
RUN pip3 install --upgrade --no-cache-dir pip==21.3.1 \
    && pip3 install --prefix /usr/local --no-cache-dir -r requirements.txt

COPY ./metrics-exporter/ /usr/src/app/

RUN chown -R ${USER_ID}:${GROUP_ID} /usr/src/app

ENV PYTHONPATH=/usr/src/app/

USER ${USER_ID}:${GROUP_ID}
