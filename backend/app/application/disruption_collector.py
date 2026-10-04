"""Write City disruption data into the store.

- backfill(): full download of every dataset for a window (first run / rebuild).
- collect(): incremental poll — live incidents (+ sightings), closures (+ removals),
  travel-time observations, new archive incidents, references when stale.
- seed_from_exports(): load the committed JSON exports when the database is empty,
  so the API works offline on a fresh checkout.

Every dataset download is recorded in fetch_runs, including failures.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.application import disruption_ingest as ingest
from app.domain import disruption_rules as rules
from app.infra import city_open_data

REFERENCE_KEYS = ("cameras", "signals", "volumes_2024", "projects")
ARCHIVE_OVERLAP = timedelta(days=2)  # re-read recent archive rows to pick up City edits


def _utc(dt):
    return dt.replace(tzinfo=None).isoformat(timespec="seconds")


class Collector:
    def __init__(self, store, fetcher=city_open_data.fetch, raw_dir=None):
        self.store, self.fetcher, self.raw_dir = store, fetcher, raw_dir
        self.report = {}

    # ------------------------------------------------------------ plumbing
    def pull(self, job, key, params=None):
        run = self.store.start_run(job, key, city_open_data.DATASETS[key][0])
        try:
            rows, meta = self.fetcher(key, params)
        except Exception as error:  # noqa: BLE001 — recorded; job continues with other datasets
            self.store.finish_run(run, "failed", error=f"{type(error).__name__}: {error}")
            self.report[key] = {"status": "failed", "error": str(error)}
            return None, None, run
        if self.raw_dir:
            Path(self.raw_dir).mkdir(parents=True, exist_ok=True)
            (Path(self.raw_dir) / f"{meta['dataset']}.json").write_text(
                json.dumps(rows), encoding="utf-8"
            )
        return rows, meta, run

    def _done(self, run, key, meta, **counts):
        self.store.finish_run(run, "ok", meta, counts.get("inserted", 0), counts.get("updated", 0))
        self.report[key] = {"status": "ok", "rows": meta["rows"], **counts}

    def reference(self, max_age_hours=None, job="collect"):
        """Refresh reference layers if missing/stale; return an indexed Reference."""
        for key in REFERENCE_KEYS:
            _, fetched = self.store.get_reference(key)
            stale = fetched is None or (
                max_age_hours is not None
                and datetime.fromisoformat(fetched)
                < datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=max_age_hours)
            )
            if stale:
                rows, meta, run = self.pull(job, key, {"$order": ":id"})
                if rows is not None:
                    self.store.put_reference(key, rows, meta["sha256"])
                    self._done(run, key, meta, inserted=len(rows))
        return load_reference(self.store)

    def _aliases(self):
        return self.store.get_meta("road_aliases", {})

    # ------------------------------------------------------------- jobs
    def backfill(self, months=6):
        start_local = ingest.window_start(months)
        # Query from one day early in UTC terms; readers filter on local start time.
        since_utc = datetime.fromisoformat(start_local.isoformat()) - timedelta(days=1)
        ref = self.reference(max_age_hours=0, job="backfill")
        inc_raw, inc_meta, inc_run = self.pull(
            "backfill", "incidents",
            {"$where": f"start_dt_utc >= '{_utc(since_utc)}'",
             "$order": "start_dt_utc ASC, id ASC"},
        )  # fmt: skip
        clo_raw, clo_meta, clo_run = self.pull("backfill", "closures", {"$order": "start_dt ASC"})
        if inc_raw is not None:
            # Aliases are rebuilt from the full window and persisted for the collector.
            texts = [r.get("incident_info") for r in inc_raw]
            texts += [r.get("construction_info") for r in clo_raw or []]
            self.store.set_meta("road_aliases", rules.build_road_aliases(texts))
            records, raw_by_uid, stats = ingest.build_incidents(inc_raw, ref, self._aliases())
            ins, upd = self.store.upsert_incidents(records, "archive", raw_by_uid)
            self._done(inc_run, "incidents", inc_meta, inserted=ins, updated=upd, **stats)
            self.store.set_meta("dedup_stats", stats)
        if clo_raw is not None:
            self.store_closures(clo_raw, clo_meta, clo_run, ref)
        self._live_and_travel(ref, "backfill")
        self.store.set_meta("window_months", months)
        self.store.set_meta("last_backfill_utc", _utc(datetime.now(UTC)))
        return self.report

    def collect(self, include_archive=True, reference_max_age_hours=24):
        ref = self.reference(max_age_hours=reference_max_age_hours)
        self._live_and_travel(ref, "collect")
        clo_raw, clo_meta, clo_run = self.pull("collect", "closures", {"$order": "start_dt ASC"})
        if clo_raw is not None:
            self.store_closures(clo_raw, clo_meta, clo_run, ref)
        if include_archive:
            since = self.store.max_incident_start("archive")
            since_dt = rules.parse_ts(since) - ARCHIVE_OVERLAP if since else (
                datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)
            )  # fmt: skip
            rows, meta, run = self.pull(
                "collect", "incidents",
                {"$where": f"start_dt_utc >= '{_utc(since_dt)}'", "$order": "start_dt_utc ASC"},
            )  # fmt: skip
            if rows is not None:
                records, raw_by_uid, stats = ingest.build_incidents(rows, ref, self._aliases())
                ins, upd = self.store.upsert_incidents(records, "archive", raw_by_uid)
                self._done(run, "incidents", meta, inserted=ins, updated=upd, **stats)
        self.store.set_meta("last_collect_utc", _utc(datetime.now(UTC)))
        return self.report

    def store_closures(self, raw, meta, run, ref):
        aliases = self._aliases()
        # The City occasionally posts the same closure twice a few metres apart; keep one
        # per identity so repeated polls are stable.
        by_uid = {}
        for r in raw:
            rec = ingest.build_closure(r, ref, aliases)
            by_uid[rec["uid"]] = (rec, r)
        records = [rec for rec, _ in by_uid.values()]
        raw_by_uid = {uid: r for uid, (_, r) in by_uid.items()}
        ins, upd, removed = self.store.upsert_closures(records, raw_by_uid, full_feed=True)
        self._done(run, "closures", meta, inserted=ins, updated=upd, removed_from_feed=removed)

    def _live_and_travel(self, ref, job):
        rows, meta, run = self.pull(job, "current_incidents", {"$order": "start_dt_utc DESC"})
        if rows is not None:
            records, raw_by_uid, _ = ingest.build_incidents(rows, ref, self._aliases())
            # Live rows may precede the archive; the archive later replaces them if newer.
            ins, upd = self.store.upsert_incidents(records, "live", raw_by_uid)
            self.store.record_live_sightings([r["uid"] for r in records])
            self.store.put_reference("current_incidents", current_snapshot(records), meta["sha256"])
            self._done(run, "current_incidents", meta, inserted=ins, updated=upd)
        rows, meta, run = self.pull(job, "travel_times", {"$order": ":id"})
        if rows is not None:
            added = self.store.add_travel_times(ingest.travel_time_observations(rows))
            self._done(run, "travel_times", meta, inserted=added)


def current_snapshot(records):
    keep = ("uid", "location_text", "description", "start_utc", "start_local", "quadrant",
            "category", "lane_impact", "lane_position", "latitude", "longitude")  # fmt: skip
    return [{k: r.get(k) for k in keep} for r in records]


def load_reference(store):
    return ingest.Reference(
        store.get_reference("cameras")[0],
        store.get_reference("signals")[0],
        store.get_reference("volumes_2024")[0],
    )


def seed_from_exports(store, analysis_dir):
    """Populate an empty database from committed JSON exports (no network needed)."""
    analysis_dir = Path(analysis_dir)
    inc_file = analysis_dir / "calgary_incidents_6mo.json"
    if store.stats()["incidents"] or not inc_file.exists():
        return False
    run = store.start_run("seed", "exports")
    inc = json.loads(inc_file.read_text(encoding="utf-8"))
    clo = json.loads((analysis_dir / "calgary_closures.json").read_text(encoding="utf-8"))
    ctx = json.loads((analysis_dir / "calgary_context_layers.json").read_text(encoding="utf-8"))
    seen = inc["manifest"]["retrieved_at_utc"][:19]
    records = []
    for r in inc["records"]:
        r = dict(r)
        r["uid"] = r.get("uid") or rules.incident_uid(r["location_text"], r["start_utc"])
        records.append(r)
    ins, _ = store.upsert_incidents(records, "archive", seen_utc=seen)
    closures = []
    for c in clo["records"]:
        c = dict(c)
        c["uid"] = c.get("uid") or rules.closure_uid(
            c["location_text"], c["start_local"], c["description"]
        )
        closures.append(c)
    store.upsert_closures(closures, full_feed=True, seen_utc=seen)
    # Exports keep reference rows without geometry; rebuild raw-shaped rows for the indexes.
    store.put_reference("cameras", [
        {"point": {"coordinates": [c["lon"], c["lat"]]}, "camera_location": c["camera_location"],
         "quadrant": c["quadrant"], "camera_url": {"url": c["image_url"], "description": c["camera_id"]}}
        for c in ctx["cameras"]
    ])  # fmt: skip
    store.put_reference("signals", [
        {"latitude": s["lat"], "longitude": s["lon"], "unitid": s["signal_id"],
         "firstroad": s["signal_name"].split(" & ")[0],
         "secondroad": s["signal_name"].split(" & ")[-1].rsplit(" ", 1)[0],
         "quadrant": s["quadrant"], "int_type": s["int_type"], "instdate": s["installed"]}
        for s in ctx["signals"]
    ])  # fmt: skip
    store.add_travel_times(
        [
            {"corridor": t["corridor"], "segment": t["segment"],
             "travel_time_min": t["travel_time_min"],
             "city_updated_local": (t["last_update_local"] or "")[:19] or None}
            for t in ctx.get("travel_times_snapshot", [])
        ],
        fetched_utc=seen,
    )  # fmt: skip
    summary = json.loads(
        (analysis_dir / "calgary_disruption_summary.json").read_text(encoding="utf-8")
    )
    store.set_meta("road_aliases", summary.get("data_quality", {}).get("road_aliases", {}))
    store.set_meta("window_months", inc["manifest"]["window"].get("months_requested", 6))
    store.finish_run(run, "ok", {"rows": len(records), "url": str(inc_file)}, inserted=ins)
    return True
