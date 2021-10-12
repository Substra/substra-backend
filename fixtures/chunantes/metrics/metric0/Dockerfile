FROM substrafoundation/substra-tools:0.0.1

RUN mkdir -p /sandbox/opener
WORKDIR /sandbox
COPY metrics.py .

ENTRYPOINT ["python3", "metrics.py"]
