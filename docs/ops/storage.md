# TimescaleDB and durable SQLite fallback

[Architecture](../design/timescale-sqlite/design.md),
[spec](../../specs/features/timescale-sqlite-backends/requirements.md).

## Local setup

1. Run `make setup`. Docker must be running.
2. Copy `.env.timescale.example` to `.env.timescale`. Replace both password
   placeholders with the same generated password using URL-safe characters.
   The file is ignored by Git and excluded from Docker build contexts.
3. Run `make db-up`. This starts TimescaleDB 2.23.1/PostgreSQL 17 on loopback
   port 5433 with a healthcheck and named `timescale_data` volume. The default
   configuration limits PostgreSQL to 30 connections and 128 MB shared buffers;
   shared buffers are not its total RAM limit.
4. Run `make db-sync`. The command imports existing SQLite rows and retained
   changes in up to 100 batches without calling City APIs. A nonzero exit means
   unavailable database or remaining backlog; rerun after resolving the cause.
5. Run `make dev-timescale`. API, MCP and collector processes must use the same
   environment and SQLite path. Relative `BB_DB_PATH` resolves from repository
   root; use an absolute path when mounting a production volume.

The existing `make dev` and `make api` commands stay in SQLite mode unless their
environment already sets Timescale variables. The frontend needs no database
credentials. API and MCP status return backend, health, queued events, last sync
and sanitized failure categories. The Intersections view polls this status.

For individual processes, from repository root:

```sh
cd backend
uv run --env-file ../.env.timescale uvicorn app.api:app --host 127.0.0.1 --port 8008
# Separate terminal, same backend directory:
uv run --env-file ../.env.timescale python ../scripts/collect_disruptions.py --every 300
# Separate terminal, same backend directory:
uv run --env-file ../.env.timescale python -m app.mcp_server --transport streamable-http --host 127.0.0.1 --port 8000
```

## Persistence and recovery

Every successful write commits domain data and a row-change log to SQLite in the
same transaction. Timescale receives ordered upserts/deletes and an atomic
checkpoint. Reads use it only when synchronized; otherwise SQLite supplies data.
Replaying a remotely committed batch after a lost local acknowledgement is safe.

Stop/start or replace the Timescale service with the same named volume to retain
its data. `docker compose --env-file .env.timescale -f compose.timescale.yml down`
preserves that volume. `down -v` deletes it and must not be used for routine updates.
Changing the configured password after initialization does not rotate an existing
PostgreSQL user's password; update that user separately before changing the URL.

Keep the **entire SQLite directory**, including any `-wal` and `-shm` files, on
durable storage. Use SQLite's online backup API for a live backup; copying only the
database file during writes can omit committed WAL changes. Back up Timescale too.
Retained local events rebuild an empty Timescale destination without City downloads.
Do not replace SQLite with a fresh file while pointing at an existing mirror: its
new source identity is rejected to prevent independent histories overwriting data.

Failure retries start at five seconds and double up to sixty. Connections time out
after two seconds; statements and lock waits are bounded. Each call replays at most
1,000 events, then uses local data if still behind. `make db-sync` drains larger
backlogs. Catch-up is driven by reads, writes or this command, not a daemon.
Recovery history is retained indefinitely; monitor SQLite disk growth. Journal
compaction, independent-host failover and recovery from a lost SQLite authority
are outside this feature.

`db_bytes` reports the whole PostgreSQL database in primary mode; `sqlite_bytes`
reports the local database file, excluding transient WAL/SHM allocation. Neither is
a RAM metric. Travel history is the real `travel_time_samples` hypertable; a
`travel_time_obs` view preserves existing API fields. Other domain timestamp text
contracts remain unchanged.

## Hosted deployment limits

The existing app image includes the adapter but does not provision Timescale or
mount either database volume. For a single persistent host, mount the SQLite
directory, provide the PostgreSQL URL as a secret and use a persistent Timescale
service reachable by that host. A container's `127.0.0.1` refers to that container;
use the database service's address when the app runs in another container.

A Codespace restart preserves its workspace; deleting/rebuilding it is not a
backup strategy. Do not enable this mode on Cloud Run or AgentCore with independent
ephemeral SQLite replicas. A durable shared-authority design is needed there.
This branch has not deployed or modified the public demo.

## Verification

```sh
cd backend
uv run pytest -q
BB_TEST_TIMESCALE=1 uv run pytest -q tests/test_timescale_integration.py
```

The second command requires Docker and creates disposable containers/volumes with
random identifiers. Only those test resources are removed. It verifies real SUMO
history parity, a real hypertable, outage/restart/replay, a lost acknowledgement,
transaction rollback, concurrent processes, source rejection, empty destination
rebuild and persistence through container replacement. No City downloads required.
