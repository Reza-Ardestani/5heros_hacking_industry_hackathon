"""LightGBM incident-count forecaster (open-source gradient-boosted trees, MIT licence).

Why LightGBM: fastest mainstream gradient-boosting library on small tabular data, native
Poisson objective for counts, deterministic with a fixed seed and single thread. It is
trained per request on the selected slice's own history (184 days x 5 periods = 920 rows,
milliseconds) and must beat the flat baseline and the Bayesian rates on held-out days to
be used (see forecast.select_and_backtest).

Features per (day, period) cell — all known in advance for future days:
  weekday, period, is_weekend, is_holiday (Alberta statutory), day_index (trend),
  city_cell_rate (citywide mean count for that weekday x period in training),
  bayes_rate (the empirical-Bayes cell rate; lets trees learn residual structure).
Target: incident count for the slice in that cell.
"""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Protocol

# Alberta general/statutory holidays observed in the data window and the next year.
HOLIDAYS = {
    date(2025, 9, 1), date(2025, 10, 13), date(2025, 11, 11), date(2025, 12, 25),
    date(2026, 1, 1), date(2026, 2, 16), date(2026, 4, 3), date(2026, 5, 18),
    date(2026, 7, 1), date(2026, 8, 3), date(2026, 9, 7), date(2026, 10, 12),
    date(2026, 11, 11), date(2026, 12, 25), date(2027, 1, 1), date(2027, 2, 15),
    date(2027, 3, 26), date(2027, 5, 24), date(2027, 7, 1), date(2027, 8, 2),
}  # fmt: skip
FEATURES = [
    "weekday", "period", "is_weekend", "is_holiday", "day_index", "city_cell_rate", "bayes_rate",
]  # fmt: skip
MIN_INCIDENTS = 30  # below this the slice is too sparse for trees to beat simple rates
PARAMS = {  # LightGBM native API (no scikit-learn dependency)
    "objective": "poisson",
    "learning_rate": 0.05,
    "num_leaves": 7,
    "min_data_in_leaf": 20,
    "lambda_l2": 1.0,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "feature_fraction": 0.9,
    "seed": 42,
    "deterministic": True,
    "num_threads": 1,
    "verbose": -1,
}
NUM_ROUNDS = 200


class Forecaster(Protocol):
    feature_importance: dict

    def fit(self, times, train_days, city_times, bayes_rates): ...

    def predict_day(self, day) -> list[float]: ...


_factory: Callable[..., Forecaster] | None = None
_available: Callable[[], bool] = lambda: False
_version: str | None = None


def configure(factory: Callable[..., Forecaster], available_check: Callable[[], bool], version=None):
    """Register an adapter from the composition root, never import it from domain."""
    global _factory, _available, _version
    _factory, _available, _version = factory, available_check, version


def available():
    return _available()


def library_version():
    return _version


class LightGBMForecaster:
    name = "lightgbm"
    label = "LightGBM (Poisson gradient-boosted trees)"

    def __init__(self, n_periods, period_of):
        if _factory is None:
            raise RuntimeError("Forecast adapter is not configured")
        self.inner = _factory(n_periods, period_of)

    def fit(self, times, train_days, city_times, bayes_rates):
        self.inner.fit(times, train_days, city_times, bayes_rates)
        self.feature_importance = self.inner.feature_importance
        return self

    def predict_day(self, day):
        return self.inner.predict_day(day)


def daterange(start, n):
    return [start + timedelta(days=i) for i in range(n)]
