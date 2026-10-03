"""Build a corridor study from one intersection's City data, and estimate the delay a
typical lane-blocking incident causes there (modeled seconds per vehicle).

Every derived value is listed in `assumptions` with its basis so the UI can show it and
the user can edit it before running.
"""

import hashlib
import json
import math
import statistics
from collections import Counter
from datetime import datetime

from app.application import disruptions
from app.domain.models import IncidentSpec, Intervention, Scenario

PEAK_HOUR_FACTOR = 0.10  # share of daily volume in the peak hour (assumption)
PEAK_DIRECTION_FACTOR = 0.55  # share of peak-hour volume in the peak direction (assumption)
LANE_CAPACITY_VPH = 900  # per-lane design flow used to choose 1-3 synthetic lanes
MAX_ARTERIAL_VPH = 1800.0  # Scenario.main_vph upper bound for the synthetic arterial
DEFAULT_INCIDENT_S = 1200  # 20 minutes when no measured durations exist (assumption)
ALL_OPTIONS = ["signal_control", "incident_clearance", "turn_lane", "turn_ban"]
EST_SEEDS = (42, 143)


def _peak_flow(volume):
    return volume * PEAK_HOUR_FACTOR * PEAK_DIRECTION_FACTOR


def fits_arterial_model(volume) -> bool:
    """Whether build_study can represent this volume without capping (freeways cannot)."""
    return not volume or _peak_flow(volume) <= MAX_ARTERIAL_VPH


def evidence(key):
    d = disruptions._load()
    item = d["intersections"].get(key)
    if item is None:
        return None
    rows = item["_rows"]
    n = len(rows)
    days = len(d["observed_days"])
    lane_blocking = [r for r in rows if (r["lane_impact_level"] or 0) >= 1]
    peak_lane_blocking = [r for r in lane_blocking if "peak" in r["period"]]
    unspecified = sum(r["category"] == "Traffic incident (unspecified)" for r in rows)
    weekdays = sum(1 for x in d["observed_days"] if x.weekday() < 5)
    live = disruptions._live.get("data") or {}
    live_here = [i for i in live.get("incidents", []) if (i.get("hotspot") or {}).get("key") == key]
    durations = [
        (datetime.fromisoformat(r["live_last_seen_utc"]) - datetime.fromisoformat(
            r["live_first_seen_utc"])).total_seconds()
        for r in rows
        if r.get("live_sightings", 0) >= 2 and r.get("live_first_seen_utc")
    ]  # fmt: skip
    return {
        "item": item,
        "rows": rows,
        "incidents": n,
        "observed_days": days,
        "per_month": n / max(1, days) * 30.4,
        "lane_blocking": len(lane_blocking),
        "lane_blocking_pct": 100 * len(lane_blocking) / max(1, n),
        "peak_lane_blocking": len(peak_lane_blocking),
        "unspecified": unspecified,
        "unspecified_pct": 100 * unspecified / max(1, n),
        "collisions": item["collisions"],
        "vulnerable_road_user": item["vulnerable_road_user"],
        "signal_faults": item["signal_faults"],
        "weekday_peak_periods": weekdays * 2,
        "live_now": live_here[0]["description"] if live_here else None,
        "observed_durations_s": durations,
    }


