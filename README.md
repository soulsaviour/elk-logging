# elk-logging

A self-contained ELK stack with Docker Compose: Filebeat ships log files,
Logstash parses them, Elasticsearch stores them in data streams with a
retention policy, and Kibana is ready with data views. Security is on from
the start, and every component has its own credentials.

```
log files ──▶ Filebeat ──▶ Logstash ──▶ Elasticsearch ──▶ Kibana
                           (parse,       logs-nginx.access-default
                            route)       logs-app-default
```

## Quick start

```bash
cp .env.example .env              # set the passwords
docker compose --profile demo up -d
```

Open Kibana at http://localhost:5601 and log in as `elastic`. The `demo`
profile adds a generator writing nginx access logs and JSON application logs,
so **Discover** has data within a minute. Leave the profile off to ship your
own logs.

Elasticsearch (9200) and Kibana (5601) are published on localhost only.

## What's in it

| Service | Role |
|---------|------|
| `elasticsearch` | Single node, security enabled |
| `setup` | One-shot: sets the `kibana_system` password, creates the `logstash_writer` role and user, the ILM policy and the `logs@custom` template |
| `kibana` | Logs in as `kibana_system` |
| `kibana-setup` | One-shot: creates data views for each data stream |
| `logstash` | Beats input on 5044, parses and routes events |
| `filebeat` | Tails log files, remembers its position across restarts |
| `log-generator` | Demo traffic (`demo` profile only) |

## Parsing

Each Filebeat input sets `log_source`, and `logstash/pipeline/20-filter.conf`
picks a parser from it:

- **nginx** access logs go through grok into ECS fields
  (`source.address`, `http.request.method`, `url.original`,
  `http.response.status_code`, `user_agent.*`), with `@timestamp` taken from
  the log line rather than the time it was read.
- **app** logs are JSON. They're parsed under `app.*`, the level is moved to
  `log.level` and the event time becomes `@timestamp`.

Lines that don't parse are kept with a `_grokparsefailure_nginx` or
`_jsonparsefailure_app` tag, so bad input is easy to find instead of being
dropped.

## Storage and retention

Logstash writes to data streams (`logs-nginx.access-default`,
`logs-app-default`), which use Elasticsearch's built-in `logs` index template.
That template includes a `logs@custom` component template if one exists, and
setup creates one pointing at the `logs-14d` ILM policy: roll over daily or at
10 GB per primary shard, delete after 14 days. Change
`setup/ilm-policy.json` to keep logs longer.

## Security

- The `elastic` superuser is only used by the setup jobs and for logging in.
- Kibana uses the built-in `kibana_system` user.
- Logstash writes as `logstash_writer`, whose role can only create documents
  in `logs-*-*` data streams. It can't read, delete or touch other indices.
- Passwords live in `.env`, which git ignores.

HTTP inside the Compose network is plain. Before exposing the stack, put TLS
in front of Kibana and Elasticsearch, or turn on
`xpack.security.http.ssl`.

## Shipping logs from other hosts

Publish Logstash's port (`"5044:5044"` under `logstash`), install Filebeat on
the host, and reuse `filebeat/filebeat.yml` with your log paths and
`output.logstash.hosts` pointing at this machine.

## Tests

`tests/run.sh` feeds `tests/sample-events.jsonl` (good and malformed nginx
lines, JSON and non-JSON app lines) through the real filter in the Logstash
image and checks the parsed fields, timestamps, tags and target data streams:

```bash
tests/run.sh
```

CI runs that, a config test of the full pipeline, Filebeat's config test,
`docker compose config` and shellcheck.
