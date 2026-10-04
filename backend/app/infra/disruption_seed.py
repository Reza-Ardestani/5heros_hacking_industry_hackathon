"""Seed storage offline from committed export files."""

import json
from pathlib import Path

from app.domain import disruption_rules as rules


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
