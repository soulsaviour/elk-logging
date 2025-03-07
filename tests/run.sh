#!/usr/bin/env bash
# Runs tests/sample-events.jsonl through logstash/pipeline/20-filter.conf and
# checks the parsed events. Uses the Logstash Docker image by default; set
# LOGSTASH=/path/to/bin/logstash to use a local install.
set -euo pipefail
cd "$(dirname "$0")/.."

version=$(grep '^STACK_VERSION=' .env.example | cut -d= -f2)
out=$(mktemp)
trap 'rm -f "$out"' EXIT

if [[ -n "${LOGSTASH:-}" ]]; then
  work=$(mktemp -d)
  cp logstash/pipeline/20-filter.conf tests/io.conf "$work/"
  TEST_OUTPUT="$out" "$LOGSTASH" --path.data "$work/data" -f "$work" --log.level=error \
    < tests/sample-events.jsonl > /dev/null
  rm -rf "$work"
else
  docker run --rm -i \
    -v "$PWD/logstash/pipeline/20-filter.conf:/test/20-filter.conf:ro" \
    -v "$PWD/tests/io.conf:/test/io.conf:ro" \
    --entrypoint bash "docker.elastic.co/logstash/logstash:${version}" \
    -c 'logstash -f /test --log.level=error > /dev/null && cat /tmp/logstash-test-output.jsonl' \
    < tests/sample-events.jsonl > "$out"
fi

python3 tests/check_output.py "$out"
