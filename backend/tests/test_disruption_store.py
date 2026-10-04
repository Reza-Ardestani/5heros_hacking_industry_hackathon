from app.application.disruption_collector import Collector
from app.domain import disruption_rules as rules
from app.infra.disruption_store import Store


def _incident(info, start, modified, desc="Traffic incident.", lat="51.05", lon="-114.07"):
    return {"incident_info": info, "description": desc, "start_dt_utc": start,
            "modified_dt_utc": modified, "quadrant": "SW", "latitude": lat, "longitude": lon}  # fmt: skip


def _closure(info, start, end, desc):
    return {"construction_info": info, "description": desc, "start_dt": start, "end_dt": end,
            "latitude": "51.05", "longitude": "-114.07"}  # fmt: skip


class FakeCity:
    """Stands in for city_open_data.fetch; tests mutate .data between polls."""

    def __init__(self):
        self.data = {k: [] for k in ("cameras", "signals", "volumes_2024", "projects",
                                     "incidents", "current_incidents", "closures", "travel_times")}  # fmt: skip
        self.calls = []

    def __call__(self, key, params=None):
        self.calls.append((key, params))
        if key == "travel_times" and self.data[key] == "boom":
            raise OSError("City API down")
        rows = self.data[key]
        return rows, {"dataset": key, "rows": len(rows), "sha256": "x", "url": f"fake://{key}"}


def test_identity_matches_across_archive_and_live_formats():
    a = rules.incident_uid("Macleod Trail and 58 Avenue SE", "2026-10-03T17:37:53.000")
    b = rules.incident_uid("macleod  trail and 58 avenue se", "2026-10-03 17:37:53+00:00")
    assert a == b
    assert rules.closure_uid("X", "2026-01-01T09:00:00.000", "NB lane") != rules.closure_uid(
        "X", "2026-01-01T09:00:00.000", "SB lane"
    )


def test_collector_accumulates_history_idempotently(tmp_path):
    store, city = Store(tmp_path / "db.sqlite"), FakeCity()
    city.data["incidents"] = [
        _incident("9 Avenue and 16 Street SW", "2026-09-18T21:36:31.000", "2026-09-18T21:39:16.000"),
        # Same event with a later City update: deduplicated, latest description kept.
        _incident("9 Avenue and 16 Street SW", "2026-09-18T21:36:31.000", "2026-09-18T21:50:00.000",
                  "Traffic incident. Blocking the left lane"),
    ]  # fmt: skip
    live = _incident("Northbound Deerfoot Trail at 17 Avenue SE", "2026-10-03 17:00:00+00:00",
                     "2026-10-03 17:05:00+00:00", "Stalled vehicle. Blocking the right lane")  # fmt: skip
    city.data["current_incidents"] = [live]
    city.data["closures"] = [
        _closure("1 Street at 12 Avenue SW", "2026-10-01T09:00:00.000", "2026-10-30T15:00:00.000",
                 "Northbound right lane closed"),
        _closure("1 Street at 12 Avenue SW", "2026-10-01T09:00:00.000", "2026-10-30T15:00:00.000",
                 "Southbound right lane closed"),
    ]  # fmt: skip
    city.data["travel_times"] = [{"corridor": "Deerfoot Trail", "road_segment": "SB A to B",
                                  "travel_time_mins": "7", "last_update": "2026-10-03T11:45:17.000"}]  # fmt: skip

    report = Collector(store, fetcher=city).backfill(months=6)
    assert all(r["status"] == "ok" for r in report.values())
    stats = store.stats()
    assert (
        stats["incidents"] == 2
        and stats["closures"] == 2
        and stats["travel_time_observations"] == 1
    )
    _, rows = store.query_incidents({"corridor_key": "9 Avenue SW"})
    assert rows[0]["lane_position"] == "Left lane"  # latest City update won

    # Second poll: same live incident still active, one closure gone, City API partly down.
    city.data["closures"] = city.data["closures"][:1]
    city.data["travel_times"] = "boom"
    report = Collector(store, fetcher=city).collect(include_archive=True)
    assert report["travel_times"]["status"] == "failed" and report["closures"]["status"] == "ok"
    stats = store.stats()
    assert stats["incidents"] == 2 and stats["closures"] == 2  # nothing duplicated
    assert stats["closures_removed_from_feed"] == 1
    _, rows = store.query_incidents({"corridor_key": "Deerfoot Trail"})
    assert rows[0]["live_sightings"] == 2 and rows[0]["live_first_seen_utc"]
    failed = [r for r in store.runs() if r["status"] == "failed"]
    assert failed and "City API down" in failed[0]["error"]

    # The archive is queried incrementally from the newest stored start (minus overlap).
    where = [p["$where"] for k, p in city.calls if k == "incidents"][-1]
    assert where.startswith("start_dt_utc >= '2026-09-16")
