"""Read service over the disruption store: summary, intersections, prediction, live feed.

Shared by the HTTP API and the MCP server. Data comes from SQLite (see
app/infra/disruption_store.py); an empty database is seeded from the committed
JSON exports. Incident counts are reported disruptions (camera-observed), not
traffic flow, delay or crash risk.
"""

import hashlib
import json
import os
import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from statistics import median

from app.application import disruption_ingest as ingest
from app.application.disruption_collector import (
    Collector,
    current_snapshot,
    load_reference,
    seed_from_exports,
)
from app.domain import forecast as model
from app.domain import ml_forecast
from app.domain.geo import PointIndex, dist_m
from app.infra import city_open_data
from app.infra.disruption_store import ROOT, Store

ANALYSIS = ROOT / "data" / "analysis"
LIVE_TTL_S = 60
NEARBY_M = 400
LINK_M = 150  # live incident -> historic intersection linking radius
HOTSPOT_MIN = 5  # incidents in the window before a location is called a hotspot
ANY = ""
MAX_HORIZON_DAYS = 28
CAVEAT = (
    "Reported disruptions from City camera monitoring; not measured flow, delay or "
    "exposure-adjusted crash risk. Use to choose a corridor to study, then calibrate with counts."
)

_state: dict = {"store": None, "version": None, "data": None}
_live: dict = {"at": 0.0, "data": None}
_lock = threading.Lock()
_live_lock = threading.Lock()


def use_store(store):
    """Point the service at a store (tests, alternate database paths)."""
    with _lock:
        _state.update(store=store, version=None, data=None)
    _live.update(at=0.0, data=None)


def store():
    with _lock:
        if _state["store"] is None:
            _state["store"] = Store()
        s = _state["store"]
    seed_from_exports(s, ANALYSIS)
    return s


def _https(url):
    return url.replace("http://", "https://", 1) if url else url


def _load():
    s = store()
    version = s.version()
    with _lock:
        if _state["version"] == version and _state["data"] is not None:
            return _state["data"]
    months = s.get_meta("window_months", 6)
    now = ingest.calgary_now()
    win_start = ingest.window_start(months, now.date())
    incidents = s.incident_records(since_local=win_start.isoformat())
    if not incidents:
        raise FileNotFoundError(
            "Disruption database is empty. Run scripts/build_disruption_dataset.py "
            "(see data/analysis/README.md)."
        )
    win_start_dt = datetime.fromisoformat(win_start.isoformat())  # naive local midnight
    closures = [ingest.closure_status(c, now, win_start_dt) for c in s.closure_records()]
    ref = load_reference(s)
    summary = ingest.summarize(incidents, closures, ref.signals, win_start, now)
    gaps = set(summary.pop("days_without_any_incident"))
    days = [win_start + timedelta(i) for i in range((now.date() - win_start).days)]
    runs = s.latest_successful_runs()
    manifest = {
        "retrieved_at_utc": max((r["finished_utc"] for r in runs.values()), default=None),
        "discovered_from": city_open_data.DISCOVERED_FROM,
        **city_open_data.LICENSE,
        "window": {"start_local": win_start.isoformat(), "months": months},
        "sources": {
            k: {"dataset": r["dataset"], "rows": r["rows"], "sha256": r["sha256"],
                "url": r["url"], "fetched_utc": r["finished_utc"],
                "name": city_open_data.DATASETS.get(k, (None, k))[1]}
            for k, r in runs.items()
        },
        "database": s.display_path(),
    }  # fmt: skip
    data = {
        "incidents": incidents,
        "closures": closures,
        "reference": ref,
        "summary": summary,
        "manifest": manifest,
        "data_quality": {
            **(s.get_meta("dedup_stats", {}) or {}),
            "dedup_rule": ingest.DEDUP_RULE,
            "road_aliases": s.get_meta("road_aliases", {}),
            "days_without_any_incident": sorted(gaps),
        },
        "observed_days": [d for d in days if d.isoformat() not in gaps],
        "forecast_start": now.date(),
        "city_times": [model_time(r) for r in incidents],
        "intersections": _build_intersections(incidents, ref.cameras_by_id),
    }
    data["intersection_index"] = PointIndex(
        [
            {"lat": i["latitude"], "lon": i["longitude"], "item": i}
            for i in data["intersections"].values()
        ]
    )
    with _lock:
        _state.update(version=version, data=data)
    return data


def model_time(r):
    return datetime.fromisoformat(r["start_local"])  # naive Calgary wall-clock time