def build_study(key):
    """Scenario + assumptions + evidence for one intersection, or None if unknown."""
    e = evidence(key)
    if e is None:
        return None
    item, rows = e["item"], e["rows"]
    assumptions, warnings = [], []
    volume = item["volume_2024"]
    if volume:
        main_vph = _peak_flow(volume)
        assumptions.append(
            f"Arterial arrivals {main_vph:,.0f} veh/h/direction = 2024 City volume "
            f"{volume:,.0f} veh/day x {PEAK_HOUR_FACTOR:.0%} peak hour x "
            f"{PEAK_DIRECTION_FACTOR:.0%} peak direction."
        )
    else:
        main_vph = 900.0
        assumptions.append("No 2024 volume matched this road; arterial arrivals set to 900 veh/h.")
    if main_vph > MAX_ARTERIAL_VPH:
        warnings.append(
            f"Estimated {main_vph:,.0f} veh/h exceeds the synthetic arterial model "
            f"(max {MAX_ARTERIAL_VPH:,.0f}); capped. Freeway interchanges are not represented "
            "by a signalized corridor."
        )
    main_vph = max(50.0, min(MAX_ARTERIAL_VPH, main_vph))
    lanes = max(1, min(3, math.ceil(main_vph / LANE_CAPACITY_VPH)))
    assumptions.append(f"{lanes} arterial lane(s) per direction (~{LANE_CAPACITY_VPH} veh/h/lane).")

    cross_road = item["roads"][1]
    corridors = {c["key"]: c for c in disruptions._load()["summary"]["top_corridors"]}
    cross_key = (
        f"{cross_road} {item['quadrant']}"
        if cross_road and cross_road[0].isdigit() and item["quadrant"]
        else cross_road
    )
    cross_volume = (corridors.get(cross_key) or {}).get("median_volume_2024")
    if cross_volume:
        cross_vph = max(20.0, min(600.0, _peak_flow(cross_volume)))
        assumptions.append(
            f"Cross-street arrivals {cross_vph:,.0f} veh/h from {cross_road} 2024 volume "
            f"{cross_volume:,.0f} veh/day (capped at 600)."
        )
    else:
        cross_vph = 160.0
        assumptions.append("No cross-street volume available; cross arrivals kept at 160 veh/h.")

    control = "signal" if item["signalized"] else "priority"
    assumptions.append(
        f"Hotspot junction J2 is {'signalized' if item['signalized'] else 'not signalized'} "
        "(City traffic-signal inventory within 75 m)."
    )
    turn_share = 0.10
    assumptions.append("Left-turn share 10% of arterial traffic (no turning counts available).")

    blocking = [r for r in rows if (r["lane_impact_level"] or 0) >= 1]
    dirs = Counter(r["travel_direction"] for r in blocking if r["travel_direction"])
    top_dir = dirs.most_common(1)[0][0] if dirs else "NB"
    direction = "east" if top_dir in ("NB", "EB") else "west"
    multi = sum((r["lane_impact_level"] or 0) >= 2 for r in blocking)
    lanes_blocked = 2 if blocking and multi / len(blocking) >= 0.5 and lanes >= 2 else 1
    durations = e["observed_durations_s"]
    if len(durations) >= 5:
        duration = int(max(60, min(3600, statistics.median(durations))))
        assumptions.append(
            f"Incident lasts {duration // 60} min (median of {len(durations)} live sightings)."
        )
    else:
        duration = DEFAULT_INCIDENT_S
        assumptions.append(
            f"Incident lasts {duration // 60} min (assumption: fewer than 5 measured durations "
            "from live sightings so far)."
        )
    assumptions.append(
        f"Incident blocks {lanes_blocked} lane(s) {top_dir} (most common direction/impact of "
        f"{len(blocking)} lane-blocking incidents here), mapped to {direction}bound J2."
    )
    weight = min(1.0, e["peak_lane_blocking"] / max(1, e["weekday_peak_periods"]))
    assumptions.append(
        f"Incident conditions weighted {weight:.1%}: {e['peak_lane_blocking']} peak-period "
        f"lane-blocking incidents / {e['weekday_peak_periods']} weekday peak periods observed."
    )
    has_incident = bool(blocking)
    if not has_incident:
        warnings.append("No lane-blocking incidents recorded here; incident options are skipped.")
    options = [o for o in ALL_OPTIONS if has_incident or o != "incident_clearance"]
    scenario = Scenario(
        main_vph=round(main_vph),
        cross_vph=round(cross_vph),
        arterial_lanes=lanes,
        junction_control=control,
        turn_share=turn_share,
        incident=IncidentSpec(
            direction=direction, start_s=120, duration_s=duration, lanes_blocked=lanes_blocked,
            label=f"Typical lane-blocking incident at {key}",
        ) if has_incident else None,
        incident_weight=round(weight, 4) if has_incident else 1.0,
        extra_options=options,
        demand_source=(
            f"Estimated for {key} from City 2024 volumes; not measured turning counts"
        )[:500],
    )  # fmt: skip
    public = {
        k: e[k]
        for k in ("incidents", "observed_days", "per_month", "lane_blocking", "lane_blocking_pct",
                  "peak_lane_blocking", "unspecified", "unspecified_pct", "collisions",
                  "vulnerable_road_user", "signal_faults", "weekday_peak_periods", "live_now")
    }  # fmt: skip
    return {
        "intersection_key": key,
        "scenario": scenario.model_dump(),
        "assumptions": assumptions,
        "warnings": warnings,
        "evidence": public,
        "geometry": "Synthetic three-junction corridor; J2 stands in for this intersection",
    }


