"""Turn raw City rows into parsed, geo-enriched records and aggregate summaries.

Pure transformation (no network or database); used by the backfill script, the
collector and the read service.
"""

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta

from app.domain import disruption_rules as rules
from app.domain.geo import LineIndex, PointIndex

SIGNAL_RADIUS_M = 75
CAMERA_RADIUS_M = 500
VOLUME_RADIUS_M = 150
DEDUP_RULE = (
    "normalized location text + start timestamp; latest update kept "
    "(heuristic, not an authoritative ID)"
)


def local_zone():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/Edmonton")
    except (ImportError, KeyError, OSError):
        return None


def to_local(utc_naive):
    """UTC naive -> Calgary naive wall-clock time."""
    zone = local_zone()
    if zone is None:  # Windows without tzdata: MDT approximation (1 h off in winter)
        return utc_naive - timedelta(hours=6)
    return utc_naive.replace(tzinfo=UTC).astimezone(zone).replace(tzinfo=None)


def calgary_now():
    return to_local(datetime.now(UTC).replace(tzinfo=None))


def window_start(months, today=None):
    """First local day of the month `months` back (complete months + current partial)."""
    today = today or calgary_now().date()
    y, m = today.year, today.month - months
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, 1)


class Reference:
    """Cameras, signals and 2024 volumes with nearest-feature indexes."""

    def __init__(self, cam_rows, sig_rows, vol_rows):
        self.cameras = []
        for r in cam_rows or []:
            try:
                lon, lat = r["point"]["coordinates"]
            except (KeyError, TypeError, ValueError):
                continue
            self.cameras.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "camera_id": (r.get("camera_url") or {}).get("description"),
                    "camera_location": r.get("camera_location"),
                    "quadrant": r.get("quadrant"),
                    "image_url": (r.get("camera_url") or {}).get("url"),
                }
            )
        self.signals = []
        for r in sig_rows or []:
            try:
                lat, lon = float(r["latitude"]), float(r["longitude"])
            except (KeyError, TypeError, ValueError):
                continue
            first, second = (
                rules.norm_road(r.get("firstroad")),
                rules.norm_road(r.get("secondroad")),
            )
            self.signals.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "signal_id": r.get("unitid") or r.get("mistno"),
                    "signal_name": f"{first} & {second} {r.get('quadrant', '')}".strip(),
                    "int_type": r.get("int_type"),
                    "installed": r.get("instdate"),
                    "quadrant": r.get("quadrant"),
                }
            )
        self.volumes = []
        for r in vol_rows or []:
            geo = r.get("multilinestring") or {}
            try:
                v = float(r.get("volume"))
            except (TypeError, ValueError):
                continue
            if geo.get("coordinates"):
                self.volumes.append(
                    {"section": r.get("section_name"), "volume": v, "year": r.get("year"),
                     "coords": geo["coordinates"]}
                )  # fmt: skip
        self.cam_idx = PointIndex(self.cameras)
        self.sig_idx = PointIndex(self.signals)
        self.vol_idx = LineIndex(self.volumes)
        self.cameras_by_id = {c["camera_id"]: c for c in self.cameras}

    def enrich(self, rec, lat, lon):
        cam, cd = self.cam_idx.nearest(lat, lon, rings=3)
        sig, sd = self.sig_idx.nearest(lat, lon)
        # Only accept a volume segment on the record's own road; at interchanges the
        # geometrically nearest segment is often the crossing freeway.
        prefix = rules.section_prefix(rec.get("primary_road"))
        vol, vd = (
            self.vol_idx.nearest(lat, lon, lambda seg: seg["section"].upper().startswith(prefix))
            if prefix
            else (None, float("inf"))
        )
        rec.update(
            {
                "nearest_camera": cam["camera_id"] if cam else None,
                "nearest_camera_location": cam["camera_location"] if cam else None,
                "nearest_camera_m": round(cd) if cam else None,
                "camera_within_500m": bool(cam and cd <= CAMERA_RADIUS_M),
                "nearest_signal_id": sig["signal_id"] if sig else None,
                "nearest_signal": sig["signal_name"] if sig else None,
                "nearest_signal_m": round(sd) if sig else None,
                "at_signalized_intersection": bool(sig and sd <= SIGNAL_RADIUS_M),
                "volume_2024_section": vol["section"] if vol and vd <= VOLUME_RADIUS_M else None,
                "volume_2024": vol["volume"] if vol and vd <= VOLUME_RADIUS_M else None,
            }
        )


