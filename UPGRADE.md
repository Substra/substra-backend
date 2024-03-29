# Rename localrep to api: substra-backend 0.29.0 -> 0.30.0

Execute this command in the backend DB, before running django migrations,

```sql
UPDATE django_content_type SET app_label='api' WHERE app_label='localrep';
UPDATE django_migrations SET app='api' WHERE app='localrep';
ALTER TABLE localrep_algo RENAME TO api_algo;
ALTER TABLE localrep_algoinput RENAME TO api_algoinput;
ALTER TABLE localrep_algooutput RENAME TO api_algooutput;
ALTER TABLE localrep_channelorganization RENAME TO api_channelorganization;
ALTER TABLE localrep_computeplan RENAME TO api_computeplan;
ALTER TABLE localrep_computetask RENAME TO api_computetask;
ALTER TABLE localrep_computetaskinput RENAME TO api_computetaskinput;
ALTER TABLE localrep_computetaskoutput RENAME TO api_computetaskoutput;
ALTER TABLE localrep_computetaskoutputasset RENAME TO api_computetaskoutputasset;
ALTER TABLE localrep_datamanager RENAME TO api_datamanager;
ALTER TABLE localrep_datasample RENAME TO api_datasample;
ALTER TABLE localrep_datasample_data_managers RENAME TO api_datasample_data_managers;
ALTER TABLE localrep_lastevent RENAME TO api_lastevent;
ALTER TABLE localrep_model RENAME TO api_model;
ALTER TABLE localrep_performance RENAME TO api_performance;
ALTER TABLE localrep_profilingstep RENAME TO api_profilingstep;
ALTER TABLE localrep_taskdatasamples RENAME TO api_taskdatasamples;
ALTER TABLE localrep_taskprofiling RENAME TO api_taskprofiling;
```

# Migration steps to change Celery Broker from RabbitMQ to Redis from substra-backend helm chart 21.1.0 and docker image 0.24.0 to upper version

## Migration without task in queues

Set `connect-backend` `events` Deployment replicas to `0`.

Wait for RabbitMQ queues to be empty with `rabbitmqctl list_queues`

Upgrade `connect-backend` upper than 0.18.0 to deploy `Redis` instead of `RabbitMQ`.

Set `connect-backend` `events` Deployment replicas to the number you set in your deployment if it hasn't been done by the upgrade.


## Migration with tasks in queues
Set `connect-backend` `worker` Replicaset to `0`.

Deploy a temporary RabbitMQ to keep the scheduled tasks : `helm install tmp-rabbit -n NAMESPACE bitnami/rabbitmq`

Migrate data from `connect-backend RabbitMQ` to `tmp-rabbit RabbitMQ`

```bash
celery -b "amqp://<username>:<password>@<url-rabbitmq-connect-backend>:<port>/" inspect scheduled > scheduled_tasks_rabbitmq.txt
celery migrate "amqp://<username>:<password>@<url-rabbitmq-connect-backend>:<port>/" "amqp://<username>:<password>@<url-tmp-rabbitmq>:<port>/"
celery -b "amqp://<username>:<password>@<url-tmp-rabbitmq>:<port>/" inspect scheduled  > scheduled_tasks_tmp_rabbitmq.txt
diff scheduled_tasks_rabbitmq.txt scheduled_tasks_tmp_rabbitmq.txt
```

Upgrade `connect-backend` upper than 0.18.0 to deploy `Redis` instead of `RabbitMQ`. Be sure to have a backup, it will remove `connect-backend` `RabbitMQ`.
RabbitMQ backup documentation : https://www.rabbitmq.com/backup.html


Migrate data from  `tmp-rabbit RabbitMQ` to `connect-backend Redis`

