#!/usr/bin/env sh
set -euxo pipefail

kubectl exec $(kubectl get -n org-1 pod -l app.kubernetes.io/name=rabbitmq,app.kubernetes.io/instance=backend-org-1 -o name) -n org-1 -- rabbitmqctl add_user rabbitmq rabbitmq
kubectl exec $(kubectl get -n org-1 pod -l app.kubernetes.io/name=rabbitmq,app.kubernetes.io/instance=backend-org-1 -o name) -n org-1 -- rabbitmqctl set_permissions -p "/" "rabbitmq" ".*" ".*" ".*"
kubectl exec $(kubectl get -n org-2 pod -l app.kubernetes.io/name=rabbitmq,app.kubernetes.io/instance=backend-org-2 -o name) -n org-2 -- rabbitmqctl add_user rabbitmq rabbitmq
kubectl exec $(kubectl get -n org-2 pod -l app.kubernetes.io/name=rabbitmq,app.kubernetes.io/instance=backend-org-2 -o name) -n org-2 -- rabbitmqctl set_permissions -p "/" "rabbitmq" ".*" ".*" ".*"


# Restart the backend worker to rerun rabbitmq connection with the correct user in the app init process
kubectl rollout restart $(kubectl get -n org-1 deployment -l app.kubernetes.io/name=substra-backend-scheduler-worker -o name) -n org-1
kubectl rollout restart $(kubectl get -n org-2 deployment -l app.kubernetes.io/name=substra-backend-scheduler-worker -o name) -n org-2
