#!/usr/bin/env python3
"""Replay local data to Timescale without fetching any City APIs."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.infra.disruption_store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-batches", type=int, default=100)
    args = parser.parse_args()
    if args.max_batches < 1:
        parser.error("--max-batches must be positive")
    store = Store()
    for _ in range(args.max_batches):
        caught_up = store.sync(force=True)
        state = store.storage_status()
        if caught_up or state["last_error"]:
            break
    print(json.dumps(store.storage_status(), indent=2))
    return 0 if caught_up else 1


if __name__ == "__main__":
    sys.exit(main())
