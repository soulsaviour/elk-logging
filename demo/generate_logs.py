"""Writes nginx access logs and JSON application logs for demos.

python generate_logs.py --out /var/log/demo --rate 5
"""

import argparse
import json
import random
import time
from datetime import UTC, datetime
from pathlib import Path

PATHS = ["/", "/items", "/items?page=2", "/items/sku-1001", "/cart", "/checkout", "/login"]
METHODS = ["GET"] * 8 + ["POST"] * 2
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "curl/8.10.1",
]
# Mostly healthy traffic with some redirects, misses and server errors.
STATUSES = [200] * 85 + [301] * 3 + [404] * 7 + [500] * 3 + [502] * 2
APP_EVENTS = {
    "info": ["order placed", "payment captured", "cache refreshed"],
    "warn": ["slow query", "retrying payment provider"],
    "error": ["payment provider timeout", "inventory lookup failed"],
}


def nginx_line(now: datetime) -> str:
    status = random.choice(STATUSES)
    size = random.randint(200, 50_000) if status == 200 else random.randint(100, 600)
    return (
        f"203.0.113.{random.randint(1, 254)} - - [{now:%d/%b/%Y:%H:%M:%S +0000}] "
        f'"{random.choice(METHODS)} {random.choice(PATHS)} HTTP/1.1" {status} {size} '
        f'"-" "{random.choice(AGENTS)}"'
    )


def app_line(now: datetime) -> str:
    level = random.choices(list(APP_EVENTS), weights=[90, 7, 3])[0]
    event = {
        "time": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "level": level,
        "msg": random.choice(APP_EVENTS[level]),
        "order_id": f"A-{random.randint(1000, 9999)}",
        "duration_ms": random.randint(5, 400) if level == "info" else random.randint(800, 30_000),
    }
    return json.dumps(event)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="/var/log/demo")
    parser.add_argument("--rate", type=float, default=5.0, help="lines per second per log")
    parser.add_argument("--count", type=int, default=0, help="stop after N lines (0 = forever)")
    args = parser.parse_args()

    nginx_log = Path(args.out, "nginx", "access.log")
    app_log = Path(args.out, "app", "app.log")
    for path in (nginx_log, app_log):
        path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with nginx_log.open("a", buffering=1) as nginx, app_log.open("a", buffering=1) as app:
        while args.count == 0 or written < args.count:
            now = datetime.now(UTC)
            nginx.write(nginx_line(now) + "\n")
            app.write(app_line(now) + "\n")
            written += 1
            time.sleep(1 / args.rate)


if __name__ == "__main__":
    main()
