"""City of Calgary Open Data (Socrata) client: paginated, retried, hashed. No credentials."""

import hashlib
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://data.calgary.ca/resource/{}.json?"
PAGE_SIZE = 50_000
LICENSE = {
    "license_url": "https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa",
    "attribution": "Contains information licensed under the Open Government Licence – City of Calgary",
}
DISCOVERED_FROM = "https://www.calgary.ca/roads/conditions/traffic-cameras.html"
DATASETS = {
    "incidents": ("35ra-9556", "Traffic Incidents (unofficial archive)"),
    "current_incidents": ("4jah-h97u", "Current Traffic Incidents"),
    "closures": ("w8zq-79bq", "Construction Detours (scheduled road/lane closures)"),
    "projects": ("sizs-hgef", "Road Construction Projects"),
    "cameras": ("k7p9-kppz", "Traffic Cameras"),
    "signals": ("qr97-4jvx", "Traffic Signals"),
    "travel_times": ("aeb8-fh2w", "Travel Times"),
    "volumes_2024": ("cauu-7hnw", "Traffic Volumes for 2024"),
}


def get_json(url, timeout=60, attempts=4):
    for attempt in range(attempts):
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "BottleneckBusters/0.1"}), timeout=timeout
            ) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def fetch(key, params=None, timeout=60, attempts=4):
    """Return (rows, meta) for a named dataset, following $offset pages to the end."""
    dataset, name = DATASETS[key]
    params = dict(params or {})
    params.setdefault("$order", ":id")
    rows, digest, first_url = [], hashlib.sha256(), None
    offset = 0
    while True:
        url = BASE.format(dataset) + urlencode({**params, "$limit": PAGE_SIZE, "$offset": offset})
        first_url = first_url or url
        payload = get_json(url, timeout, attempts)
        page = json.loads(payload)
        if not isinstance(page, list):
            raise TypeError(f"{dataset}: expected a row list")
        digest.update(payload)
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows, {
        "key": key,
        "dataset": dataset,
        "name": name,
        "page": f"https://data.calgary.ca/d/{dataset}",
        "url": first_url,
        "sha256": digest.hexdigest(),
        "rows": len(rows),
    }
