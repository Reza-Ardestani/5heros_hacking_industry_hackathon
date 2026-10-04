"""Injected dependencies for the existing process-local disruption service."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.application.ports import CityFetcher, DisruptionStore


@dataclass(frozen=True)
class DisruptionDependencies:
    store_factory: Callable[[], DisruptionStore]
    seed_store: Callable[[DisruptionStore], bool]
    fetch_city: CityFetcher
    get_json: Callable[[str], bytes]
    analysis_dir: Path