```bash
celery migrate "amqp://<username>:<password>@<url-tmp-rabbitmq>:<port>/" "redis://<username>:<password>@<url-redis-connect-backend>:<port>/"
celery -b "redis://<username>:<password>@<url-redis-connect-backend>:<port>/" inspect scheduled  > scheduled_tasks_redis.txt
diff scheduled_tasks_tmp_rabbitmq.txt scheduled_tasks_redis.txt
```

Set `connect-backend` `worker` Replicaset to the number you set in your deployment.


# Migration steps for Merge Metric and Algo view from substra-backend 0.11.0 to upper version

Be sure to backup Django model databases and MinIO data before doing those steps

## Backup and restore data

### Backup and restore MinIO data

There are several buckets that need to be backup

```
substra-algo
substra-datamanager
substra-datasample
substra-metrics
substra-model
```

#### Backup
```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o name) -- mc mirror --remove --preserve $MINIO_ENV/<bucket> $BACKUPS_DIR/$BACKUP_NAME
kubectl cp NAMESPACE/$(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o custom-columns=":metadata.name" --no-headers):/$BACKUPS_DIR/$BACKUP_NAME /PATH/TO/BACKUPS/<bucket>
```

#### Restore

```bash
kubectl cp /PATH/TO/BACKUPS/<bucket> NAMESPACE/$(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o custom-columns=":metadata.name" --no-headers):$BACKUPS_DIR/$BACKUP_NAME -c server
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o name) -- mc mirror --remove --preserve $BACKUPS_DIR/$BACKUP_NAME $MINIO_ENV/<bucket>

```

### Backup and restore Django databases

#### Backup

##### localrep
```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=substra-backend-server  -n NAMESPACE -o name) -c server -- python manage.py dumpdata localrep --indent=4 > /PATH/TO/BACKUPS/localrep.json
```

##### substrapp
```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=substra-backend-server  -n NAMESPACE -o name) -c server -- python manage.py dumpdata substrapp --indent=4 > /PATH/TO/BACKUPS/substrapp.json
```

#### Restore

##### localrep
```bash
# Copy backup into the pod
kubectl cp /PATH/TO/BACKUPS/localrep.json NAMESPACE/$(kubectl get pod -l app.kubernetes.io/name=substra-backend-server -n NAMESPACE -o custom-columns=":metadata.name" --no-headers):localrep.json -c server
# Load data with Django
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=substra-backend-server  -n NAMESPACE -o name) -c server -- python manage.py loaddata localrep.json
```

##### substrapp
```bash
# Copy backup into the pod
kubectl cp /PATH/TO/BACKUPS/substrapp.json NAMESPACE/$(kubectl get pod -l app.kubernetes.io/name=substra-backend-server -n NAMESPACE -o custom-columns=":metadata.name" --no-headers):substrapp.json -c server
# Load data with Django
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=substra-backend-server  -n NAMESPACE -o name) -c server -- python manage.py loaddata substrapp.json
```



## Upgrade procedure

For each org or a substra network you need to do manual minio migration before update substra-backend

Example with a substra-backend deployed in kubernetes namespace `NAMESPACE`


## 1 - Copy data from metrics minio bucket to algos one

```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o name) -- mc cp --recursive /data/substra-metrics/metrics/ /data/substra-algo/algos
```

## 2 - Update substra-backend to the last version

Update your substra-backend version

## 3 - Sanity verification

Verify that we can access and download "metrics" with ALGO_METRICS algo from algo view !

```
substra config --profile PROFILE URL
substra login --profile PROFILE --username USER --password PASSWORD

# Check list works
substra list metric --profile PROFILE

# For each metric KEY show description and  download file
substra list metric --profile PROFILE | awk '(NR>1) {print $1}' | xargs -I % substra describe metric % --profile PROFILE
substra list metric --profile PROFILE | awk '(NR>1) {print $1}' | xargs -I % substra download metric % --profile PROFILE

```

## 3 - Clean data from metrics minio bucket

```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o name) -- mc rm --force --recursive /data/substra-metrics
```