def build_incident(raw, ref, aliases):
    """One City incident row (archive or live feed) -> parsed record, or None if invalid."""
    try:
        lat, lon = float(raw["latitude"]), float(raw["longitude"])
        if not (49 < lat < 53 and -116 < lon < -112):
            return None
        start = rules.parse_ts(raw["start_dt_utc"])
    except (KeyError, TypeError, ValueError):
        return None
    desc = " ".join((raw.get("description") or "").split())
    group, cat = rules.classify_incident(desc)
    impact, impact_lvl = rules.lane_impact(desc)
    location = (raw.get("incident_info") or "").strip()
    loc = rules.parse_location(location, raw.get("quadrant"), aliases)
    mod = rules.parse_ts(raw.get("modified_dt_utc"))
    local = to_local(start)
    rec = {
        "uid": rules.incident_uid(location, start),
        "incident_id": raw.get("id"),
        "start_utc": start.isoformat(),
        "start_local": local.strftime("%Y-%m-%d %H:%M"),
        "date_local": local.strftime("%Y-%m-%d"),
        "month": local.strftime("%Y-%m"),
        "season": rules.SEASON[local.month],
        "weekday": local.strftime("%a"),
        "is_weekend": local.weekday() >= 5,
        "hour_local": local.hour,
        "period": rules.peak_period(local),
        "last_update_utc": mod.isoformat() if mod else None,
        "update_lag_min": round((mod - start).total_seconds() / 60, 1) if mod else None,
        "location_text": location,
        "description": desc,
        "category_group": group,
        "category": cat,
        "lane_impact": impact,
        "lane_impact_level": impact_lvl,
        "lane_position": rules.lane_position(desc),
        "ems_involved": rules.ems_involved(desc),
        "travel_direction": loc["travel_direction"] or rules.dir_from_desc(desc),
        "quadrant": raw.get("quadrant") or loc["quadrant_parsed"],
        "primary_road": loc["primary_road"],
        "cross_road": loc["roads"][1] if len(loc["roads"]) > 1 else None,
        "corridor_key": loc["corridor_key"],
        "intersection_key": loc["intersection_key"],
        "latitude": lat,
        "longitude": lon,
    }
    ref.enrich(rec, lat, lon)
    return rec


def build_incidents(raw_rows, ref, aliases):
    """Parse and deduplicate (latest City update wins). Returns records, raw-by-uid, stats."""
    latest, discarded = {}, 0
    for raw in sorted(
        raw_rows, key=lambda r: r.get("modified_dt_utc") or r.get("start_dt_utc") or ""
    ):
        rec = build_incident(raw, ref, aliases)
        if rec is None:
            discarded += 1
            continue
        latest[rec["uid"]] = (rec, raw)
    records = sorted((r for r, _ in latest.values()), key=lambda r: r["start_utc"])
    stats = {
        "raw_rows": len(raw_rows),
        "deduplicated": len(records),
        "duplicates_removed": len(raw_rows) - discarded - len(records),
        "discarded_bad_coordinates": discarded,
    }
    return records, {u: raw for u, (_, raw) in latest.items()}, stats


def build_closure(raw, ref, aliases):
    try:
        lat, lon = float(raw["latitude"]), float(raw["longitude"])
    except (KeyError, TypeError, ValueError):
        lat = lon = None
    s, e = rules.parse_ts(raw.get("start_dt")), rules.parse_ts(raw.get("end_dt"))
    desc = " ".join((raw.get("description") or "").replace("�", " ").split())
    location = (raw.get("construction_info") or "").strip()
    loc = rules.parse_location(location, None, aliases)
    rec = {
        "uid": rules.closure_uid(location, s, desc),
        "location_text": location,
        "description": desc,
        "start_local": s.strftime("%Y-%m-%d %H:%M") if s else None,
        "end_local": e.strftime("%Y-%m-%d %H:%M") if e else None,
        "duration_days": round((e - s).total_seconds() / 86400, 1) if s and e else None,
        **rules.classify_closure(desc + " " + location),
        "quadrant": loc["quadrant_parsed"],
        "primary_road": loc["primary_road"],
        "cross_road": loc["roads"][1] if len(loc["roads"]) > 1 else None,
        "corridor_key": loc["corridor_key"],
        "latitude": lat,
        "longitude": lon,
    }
    if lat is not None:
        ref.enrich(rec, lat, lon)
    return rec


