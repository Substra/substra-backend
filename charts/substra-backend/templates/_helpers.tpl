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
Return the appropriate apiVersion for PodSecurityPolicy.
*/}}
{{- define "podsecuritypolicy.apiVersion" -}}
{{- if semverCompare ">=1.14-0" .Capabilities.KubeVersion.GitVersion -}}
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
Redefine the postgresql service name because we can't use subchart templates directly.
*/}}
{{- define "postgresql.serviceName" -}}
{{- $name := default "postgresql" .Values.postgresql.nameOverride -}}
{{- $fullname := default (printf "%s-%s" .Release.Name $name) .Values.postgresql.fullnameOverride -}}
{{- if .Values.postgresql.replication.enabled -}}
{{- printf "%s-%s" $fullname "primary" | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" $fullname | trunc 63 | trimSuffix "-" }}
{{- end -}}
{{- end -}}


{{/*
Redefine the rabbitmq service name because we can't use subchart templates directly.
*/}}
{{- define "rabbitmq.serviceName" -}}
{{- if .Values.rabbitmq.fullnameOverride -}}
{{- .Values.rabbitmq.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default "rabbitmq" .Values.rabbitmq.nameOverride -}}
{{- if contains $name (printf "%s" .Release.Name) -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}
