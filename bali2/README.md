# scheduled

A small scheduled job. It reads a list of endpoints from the `CONFIG` secret,
requests each one, and opens an issue when an endpoint reports an available
state.

## Configuration

Set the repository secret `CONFIG` to a JSON array of endpoint URLs.

## Run

The job runs on a schedule. You can also start it by hand from the Actions tab.
