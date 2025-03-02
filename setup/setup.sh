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

# Logstash writes with its own user, which can only append documents to
# logs-* data streams.
echo "Creating the logstash_writer role and user"
es PUT /_security/role/logstash_writer "$(cat /setup/logstash-writer-role.json)"
es PUT /_security/user/logstash_writer \
  "{\"password\": \"${LOGSTASH_WRITER_PASSWORD}\", \"roles\": [\"logstash_writer\"], \"full_name\": \"Logstash writer\"}"

# logs-*-* data streams use Elasticsearch's built-in "logs" index template,
# which pulls in a logs@custom component template if one exists. Pointing
# that at our ILM policy sets retention for every logs data stream.
echo "Creating the retention policy"
es PUT /_ilm/policy/logs-14d "$(cat /setup/ilm-policy.json)"
es PUT /_component_template/logs@custom \
  '{"template": {"settings": {"index.lifecycle.name": "logs-14d"}}}'

echo "Setup complete"
