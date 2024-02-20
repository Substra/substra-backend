{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "substra.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "substra.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}


{{/*
Create a fully qualified app name for the server.
We truncate at 56 chars because some Kubernetes name fields are limited to 63 chars (by the DNS naming spec).
*/}}
{{- define "substra.server.fullname" -}}
{{- $name := include "substra.fullname" . | trunc 56 | trimSuffix "-" -}}
{{- printf "%s-server" $name -}}
{{- end -}}


{{/*
Return the appropriate apiVersion for PodSecurityPolicy.
*/}}
{{- define "podsecuritypolicy.apiVersion" -}}
{{- if semverCompare ">=1.14-0" .Capabilities.KubeVersion.Version -}}
{{- print "policy/v1beta1" -}}
{{- else -}}
{{- print "extensions/v1beta1" -}}
{{- end -}}
{{- end -}}


{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "substra.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Common labels
*/}}
{{- define "substra.labels" -}}
helm.sh/chart: {{ include "substra.chart" . }}
{{ include "substra.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ template "substra.name" . }}
{{- end }}


{{/*
Selector labels
*/}}
{{- define "substra.selectorLabels" -}}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Redefine the redis service name because we can't use subchart templates directly.
*/}}
{{- define "redis.serviceName" -}}
{{- if .Values.redis.fullnameOverride -}}
{{- .Values.redis.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "redis-master" .Values.redis.nameOverride -}}
{{- if contains $name (printf "%s" .Release.Name) -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Renders a value that contains template.
Usage:
{{ include "common.tplvalues.render" ( dict "value" .Values.path.to.the.Value "context" $) }}
*/}}
{{- define "common.tplvalues.render" -}}
    {{- if typeIs "string" .value }}
        {{- tpl .value .context }}
    {{- else }}
        {{- tpl (.value | toYaml) .context }}
    {{- end }}
{{- end -}}

{{/*
Return the proper image name
{{ include "common.images.name" .Values.path.to.the.image }}
*/}}
{{- define "common.images.name" -}}
{{- if .registry -}}
{{- printf "%s/%s:%s" .registry .repository .tag -}}
{{- else -}}
{{- printf "%s:%s" .repository .tag -}}
{{- end -}}
{{- end -}}


{{/*
Return the proper Storage Class
{{ include "common.storage.class" .Values.path.to.the.persistence}}
*/}}
{{- define "common.storage.class" -}}
{{- $storageClass := .storageClass -}}
{{- if $storageClass -}}
    {{- if (eq "-" $storageClass) -}}
        {{- printf "storageClassName: \"\"" -}}
    {{- else -}}
        {{- printf "storageClassName: %s" $storageClass -}}
    {{- end -}}
{{- end -}}
{{- end -}}


{{/*
Return the user list
{{ include "common.users" .Values.path.to.the.users }}
*/}}
{{- define "common.users" -}}
{{- range . }}
{{- if .channel }}
    {{- printf "%s %s %s\n" .name .secret .channel }}
{{- else }}
    {{- printf "%s %s\n" .name .secret }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
    Create the name fo the service account to use for the worker event app
*/}}
{{- define "substra.worker.events.serviceAccountName" -}}
{{- if .Values.worker.events.serviceAccount.create -}}
    {{ default (printf "%s-event" ( include "substra.fullname" .)) .Values.worker.events.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.worker.events.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
    Create the name fo the service account to use for the api event app
*/}}
{{- define "substra.api.events.serviceAccountName" -}}
{{- if .Values.api.events.serviceAccount.create -}}
    {{ default (printf "%s-event" ( include "substra.fullname" .)) .Values.api.events.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.api.events.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Return the proper image name, with option for a default tag
example:
    {{ include "substra-backend.images.name" (dict "img" .Values.path.to.the.image "defaultTag" $.Chart.AppVersion) }}
*/}}
{{- define "substra-backend.images.name" -}}
    {{- $tag := (.img.tag | default .defaultTag) }}
    {{- if .img.registry -}}
    {{- printf "%s/%s:%s" .img.registry .img.repository $tag -}}
    {{- else -}}
    {{- printf "%s:%s" .img.repository $tag -}}
    {{- end -}}
{{- end -}}


{{- define "substra-backend.database.secret-name" -}}
    {{- if .Values.database.auth.credentialsSecretName -}}
        {{- .Values.database.auth.credentialsSecretName }}
    {{- else -}}
        {{- template "substra.fullname" . }}-database
    {{- end -}}
{{- end -}}

{{/*
The hostname we should connect to (external is defined, otherwise integrated)
*/}}
{{- define "substra-backend.database.host" -}}
    {{- if .Values.database.host }}
        {{- .Values.database.host }}
    {{- else }}
        {{- template "postgresql.v1.primary.fullname" .Subcharts.postgresql }}.{{ .Release.Namespace }}
    {{- end }}
{{- end -}}