def context_for(key):
    """Compact evidence attached to a job so the summary can cite six-month facts."""
    study = build_study(key)
    return study and {"intersection_key": key, "evidence": study["evidence"]}


def estimate_incident_delay(key, simulator, force=False):
    """Modeled extra seconds of delay per vehicle from one typical lane-blocking incident."""
    study = build_study(key)
    if study is None:
        return None
    scenario = Scenario(**study["scenario"])
    e = study["evidence"]
    base = {
        "intersection_key": key,
        "unspecified_pct": round(e["unspecified_pct"], 1),
        "unspecified": e["unspecified"],
        "incidents": e["incidents"],
        "lane_blocking": e["lane_blocking"],
    }
    if not scenario.incident:
        return {**base, "status": "no_lane_blocking_incidents"}
    params = json.dumps({"scenario": study["scenario"], "seeds": EST_SEEDS}, sort_keys=True)
    params_sha = hashlib.sha256(params.encode()).hexdigest()
    store = disruptions.store()
    if not force and (cached := store.get_estimate(key, params_sha)):
        return {**cached, "cached": True}
    reference = Intervention("reference", "Reference", 0.5, scenario.arterial_lanes, 0)
    normal = scenario.model_copy(update={"incident": None})
    trials = []
    for seed in EST_SEEDS:
        with_i = simulator.run(scenario, reference, seed)["metrics"]
        without = simulator.run(normal, reference, seed)["metrics"]
        trials.append((with_i, without))
    extra = [(w["total_delay_s"] - n["total_delay_s"]) for w, n in trials]
    planned = [n["planned"] for _, n in trials]
    axis = "east_mean_delay_s" if scenario.incident.direction == "east" else "west_mean_delay_s"
    direction_extra = [w[axis] - n[axis] for w, n in trials]
    per_vehicle = statistics.mean(x / max(1, p) for x, p in zip(extra, planned, strict=True))
    hours = statistics.mean(extra) / 3600
    result = {
        **base,
        "status": "ok",
        "extra_delay_s_per_vehicle": round(per_vehicle, 1),
        "extra_delay_s_per_vehicle_blocked_direction": round(statistics.mean(direction_extra), 1),
        "vehicle_hours_lost_per_incident": round(hours, 2),
        "six_month_vehicle_hours_lost": round(hours * e["peak_lane_blocking"], 1),
        "normal_delay_s_per_vehicle": round(
            statistics.mean(n["mean_delay_s"] for _, n in trials), 1
        ),
        "incident": scenario.incident.model_dump(),
        "seeds": list(EST_SEEDS),
        "assumptions": study["assumptions"],
        "warnings": study["warnings"],
        "method": (
            "SUMO reference plan on the synthetic corridor with vs without one typical incident "
            "at J2, same arrivals, mean of two seeds. Six-month figure multiplies by peak-period "
            "lane-blocking incidents recorded here."
        ),
    }
    store.put_estimate(key, params_sha, result)
    return {**result, "cached": False}
