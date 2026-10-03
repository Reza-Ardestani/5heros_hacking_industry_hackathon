#!/usr/bin/env python3
"""Fetch a bounded, attributed Calgary context snapshot; no credentials required."""

import argparse
import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "snapshots")
    args = parser.parse_args()
    if not 1 <= args.limit <= 5000:
        parser.error("limit must be between 1 and 5000")
    url = "https://data.calgary.ca/resource/35ra-9556.json?" + urlencode(
        {"$limit": args.limit, "$order": "start_dt_utc DESC,id ASC"}
    )
    with urlopen(
        Request(url, headers={"User-Agent": "BottleneckBusters/0.1"}), timeout=30
    ) as response:
        payload = response.read(10_000_001)
    if len(payload) > 10_000_000:
        raise ValueError("Snapshot exceeds bounded response size")
    rows = json.loads(payload)
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        raise ValueError("Expected nonempty incident row list; existing snapshot retained")
    source = {
        "url": url,
        "dataset": "35ra-9556",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "rows": len(rows),
        "license_url": "https://data.calgary.ca/stories/s/Open-Calgary-Terms-of-Use/u45n-7awa",
        "attribution": "Contains information licensed under the Open Government Licence – City of Calgary",
        "limitations": [
            "Unofficial archive; gaps possible",
            "Changed location may create multiple records for one event",
            "Not traffic-flow counts; no reliable clearance/duration field",
        ],
    }
    destination = args.output_dir
    destination.mkdir(parents=True, exist_ok=True)
    # Fetch and validate before replacing files. Each replacement is atomic;
    # refresh while the API is stopped to avoid observing the pair mid-update.
    for name, data in [
        ("incidents.json", payload),
        ("incidents_source.json", (json.dumps(source, indent=2) + "\n").encode()),
    ]:
        with tempfile.NamedTemporaryFile(dir=destination, delete=False) as temp:
            temp.write(data)
            pending = temp.name
        os.replace(pending, destination / name)
    print(f"Saved {len(rows)} rows; {source['retrieved_at_utc']}; SHA256 {source['sha256']}")


if __name__ == "__main__":
    main()