{{/*
`wait-minio` container initialisation used inside of `initContainers`
*/}}
{{- define "common.waitMinIOContainer" -}}
{{- if .Values.minio.enabled }}
- name: wait-minio
  image: jwilder/dockerize:0.6.1
  command: ['dockerize', '-wait', 'tcp://{{ .Release.Name }}-minio:9000']
{{- end }}
{{- end -}}


{{/*
`wait-postgresql` container initialisation used inside of `initContainers`
*/}}
{{- define "common.waitPostgresqlInitContainer" -}}
- name: wait-postgresql
  image: postgres
  env:
   - name: PGUSER
     value: {{ .Values.database.auth.username }}
   - name: PGPASSWORD
     value: {{ .Values.database.auth.password }}
   - name: PGDATABASE
     value: {{ .Values.database.auth.database }}
  command: ['sh', '-c', 'until pg_isready --host={{ template "substra-backend.database.host" . }} --port={{ .Values.database.port }}; do echo "Waiting for postgresql service"; sleep 2; done;']
{{- end -}}

{{/*
'add-cert' container initialisation used inside of 'initContainers'
*/}}
{{- define "common.addCertInitContainer" -}}
{{- if .Values.privateCa.enabled }}
- name: add-cert
  image: {{ .Values.privateCa.image.repository }}
  imagePullPolicy: {{ .Values.privateCa.image.pullPolicy }}
  securityContext:
    runAsUser: 0
  command: ['sh', '-c']
  args:
  - |
    {{- if .Values.privateCa.image.apkAdd }}
    apt update
    apt install -y ca-certificates openssl
    {{- end }}
    update-ca-certificates && cp /etc/ssl/certs/* /tmp/certs/
  volumeMounts:
    - mountPath: /usr/local/share/ca-certificates/{{ .Values.privateCa.configMap.fileName }}
      name: private-ca
      subPath: {{ .Values.privateCa.configMap.fileName }}
    - mountPath: /tmp/certs/
      name: ssl-certs
{{- end }}
{{- end -}}
{{/*
  'wait-init-migrations' container initialisation used inside of 'initContainers'
*/}}
{{- define "common.waitInitMigrationsInitContainer" -}}
- name: wait-init-migrations
  image: {{ include "substra-backend.images.name" (dict "img" .Values.worker.events.image "defaultTag" $.Chart.AppVersion) }}
  command: ['bash', '/usr/src/app/wait-init-migration.sh']
  volumeMounts:
  - name: volume-wait-init-migrations
    mountPath: /usr/src/app/wait-init-migration.sh
    subPath: wait-init-migration.sh
  envFrom:
  - configMapRef:
      name: {{ include "substra.fullname" . }}-orchestrator
  - configMapRef:
      name: {{ include "substra.fullname" . }}-database
  - configMapRef:
      name: {{ include "substra.fullname" . }}-settings
  - secretRef:
      name: {{ include "substra-backend.database.secret-name" . }}
  env:
  - name: DJANGO_SETTINGS_MODULE
    value: backend.settings.{{ .Values.settings }}
{{- end -}}


{{/*
Define service URL based on MinIO or LocalStack enablement
*/}}
{{- define "substra-backend.objectStore.url" -}}
    {{- if .Values.minio.enabled -}}
        {{- printf "%s-minio:9000" .Release.Name -}}
    {{- else if .Values.localstack.enabled -}}
        {{- printf "%s-localstack:4566" .Release.Name -}}
    {{- end -}}
{{- end -}}


{{/*
Define objectstore access key based on MinIO or LocalStack enablement
*/}}
{{- define "substra-backend.objectStore.accessKey" -}}
    {{- if .Values.minio.enabled -}}
        {{- .Values.minio.auth.rootUser }}
    {{- else if .Values.localstack.enabled -}}
        {{- include "substra-backend.localstack.envValue" (dict "name" "AWS_ACCESS_KEY_ID" "context" .) -}}
    {{- end -}}
{{- end -}}

{{/*
Define objectstore secret key bassed on MinIO and Localstack enablemement
*/}}
{{- define "substra-backend.objectStore.secretKey" -}}
  {{- if .Values.minio.enabled -}}
        {{- .Values.minio.auth.rootPassword }}
    {{- else if .Values.localstack.enabled -}}
        {{- include "substra-backend.localstack.envValue" (dict "name" "AWS_SECRET_ACCESS_KEY" "context" .) -}}
    {{- end -}}
{{- end -}}

{{/*
Retrieve AWS environment variable value
*/}}
{{- define "substra-backend.localstack.envValue" -}}
{{- $envName := .name -}}
{{- $context := .context -}}
{{- $value := "" -}}
{{- range $context.Values.localstack.environment -}}
  {{- if eq .name $envName -}}
    {{- $value = .value -}}
  {{- end -}}
{{- end -}}
{{- $value -}}
{{- end -}}