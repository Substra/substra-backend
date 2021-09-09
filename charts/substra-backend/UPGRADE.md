## 5.0.0

This version adds support for Kubernetes 1.22. This required some changes to the Ingress.

If you had a single host and a single path for your ingress:
- move `backend.ingress.hosts[0].host` to `backend.ingress.hostname`
- move `backend.ingress.hosts[0].paths[0]` to `backend.ingress.path`

If you had multiple hosts you can proceed as for a single host for your first host and then add your other hosts to `backend.ingress.extraHosts`.

The other significant change is a rename from `backend.ingress.tls` to `backend.ingress.extraTls`, the data structure inside is the same.

## 4.0.0

 - Add orchestrator connection (grpc + rabbitmq). You need to handle certificates generation if you want to use tls or mutual tls with those connection
## 3.0.0

- Replace `rabbitmq.rabbitmq` with `rabbitmq.auth`
