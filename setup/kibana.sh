#!/usr/bin/env bash
# Creates Kibana data views for the log data streams. Idempotent.
set -euo pipefail

KB=http://kibana:5601

create_data_view() {
  local id=$1 pattern=$2 name=$3
  curl -fsS -u "elastic:${ELASTIC_PASSWORD}" -X POST "${KB}/api/data_views/data_view" \
    -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
    -d "{\"override\": true, \"data_view\": {\"id\": \"${id}\", \"title\": \"${pattern}\", \"name\": \"${name}\", \"timeFieldName\": \"@timestamp\"}}" \
    > /dev/null
  echo "Data view ready: ${name} (${pattern})"
}

create_data_view nginx-access 'logs-nginx.access-*' 'nginx access logs'
create_data_view app-logs 'logs-app-*' 'Application logs'