def _build_intersections(incidents, cams):
    groups: dict[str, list] = {}
    for r in incidents:
        if r.get("intersection_key"):
            groups.setdefault(r["intersection_key"], []).append(r)
    out = {}
    for key, rows in groups.items():
        lat, lon = median(r["latitude"] for r in rows), median(r["longitude"] for r in rows)
        sig = Counter(
            r["nearest_signal"] for r in rows if r["at_signalized_intersection"]
        ).most_common(1)
        cam_id = Counter(r["nearest_camera"] for r in rows if r["nearest_camera"]).most_common(1)
        cam = cams.get(cam_id[0][0]) if cam_id else None
        vols = [r["volume_2024"] for r in rows if r.get("volume_2024")]
        road = Counter(r["primary_road"] for r in rows).most_common(1)[0][0]
        cross = Counter(r["cross_road"] for r in rows if r["primary_road"] == road).most_common(1)
        out[key] = {
            "key": key,
            "roads": [road, cross[0][0] if cross else None],
            "quadrant": Counter(r["quadrant"] for r in rows).most_common(1)[0][0],
            "latitude": lat,
            "longitude": lon,
            "incidents": len(rows),
            "collisions": sum(r["category_group"] == "Collision" for r in rows),
            "vulnerable_road_user": sum(
                r["category_group"] == "Vulnerable road user" for r in rows
            ),
            "signal_faults": sum(r["category_group"] == "Signal fault" for r in rows),
            "lane_blocking": sum((r["lane_impact_level"] or 0) >= 1 for r in rows),
            "unspecified": sum(r["category"] == "Traffic incident (unspecified)" for r in rows),
            "unspecified_pct": round(
                100
                * sum(r["category"] == "Traffic incident (unspecified)" for r in rows)
                / len(rows),
                1,
            ),
            "peak_period": sum("peak" in r["period"] for r in rows),
            "last_seen_local": max(r["start_local"] for r in rows),
            "signalized": bool(sig),
            "signal": sig[0][0] if sig else None,
            "camera": (
                {
                    "id": cam["camera_id"],
                    "location": cam["camera_location"],
                    "image_url": _https(cam["image_url"]),
                    "distance_m": round(dist_m(lat, lon, cam["lat"], cam["lon"])),
                }
                if cam
                else None
            ),
            "volume_2024": median(vols) if vols else None,
            "_rows": rows,
        }
    return out


MAX_RADIUS_M = 10_000


def _near(items, lat, lon, radius_m):
    """Keep records/intersections within radius_m of (lat, lon); no-op without an area."""
    if lat is None or lon is None or not radius_m:
        return items
    radius_m = max(50, min(float(radius_m), MAX_RADIUS_M))
    return [i for i in items if dist_m(lat, lon, i["latitude"], i["longitude"]) <= radius_m]


def _area_label(lat, lon, radius_m, label=""):
    if lat is None or lon is None or not radius_m:
        return None
    where = label or f"{lat:.4f}, {lon:.4f}"
    return f"within {radius_m / 1000:g} km of {where}"


def _public(i):
    return {k: v for k, v in i.items() if not k.startswith("_")}


def summary():
    d = _load()
    s = d["summary"]
    return {
        "caveat": CAVEAT,
        "manifest": d["manifest"],
        "headline": s["headline"],
        "data_quality": d["data_quality"],
        "by_category": s["by_category"],
        "monthly": s["monthly"],
        "hour_by_weekday": s["hour_by_weekday"],
        "by_lane_impact": s["by_lane_impact"],
        "top_corridors": s["top_corridors"][:15],
        "closures_by_type": s["closures_by_type"],
        "intersections_indexed": len(d["intersections"]),
    }


def full_summary():
    """Everything the exports need (workbook, summary JSON)."""
    d = _load()
    return {**d["summary"], "data_quality": d["data_quality"], "manifest": d["manifest"]}


def list_intersections(q="", quadrant="", category="", sort="incidents", limit=40,
                       lat=None, lon=None, radius_m=0):  # fmt: skip
    items = _near(list(_load()["intersections"].values()), lat, lon, radius_m)
    if q:
        needle = q.lower()
        items = [i for i in items if needle in i["key"].lower()]
    if quadrant:
        items = [i for i in items if i["quadrant"] == quadrant.upper()]
    if category:
        items = [i for i in items if any(r["category_group"] == category for r in i["_rows"])]
    keys = {
        "incidents": lambda i: (-i["incidents"], -i["lane_blocking"]),
        "lane_blocking": lambda i: (-i["lane_blocking"], -i["incidents"]),
        "collisions": lambda i: (-i["collisions"], -i["incidents"]),
        "recent": lambda i: i["last_seen_local"],
    }
    items.sort(key=keys.get(sort, keys["incidents"]))
    if sort == "recent":
        items.reverse()
    estimates = store().latest_estimates()
    out = []
    for i in items[:limit]:
        est = estimates.get(i["key"]) or {}
        out.append({**_public(i), "incident_delay_s": est.get("extra_delay_s_per_vehicle")})
    return {"total": len(items), "items": out}


