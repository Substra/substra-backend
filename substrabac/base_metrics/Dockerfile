FROM substra-model

RUN mkdir -p /sandbox/metrics
ADD ./calc_metrics.py .

ENTRYPOINT ["python3", "calc_metrics.py"]
