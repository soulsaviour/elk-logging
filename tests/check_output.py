"""Asserts on the events Logstash produced from tests/sample-events.jsonl."""

import json
import sys


def main(path: str) -> None:
    with open(path) as fh:
        events = [json.loads(line) for line in fh]
    assert len(events) == 5, f"expected 5 events, got {len(events)}"

    def find(prefix: str) -> dict:
        matches = [e for e in events if e["message"].startswith(prefix)]
        assert len(matches) == 1, f"expected one event starting {prefix!r}"
        return matches[0]

    get = find("203.0.113.7 ")
    assert get["@timestamp"] == "2026-10-29T10:15:32.000Z", get["@timestamp"]
    assert get["source"]["address"] == "203.0.113.7"
    assert get["http"]["request"]["method"] == "GET"
    assert get["http"]["response"]["status_code"] == 200
    assert get["url"]["original"] == "/items?page=2"
    assert get["user_agent"]["name"] == "Firefox"
    assert get["data_stream"]["dataset"] == "nginx.access"
    assert "timestamp" not in get and "log_source" not in get

    post = find("198.51.100.23 ")
    assert post["http"]["response"]["status_code"] == 502
    assert post["user"]["name"] == "alice"

    broken = find("this is not")
    assert "_grokparsefailure_nginx" in broken["tags"]
    assert broken["data_stream"]["dataset"] == "nginx.access"

    app = find('{"time"')
    assert app["@timestamp"] == "2026-10-29T10:16:00.123Z", app["@timestamp"]
    assert app["log"]["level"] == "error"
    assert app["app"]["order_id"] == "A-1042"
    assert app["data_stream"]["dataset"] == "app"

    not_json = find("plain text")
    assert "_jsonparsefailure_app" in not_json["tags"]

    print(f"OK: {len(events)} events parsed as expected")


if __name__ == "__main__":
    main(sys.argv[1])
