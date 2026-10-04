"""Pure text rules for City of Calgary incident/closure records.

No I/O. Shared by the backfill script, the collector, the API and the MCP server
so every path classifies and parses records identically.
"""

import hashlib
import re
from collections import Counter, defaultdict
from datetime import datetime

ABBREV = {
    "tr": "trail",
    "tr.": "trail",
    "av": "avenue",
    "ave": "avenue",
    "st": "street",
    "dr": "drive",
    "bv": "boulevard",
    "blvd": "boulevard",
    "rd": "road",
    "hwy": "highway",
    "cr": "crescent",
    "pl": "place",
    "gt": "gate",
    "wy": "way",
    "pkwy": "parkway",
}
QUADRANT_RE = re.compile(r"\s+(NE|NW|SE|SW)\.?$", re.IGNORECASE)
DIRWORD_RE = re.compile(r"^(north|south|east|west)bound\s+", re.IGNORECASE)
SPLIT_RE = re.compile(
    r"\s+(?:and|at|&|approaching|near|between|past|onto|from|to|before|after|under|over|off)\s+",
    re.IGNORECASE,
)

# City volume section codes (e.g. DEERFOOT12, 16AV/TCH5, 14STSW1) abbreviate road names.
SECTION_PREFIX = {
    "Deerfoot Trail": "DEERFOOT",
    "Stoney Trail": "STONEY",
    "Glenmore Trail": "GLENMORE",
    "Crowchild Trail": "CRWCHLD",
    "Memorial Drive": "MEMOR",
    "Macleod Trail": "MACLEOD",
    "Barlow Trail": "BARLOW",
    "McKnight Boulevard": "MCKNIGHT",
    "Metis Trail": "METISTR",
    "Shaganappi Trail": "SHGNPPI",
    "Sarcee Trail": "SARCEE",
    "Peigan Trail": "PEIGAN",
    "Anderson Road": "ANDERSON",
    "Beddington Trail": "BEDDING",
    "John Laurie Boulevard": "JLBV",
    "Centre Street": "CENTRE",
    "Bow Trail": "BOW",
    "Bowness Road": "BOWNESS",
    "Symons Valley Road": "SYMONSVALLEY",
    "Highway 22x": "22X",
}

INCIDENT_RULES = [
    # (pattern, category_group, category) — evaluated in order, first match wins.
    (r"pedestrian", "Vulnerable road user", "Pedestrian involved"),
    (r"cyclist|bicycle", "Vulnerable road user", "Cyclist involved"),
    (r"multi[- ]vehicle", "Collision", "Multi-vehicle collision"),
    (r"two vehicle", "Collision", "Two-vehicle collision"),
    (r"single vehicle", "Collision", "Single-vehicle collision"),
    (r"stalled", "Vehicle breakdown", "Stalled vehicle"),
    (r"flashing red", "Signal fault", "Signals flashing red"),
    (
        r"signals? (?:are )?blank|lights? (?:are )?(?:out|blank)",
        "Signal fault",
        "Signals blank/dark",
    ),
    (r"power outage", "Signal fault", "Power outage"),
    (r"signals? work in progress", "Signal fault", "Signal work in progress"),
    (r"signals? issue|signal", "Signal fault", "Signal issue (other)"),
    (r"police", "Police / emergency activity", "Police incident"),
    (r"water emergency|water main", "Road works / utility", "Emergency utility repair"),
    (r"road work|roadwork|construction", "Road works / utility", "Road work"),
    (r"hazardous road|loose tire|debris|object on", "Road hazard", "Road hazard / debris"),
    (r"weather|snow|ice|flood", "Road hazard", "Severe weather"),
    (
        r"ramp is closed|road is closed|road closed|is closed|closed",
        "Closure",
        "Unplanned road/ramp closure",
    ),
    (r"traffic incident", "Traffic incident (unspecified)", "Traffic incident (unspecified)"),
]

