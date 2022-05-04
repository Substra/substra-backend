# Migration steps for Merge Metric and Algo view (#976) from connect-backend 0.11.0 to upper version

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

For each org or a connect network you need to do manual minio migration before update connect-backend

Example with a connect-backend deployed in kubernetes namespace `NAMESPACE`


## 1 - Copy data from metrics minio bucket to algos one

```bash
kubectl exec -it -n NAMESPACE $(kubectl get pod -l app.kubernetes.io/name=minio  -n NAMESPACE -o name) -- mc cp --recursive /data/substra-metrics/metrics/ /data/substra-algo/algos
```

## 2 - Update connect-backend to the last version

Update your connect-backend version

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


