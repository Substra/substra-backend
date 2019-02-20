FROM nvidia/cuda:9.0-base

RUN apt-get update; apt-get install -y build-essential libssl-dev  python3 python3-dev python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install pillow numpy sklearn pandas

RUN mkdir -p /sandbox/metrics

WORKDIR /sandbox

ADD ./calc_fake_metrics.py .

ENTRYPOINT ["python3", "calc_fake_metrics.py"]
