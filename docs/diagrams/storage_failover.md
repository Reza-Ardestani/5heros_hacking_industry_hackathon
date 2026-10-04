# D-BB-STORAGE-1 — storage flow and recovery keys

[Design](../design/timescale-sqlite/design.md),
[spec](../../specs/features/timescale-sqlite-backends/requirements.md).

```mermaid
flowchart LR
  Consumers[API / MCP / collectors] --> Store[Store facade]
  Store -->|atomic local writes| SQLite[(SQLite data + durable journal)]
  SQLite -->|ordered events| Mirror[Timescale adapter]
  Mirror -->|rows + checkpoint in one transaction| TS[(TimescaleDB)]
  Store -->|healthy and caught up reads| TS
  Store -->|outage or pending events| SQLite
  Store --> Status[Data status / visible frontend state]
```

```mermaid
erDiagram
  SQLITE_REPLICA_STATE ||--o{ SQLITE_REPLICA_EVENTS : identifies
  SQLITE_REPLICA_EVENTS }o--|| PG_REPLICA_STATE : advances
  SQLITE_REPLICA_STATE {
    integer singleton PK
    text source_id UK
    integer acknowledged_seq
    text last_sync_utc
  }
  SQLITE_REPLICA_EVENTS {
    integer seq PK
    text table_name
    text operation
    text row_json
  }
  PG_REPLICA_STATE {
    integer singleton PK
    text source_id UK
    bigint applied_seq
    timestamptz last_sync_utc
  }
  TRAVEL_TIME_SAMPLES {
    text segment PK
    text city_updated_local PK
    timestamptz observed_at PK
    text corridor
    double travel_time_min
    text fetched_utc
  }
```

Internal replication relationships cross database boundaries; they are logical
relationships, not cross-database foreign keys. Domain tables retain existing keys;
simulation trial mirrors add `replica_rowid` to identify otherwise unkeyed rows.
