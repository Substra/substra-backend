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


{{- define "substra-backend.postgresql.secret-name" -}}
    {{- if .Values.postgresql.auth.credentialsSecretName -}}
        {{- .Values.postgresql.auth.credentialsSecretName }}
    {{- else -}}
        {{- template "substra.fullname" . }}-database
    {{- end -}}
{{- end -}}

{{/*
The hostname we should connect to (external is defined, otherwise integrated)
*/}}
{{- define "substra-backend.postgresql.host" -}}
    {{- if .Values.postgresql.host }}
        {{- .Values.postgresql.host }}
    {{- else }}
        {{- template "postgresql.primary.fullname" (index .Subcharts "integrated-postgresql") }}.{{ .Release.Namespace }}
    {{- end }}
{{- end -}}