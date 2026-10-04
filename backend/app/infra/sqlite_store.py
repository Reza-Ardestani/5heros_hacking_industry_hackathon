"""SQLite store for Calgary disruption data (single local file, standard library only).

Tables
- fetch_runs        one row per dataset download: URL, SHA256, rows, inserted/updated, errors
- incidents         deduplicated incidents (parsed record JSON + raw City row + live sightings)
- closures          closures ever seen, with first/last seen and when they left the City feed
- travel_time_obs   travel-time time series (one row per segment per City update)
- reference_layers  latest cameras/signals/volumes/projects rows
- predictions       forecasts generated via API/MCP, kept for later scoring
- meta              schema version, road aliases, window settings
- sim_runs          one row per simulation study (scenario, decision, summary, status)
- sim_actions       every agent action/tool call in a study, in order (the action log)
- sim_alternatives  every option tested in a study with metrics and rejection reasons
- sim_trials        every individual SUMO run (option x seed x demand factor)
- intersection_estimates  cached modeled seconds-of-delay per intersection incident

WAL mode lets the API/MCP server read while the collector writes.
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = ROOT / "data" / "db" / "disruptions.sqlite"
SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS fetch_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job TEXT NOT NULL, dataset_key TEXT NOT NULL, dataset TEXT, url TEXT,
  started_utc TEXT NOT NULL, finished_utc TEXT, status TEXT NOT NULL,
  rows INTEGER, sha256 TEXT, inserted INTEGER DEFAULT 0, updated INTEGER DEFAULT 0, error TEXT
);
CREATE TABLE IF NOT EXISTS incidents (
  uid TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  start_utc TEXT NOT NULL, start_local TEXT NOT NULL, last_update_utc TEXT,
  first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL,
  live_first_seen_utc TEXT, live_last_seen_utc TEXT, live_sightings INTEGER NOT NULL DEFAULT 0,
  category_group TEXT, category TEXT, lane_position TEXT, travel_direction TEXT,
  quadrant TEXT, corridor_key TEXT, intersection_key TEXT, latitude REAL, longitude REAL,
  record_json TEXT NOT NULL, raw_json TEXT
);
CREATE INDEX IF NOT EXISTS ix_incidents_start ON incidents(start_local);
CREATE INDEX IF NOT EXISTS ix_incidents_corridor ON incidents(corridor_key, start_local);
CREATE INDEX IF NOT EXISTS ix_incidents_intersection ON incidents(intersection_key, start_local);
CREATE TABLE IF NOT EXISTS closures (
  uid TEXT PRIMARY KEY,
  location_text TEXT, start_local TEXT, end_local TEXT, closure_type TEXT, corridor_key TEXT,
  latitude REAL, longitude REAL,
  first_seen_utc TEXT NOT NULL, last_seen_utc TEXT NOT NULL, removed_from_feed_utc TEXT,
  record_json TEXT NOT NULL, raw_json TEXT
);
CREATE INDEX IF NOT EXISTS ix_closures_dates ON closures(start_local, end_local);
CREATE TABLE IF NOT EXISTS travel_time_obs (
  segment TEXT NOT NULL, corridor TEXT, city_updated_local TEXT NOT NULL,
  travel_time_min REAL, fetched_utc TEXT NOT NULL,
  PRIMARY KEY (segment, city_updated_local)
);
CREATE TABLE IF NOT EXISTS reference_layers (
  name TEXT PRIMARY KEY, fetched_utc TEXT NOT NULL, sha256 TEXT, rows_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sim_runs (
  id TEXT PRIMARY KEY, created_utc TEXT NOT NULL, finished_utc TEXT, status TEXT NOT NULL,
  origin TEXT, intersection_key TEXT, scenario_json TEXT NOT NULL, simulator_version TEXT,
  recommended_id TEXT, lowest_delay_id TEXT, decision_json TEXT, summary_json TEXT,
  error TEXT, log_path TEXT
);
CREATE TABLE IF NOT EXISTS sim_actions (
  run_id TEXT NOT NULL, seq INTEGER NOT NULL, at_utc TEXT, agent TEXT, action TEXT,
  detail TEXT, evidence_json TEXT, PRIMARY KEY (run_id, seq)
);
CREATE TABLE IF NOT EXISTS sim_alternatives (
  run_id TEXT NOT NULL, alt_id TEXT NOT NULL, label TEXT, params_json TEXT,
  capital_cost_cad REAL, mean_delay_s REAL, total_delay_s REAL, cross_delay_change_pct REAL,
  delay_reduction_pct REAL, feasible INTEGER, rejection_json TEXT, recommended INTEGER,
  lowest_delay INTEGER, metrics_json TEXT, PRIMARY KEY (run_id, alt_id)
);
CREATE TABLE IF NOT EXISTS sim_trials (
  run_id TEXT NOT NULL, alt_id TEXT NOT NULL, purpose TEXT NOT NULL, seed INTEGER,
  demand_factor REAL, demand_sha256 TEXT, network_sha256 TEXT, metrics_json TEXT,
  condition TEXT
);
CREATE INDEX IF NOT EXISTS ix_sim_trials_run ON sim_trials(run_id, alt_id);
CREATE TABLE IF NOT EXISTS intersection_estimates (
  intersection_key TEXT NOT NULL, params_sha256 TEXT NOT NULL, computed_utc TEXT NOT NULL,
  result_json TEXT NOT NULL, PRIMARY KEY (intersection_key, params_sha256)
);
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL, origin TEXT,
  selection_json TEXT NOT NULL, forecast_start TEXT, horizon_days INTEGER,
  expected_total REAL, interval_lo INTEGER, interval_hi INTEGER, result_json TEXT NOT NULL
);
"""

