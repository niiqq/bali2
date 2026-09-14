# scheduled

A small scheduled job. It reads a list of entries from the `CONFIG` secret,
requests each endpoint, and opens an issue when an entry's flag reads true.

## Configuration

Set the repository secret `CONFIG` to a JSON array. Each entry has:

- `u` — the endpoint to request, used exactly as given
- `f` — the path to the boolean flag in the response

A path is a dotted list of keys. A key ending in `[]` steps into a list and
tests every element.

```json
[{"u": "https://example.com/a.json", "f": "items[].ready"}]
```

## Run

The job runs on a schedule. You can also start it by hand from the Actions tab.
