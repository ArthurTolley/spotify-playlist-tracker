{{- define "spotify-tracker.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "spotify-tracker.labels" -}}
app.kubernetes.io/name: spotify-tracker
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "spotify-tracker.backendSecretName" -}}
{{- if .Values.secrets.existingSecret -}}
{{ .Values.secrets.existingSecret }}
{{- else -}}
{{ include "spotify-tracker.fullname" . }}-secrets
{{- end -}}
{{- end -}}

{{- define "spotify-tracker.postgresPassword" -}}
{{- if .Values.postgresql.auth.password -}}
{{- if eq .Values.postgresql.auth.password "REPLACE_WITH_SECURE_PASSWORD" -}}
{{- fail "postgresql.auth.password is placeholder — replace with a secure password and keep it in sync with DATABASE_URL in spotify-tracker-secrets" -}}
{{- end -}}
{{ .Values.postgresql.auth.password }}
{{- else -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace (printf "%s-postgres" (include "spotify-tracker.fullname" .)) -}}
{{- if $existing -}}
{{- index $existing.data "POSTGRES_PASSWORD" | b64dec -}}
{{- else -}}
{{- if .Values.secrets.existingSecret -}}
{{- fail "postgresql.auth.password is required when postgresql.enabled and secrets.existingSecret is set — set it and make DATABASE_URL use the same password" -}}
{{- end -}}
{{ randAlphaNum 24 }}
{{- end -}}
{{- end -}}
{{- end -}}
