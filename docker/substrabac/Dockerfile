#FROM python:3-alpine
#
#COPY ./substrabac/requirements.txt /usr/src/.
#
#RUN apk add --no-cache libstdc++ && \
#    apk add --no-cache \
#    --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community \
#    lapack-dev && \
#    apk add --no-cache \
#    --virtual=.build-dependencies \
#    g++ gfortran musl-dev postgresql-libs gcc postgresql-dev libffi-dev\
#    python3-dev && \
#    ln -s locale.h /usr/include/xlocale.h && \
#    pip install -r /usr/src/requirements.txt && \
#    apk del .build-dependencies

# RUN apk add postgresql-dev curl

FROM python:3.6
RUN apt-get update
RUN apt-get install -y g++ gfortran musl-dev postgresql-contrib gcc libffi-dev python3-dev curl


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./substrabac/requirements.txt /usr/src/app/.
RUN sed -i '/substrabacSDK/d' /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY ./bootstrap.sh /usr/src/

RUN cd /usr/src; sh bootstrap.sh

COPY ./substrabac /usr/src/app
COPY ./assets /usr/src/assets

RUN sed -i 's/localhost/rabbit/g' /usr/src/app/substrabac/celery.py
RUN sed -i 's/8051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/8051/7051/g' /usr/src/app/substrapp/conf/owkin/peer1/core.yaml
RUN sed -i 's/9051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/9051/7051/g' /usr/src/app/substrapp/conf/chu-nantes/peer1/core.yaml
RUN sed -i 's/10051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/10051/7051/g' /usr/src/app/substrapp/conf/chu-nantes/peer1/core.yaml

RUN apt-get install -y netcat
