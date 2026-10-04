"""Optional raw dataset export adapter."""

import json
from pathlib import Path


class JsonRawSink:
    def __init__(self, directory):
        self.directory = Path(directory)

    def __call__(self, meta, rows):
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / f"{meta['dataset']}.json").write_text(json.dumps(rows), encoding="utf-8")
