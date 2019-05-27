FROM eu.gcr.io/substra-208412/substratools

RUN apt-get update; apt-get install -y build-essential libssl-dev  python3 python3-dev python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install pillow numpy sklearn pandas

RUN mkdir -p /sandbox/metrics

WORKDIR /sandbox

ADD ./open_data_sample.py .

ENTRYPOINT ["python3", "open_data_sample.py"]
