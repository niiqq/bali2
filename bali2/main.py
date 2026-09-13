#!/usr/bin/env python3
"""Scheduled endpoint probe.

Reads a JSON array of endpoints from the CONFIG environment variable and
reports which of them return an available state.

Endpoints are referenced by position only. No endpoint value is ever written
to stdout or to the output file.
"""

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

OUT_FILE = pathlib.Path(__file__).resolve().parent / "hits.json"
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (compatible; probe/1.0)"


def endpoint(url: str) -> str:
    url = url.split("?")[0].split("#")[0].rstrip("/")
    if url.endswith(".js") or url.endswith(".json"):
        return url
    return url + ".js"


def fetch(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def reason(error) -> str:
    """A short error label that cannot contain the endpoint value."""
    if isinstance(error, urllib.error.HTTPError):
        return "http {}".format(error.code)
    return type(error).__name__


def main() -> int:
    raw = os.environ.get("CONFIG", "").strip()
    if not raw:
        print("CONFIG is empty", file=sys.stderr)
        return 1

    try:
        items = json.loads(raw)
    except ValueError:
        print("CONFIG is not valid JSON", file=sys.stderr)
        return 1

    if not isinstance(items, list) or not items:
        print("CONFIG must be a non-empty JSON array", file=sys.stderr)
        return 1

    hits = []
    failures = 0

    for index, url in enumerate(items, start=1):
        try:
            data = fetch(endpoint(url))
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
            failures += 1
            print("[{}] error: {}".format(index, reason(error)))
            continue

        if any(v.get("available") for v in data.get("variants", [])):
            hits.append(index)
            print("[{}] hit".format(index))
        else:
            print("[{}] ok".format(index))

    OUT_FILE.write_text(json.dumps(hits))

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as handle:
            handle.write("found={}\n".format("true" if hits else "false"))

    if failures == len(items):
        print("all endpoints failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