def closure_status(rec, now_local, window_start_local):
    """Status is evaluated at read time so it never goes stale."""
    now = now_local.strftime("%Y-%m-%d %H:%M")
    start, end = rec.get("start_local"), rec.get("end_local")
    status = (
        "Active" if start and end and start <= now <= end
        else "Scheduled (future)" if start and start > now
        else "Ended" if end and end < now
        else "Unknown"
    )  # fmt: skip
    win = window_start_local.strftime("%Y-%m-%d %H:%M")
    return {
        **rec,
        "status_at_retrieval": status,
        "overlaps_window": bool(start and end and start <= now and end >= win),
        "started_before_window": bool(start and start < win),
    }


def travel_time_observations(raw_rows):
    out = []
    for r in raw_rows:
        try:
            minutes = float(r["travel_time_mins"]) if r.get("travel_time_mins") else None
        except (TypeError, ValueError):
            minutes = None
        out.append(
            {
                "corridor": r.get("corridor"),
                "segment": r.get("road_segment"),
                "travel_time_min": minutes,
                "city_updated_local": (r.get("last_update") or "")[:19] or None,
            }
        )
    return out


def summarize(incidents, closures, signals, win_start, now_local):
    """Aggregates for the summary JSON, workbook, API and MCP. Inputs are parsed records."""
    n = len(incidents) or 1
    lane_blocking = lambda rows: sum(1 for r in rows if (r["lane_impact_level"] or 0) >= 1)
    months = sorted({r["month"] for r in incidents})
    groups = sorted({r["category_group"] for r in incidents})
    by_cat = []
    for cat, count in Counter(r["category"] for r in incidents).most_common():
        rows = [r for r in incidents if r["category"] == cat]
        by_cat.append(
            {
                "category_group": rows[0]["category_group"],
                "category": cat,
                "incidents": count,
                "share_pct": round(100 * count / n, 2),
                "lane_blocking": lane_blocking(rows),
                "multi_lane_or_closure": sum(1 for r in rows if (r["lane_impact_level"] or 0) >= 2),
                "at_signalized_intersection": sum(r["at_signalized_intersection"] for r in rows),
                "peak_period": sum(1 for r in rows if "peak" in r["period"]),
                **{m: sum(1 for r in rows if r["month"] == m) for m in months},
            }
        )
    monthly = []
    for m in months:
        rows = [r for r in incidents if r["month"] == m]
        days = len({r["date_local"] for r in rows})
        monthly.append(
            {
                "month": m,
                "incidents": len(rows),
                "days_with_data": days,
                "per_day": round(len(rows) / days, 2) if days else None,
                **{g: sum(1 for r in rows if r["category_group"] == g) for g in groups},
                "lane_blocking": lane_blocking(rows),
            }
        )
    wd = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hour_wd = [
        {
            "hour_local": h,
            **{
                d: sum(1 for r in incidents if r["hour_local"] == h and r["weekday"] == d)
                for d in wd
            },
            "total": sum(1 for r in incidents if r["hour_local"] == h),
        }
        for h in range(24)
    ]

    def hotspot(key_fn, extra=None):
        bucket = defaultdict(list)
        for r in incidents:
            k = key_fn(r)
            if k:
                bucket[k].append(r)
        out = []
        for k, rows in bucket.items():
            vols = sorted(r["volume_2024"] for r in rows if r["volume_2024"])
            rec = {
                "key": k,
                "incidents": len(rows),
                "collisions": sum(r["category_group"] == "Collision" for r in rows),
                "vulnerable_road_user": sum(
                    r["category_group"] == "Vulnerable road user" for r in rows
                ),
                "signal_faults": sum(r["category_group"] == "Signal fault" for r in rows),
                "stalled": sum(r["category"] == "Stalled vehicle" for r in rows),
                "lane_blocking": lane_blocking(rows),
                "multi_lane_or_closure": sum(1 for r in rows if (r["lane_impact_level"] or 0) >= 2),
                "peak_period": sum(1 for r in rows if "peak" in r["period"]),
                "months_active": len({r["month"] for r in rows}),
                "at_signal_share_pct": round(
                    100 * sum(r["at_signalized_intersection"] for r in rows) / len(rows), 1
                ),
                "median_volume_2024": vols[len(vols) // 2] if vols else None,
                "volume_matched_incidents": len(vols),
                "quadrants": ",".join(sorted({r["quadrant"] or "?" for r in rows})),
                "first_seen": rows[0]["date_local"],
                "last_seen": rows[-1]["date_local"],
            }
            if extra:
                rec.update(extra(rows))
            out.append(rec)
        return sorted(out, key=lambda x: (-x["incidents"], -x["lane_blocking"]))

    corridors = hotspot(lambda r: r["corridor_key"])
    closure_by_corr = Counter(
        c["corridor_key"] for c in closures if c["overlaps_window"] and c["corridor_key"]
    )
    for c in corridors:
        c["closures_overlapping_window"] = closure_by_corr.get(c["key"], 0)
        c["incidents_per_10k_daily_veh"] = (
            round(c["incidents"] / (c["median_volume_2024"] / 10000), 2)
            if c["median_volume_2024"] and c["volume_matched_incidents"] >= 5
            else None
        )
    sig_name = {s["signal_id"]: s["signal_name"] for s in signals}
    sig_hot = hotspot(lambda r: r["nearest_signal_id"] if r["at_signalized_intersection"] else None)
    for s in sig_hot:
        s["signal_name"] = sig_name.get(s["key"])
    cam_hot = hotspot(
        lambda r: r["nearest_camera"] if r["camera_within_500m"] else None,
        lambda rows: {"camera_location": rows[0]["nearest_camera_location"]},
    )
    days = {r["date_local"] for r in incidents}
    all_days = [win_start + timedelta(i) for i in range((now_local.date() - win_start).days + 1)]
    return {
        "headline": {
            "incidents": len(incidents),
            "window_days": len(all_days),
            "incidents_per_day": round(len(incidents) / max(1, len(all_days)), 2),
            "lane_blocking_pct": round(100 * lane_blocking(incidents) / n, 1),
            "at_signalized_intersection_pct": round(
                100 * sum(r["at_signalized_intersection"] for r in incidents) / n, 1
            ),
            "within_500m_of_camera_pct": round(
                100 * sum(r["camera_within_500m"] for r in incidents) / n, 1
            ),
            "closures_in_feed": sum(1 for c in closures if not c.get("removed_from_feed_utc")),
            "closures_overlapping_window": sum(c["overlaps_window"] for c in closures),
            "category_groups": dict(Counter(r["category_group"] for r in incidents).most_common()),
        },
        "by_category": by_cat,
        "monthly": monthly,
        "hour_by_weekday": hour_wd,
        "by_period": [{"period": p, "incidents": c} for p, c in Counter(r["period"] for r in incidents).most_common()],
        "by_quadrant": [
            {
                "quadrant": q,
                "incidents": sum(1 for r in incidents if (r["quadrant"] or "Unknown") == q),
                **{g: sum(1 for r in incidents if (r["quadrant"] or "Unknown") == q and r["category_group"] == g) for g in groups},
            }
            for q in sorted({r["quadrant"] or "Unknown" for r in incidents})
        ],
        "by_lane_impact": [{"lane_impact": k, "incidents": v} for k, v in Counter(r["lane_impact"] for r in incidents).most_common()],
        "top_corridors": corridors[:100],
        "top_intersections": hotspot(lambda r: r["intersection_key"])[:100],
        "signal_hotspots": sig_hot[:100],
        "camera_hotspots": cam_hot[:100],
        "closures_by_type": [
            {"closure_type": k, "closures": v}
            for k, v in Counter(c["closure_type"] for c in closures if c["overlaps_window"]).most_common()
        ],
        "closures_by_status": [
            {"status": k, "closures": v}
            for k, v in Counter(c["status_at_retrieval"] for c in closures).most_common()
        ],
        "category_rules": [{"pattern": p, "category_group": g, "category": c} for p, g, c in rules.INCIDENT_RULES],
        "days_without_any_incident": [d.isoformat() for d in all_days if d.isoformat() not in days],
    }  # fmt: skip