def intersection_detail(key):
    d = _load()
    i = d["intersections"].get(key)
    if i is None:
        return None
    rows = i["_rows"]
    closures = []
    for c in d["closures"]:
        if c.get("latitude") is None or not c["overlaps_window"]:
            continue
        m = dist_m(i["latitude"], i["longitude"], c["latitude"], c["longitude"])
        if m <= NEARBY_M:
            closures.append(
                {
                    **{k: c[k] for k in ("location_text", "description", "start_local",
                                         "end_local", "closure_type", "status_at_retrieval")},
                    "removed_from_feed_utc": c.get("removed_from_feed_utc"),
                    "distance_m": round(m),
                }
            )  # fmt: skip
    months = sorted({r["month"] for r in d["incidents"]})
    estimate = store().latest_estimates().get(key)
    return {
        **_public(i),
        "incident_delay_estimate": estimate,
        "caveat": CAVEAT,
        "by_category": [{"category": k, "incidents": v} for k, v in Counter(r["category"] for r in rows).most_common()],
        "by_lane_impact": [{"lane_impact": k, "incidents": v} for k, v in Counter(r["lane_impact"] for r in rows).most_common()],
        "by_direction": [{"direction": k or "Not reported", "incidents": v} for k, v in Counter(r["travel_direction"] for r in rows).most_common()],
        "by_hour": [sum(r["hour_local"] == h for r in rows) for h in range(24)],
        "by_weekday": {w: sum(r["weekday"] == w for r in rows) for w in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")},
        "by_month": [{"month": m, "incidents": sum(r["month"] == m for r in rows)} for m in months],
        "closures_nearby": sorted(closures, key=lambda c: c["distance_m"]),
        "recent": [
            {k: r.get(k) for k in ("start_local", "category", "lane_impact", "travel_direction",
                                   "description", "location_text", "period", "live_sightings")}
            for r in sorted(rows, key=lambda r: r["start_local"], reverse=True)[:25]
        ],
    }  # fmt: skip


def options(quadrant=ANY, route=ANY):
    """Selectable areas, routes (corridors), directions, lanes and incident types."""
    rows = _load()["incidents"]
    in_area = [r for r in rows if not quadrant or r["quadrant"] == quadrant]
    on_route = [r for r in in_area if not route or r["corridor_key"] == route]

    def count(field, src):
        return [
            {"value": k, "incidents": v}
            for k, v in Counter(r[field] for r in src if r[field]).most_common()
        ]

    return {
        "quadrants": count("quadrant", rows),
        "routes": [x for x in count("corridor_key", in_area) if x["incidents"] >= 3],
        "directions": count("travel_direction", on_route),
        "lanes": count("lane_position", on_route),
        "categories": count("category_group", on_route),
        "intersections": count("intersection_key", on_route)[:150] if route else [],
        "max_horizon_days": MAX_HORIZON_DAYS,
    }  # fmt: skip


FORECAST_MODELS = ("auto", "flat", "bayes", "lightgbm")


def predict(quadrant=ANY, route=ANY, direction=ANY, lane=ANY, category=ANY, intersection=ANY,
            horizon_days=7, save=False, origin="api", model_name="auto",
            lat=None, lon=None, radius_m=0, area_label=""):  # fmt: skip
    """Forecast reported incidents. model_name="auto" uses the model chosen on validation
    days (flat baseline, empirical-Bayes rates or LightGBM); others force that model."""
    d = _load()
    days = d["observed_days"]
    if intersection:
        # An intersection is more specific than its route: incidents may be logged
        # under either crossing road, so the route/area filters would drop some.
        quadrant = route = ANY
    filters = {
        "quadrant": quadrant,
        "corridor_key": route,
        "travel_direction": direction,
        "lane_position": lane,
        "category_group": category,
        "intersection_key": intersection,
    }
    rows = [r for r in d["incidents"] if all(not v or r[k] == v for k, v in filters.items())]
    rows = _near(rows, lat, lon, radius_m)
    area = _area_label(lat, lon, radius_m, area_label)
    times = [model_time(r) for r in rows]
    horizon_days = max(1, min(int(horizon_days), MAX_HORIZON_DAYS))
    start = d["forecast_start"]
    if model_name not in FORECAST_MODELS:
        raise ValueError(f"model must be one of {FORECAST_MODELS}")
    backtest = model.select_and_backtest(times, days, d["city_times"])
    eligible = model.eligible_models(times, days)
    chosen = (
        (backtest["selected_model"] if backtest else "bayes")
        if model_name == "auto"
        else model_name
    )
    note = None
    if chosen not in eligible:
        note = f"{chosen} needs at least {ml_forecast.MIN_INCIDENTS} incidents; used bayes"
        chosen = "bayes"
    result = model.forecast(times, days, d["city_times"], start, horizon_days, chosen)
    result["model"].update(requested=model_name, eligible=eligible, note=note)
    spots = Counter(r["intersection_key"] for r in rows if r["intersection_key"])
    n_days = len(days)
    selection = {
        k: v
        for k, v in {"quadrant": quadrant, "route": route, "direction": direction, "lane": lane,
                     "category": category, "intersection": intersection, "area": area}.items()
        if v
    }  # fmt: skip
    out = {
        "selection": selection,
        "history": {
            "incidents": len(rows),
            "observed_days": n_days,
            "per_day": round(len(rows) / n_days, 3),
            "lane_blocking_pct": round(
                100 * sum((r["lane_impact_level"] or 0) >= 1 for r in rows) / len(rows), 1
            )
            if rows
            else None,
            "category_mix": [
                {"category": k, "share_pct": round(100 * v / len(rows), 1)}
                for k, v in Counter(r["category"] for r in rows).most_common(6)
            ],
        },
        "forecast_start": start.isoformat(),
        "horizon_days": horizon_days,
        **result,
        "periods": [p[0] for p in model.PERIODS],
        "backtest": backtest,
        "forecast_evaluation": model.forecast_evaluation(backtest, result["model"]["name"]),
        "top_intersections": [
            {"key": k, "incidents": v, "expected_in_horizon": round(v / n_days * horizon_days, 2)}
            for k, v in spots.most_common(8)
        ],
        "low_data": len(rows) < 20,
        "method": model.__doc__.strip(),
        "caveat": CAVEAT,
    }
    if save:
        out["saved_prediction_id"] = store().save_prediction(origin, selection, out)
    return out


# --------------------------------------------------------------- priorities
PRIORITY_MIN = {"corridor": 10, "intersection": HOTSPOT_MIN}
RECENT_DAYS = 28  # trend window, and the hold-out window of the ranking check
TOP_N = 10
LANE_PRIOR = 10  # pseudo-incidents shrinking a slice's lane-blocking share to the city's
PRIORITY_SORTS = {
    "expected": lambda i: -i["expected"],
    "lane_blocking": lambda i: -i["expected_lane_blocking"],
    "rising": lambda i: (i["trend"] != "rising", -(i["trend_ratio"] or 0)),
    "exposure": lambda i: (i["per_10k_daily_vehicles"] is None, -(i["per_10k_daily_vehicles"] or 0)),
}  # fmt: skip
PRIORITY_METHOD = (
    "Each corridor (or intersection) is forecast with the disruption model over the horizon; "
    "default rank is expected incidents. Expected lane-blocking = expected incidents x the "
    "slice's lane-blocking share, shrunk toward the citywide share (many records do not "
    "report lane impact). Recent change compares the slice's share of incidents in the "
    "last 28 observed days with the citywide share, so citywide shocks such as weather "
    "cancel out; it is called rising or falling only if an exact binomial test survives a "
    "10% false-discovery-rate adjustment across all ranked slices. Ranking check: the same "
    "ranking built only from data before the last 28 days, scored on what then happened."
)


def _spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    var = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(cov / var, 3) if var else None


def _ranking_check(groups, city_times, days):
    """Rank on data before the last RECENT_DAYS observed days; score on those days."""
    if len(days) < RECENT_DAYS + 56 or len(groups) < TOP_N * 2:
        return None
    train, test = days[:-RECENT_DAYS], set(days[-RECENT_DAYS:])
    train_set = set(train)
    rows = []
    for key, times in groups.items():
        rates = model.fit(times, train, city_times)
        expected = sum(
            sum(rates[(d.weekday(), p)] for p in range(len(model.PERIODS))) for d in test
        )
        past = sum(1 for t in times if t.date() in train_set)
        actual = sum(1 for t in times if t.date() in test)
        rows.append((key, expected, past, actual))
    total_actual = sum(r[3] for r in rows) or 1
    actual_top = {r[0] for r in sorted(rows, key=lambda r: -r[3])[:TOP_N]}

    def score(col):
        top = sorted(rows, key=lambda r: -r[col])[:TOP_N]
        return {
            "overlap_with_actual_top": len(actual_top & {r[0] for r in top}),
            "captured_pct": round(100 * sum(r[3] for r in top) / total_actual, 1),
        }

    return {
        "train_days": len(train),
        "test_start": min(test).isoformat(),
        "test_end": max(test).isoformat(),
        "top_n": TOP_N,
        "forecast": score(1),
        "past_counts": score(2),
        "spearman": _spearman([r[1] for r in rows], [r[3] for r in rows]),
    }


def priorities(level="corridor", horizon_days=28, quadrant=ANY, sort="expected", limit=15):
    """Rank corridors or intersections to study first, with forecast-analysis statistics."""
    level = "intersection" if level == "intersection" else "corridor"
    horizon_days = max(1, min(int(horizon_days), MAX_HORIZON_DAYS))
    sort = sort if sort in PRIORITY_SORTS else "expected"
    d = _load()
    # Results depend only on the loaded data and these inputs; sorting happens per request.
    cache = d.setdefault("_priorities", {})
    key = (level, horizon_days, quadrant.upper())
    if key not in cache:
        cache[key] = _priorities(d, level, horizon_days, quadrant)
    out = dict(cache[key])
    out["sort"] = sort
    out["items"] = sorted(out["items"], key=PRIORITY_SORTS[sort])[: max(1, min(limit, 100))]
    return out


def _priorities(d, level, horizon_days, quadrant):
    # Local import: intersection_study imports this module.
    from app.application.intersection_study import fits_arterial_model as fits

    field = "corridor_key" if level == "corridor" else "intersection_key"
    days, start, city_times = d["observed_days"], d["forecast_start"], d["city_times"]
    observed = set(days)
    rows_by = {}
    for r in d["incidents"]:
        if r[field] and (not quadrant or r["quadrant"] == quadrant.upper()):
            rows_by.setdefault(r[field], []).append(r)
    rows_by = {k: v for k, v in rows_by.items() if len(v) >= PRIORITY_MIN[level]}
    groups = {k: [model_time(r) for r in v] for k, v in rows_by.items()}

    phi = model.dispersion(city_times, days)
    recent = set(days[-RECENT_DAYS:])
    city_n = sum(1 for t in city_times if t.date() in observed)
    city_recent_share = sum(1 for t in city_times if t.date() in recent) / (city_n or 1)
    city_lane_share = sum((r["lane_impact_level"] or 0) >= 1 for r in d["incidents"]) / len(
        d["incidents"]
    )
    city_rates = model.fit(city_times, days, city_times)
    city_lams = model.daily_expected(city_rates, start, horizon_days)
    city_expected = sum(city_lams)
    estimates = store().latest_estimates() if level == "intersection" else {}

    items = []
    for key, rows in rows_by.items():
        times = groups[key]
        rates = model.fit(times, days, city_times)
        lams = model.daily_expected(rates, start, horizon_days)
        expected = sum(lams)
        lo, hi = model.nb_interval(expected, model.total_dispersion(lams, phi))
        n = sum(1 for t in times if t.date() in observed)
        shift = model.recent_shift(
            sum(1 for t in times if t.date() in recent), n, city_recent_share
        )
        lane_blocking = sum((r["lane_impact_level"] or 0) >= 1 for r in rows)
        lane_share = (lane_blocking + LANE_PRIOR * city_lane_share) / (len(rows) + LANE_PRIOR)
        (pw, pp), peak_rate = max(rates.items(), key=lambda kv: kv[1])
        vols = [r["volume_2024"] for r in rows if r.get("volume_2024")]
        volume = median(vols) if vols else None
        spots = Counter(r["intersection_key"] for r in rows if r["intersection_key"])
        # Busiest hotspot the arterial simulator can represent (freeway interchanges are capped).
        study_spot = next(
            (
                k
                for k, n in spots.most_common()
                if n >= HOTSPOT_MIN and fits(d["intersections"][k]["volume_2024"])
            ),
            None,
        )
        est = estimates.get(key) or {}
        items.append(
            {
                "key": key,
                "corridor": Counter(r["corridor_key"] for r in rows).most_common(1)[0][0],
                "quadrants": sorted({r["quadrant"] for r in rows if r["quadrant"]}),
                "history_incidents": len(rows),
                "expected": round(expected, 2),
                "interval_80": [lo, hi],
                "expected_lane_blocking": round(expected * lane_share, 2),
                "lane_blocking_pct": round(100 * lane_blocking / len(rows), 1),
                "lane_impact_reported_pct": round(
                    100 * sum(r["lane_impact_level"] is not None for r in rows) / len(rows), 1
                ),
                "trend": "steady",  # set after the false-discovery-rate adjustment below
                "trend_direction": shift["direction"],
                "trend_ratio": shift["ratio"],
                "trend_p_value": round(shift["p_value"], 4),
                "peak_window": f"{model.WEEKDAYS[pw]} {model.PERIODS[pp][0]}",
                "peak_window_share_pct": round(100 * peak_rate / (sum(rates.values()) or 1), 1),
                "median_volume_2024": volume,
                "per_10k_daily_vehicles": round(expected / (volume / 10_000), 2) if volume else None,
                "top_intersections": [k for k, _ in spots.most_common(3)] if level == "corridor" else [],
                "study_spot": study_spot,
                "study_spot_incidents": spots[study_spot] if study_spot else 0,
                "incident_delay_s": est.get("extra_delay_s_per_vehicle"),
            }
        )  # fmt: skip

    # Screening dozens of slices at p < 0.05 flags a few by chance; control the FDR.
    for item, keep in zip(items, model.benjamini_hochberg([i["trend_p_value"] for i in items])):
        if keep and item["trend_direction"]:
            item["trend"] = item["trend_direction"]
    ranked = sorted(items, key=lambda i: -i["expected"])
    top = ranked[:TOP_N]
    (cw, cp), _ = max(city_rates.items(), key=lambda kv: kv[1])
    backtest = model.backtest(city_times, days, city_times)
    return {
        "level": level,
        "horizon_days": horizon_days,
        "forecast_start": start.isoformat(),
        "quadrant": quadrant.upper() if quadrant else None,
        "min_incidents": PRIORITY_MIN[level],
        "eligible": len(items),
        "items": items,
        "analysis": {
            "citywide_expected": round(city_expected, 1),
            "citywide_interval_80": list(
                model.nb_interval(city_expected, model.total_dispersion(city_lams, phi))
            ),
            "citywide_peak_window": f"{model.WEEKDAYS[cw]} {model.PERIODS[cp][0]}",
            "top_n": TOP_N,
            "top_share_of_citywide_pct": round(
                100 * sum(i["expected"] for i in top) / (city_expected or 1), 1
            ),
            "top_keys": [i["key"] for i in top],
            "rising": [i["key"] for i in items if i["trend"] == "rising"],
            "falling": [i["key"] for i in items if i["trend"] == "falling"],
            "recent_window_days": RECENT_DAYS,
            "ranking_check": _ranking_check(groups, city_times, days),
            "calibration": backtest
            and {
                "interval_80_coverage_pct": backtest["interval_80_coverage_pct"],
                "model_daily_mae": backtest["model_daily_mae"],
                "baseline_daily_mae": backtest["baseline_daily_mae"],
                "test_days": backtest["test_days"],
            },
            "dispersion": round(phi, 4),
        },
        "method": PRIORITY_METHOD,
        "caveat": CAVEAT,
    }


# ------------------------------------------------------------------ history
def incident_history(route=ANY, intersection=ANY, quadrant=ANY, category=ANY, lane=ANY,
                     direction=ANY, since="", until="", limit=100):  # fmt: skip
    total, rows = store().query_incidents(
        {"corridor_key": route, "intersection_key": intersection, "quadrant": quadrant,
         "category_group": category, "lane_position": lane, "travel_direction": direction},
        since or None, until or None, max(1, min(int(limit), 500)),
    )  # fmt: skip
    keep = ("uid", "start_local", "location_text", "description", "category_group", "category",
            "lane_impact", "lane_position", "travel_direction", "quadrant", "corridor_key",
            "intersection_key", "latitude", "longitude", "at_signalized_intersection",
            "stored_source", "live_sightings", "live_first_seen_utc", "live_last_seen_utc")  # fmt: skip
    return {"total_matching": total, "returned": len(rows),
            "incidents": [{k: r.get(k) for k in keep} for r in rows], "caveat": CAVEAT}  # fmt: skip


def travel_time_history(corridor="", segment="", since="", limit=500):
    rows = store().travel_times(corridor, segment, since, max(1, min(int(limit), 5000)))
    return {"returned": len(rows), "observations": rows,
            "note": "One row per segment per City update; accumulates while the collector runs."}  # fmt: skip


def status():
    s = store()
    return {**s.stats(), "recent_runs": s.runs(15), "recent_predictions": s.predictions(5),
            "last_collect_utc": s.get_meta("last_collect_utc"),
            "last_backfill_utc": s.get_meta("last_backfill_utc")}  # fmt: skip


def collect_now(include_archive=True):
    report = Collector(store()).collect(include_archive=include_archive)
    return {"report": report, "status": store().stats()}


# --------------------------------------------------------------------- live
def _fetch(url):
    """Kept as a seam for tests; the collector uses city_open_data.fetch."""
    return city_open_data.get_json(url, timeout=10, attempts=1)


def _live_fetcher(key, params=None):
    dataset, name = city_open_data.DATASETS[key]
    limit = 500 if key == "current_incidents" else 2000
    url = city_open_data.BASE.format(dataset) + f"$limit={limit}"
    payload = _fetch(url)
    rows = json.loads(payload)
    return rows, {"key": key, "dataset": dataset, "name": name, "url": url,
                  "sha256": hashlib.sha256(payload).hexdigest(), "rows": len(rows)}  # fmt: skip


def live(force=False):
    """Current City incidents/closures (60 s cache), stored in the database and linked
    to historic hotspots. Set BB_LIVE_PERSIST=0 to disable writing."""
    now = time.time()
    with _live_lock:
        if not force and _live["data"] and now - _live["at"] < LIVE_TTL_S:
            return {**_live["data"], "cache_age_s": round(now - _live["at"])}
        s = store()
        persist = os.environ.get("BB_LIVE_PERSIST", "1") != "0"
        collector = Collector(s, fetcher=_live_fetcher)
        ref = load_reference(s)
        cur_rows, cur_meta, cur_run = collector.pull("live", "current_incidents")
        clo_rows, clo_meta, clo_run = collector.pull("live", "closures")
        errors = [
            f"{k}: {v['error']}" for k, v in collector.report.items() if v["status"] == "failed"
        ]
        aliases = s.get_meta("road_aliases", {})
        cur_records = [
            r for r in (ingest.build_incident(x, ref, aliases) for x in cur_rows or []) if r
        ]
        if persist and cur_rows is not None:
            ins, upd = s.upsert_incidents(
                cur_records,
                "live",
                {r["uid"]: x for r, x in zip(cur_records, cur_rows, strict=False)},
            )
            s.record_live_sightings([r["uid"] for r in cur_records])
            s.put_reference("current_incidents", current_snapshot(cur_records))
            s.finish_run(cur_run, "ok", cur_meta, ins, upd)
        elif cur_rows is not None:
            s.finish_run(cur_run, "ok", cur_meta)
        if persist and clo_rows is not None:
            collector.store_closures(clo_rows, clo_meta, clo_run, ref)
        elif clo_rows is not None:
            s.finish_run(clo_run, "ok", clo_meta)
        index = _load()["intersection_index"]
        local_now = ingest.calgary_now().isoformat()

        intersections = _load()["intersections"]

        def nearest_hotspot(lat, lon, key=None):
            """Prefer the record's own parsed intersection; otherwise the busiest
            intersection within LINK_M (a one-off mis-typed location sitting at the
            same point must not outrank the real hotspot), then the nearest within
            NEARBY_M."""
            if key in intersections:
                i = intersections[key]
                m = dist_m(lat, lon, i["latitude"], i["longitude"]) if lat is not None else None
                return {"key": key, "distance_m": round(m) if m is not None else None,
                        "incidents_6mo": i["incidents"], "match": "intersection name"}  # fmt: skip
            if lat is None or lon is None:
                return None
            close = index.within(lat, lon, LINK_M)
            if close:
                hit, m = max(close, key=lambda t: (t[0]["item"]["incidents"], -t[1]))
            else:
                hit, m = index.nearest(lat, lon, rings=1)
                if not hit or m > NEARBY_M:
                    return None
            return {"key": hit["item"]["key"], "distance_m": round(m),
                    "incidents_6mo": hit["item"]["incidents"], "match": "location"}  # fmt: skip

        def parsed_key(raw):
            rec = ingest.build_incident(raw, ref, aliases)
            return rec["intersection_key"] if rec else None

        def num(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        incidents = [
            {
                "location_text": r.get("incident_info"),
                "description": r.get("description"),
                "start_utc": r.get("start_dt_utc"),
                "quadrant": r.get("quadrant"),
                "latitude": num(r.get("latitude")),
                "longitude": num(r.get("longitude")),
                "hotspot": nearest_hotspot(
                    num(r.get("latitude")), num(r.get("longitude")), parsed_key(r)
                ),
            }
            for r in cur_rows or []
        ]
        closures = [
            {
                "location_text": r.get("construction_info"),
                "description": " ".join((r.get("description") or "").replace("�", " ").split()),
                "start": r.get("start_dt"),
                "end": r.get("end_dt"),
                "hotspot": nearest_hotspot(num(r.get("latitude")), num(r.get("longitude"))),
            }
            for r in clo_rows or []
            if (r.get("start_dt") or "") <= local_now <= (r.get("end_dt") or "")
        ]
        data = {
            "fetched_at_epoch": now,
            "ok": not errors,
            "errors": errors,
            "persisted": persist and not errors,
            "sources": {
                k: city_open_data.DATASETS[k][0] for k in ("current_incidents", "closures")
            },
            "incidents": incidents,
            "active_closures": closures,
            "hotspot_threshold": HOTSPOT_MIN,
            "active_closures_at_hotspots": sum(
                1 for c in closures if c["hotspot"] and c["hotspot"]["incidents_6mo"] >= HOTSPOT_MIN
            ),
        }
        if not errors:
            _live.update(at=now, data=data)
            return {**data, "cache_age_s": 0}
        if _live["data"]:
            # Serve the last good response, flagged; failures are never cached.
            return {
                **_live["data"],
                "errors": errors,
                "ok": False,
                "cache_age_s": round(now - _live["at"]),
            }
        return {**data, "cache_age_s": 0}  # fmt: skip


# --------------------------------------------------------------------- ML info
BENCHMARK_SLICES = [
    ("All Calgary", {}),
    ("SE quadrant", {"quadrant": "SE"}),
    ("NE quadrant", {"quadrant": "NE"}),
    ("NW quadrant", {"quadrant": "NW"}),
    ("SW quadrant", {"quadrant": "SW"}),
    ("Collisions", {"category": "Collision"}),
    ("Deerfoot Trail", {"route": "Deerfoot Trail"}),
    ("Stoney Trail", {"route": "Stoney Trail"}),
    ("Glenmore Trail", {"route": "Glenmore Trail"}),
    ("Deerfoot Trail SB right lane",
     {"route": "Deerfoot Trail", "direction": "SB", "lane": "Right lane"}),
    ("Deerfoot Trail & Glenmore Trail SE", {"intersection": "Deerfoot Trail & Glenmore Trail SE"}),
]  # fmt: skip
_benchmark: dict = {"version": None, "data": None}


def ml_info():
    """What the forecasting models are, how they are chosen, and their settings."""
    from app.domain import forecast as fc

    try:
        import importlib.metadata as md

        lgb_version = md.version("lightgbm")
    except Exception:  # noqa: BLE001 - optional dependency
        lgb_version = None
    return {
        "task": "Forecast City-reported incidents per day and time-of-day period for any selection",
        "models": [
            {
                "name": "flat",
                "label": fc.FlatModel.label,
                "type": "Baseline",
                "how": "Average incidents per day over the training days.",
            },
            {
                "name": "bayes",
                "label": fc.BayesModel.label,
                "type": "Statistical",
                "how": "Weekday x period rates from the selection's history, shrunk toward the "
                f"citywide weekly shape with {fc.PRIOR_WEEKS:g} pseudo-weeks (empirical Bayes).",
            },
            {
                "name": "lightgbm",
                "label": fc.LightGBMModel.label,
                "type": "Machine learning",
                "library": f"LightGBM {lgb_version} (Microsoft, MIT licence), native API",
                "available": ml_forecast.available(),
                "how": "Gradient-boosted decision trees with a Poisson objective, trained per "
                "request on the selection's (day, period) counts.",
                "params": ml_forecast.PARAMS,
                "rounds": ml_forecast.NUM_ROUNDS,
                "features": [
                    {"name": "weekday", "meaning": "Day of week (categorical)"},
                    {
                        "name": "period",
                        "meaning": "Night / AM peak / Midday / PM peak / Evening (categorical)",
                    },
                    {"name": "is_weekend", "meaning": "Saturday or Sunday"},
                    {
                        "name": "is_holiday",
                        "meaning": f"Alberta statutory holiday ({len(ml_forecast.HOLIDAYS)} dates listed)",
                    },
                    {"name": "day_index", "meaning": "Days since the window start (trend)"},
                    {
                        "name": "city_cell_rate",
                        "meaning": "Citywide mean count for that weekday x period",
                    },
                    {"name": "bayes_rate", "meaning": "The empirical-Bayes rate for that cell"},
                ],
                "min_incidents": ml_forecast.MIN_INCIDENTS,
            },
        ],
        "selection": {
            "validation_days": fc.VALIDATION_DAYS,
            "validation_folds": fc.VALIDATION_FOLDS,
            "test_days": fc.TEST_DAYS,
            "default_model": fc.DEFAULT_MODEL,
            "rule": f"Use {fc.DEFAULT_MODEL} unless another model has lower daily error by more "
            f"than {fc.SWITCH_Z:g} standard errors across {fc.VALIDATION_FOLDS} rolling "
            f"{fc.VALIDATION_FOLD_DAYS}-day validation windows; then report every model on later "
            "test days that were not used to choose. Picking the lowest validation error "
            "outright chased noise (scripts/evaluate_model_selection.py).",
            "metric": "Mean absolute error of the daily incident count (MAE)",
            "interval": "80% negative-binomial range around the expected count (citywide "
            "overdispersion; daily counts vary more than Poisson allows)",
        },
        "periods": [p[0] for p in fc.PERIODS],
        "no_external_models": "No Hugging Face, LLM or pretrained weights are used.",
    }


def ml_benchmark():
    """Three-model comparison on standard selections (cached until data changes)."""
    d = _load()
    version = _state["version"]
    if _benchmark["version"] == version and _benchmark["data"]:
        return _benchmark["data"]
    rows = []
    for label, sel in BENCHMARK_SLICES:
        p = predict(**sel, horizon_days=7)
        bt = p["backtest"] or {}
        rows.append(
            {
                "slice": label,
                "selection": sel,
                "incidents": p["history"]["incidents"],
                "selected_model": bt.get("selected_model"),
                "models": {k: {"validation_mae": v["validation_daily_mae"], "test_mae": v["test_daily_mae"],
                               "test_coverage_pct": v["test_interval_80_coverage_pct"]}
                           for k, v in (bt.get("models") or {}).items()},
                "best_on_test": min((bt.get("models") or {"-": {"test_daily_mae": 0}}).items(),
                                    key=lambda kv: kv[1]["test_daily_mae"])[0],
                "forecast_7d": p["expected_total"],
                "interval_80": p["interval_80"],
            }
        )  # fmt: skip
    wins = Counter(r["best_on_test"] for r in rows)
    data = {
        "computed_for_data_version": version,
        "observed_days": len(d["observed_days"]),
        "slices": rows,
        "best_on_test_counts": dict(wins),
        "selected_counts": dict(Counter(r["selected_model"] for r in rows)),
    }
    _benchmark.update(version=version, data=data)
    return data
