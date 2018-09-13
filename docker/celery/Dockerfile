FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./substrabac/requirements.txt /usr/src/app/.
RUN pip install -r requirements.txt

COPY ./assets /usr/src/assets
COPY ./bootstrap.sh /usr/src/
RUN cd /usr/src; sh bootstrap.sh

COPY ./substrabac /usr/src/app

RUN sed -i 's/localhost/rabbit/g' /usr/src/app/substrabac/celery.py
RUN sed -i 's/8051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/8051/7051/g' /usr/src/app/substrapp/conf/owkin/peer1/core.yaml
RUN sed -i 's/9051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/9051/7051/g' /usr/src/app/substrapp/conf/chu-nantes/peer1/core.yaml
RUN sed -i 's/10051/7051/g' /usr/src/app/substrapp/conf.py
RUN sed -i 's/10051/7051/g' /usr/src/app/substrapp/conf/chu-nantes/peer1/core.yaml