INCIDENT_COLUMNS = (
    "category_group", "category", "lane_position", "travel_direction",
    "quadrant", "corridor_key", "intersection_key", "latitude", "longitude",
)  # fmt: skip


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


class SQLiteStore:
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get("BB_DB_PATH") or DEFAULT_PATH)
        if path is None and not self.path.is_absolute():
            self.path = ROOT / self.path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        with self.connect() as db:
            db.executescript(SCHEMA)
            trial_cols = {r[1] for r in db.execute("PRAGMA table_info(sim_trials)")}
            if "condition" not in trial_cols:
                db.execute("ALTER TABLE sim_trials ADD COLUMN condition TEXT")
            db.execute(
                "INSERT INTO meta VALUES ('schema_version', ?) ON CONFLICT(key) DO UPDATE"
                " SET value=excluded.value",
                (str(SCHEMA_VERSION),),
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def display_path(self):
        """Repository-relative path when possible, so exports never embed local user paths."""
        try:
            return self.path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return self.path.name

    # ----------------------------------------------------------------- meta
    def get_meta(self, key, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set_meta(self, key, value):
        with self.connect() as db:
            db.execute(
                "INSERT INTO meta VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )

    def version(self):
        """Changes whenever data is written; readers use it to invalidate caches."""
        with self.connect() as db:
            row = db.execute(
                "SELECT CAST((SELECT COUNT(*) FROM fetch_runs) AS TEXT) || ':' ||"
                " (SELECT COALESCE(MAX(last_seen_utc), '') FROM incidents) || ':' ||"
                " CAST((SELECT COUNT(*) FROM incidents) AS TEXT) || ':' ||"
                " CAST((SELECT COUNT(*) FROM closures) AS TEXT)"
            ).fetchone()
        return row[0]

    # ----------------------------------------------------------------- runs
    def start_run(self, job, dataset_key, dataset=None):
        with self.connect() as db:
            cur = db.execute(
                "INSERT INTO fetch_runs(job, dataset_key, dataset, started_utc, status)"
                " VALUES (?, ?, ?, ?, 'running')",
                (job, dataset_key, dataset, utc_now()),
            )
            return cur.lastrowid

    def finish_run(self, run_id, status, meta=None, inserted=0, updated=0, error=None):
        meta = meta or {}
        with self.connect() as db:
            db.execute(
                "UPDATE fetch_runs SET finished_utc=?, status=?, url=?, rows=?, sha256=?,"
                " inserted=?, updated=?, error=?, dataset=COALESCE(?, dataset) WHERE id=?",
                (
                    utc_now(), status, meta.get("url"), meta.get("rows"), meta.get("sha256"),
                    inserted, updated, error, meta.get("dataset"), run_id,
                ),
            )  # fmt: skip

    def runs(self, limit=50):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute("SELECT * FROM fetch_runs ORDER BY id DESC LIMIT ?", (limit,))
            ]

    def latest_successful_runs(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM fetch_runs WHERE id IN (SELECT MAX(id) FROM fetch_runs"
                " WHERE status='ok' GROUP BY dataset_key)"
            ).fetchall()
        return {r["dataset_key"]: dict(r) for r in rows}

    # ------------------------------------------------------------ incidents
    def upsert_incidents(self, records, source, raw_by_uid=None, seen_utc=None):
        """Insert new incidents; update existing ones only when the City update is newer."""
        raw_by_uid = raw_by_uid or {}
        seen = seen_utc or utc_now()
        inserted = updated = 0
        with self._write_lock, self.connect() as db:
            for rec in records:
                uid = rec["uid"]
                old = db.execute(
                    "SELECT last_update_utc FROM incidents WHERE uid=?", (uid,)
                ).fetchone()
                cols = [rec.get(c) for c in INCIDENT_COLUMNS]
                raw = json.dumps(raw_by_uid[uid]) if uid in raw_by_uid else None
                if old is None:
                    db.execute(
                        "INSERT INTO incidents(uid, source, start_utc, start_local,"
                        " last_update_utc, first_seen_utc, last_seen_utc, "
                        + ", ".join(INCIDENT_COLUMNS)
                        + ", record_json, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?, "
                        + ", ".join("?" * len(INCIDENT_COLUMNS))
                        + ", ?, ?)",
                        (
                            uid, source, rec["start_utc"], rec["start_local"],
                            rec.get("last_update_utc"), seen, seen, *cols,
                            json.dumps(rec), raw,
                        ),
                    )  # fmt: skip
                    inserted += 1
                elif (rec.get("last_update_utc") or "") > (old["last_update_utc"] or ""):
                    db.execute(
                        "UPDATE incidents SET last_update_utc=?, last_seen_utc=?, "
                        + ", ".join(f"{c}=?" for c in INCIDENT_COLUMNS)
                        + ", record_json=?, raw_json=COALESCE(?, raw_json) WHERE uid=?",
                        (rec.get("last_update_utc"), seen, *cols, json.dumps(rec), raw, uid),
                    )
                    updated += 1
                else:
                    db.execute("UPDATE incidents SET last_seen_utc=? WHERE uid=?", (seen, uid))
        return inserted, updated

    def record_live_sightings(self, uids, seen_utc=None):
        """Mark incidents seen in the live feed; first/last sighting bound how long it lasted."""
        seen = seen_utc or utc_now()
        with self._write_lock, self.connect() as db:
            db.executemany(
                "UPDATE incidents SET live_sightings=live_sightings+1, last_seen_utc=?,"
                " live_last_seen_utc=?, live_first_seen_utc=COALESCE(live_first_seen_utc, ?)"
                " WHERE uid=?",
                [(seen, seen, seen, u) for u in uids],
            )

    def incident_records(self, since_local=None, until_local=None):
        sql, args = "SELECT * FROM incidents WHERE 1=1", []
        if since_local:
            sql, args = sql + " AND start_local >= ?", [*args, since_local]
        if until_local:
            sql, args = sql + " AND start_local < ?", [*args, until_local]
        with self.connect() as db:
            rows = db.execute(sql + " ORDER BY start_local, uid", args).fetchall()
        return [self._incident(r) for r in rows]

    def query_incidents(self, filters, since_local=None, until_local=None, limit=100):
        allowed = {"corridor_key", "intersection_key", "quadrant", "category_group",
                   "category", "lane_position", "travel_direction"}  # fmt: skip
        sql, args = "SELECT * FROM incidents WHERE 1=1", []
        for k, v in filters.items():
            if v and k in allowed:
                sql, args = sql + f" AND {k} = ?", [*args, v]
        if since_local:
            sql, args = sql + " AND start_local >= ?", [*args, since_local]
        if until_local:
            sql, args = sql + " AND start_local < ?", [*args, until_local]
        with self.connect() as db:
            total = db.execute(sql.replace("SELECT *", "SELECT COUNT(*)", 1), args).fetchone()[0]
            rows = db.execute(sql + " ORDER BY start_local DESC, uid LIMIT ?", [*args, limit])
            return total, [self._incident(r) for r in rows.fetchall()]

    @staticmethod
    def _incident(row):
        rec = json.loads(row["record_json"])
        rec.update(
            uid=row["uid"],
            stored_source=row["source"],
            first_seen_utc=row["first_seen_utc"],
            live_sightings=row["live_sightings"],
            live_first_seen_utc=row["live_first_seen_utc"],
            live_last_seen_utc=row["live_last_seen_utc"],
        )
        return rec

    def max_incident_start(self, source):
        with self.connect() as db:
            row = db.execute(
                "SELECT MAX(start_utc) FROM incidents WHERE source=?", (source,)
            ).fetchone()
        return row[0]

    # ------------------------------------------------------------- closures
    def upsert_closures(self, records, raw_by_uid=None, full_feed=True, seen_utc=None):
        """Upsert the feed; with a complete feed, closures no longer listed are marked removed."""
        raw_by_uid = raw_by_uid or {}
        seen = seen_utc or utc_now()
        inserted = updated = 0
        with self._write_lock, self.connect() as db:
            for rec in records:
                uid = rec["uid"]
                exists = db.execute(
                    "SELECT record_json, removed_from_feed_utc FROM closures WHERE uid=?", (uid,)
                ).fetchone()
                vals = (
                    rec["location_text"], rec["start_local"], rec["end_local"],
                    rec["closure_type"], rec["corridor_key"], rec["latitude"], rec["longitude"],
                )  # fmt: skip
                raw = json.dumps(raw_by_uid[uid]) if uid in raw_by_uid else None
                if (
                    exists
                    and exists["record_json"] == json.dumps(rec)
                    and not exists["removed_from_feed_utc"]
                ):
                    db.execute("UPDATE closures SET last_seen_utc=? WHERE uid=?", (seen, uid))
                elif exists:
                    db.execute(
                        "UPDATE closures SET location_text=?, start_local=?, end_local=?,"
                        " closure_type=?, corridor_key=?, latitude=?, longitude=?,"
                        " last_seen_utc=?, removed_from_feed_utc=NULL, record_json=?,"
                        " raw_json=COALESCE(?, raw_json) WHERE uid=?",
                        (*vals, seen, json.dumps(rec), raw, uid),
                    )
                    updated += 1
                else:
                    db.execute(
                        "INSERT INTO closures(uid, location_text, start_local, end_local,"
                        " closure_type, corridor_key, latitude, longitude, first_seen_utc,"
                        " last_seen_utc, record_json, raw_json)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (uid, *vals, seen, seen, json.dumps(rec), raw),
                    )
                    inserted += 1
            removed = 0
            if full_feed:
                current = {r["uid"] for r in records}
                stale = [
                    r["uid"]
                    for r in db.execute(
                        "SELECT uid FROM closures WHERE removed_from_feed_utc IS NULL"
                    )
                    if r["uid"] not in current
                ]
                db.executemany(
                    "UPDATE closures SET removed_from_feed_utc=? WHERE uid=?",
                    [(seen, u) for u in stale],
                )
                removed = len(stale)
        return inserted, updated, removed

    def closure_records(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM closures ORDER BY CASE WHEN start_local IS NULL THEN 0 ELSE 1 END,"
                " start_local, uid"
            ).fetchall()
        out = []
        for r in rows:
            rec = json.loads(r["record_json"])
            rec.update(
                uid=r["uid"],
                first_seen_utc=r["first_seen_utc"],
                last_seen_utc=r["last_seen_utc"],
                removed_from_feed_utc=r["removed_from_feed_utc"],
            )
            out.append(rec)
        return out

    # --------------------------------------------------------- travel times
    def add_travel_times(self, observations, fetched_utc=None):
        fetched = fetched_utc or utc_now()
        with self._write_lock, self.connect() as db:
            before = db.total_changes
            db.executemany(
                "INSERT OR IGNORE INTO travel_time_obs VALUES (?, ?, ?, ?, ?)",
                [
                    (o["segment"], o["corridor"], o["city_updated_local"], o["travel_time_min"],
                     fetched)
                    for o in observations
                    if o["segment"] and o["city_updated_local"]
                ],
            )  # fmt: skip
            return db.total_changes - before

    def travel_times(self, corridor="", segment="", since_local="", limit=500):
        sql, args = "SELECT * FROM travel_time_obs WHERE 1=1", []
        for col, v in (("corridor", corridor), ("segment", segment)):
            if v:
                sql, args = sql + f" AND {col} = ?", [*args, v]
        if since_local:
            sql, args = sql + " AND city_updated_local >= ?", [*args, since_local]
        with self.connect() as db:
            rows = db.execute(
                sql + " ORDER BY city_updated_local DESC, segment LIMIT ?", [*args, limit]
            )
            return [dict(r) for r in rows.fetchall()]

    # ----------------------------------------------------- reference layers
    def put_reference(self, name, rows, sha256=None):
        with self._write_lock, self.connect() as db:
            db.execute(
                "INSERT INTO reference_layers VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE"
                " SET fetched_utc=excluded.fetched_utc, sha256=excluded.sha256,"
                " rows_json=excluded.rows_json",
                (name, utc_now(), sha256, json.dumps(rows)),
            )

    def get_reference(self, name):
        with self.connect() as db:
            row = db.execute("SELECT * FROM reference_layers WHERE name=?", (name,)).fetchone()
        return (json.loads(row["rows_json"]), row["fetched_utc"]) if row else (None, None)

    # ----------------------------------------------------------- predictions
    def save_prediction(self, origin, selection, result):
        with self._write_lock, self.connect() as db:
            cur = db.execute(
                "INSERT INTO predictions(created_utc, origin, selection_json, forecast_start,"
                " horizon_days, expected_total, interval_lo, interval_hi, result_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    utc_now(), origin, json.dumps(selection), result["forecast_start"],
                    result["horizon_days"], result["expected_total"], result["interval_80"][0],
                    result["interval_80"][1], json.dumps(result),
                ),
            )  # fmt: skip
            return cur.lastrowid

    def predictions(self, limit=20):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id, created_utc, origin, selection_json, forecast_start, horizon_days,"
                " expected_total, interval_lo, interval_hi FROM predictions ORDER BY id DESC"
                " LIMIT ?",
                (limit,),
            ).fetchall()
        return [{**dict(r), "selection": json.loads(r["selection_json"])} for r in rows]

    # ----------------------------------------------------------- simulations
    def start_sim(self, run_id, scenario, origin="manual", intersection_key=None, log_path=None):
        with self._write_lock, self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO sim_runs(id, created_utc, status, origin,"
                " intersection_key, scenario_json, log_path)"
                " VALUES (?, ?, 'running', ?, ?, ?, ?)",
                (run_id, utc_now(), origin, intersection_key, json.dumps(scenario), log_path),
            )

    def add_sim_action(self, run_id, seq, event):
        core = ("at_utc", "agent", "action", "detail")
        evidence = {k: v for k, v in event.items() if k not in core}
        with self._write_lock, self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO sim_actions VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, seq, event.get("at_utc"), event.get("agent"), event.get("action"),
                 event.get("detail"), json.dumps(evidence, default=str)),
            )  # fmt: skip

    def finish_sim(self, run_id, result, summary=None):
        decision = result.get("decision") or {}
        lowest = decision.get("lowest_delay_id")
        skip = ("metrics", "comparison", "economics", "holdout_trials", "tuning_trial")
        insert_trial = "INSERT INTO sim_trials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        with self._write_lock, self.connect() as db:
            db.execute(
                "UPDATE sim_runs SET finished_utc=?, status='completed', simulator_version=?,"
                " recommended_id=?, lowest_delay_id=?, decision_json=?, summary_json=?"
                " WHERE id=?",
                (utc_now(), result.get("simulator_version"), result.get("recommended_id"),
                 lowest, json.dumps(decision), json.dumps(summary) if summary else None, run_id),
            )  # fmt: skip
            for alt in result.get("alternatives", []):
                c, m = alt["comparison"], alt["metrics"]
                params = {k: v for k, v in alt.items() if k not in skip}
                db.execute(
                    "INSERT OR REPLACE INTO sim_alternatives VALUES"
                    " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, alt["id"], alt["label"], json.dumps(params), alt["capital_cost_cad"],
                     m["mean_delay_s"], m["total_delay_s"], c["cross_delay_change_pct"],
                     c["delay_reduction_pct"], int(c["feasible"]),
                     json.dumps(c.get("rejection_details") or c["rejection_reasons"]),
                     int(alt["id"] == result.get("recommended_id")), int(alt["id"] == lowest),
                     json.dumps(m)),
                )  # fmt: skip
                trials = [("tuning", alt.get("tuning_trial"))]
                trials += [("holdout", t) for t in alt.get("holdout_trials", [])]
                for purpose, t in trials:
                    if t:
                        db.execute(
                            insert_trial,
                            (run_id, alt["id"], purpose, t["seed"], t["demand_factor"],
                             t["demand_sha256"], t["network_sha256"], json.dumps(t["metrics"]),
                             t.get("condition")),
                        )  # fmt: skip
            for stress in result.get("stress_tests", []):
                pairs = (("reference", stress["reference"]),
                         (result["recommended_id"], stress["selected"]))  # fmt: skip
                for alt_id, t in pairs:
                    db.execute(
                        insert_trial,
                        (run_id, alt_id, "stress", t["seed"], t["demand_factor"],
                         t["demand_sha256"], t["network_sha256"], json.dumps(t["metrics"]),
                         None),
                    )  # fmt: skip

    def fail_sim(self, run_id, error):
        with self._write_lock, self.connect() as db:
            db.execute(
                "UPDATE sim_runs SET finished_utc=?, status='failed', error=? WHERE id=?",
                (utc_now(), error, run_id),
            )

    def list_sims(self, limit=20, run_id=None):
        sql = (
            "SELECT r.*, (SELECT COUNT(*) FROM sim_actions a WHERE a.run_id=r.id) AS actions,"
            " (SELECT COUNT(*) FROM sim_trials t WHERE t.run_id=r.id) AS trials FROM sim_runs r"
        )
        args = []
        if run_id:
            sql, args = sql + " WHERE r.id=?", [run_id]
        with self.connect() as db:
            rows = db.execute(sql + " ORDER BY created_utc DESC, r.id LIMIT ?", [*args, limit])
            rows = rows.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["scenario"] = json.loads(d.pop("scenario_json"))
            d["decision"] = json.loads(d.pop("decision_json") or "null")
            d["summary"] = json.loads(d.pop("summary_json") or "null")
            out.append(d)
        return out

    def get_sim(self, run_id):
        runs = self.list_sims(1, run_id)
        if not runs:
            return None
        with self.connect() as db:
            actions = [
                {**dict(a), "evidence": json.loads(a["evidence_json"] or "{}")}
                for a in db.execute(
                    "SELECT * FROM sim_actions WHERE run_id=? ORDER BY seq", (run_id,)
                )
            ]
            alternatives = [
                {**dict(a), "params": json.loads(a["params_json"]),
                 "rejection": json.loads(a["rejection_json"] or "[]"),
                 "metrics": json.loads(a["metrics_json"])}
                for a in db.execute(
                    "SELECT * FROM sim_alternatives WHERE run_id=? ORDER BY alt_id", (run_id,)
                )
            ]  # fmt: skip
            trials = [
                {**dict(t), "metrics": json.loads(t["metrics_json"])}
                for t in db.execute(
                    "SELECT * FROM sim_trials WHERE run_id=? ORDER BY alt_id, purpose, seed,"
                    " CASE WHEN condition IS NULL THEN 0 ELSE 1 END, condition, demand_factor",
                    (run_id,),
                )
            ]
        for group in (actions, alternatives, trials):
            for item in group:
                for k in [k for k in item if k.endswith("_json")]:
                    item.pop(k)
        return {**runs[0], "actions": actions, "alternatives": alternatives, "trials": trials}

    # ------------------------------------------------- intersection estimates
    def latest_estimates(self):
        """Most recent cached estimate per intersection."""
        with self.connect() as db:
            rows = db.execute(
                "SELECT intersection_key, result_json FROM intersection_estimates e WHERE"
                " computed_utc = (SELECT MAX(computed_utc) FROM intersection_estimates x"
                " WHERE x.intersection_key = e.intersection_key)"
            ).fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}

    def get_estimate(self, key, params_sha):
        with self.connect() as db:
            row = db.execute(
                "SELECT result_json FROM intersection_estimates WHERE intersection_key=?"
                " AND params_sha256=?",
                (key, params_sha),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def put_estimate(self, key, params_sha, result):
        with self._write_lock, self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO intersection_estimates VALUES (?, ?, ?, ?)",
                (key, params_sha, utc_now(), json.dumps(result)),
            )

    # ---------------------------------------------------------------- stats
    def stats(self):
        with self.connect() as db:
            one = lambda sql: db.execute(sql).fetchone()[0]
            return {
                "db_path": self.display_path(),
                "db_bytes": self.path.stat().st_size if self.path.exists() else 0,
                "schema_version": self.get_meta("schema_version"),
                "incidents": one("SELECT COUNT(*) FROM incidents"),
                "incidents_by_source": {
                    r[0]: r[1]
                    for r in db.execute("SELECT source, COUNT(*) FROM incidents GROUP BY source")
                },
                "incident_start_range_local": list(
                    db.execute(
                        "SELECT MIN(start_local), MAX(start_local) FROM incidents"
                    ).fetchone()
                ),
                "incidents_seen_live": one("SELECT COUNT(*) FROM incidents WHERE live_sightings>0"),
                "closures": one("SELECT COUNT(*) FROM closures"),
                "closures_removed_from_feed": one(
                    "SELECT COUNT(*) FROM closures WHERE removed_from_feed_utc IS NOT NULL"
                ),
                "travel_time_observations": one("SELECT COUNT(*) FROM travel_time_obs"),
                "reference_layers": {
                    r[0]: r[1] for r in db.execute("SELECT name, fetched_utc FROM reference_layers")
                },
                "predictions_saved": one("SELECT COUNT(*) FROM predictions"),
                "simulation_runs": one("SELECT COUNT(*) FROM sim_runs"),
                "simulation_actions": one("SELECT COUNT(*) FROM sim_actions"),
                "simulation_trials": one("SELECT COUNT(*) FROM sim_trials"),
                "intersection_estimates": one("SELECT COUNT(*) FROM intersection_estimates"),
                "fetch_runs": one("SELECT COUNT(*) FROM fetch_runs"),
                "last_run_utc": one("SELECT MAX(finished_utc) FROM fetch_runs"),
            }
