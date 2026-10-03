"""Disruption-count forecast for a user-chosen area/route/lane slice.

Three competing models, one interface (fit on days -> predict_day(date) = 5 period rates):

- flat      Flat daily average over the training days (the named baseline).
- bayes     Expected incidents per (weekday, time-of-day period) from the slice's own
            history, shrunk toward the citywide weekly shape scaled to the slice's rate
            (empirical Bayes, `prior_weeks` pseudo-weeks).
- lightgbm  Poisson gradient-boosted trees (app/domain/ml_forecast.py) on calendar,
            holiday, trend, citywide-rate and Bayes-rate features.

Counts are treated as Poisson for ranges and probabilities. `select_and_backtest` picks
the model on validation days inside the training window, then scores every model on a
later held-out test window that played no part in the choice. The forecast uses the
selected model refit on all observed days. Forecasts *reported disruptions*, not flow,
delay or crash risk, and assume the coming weeks resemble the training window.
"""

import math
from collections import Counter
from datetime import date, datetime, timedelta

from app.domain import ml_forecast

PERIODS = [
    ("Night 00–06", 0, 6),
    ("AM peak 06–10", 6, 10),
    ("Midday 10–15", 10, 15),
    ("PM peak 15–19", 15, 19),
    ("Evening 19–24", 19, 24),
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BASELINE = "Flat daily average over the same training days"
TEST_DAYS = 28
VALIDATION_DAYS = 28


def period_of(hour: int) -> int:
    return next(i for i, (_, a, b) in enumerate(PERIODS) if a <= hour < b)


def _cell_counts(times: list[datetime], days: set[date]) -> Counter:
    return Counter((t.weekday(), period_of(t.hour)) for t in times if t.date() in days)


def fit(times, train_days, city_times, prior_weeks=4.0):
    """Empirical-Bayes rates: {(weekday, period): expected incidents} for one future day."""
    train_days = set(train_days)
    if not train_days:
        raise ValueError("No training days")
    n_wd = Counter(d.weekday() for d in train_days)
    own = _cell_counts(times, train_days)
    city = _cell_counts(city_times, train_days)
    city_total = sum(city.values()) or 1
    own_daily = sum(own.values()) / len(train_days)
    rates = {}
    for w in range(7):
        for p in range(len(PERIODS)):
            # Citywide share of a week's incidents in this cell, scaled to the slice.
            prior = own_daily * 7 * city[(w, p)] / city_total
            n = n_wd[w]
            rates[(w, p)] = (own[(w, p)] + prior_weeks * prior) / (n + prior_weeks)
    return rates


class FlatModel:
    name, label = "flat", "Flat daily average (baseline)"

    def fit(self, times, train_days, city_times):
        train_days = set(train_days)
        own = Counter(period_of(t.hour) for t in times if t.date() in train_days)
        total = sum(own.values())
        daily = total / max(1, len(train_days))
        # Same daily total every day; periods split by the slice's own shares (display only).
        self.cells = [daily * own[p] / total if total else daily / 5 for p in range(len(PERIODS))]
        return self

    def predict_day(self, d):
        return list(self.cells)


class BayesModel:
    name, label = "bayes", "Weekday x period rates (empirical Bayes)"

    def __init__(self, prior_weeks=4.0):
        self.prior_weeks = prior_weeks

    def fit(self, times, train_days, city_times):
        self.rates = fit(times, train_days, city_times, self.prior_weeks)
        return self

    def predict_day(self, d):
        return [self.rates[(d.weekday(), p)] for p in range(len(PERIODS))]


class LightGBMModel:
    name, label = "lightgbm", ml_forecast.LightGBMForecaster.label

    def fit(self, times, train_days, city_times):
        bayes = fit(times, train_days, city_times)
        self.inner = ml_forecast.LightGBMForecaster(len(PERIODS), period_of)
        self.inner.fit(times, train_days, city_times, bayes)
        self.feature_importance = self.inner.feature_importance
        return self

    def predict_day(self, d):
        return self.inner.predict_day(d)


MODELS = {"flat": FlatModel, "bayes": BayesModel, "lightgbm": LightGBMModel}


def eligible_models(times, train_days):
    """Model names allowed for this slice (trees need enough incidents to learn from)."""
    names = ["flat", "bayes"]
    n = sum(1 for t in times if t.date() in set(train_days))
    if ml_forecast.available() and n >= ml_forecast.MIN_INCIDENTS:
        names.append("lightgbm")
    return names


def poisson_interval(lam: float, level: float = 0.8) -> tuple[int, int]:
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    k, cdf, term, lo = 0, 0.0, math.exp(-lam), None
    while True:
        cdf += term
        if lo is None and cdf >= lo_q:
            lo = k
        if cdf >= hi_q or k > 10_000:
            return lo, k
        k += 1
        term *= lam / k


def _score(model, times, eval_days):
    actual = Counter(t.date() for t in times)
    err = covered = expected = 0.0
    for d in eval_days:
        lam = sum(model.predict_day(d))
        y = actual.get(d, 0)
        err += abs(y - lam)
        expected += lam
        lo, hi = poisson_interval(lam)
        covered += lo <= y <= hi
    n = max(1, len(eval_days))
    return {
        "daily_mae": round(err / n, 3),
        "expected": round(expected, 1),
        "interval_80_coverage_pct": round(100 * covered / n, 1),
    }


def select_and_backtest(times, days, city_times, test_days=TEST_DAYS, val_days=VALIDATION_DAYS):
    """Choose a model on validation days, then score all models on later unseen test days.

    Timeline: [ inner training | validation (choose) ] [ test (report only) ]
    """
    ordered = sorted(days)
    if len(ordered) < test_days + val_days + 28:
        return None
    train, test = ordered[:-test_days], ordered[-test_days:]
    inner, val = train[:-val_days], train[-val_days:]
    names = eligible_models(times, inner)
    validation = {n: _score(MODELS[n]().fit(times, inner, city_times), times, val) for n in names}
    selected = min(names, key=lambda n: (validation[n]["daily_mae"], names.index(n)))
    results = {}
    for n in names:
        model = MODELS[n]().fit(times, train, city_times)
        results[n] = {
            "label": MODELS[n].label,
            "validation_daily_mae": validation[n]["daily_mae"],
            **{f"test_{k}": v for k, v in _score(model, times, test).items()},
        }
    actual = Counter(t.date() for t in times)
    flat, chosen = results["flat"], results[selected]
    return {
        "train_days": len(train),
        "validation_start": val[0].isoformat(),
        "validation_end": val[-1].isoformat(),
        "test_days": len(test),
        "test_start": test[0].isoformat(),
        "test_end": test[-1].isoformat(),
        "selected_model": selected,
        "selected_label": MODELS[selected].label,
        "selection_rule": (
            "Lowest daily error on the validation days; test days were not used to choose."
        ),
        "models": results,
        "not_eligible": [n for n in MODELS if n not in names],  # e.g. lightgbm on sparse slices
        "actual_test_incidents": sum(actual.get(d, 0) for d in test),
        "model_expected_test_incidents": chosen["test_expected"],
        "model_daily_mae": chosen["test_daily_mae"],
        "baseline": BASELINE,
        "baseline_daily_mae": flat["test_daily_mae"],
        "improvement_vs_baseline_pct": round(
            100 * (1 - chosen["test_daily_mae"] / flat["test_daily_mae"]), 1
        )
        if flat["test_daily_mae"]
        else None,
        "interval_80_coverage_pct": chosen["test_interval_80_coverage_pct"],
    }


def backtest(times, days, city_times, test_days=TEST_DAYS, prior_weeks=4.0):
    """Bayes-only backtest against the flat baseline (kept for compatibility/tests)."""
    ordered = sorted(days)
    if len(ordered) < test_days + 28:
        return None
    train, test = ordered[:-test_days], ordered[-test_days:]
    bayes = BayesModel(prior_weeks).fit(times, train, city_times)
    flat = FlatModel().fit(times, train, city_times)
    b, f = _score(bayes, times, test), _score(flat, times, test)
    return {
        "train_days": len(train),
        "test_days": len(test),
        "model_daily_mae": b["daily_mae"],
        "baseline": BASELINE,
        "baseline_daily_mae": f["daily_mae"],
        "improvement_vs_baseline_pct": round(100 * (1 - b["daily_mae"] / f["daily_mae"]), 1)
        if f["daily_mae"]
        else None,
        "interval_80_coverage_pct": b["interval_80_coverage_pct"],
    }


def forecast(times, days, city_times, start: date, horizon_days: int, model="bayes"):
    m = MODELS[model]().fit(times, days, city_times)
    out = []
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        cells = m.predict_day(d)
        lam = sum(cells)
        out.append(
            {
                "date": d.isoformat(),
                "weekday": WEEKDAYS[d.weekday()],
                "holiday": d in ml_forecast.HOLIDAYS,
                "expected": round(lam, 3),
                "p_at_least_one": round(1 - math.exp(-lam), 3),
                "periods": [
                    {
                        "period": PERIODS[p][0],
                        "expected": round(c, 3),
                        "p_at_least_one": round(1 - math.exp(-c), 3),
                    }
                    for p, c in enumerate(cells)
                ],
            }
        )
    total = sum(x["expected"] for x in out)
    lo, hi = poisson_interval(total)
    return {
        "model": {
            "name": m.name,
            "label": m.label,
            "feature_importance": getattr(m, "feature_importance", None),
        },
        "days": out,
        "expected_total": round(total, 2),
        "interval_80": [lo, hi],
        "p_at_least_one": round(1 - math.exp(-total), 3),
    }
