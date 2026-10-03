import json

from fastapi.testclient import TestClient

from app.api import app
from app.application import disruptions


def test_disruption_snapshot_endpoints_are_consistent():
    client = TestClient(app)
    summary = client.get("/api/disruptions/summary").json()
    headline = summary["headline"]
    assert headline["incidents"] == sum(c["incidents"] for c in summary["by_category"])
    assert headline["incidents"] == sum(m["incidents"] for m in summary["monthly"])
    assert len(summary["monthly"]) >= 6 and summary["manifest"]["database"]

    listing = client.get("/api/disruptions/intersections", params={"limit": 5}).json()
    counts = [i["incidents"] for i in listing["items"]]
    assert counts == sorted(counts, reverse=True) and listing["total"] >= len(counts)

    key = listing["items"][0]["key"]
    detail = client.get("/api/disruptions/intersection", params={"key": key}).json()
    assert detail["incidents"] == counts[0] == sum(detail["by_hour"])
    assert sum(c["incidents"] for c in detail["by_category"]) == detail["incidents"]
    assert client.get("/api/disruptions/intersection", params={"key": "nowhere"}).status_code == 404

    quadrant = client.get("/api/disruptions/intersections", params={"quadrant": "NW"}).json()
    assert all(i["quadrant"] == "NW" for i in quadrant["items"])


def test_history_status_and_saved_predictions_come_from_the_database(seeded_store):
    client = TestClient(app)
    route = client.get("/api/disruptions/options").json()["routes"][0]["value"]
    history = client.get("/api/disruptions/history", params={"route": route, "limit": 3}).json()
    assert history["returned"] == 3 and history["total_matching"] > 3
    assert all(i["corridor_key"] == route for i in history["incidents"])
    before = seeded_store.stats()["predictions_saved"]
    saved = client.get("/api/disruptions/predict", params={"route": route, "save": True}).json()
    assert saved["saved_prediction_id"] and seeded_store.stats()["predictions_saved"] == before + 1
    status = client.get("/api/disruptions/status").json()
    assert status["incidents"] >= history["total_matching"] and status["recent_runs"]


def test_live_feed_reports_failure_without_caching_it(monkeypatch):
    def offline(url):
        raise OSError("offline")

    monkeypatch.setattr(disruptions, "_fetch", offline)
    monkeypatch.setitem(disruptions._live, "data", None)
    data = TestClient(app).get("/api/disruptions/live", params={"refresh": True}).json()
    assert data["ok"] is False and len(data["errors"]) == 2 and not data["persisted"]
    assert data["incidents"] == [] and data["active_closures"] == []
    assert disruptions._live["data"] is None  # the failure is not cached


def test_live_feed_persists_incidents_and_sightings(monkeypatch, seeded_store):
    row = {
        "incident_info": "Eastbound 99 Avenue and 99 Street SE",
        "description": "Two vehicle incident. Blocking the right lane",
        "start_dt_utc": "2026-10-03 17:37:53+00:00",
        "modified_dt_utc": "2026-10-03 17:40:02+00:00",
        "quadrant": "SE",
        "latitude": "51.0",
        "longitude": "-114.0",
    }

    def fake(url):
        return json.dumps([row] if "4jah-h97u" in url else []).encode()

    monkeypatch.setattr(disruptions, "_fetch", fake)
    monkeypatch.setitem(disruptions._live, "data", None)
    monkeypatch.setattr(seeded_store, "upsert_closures", lambda *a, **k: (0, 0, 0))
    for _ in range(2):
        data = TestClient(app).get("/api/disruptions/live", params={"refresh": True}).json()
    assert data["persisted"] and data["incidents"][0]["location_text"] == row["incident_info"]
    total, rows = seeded_store.query_incidents({"corridor_key": "99 Avenue SE"})
    assert total == 1 and rows[0]["live_sightings"] == 2 and rows[0]["stored_source"] == "live"
    assert (
        rows[0]["category"] == "Two-vehicle collision" and rows[0]["lane_position"] == "Right lane"
    )


def test_live_incident_links_to_its_own_intersection_not_a_nearby_typo(monkeypatch):
    client = TestClient(app)
    items = client.get("/api/disruptions/intersections", params={"limit": 200}).json()["items"]
    top, small = items[0], items[-1]
    road, cross = top["key"].rsplit(" ", 1)[0].split(" & ")
    row = {
        "incident_info": f"{road} and {cross} {top['quadrant']}",
        "description": "Traffic incident.",
        "start_dt_utc": "2026-10-03 18:00:00+00:00",
        "modified_dt_utc": "2026-10-03 18:01:00+00:00",
        "quadrant": top["quadrant"],
        # Placed exactly on a different, small intersection's centroid.
        "latitude": str(small["latitude"]),
        "longitude": str(small["longitude"]),
    }

    def fake(url):
        return json.dumps([row] if "4jah-h97u" in url else []).encode()

    monkeypatch.setattr(disruptions, "_fetch", fake)
    monkeypatch.setitem(disruptions._live, "data", None)
    monkeypatch.setenv("BB_LIVE_PERSIST", "0")
    hotspot = client.get("/api/disruptions/live", params={"refresh": True}).json()["incidents"][0][
        "hotspot"
    ]
    assert hotspot["key"] == top["key"] and hotspot["match"] == "intersection name"
