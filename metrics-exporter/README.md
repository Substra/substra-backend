# Metrics exporter

The goal of this component is to expose metrics produced by a Django app.
Using the `PROMETHEUS_MULTIPROC_DIR` env variable you can make an app that run in multiple proceses write metrics in a folder. This app gather these metrics from the folder and expose them.

This is particularly useful if you want to expose your metrics on a different port than the Django app.

This is based on the [prometheus-client](https://github.com/prometheus/client_python) Python library.

## Installation

There is no specific installation steps, you just have to install the dependecies:
```
$ pip install -r requirements.txt
```

## Launching the server

You can start the server exposing metrics by using this command:
```
$ PYTHONPATH=. python metrics_exporter/server.py
```

## Settings
These settings can be set through env variables.

| Env variable                | Description                                      |
| ---                         | ---                                              |
| `PROMETHEUS_MULTIPROC_DIR`  | Directory in which the app will look for metrics |
| `PORT`                      | Port on which the server is exposed              |
| `LOG_LEVEL`                 | Control the amount of log output                 |
| `CELERY_MONITORING_ENABLED` | Enable monitoring of celery events               |
| `CELERY_BROKER_USER`        | User used to access the Celery Redis             |
| `CELERY_BROKER_PASSWORD`    | Password used to access the Celery Redis         |
| `CELERY_BROKER_HOST`        | Redis hostname                                   |
| `CELERY_BROKER_PORT`        | Port on which Redis is exposed                   |
