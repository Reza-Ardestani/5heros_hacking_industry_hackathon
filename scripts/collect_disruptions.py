#!/usr/bin/env python3
"""Poll City of Calgary feeds and append to the disruption database.

Each poll stores: live incidents (and a sighting per incident, which bounds how
long it stayed active), the full closure feed (closures that disappear are marked
removed_from_feed_utc, building the history the City does not keep), a travel-time
observation per segment, new/edited archive incidents, and reference layers when
older than 24 h. Every download is logged in fetch_runs.

  python scripts/collect_disruptions.py               # one poll
  python scripts/collect_disruptions.py --every 300   # poll every 5 minutes until stopped
  python scripts/collect_disruptions.py --export      # poll, then refresh data/analysis exports
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.application.disruption_collector import Collector
from app.bootstrap import configure_services
from app.infra import city_open_data
from app.infra.disruption_seed import seed_from_exports
from app.infra.disruption_store import Store

configure_services()


def poll(store, include_archive, export):
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    report = Collector(store, fetcher=city_open_data.fetch).collect(include_archive=include_archive)
    summary = {
        k: (v["status"], v.get("inserted", 0), v.get("updated", 0)) for k, v in report.items()
    }
    print(f"[{started}] {json.dumps(summary)}", flush=True)
    if export:
        import build_disruption_dataset

        build_disruption_dataset.export(store, ROOT / "data" / "analysis")
    return all(v["status"] == "ok" for v in report.values())


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--every", type=int, default=0, help="seconds between polls (min 60)")
    ap.add_argument("--no-archive", action="store_true", help="skip the incident archive query")
    ap.add_argument("--export", action="store_true", help="re-export JSON/Excel after each poll")
    ap.add_argument("--db", type=Path, default=None)
    args = ap.parse_args()
    store = Store(args.db)
    seed_from_exports(store, ROOT / "data" / "analysis")
    if not args.every:
        sys.exit(0 if poll(store, not args.no_archive, args.export) else 1)
    every = max(60, args.every)
    while True:
        try:
            poll(store, not args.no_archive, args.export)
        except Exception as error:  # noqa: BLE001 — keep the loop alive; failures are logged
            print(f"poll failed: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        time.sleep(every)


if __name__ == "__main__":
    main()
