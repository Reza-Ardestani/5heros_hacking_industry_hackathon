# S-BB-STORAGE-1 — TimescaleDB with durable SQLite fallback

User authorized October 4, 2026 on `codex/timescale-sqlite-backends`, based on
main `0a0d4ab`. Constitution updated before implementation. The user's direction
settles adding TimescaleDB while keeping SQLite usable through outages.

Stories: [DATA-2](../../../UJ_US/User_Journey_3/User_Stories/DATA-2/story.md),
[DASH-1](../../../UJ_US/User_Journey_2/User_Stories/DASH-1/story.md).
Design: [DES-BB-STORAGE-1](../../../docs/design/timescale-sqlite/design.md).
Diagram: [D-BB-STORAGE-1](../../../docs/diagrams/storage_failover.md).

## Decisions and requirements

- FR-1 Existing SQLite mode remains the default; explicit Timescale mode requires
  a valid PostgreSQL URL. API, MCP, collector, forecast, and simulation persistence
  use the same Store methods; no changes to numerical models.
- FR-2 Every acknowledged write commits to SQLite, together with row-change
  journal entries. SQLite disk/transaction failure fails the write. PostgreSQL
  failure cannot undo a completed local write or falsely report lost collection.
- FR-3 Mirror all current data tables. Convert measured travel-time observations
  to a real Timescale hypertable using `observed_at TIMESTAMPTZ`. Preserve original
  City local timestamp text and return shapes. Calgary local times without offsets
  use America/Edmonton; ambiguous fall-back times use the first occurrence.
- FR-4 Persist source UUID and increasing event sequence locally. PostgreSQL
  locks its source checkpoint, applies ordered changes and advances the checkpoint
  atomically. Replays after lost acknowledgements must not duplicate sightings,
  predictions, actions, or trial rows. Different local source UUIDs are rejected.
- FR-5 Bootstrap existing SQLite data from local rows, never City downloads.
  Retain journal history so a lost/new empty Timescale destination can be rebuilt.
  Journal compaction/retention is future work; persistent SQLite disk is required.
- FR-6 Serve Timescale reads only when its checkpoint has caught up with local
  committed writes. On connection/query/replay failure or pending backlog, serve
  SQLite with explicit active backend, health, pending count, last sync, sanitized
  failure category, and retry delay. Use bounded connections/statements, backoff,
  and deterministic retries. Recover automatically on subsequent reads/writes.
- FR-7 Publish storage status through existing data-status API/MCP and a visible
  frontend status indicator. Do not expose passwords, DSNs, or raw provider errors.
- FR-8 Provide a pinned Timescale container, healthcheck, named persistent volume,
  configuration example, offline sync CLI, deployment/recovery instructions.

## Acceptance

AC-1 SQLite tests and full existing backend suite pass without Timescale configuration.
AC-2 Real Timescale reads match SQLite across incidents, closures, references,
travel times, forecasts, simulation actions/alternatives/trials, and estimates.
AC-3 Existing populated SQLite bootstraps without a City API call; travel samples
are listed as a hypertable with a typed time partition.
AC-4 Stop Timescale, continue reading/writing, restart app and database, replay,
and verify no loss or duplicates, including the remote-commit/local-ack crash window.
AC-5 Local rollback leaves neither domain data nor journal events. Concurrent
processes sharing one SQLite file converge; a different source cannot overwrite
the destination. An empty recreated destination can rebuild from retained events.
AC-6 Status identifies fallback and queued writes; synthetic credentials in errors
never appear in status. Frontend build and focused indicator test pass.
AC-7 Container replacement with the same named volume retains the data.

## Bounds

Single shared SQLite volume for all writers; independent server replicas unsupported.
SQLite is the durable write authority; Timescale is the preferred analytical/read
backend when caught up. Direct writes to the mirror are unsupported. Neither this
feature nor a successful container test deploys the public demo. No RL, automatic
City infrastructure control, new resource providers, or guaranteed latency claim.
