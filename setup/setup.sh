#!/usr/bin/env bash
# Runs once per `docker compose up`, after Elasticsearch is healthy. Every
# call is idempotent, so re-running is safe.
set -euo pipefail

ES=http://elasticsearch:9200

es() {
  local method=$1 path=$2 body=${3:-}
  local args=(-fsS -u "elastic:${ELASTIC_PASSWORD}" -X "$method" -H 'Content-Type: application/json')
  if [[ -n "$body" ]]; then
    args+=(-d "$body")
  fi
  curl "${args[@]}" "${ES}${path}"
  echo
}

echo "Setting the kibana_system password"
es POST /_security/user/kibana_system/_password \
  "{\"password\": \"${KIBANA_SYSTEM_PASSWORD}\"}"

echo "Setup complete"
