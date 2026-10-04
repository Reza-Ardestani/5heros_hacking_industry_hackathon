# Implementation plan

1. Preserve SQLite Store behavior as an adapter. Add atomic outbox triggers,
   stable source identity, baseline snapshot, and rollback tests.
2. Add psycopg and Timescale schema/read adapter, typed hypertable plus compatible
   read view, ordered transactional replication, source guards, retry/backoff.
3. Introduce Store facade; shared consumers select healthy primary or local
   fallback, and status exposes backlog/freshness without credentials.
4. Add persistent Timescale Compose service, environment example, offline sync
   CLI, and operating instructions. Document both persistent-volume boundaries.
5. Verify real container parity, outage/offline restart/replay, lost-ack replay,
   rollback, destination recreation, competing source rejection, persistence.
6. Add frontend storage state; run full backend suite, targeted UI tests/build,
   scoped lint/link checks. Update evidence with exact commands/results/limits.

No external deployment, commit, push, or merge included in this implementation request.
