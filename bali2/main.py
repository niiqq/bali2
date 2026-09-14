#!/usr/bin/env python3
"""Scheduled endpoint probe.

Reads a JSON array of entries from the CONFIG environment variable. Each entry
has two fields:

    u  the endpoint to request, used exactly as given
    f  a path to the boolean flag inside the JSON response

A path is a dotted list of keys. A key that ends with "[]" means "step into
this list and test every element". An empty key before "[]" means the value at
that point is itself the list. Examples:

    "nodes[].ready"   ->  {"nodes": [{"ready": true}]}
    "[].active"       ->  [{"active": true}]
    "data.item.flag"  ->  {"data": {"item": {"flag": true}}}

An entry is a hit when any value the path resolves to is true.

Entries are referenced by position only. No entry value is ever written to
stdout or to the output file.
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


def fetch(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve(node, parts):
    """Return every value the remaining path parts reach. Never raises."""
    if not parts:
        return [node]

    head, rest = parts[0], parts[1:]

    if head.endswith("[]"):
        key = head[:-2]
        if key:
            if not isinstance(node, dict):
                return []
            node = node.get(key)
        if not isinstance(node, list):
            return []
        found = []
        for element in node:
            found.extend(resolve(element, rest))
        return found

    if not isinstance(node, dict) or head not in node:
        return []
    return resolve(node[head], rest)


def is_hit(data, flag_path: str) -> bool:
    return any(bool(v) for v in resolve(data, flag_path.split(".")))


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
        entries = json.loads(raw)
    except ValueError:
        print("CONFIG is not valid JSON", file=sys.stderr)
        return 1

    if not isinstance(entries, list) or not entries:
        print("CONFIG must be a non-empty JSON array", file=sys.stderr)
        return 1

    hits = []
    failures = 0

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or "u" not in entry or "f" not in entry:
            failures += 1
            print("[{}] error: entry needs both u and f".format(index))
            continue

        try:
            data = fetch(entry["u"])
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
            failures += 1
            print("[{}] error: {}".format(index, reason(error)))
            continue

        if is_hit(data, entry["f"]):
            hits.append(index)
            print("[{}] hit".format(index))
        else:
            print("[{}] ok".format(index))

    OUT_FILE.write_text(json.dumps(hits))

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as handle:
            handle.write("found={}\n".format("true" if hits else "false"))

    if failures:
        print(
            "{} of {} entries failed".format(failures, len(entries)),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
