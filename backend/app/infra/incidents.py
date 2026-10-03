import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS = ROOT / "data" / "snapshots"


def load_incidents():
    source = json.loads((SNAPSHOTS / "incidents_source.json").read_text())
    rows = json.loads((SNAPSHOTS / "incidents.json").read_text())
    # Keep newest description for same normalized title/start, irrespective of
    # coordinate updates. This is a context deduplication heuristic, not a crash ID.
    unique = {}
    discarded = 0
    for row in sorted(rows, key=lambda r: r.get("modified_dt_utc", r.get("start_dt_utc", ""))):
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if not 49 < lat < 53 or not -116 < lon < -112:
                raise ValueError("Coordinates outside Calgary region")
        except (KeyError, ValueError, TypeError):
            discarded += 1
            continue
        key = (" ".join(row.get("incident_info", "").lower().split()), row.get("start_dt_utc"))
        unique[key] = {
            "title": row.get("incident_info", "").strip(),
            "description": row.get("description", ""),
            "latitude": lat,
            "longitude": lon,
            "start_utc": row.get("start_dt_utc"),
            "modified_utc": row.get("modified_dt_utc"),
            "source_id": row.get("id"),
        }
    records = sorted(unique.values(), key=lambda r: r.get("start_utc") or "", reverse=True)
    return {
        "source": source,
        "raw_rows": len(rows),
        "context_events": len(records),
        "discarded": discarded,
        "records": records[:60],
        "deduplication": "Heuristic normalized title + start time; not authoritative incident identity",
    }