SEASON = {
    m: s
    for s, ms in {
        "Winter": (12, 1, 2),
        "Spring": (3, 4, 5),
        "Summer": (6, 7, 8),
        "Fall": (9, 10, 11),
    }.items()
    for m in ms
}


def norm_road(name):
    words = re.sub(r"[^\w\s.]", " ", name or "").lower().split()
    words = [ABBREV.get(w, w).rstrip(".") for w in words]
    words = [re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", w) for w in words]
    words = [w.capitalize() for w in words]
    return " ".join(
        "Mc" + w[2:].capitalize() if w.startswith("Mc") and len(w) > 3 else w for w in words
    )


def corridor_key(road, quad):
    if not road:
        return None
    # Numbered streets/avenues repeat in every quadrant; named trails span quadrants.
    return f"{road} {quad}" if quad and road[0].isdigit() else road


def parse_location(info, quadrant=None, aliases=None):
    aliases = aliases or {}
    text = " ".join((info or "").split())
    direction = None
    m = DIRWORD_RE.match(text)
    if m:
        direction = m.group(1)[0].upper() + "B"
        text = text[m.end() :]
    qm = QUADRANT_RE.search(text)
    quad = (qm.group(1).upper() if qm else None) or (quadrant or None)
    if qm:
        text = text[: qm.start()]
    roads = [norm_road(p) for p in SPLIT_RE.split(text) if p.strip()]
    roads = [aliases.get(r, r) for r in roads if r]
    primary = roads[0] if roads else None
    return {
        "travel_direction": direction,
        "quadrant_parsed": quad,
        "roads": roads,
        "primary_road": primary,
        "corridor_key": corridor_key(primary, quad),
        "intersection_key": (" & ".join(sorted(roads[:2])) + (f" {quad}" if quad else ""))
        if len(roads) >= 2
        else None,
    }


def build_road_aliases(texts):
    """Map bare names ("Deerfoot") to the dominant full road name ("Deerfoot Trail")."""
    seen = Counter()
    for t in texts:
        seen.update(parse_location(t)["roads"])
    full = defaultdict(Counter)
    for n, c in seen.items():
        if " " in n and not n[0].isdigit():
            full[n.split()[0]][n] = c
    aliases = {}
    for bare, cands in full.items():
        ranked = cands.most_common(2)
        # Only alias when one full name clearly dominates (5x the runner-up).
        if bare in seen and (len(ranked) == 1 or ranked[0][1] >= 5 * ranked[1][1]):
            aliases[bare] = ranked[0][0]
    return aliases


def section_prefix(road):
    """Volume-section prefix for a parsed road name, or None when unknown."""
    if not road:
        return None
    if road in SECTION_PREFIX:
        return SECTION_PREFIX[road]
    m = re.match(r"(\d+) (Avenue|Street)", road)
    return f"{m.group(1)}{'AV' if m.group(2) == 'Avenue' else 'ST'}" if m else None


def classify_incident(desc):
    d = (desc or "").lower()
    for pat, group, cat in INCIDENT_RULES:
        if re.search(pat, d):
            return group, cat
    if "blocking" in d or "ongoing incident" in d or "ramp" in d:
        return "Traffic incident (unspecified)", "Lane blockage (cause unspecified)"
    return "Other", "Other"


def lane_impact(desc):
    d = (desc or "").lower()
    if re.search(
        r"road is closed|road closed|all (?:the )?lanes|closed (?:nb|sb|eb|wb)|is closed"
        r"|full closure|multiple road closures",
        d,
    ):
        return "Full closure", 3
    if re.search(
        r"multiple lanes|two (?:right|left) lanes|right two|left two|(?:right|left|nb|sb|eb|wb) lanes",
        d,
    ):
        return "Multiple lanes blocked", 2
    if re.search(r"(?:right|left|centre|center|middle|turn) lane|blocking the (?:nb|sb|eb|wb)", d):
        return "Single lane blocked", 1
    if "shoulder" in d:
        return "Shoulder only", 0
    return "Not reported", None


def lane_position(desc):
    """Which lane(s) the City text says are blocked: Right/Left/Centre/Turn/..."""
    d = (desc or "").lower()
    impact, _ = lane_impact(desc)
    if impact == "Full closure":
        return "All lanes / road closed"
    if impact == "Multiple lanes blocked":
        if re.search(r"right (?:two )?lanes|two right|right two", d):
            return "Right lanes (multiple)"
        if re.search(r"left (?:two )?lanes|two left|left two", d):
            return "Left lanes (multiple)"
        return "Multiple lanes"
    for pat, name in [
        (r"right lane", "Right lane"),
        (r"left lane", "Left lane"),
        (r"(?:centre|center|middle) lane", "Centre lane"),
        (r"turn lane|turn bay", "Turn lane"),
        (r"shoulder", "Shoulder"),
    ]:
        if re.search(pat, d):
            return name
    return "Not reported"


def ems_involved(desc):
    return bool(re.search(r"\bems\b", desc or "", re.IGNORECASE))


def dir_from_desc(desc):
    m = re.search(r"\b(NB|SB|EB|WB)\b", desc or "")
    return m.group(1) if m else None


def classify_closure(text):
    d = (text or "").lower()
    if re.search(r"ramp", d) and "clos" in d:
        t = "Ramp closure"
    elif re.search(
        r"full closure|road (?:is )?closed|road closure|closed to (?:all )?traffic"
        r"|will be closed|detour in place|is closed",
        d,
    ):
        t = "Full road closure"
    elif re.search(r"lane", d) and re.search(r"clos|reduc|shift", d):
        t = "Lane closure / reduction"
    elif re.search(r"speed", d):
        t = "Speed restriction"
    elif re.search(r"sidewalk|cycle track|pathway|bike", d):
        t = "Sidewalk / cycle facility"
    elif re.search(r"turn|no right|no left", d):
        t = "Turn restriction"
    elif re.search(r"parking", d):
        t = "Parking lane"
    else:
        t = "Other / unspecified"
    return {
        "closure_type": t,
        "detour_signed": bool(re.search(r"detour", d)),
        "time_restricted": bool(
            re.search(r"night|\d\s*(?:am|pm)|weekday|weekend|off[- ]peak|overnight", d)
        ),
        "two_way_or_shift": bool(re.search(r"two-way|shift", d)),
        "multi_lane": bool(
            re.search(
                r"two (?:right|left)? ?lanes|multiple lanes|both lanes|two left|two right|all lanes",
                d,
            )
        ),
    }


def parse_ts(s):
    """City timestamp ('2026-10-03T17:37:53.000' or '2026-10-03 17:37:53+00:00') -> naive."""
    if not s:
        return None
    s = s.strip().replace(" ", "T").replace("+00:00", "")
    return datetime.fromisoformat(s[:19])


def peak_period(local):
    if local.weekday() >= 5:
        return "Weekend"
    h = local.hour + local.minute / 60
    if 6.5 <= h < 9:
        return "AM peak (06:30-09:00)"
    if 15 <= h < 18.5:
        return "PM peak (15:00-18:30)"
    if 9 <= h < 15:
        return "Midday"
    return "Evening/overnight"


def _uid(*parts):
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20]


def incident_uid(location_text, start_utc):
    """Stable identity across the archive and live feeds (they format times differently)."""
    start = parse_ts(start_utc) if isinstance(start_utc, str) else start_utc
    return _uid(" ".join((location_text or "").lower().split()), start.isoformat())


def closure_uid(location_text, start_local, description):
    """Location + start + description. The City lists separate closures (e.g. NB and SB
    lanes) at one location and start time, so description is part of the identity; a
    reworded description therefore appears as a new closure and the old one as removed.
    The end date is excluded because the City extends it in place."""
    start = parse_ts(start_local) if isinstance(start_local, str) else start_local
    norm = lambda t: " ".join((t or "").lower().split())
    return _uid(norm(location_text), start.isoformat() if start else "", norm(description))
