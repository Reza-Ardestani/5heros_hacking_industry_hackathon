# DES-BB-STORAGE-1 — mirrored Timescale storage with local recovery

[Spec](../../../specs/features/timescale-sqlite-backends/requirements.md),
[diagram/ERD](../../diagrams/storage_failover.md).

The local SQLite file remains the durable write authority. SQLite triggers append
complete changed rows to an outbox in the same transaction as data writes. Existing
data receives a baseline snapshot when mirroring is first enabled. A source UUID
and monotonic SQLite sequence identify this writer history across processes/restarts.
REAL columns travel as round-trip decimal strings, converted back to doubles by
the mirror, because SQLite JSON1's default numeric formatting loses precision.

The PostgreSQL adapter owns a dedicated `bottleneck_busters` schema. It locks a
singleton source/checkpoint row, upserts or deletes rows in event order, then
advances the checkpoint in the same transaction. Non-keyed SQLite simulation
trials use their stable SQLite rowid as a mirror key. This preserves IDs and avoids
increment replay. A different source UUID cannot take over the same destination.
Acknowledgements update local replication state after remote commit. Retained
history covers both a lost acknowledgement and a lost/recreated destination.

Travel samples are partitioned on typed observation time in a Timescale hypertable;
a compatibility view retains the original five-column read contract. Original
Calgary local timestamps remain unchanged, with timezone conversion confined to
the physical partition column. Other existing table contracts remain unchanged.

Reads use the Timescale adapter after bounded replication has caught up. During
backoff, outage, replay backlog, or a read error, callers use fresh local SQLite.
Status records selected backend, pending events, last successful sync and a safe
error category. A failed SQLite commit is never acknowledged as a successful write.
An already-running adapter detects a missing destination schema and reinitializes
on its next retry. Recovery never fetches source datasets from the City.

The design deliberately avoids naive two independent writes: a crash between
those writes loses their relationship, and retrying additive operations can count
sightings or simulations twice. There is no automatic independent-host failover.
Both SQLite and Timescale need durable storage; journal history grows until a
separate retention design is implemented.

References: [TimescaleDB](https://github.com/timescale/timescaledb),
[psycopg transaction contexts](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).
