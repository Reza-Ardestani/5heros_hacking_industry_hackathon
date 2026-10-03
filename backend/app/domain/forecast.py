"""Disruption-count forecast for a user-chosen area/route/lane slice.

Model: expected incidents per (weekday, time-of-day period), estimated from the
slice's own history and shrunk toward a citywide weekly shape scaled to the
slice's overall rate (empirical-Bayes style; `prior_weeks` pseudo-weeks). Counts
are treated as Poisson. It forecasts *reported disruptions*, not traffic flow,
delay or crash risk, and assumes the next weeks resemble the training window.

Baseline for comparison: flat daily average over the same training window.
"""

import math
from collections import Counter
from datetime import date, datetime, timedelta

PERIODS = [
    ("Night 00–06", 0, 6),
    ("AM peak 06–10", 6, 10),
    ("Midday 10–15", 10, 15),
    ("PM peak 15–19", 15, 19),
    ("Evening 19–24", 19, 24),
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BASELINE = "Flat daily average over the same training days"


def period_of(hour: int) -> int:
    return next(i for i, (_, a, b) in enumerate(PERIODS) if a <= hour < b)


def _cell_counts(times: list[datetime], days: set[date]) -> Counter:
    return Counter((t.weekday(), period_of(t.hour)) for t in times if t.date() in days)


def fit(times, train_days, city_times, prior_weeks=4.0):
    """Return {(weekday, period): expected incidents} for one future day."""
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


def backtest(times, days, city_times, test_days=28, prior_weeks=4.0):
    """Hold out the last `test_days` observed days; compare daily MAE with baseline."""
    ordered = sorted(days)
    if len(ordered) < test_days + 28:
        return None
    train, test = set(ordered[:-test_days]), ordered[-test_days:]
    rates = fit(times, train, city_times, prior_weeks)
    flat = sum(1 for t in times if t.date() in train) / len(train)
    actual = Counter(t.date() for t in times)
    model_err = base_err = covered = 0.0
    for d in test:
        lam = sum(rates[(d.weekday(), p)] for p in range(len(PERIODS)))
        y = actual.get(d, 0)
        model_err += abs(y - lam)
        base_err += abs(y - flat)
        lo, hi = poisson_interval(lam)
        covered += lo <= y <= hi
    n = len(test)
    return {
        "train_days": len(train),
        "test_days": n,
        "test_start": test[0].isoformat(),
        "test_end": test[-1].isoformat(),
        "actual_test_incidents": sum(actual.get(d, 0) for d in test),
        "model_expected_test_incidents": round(
            sum(sum(rates[(d.weekday(), p)] for p in range(len(PERIODS))) for d in test), 1
        ),
        "model_daily_mae": round(model_err / n, 3),
        "baseline": BASELINE,
        "baseline_daily_mae": round(base_err / n, 3),
        "improvement_vs_baseline_pct": round(100 * (1 - model_err / base_err), 1)
        if base_err
        else None,
        "interval_80_coverage_pct": round(100 * covered / n, 1),
    }


def forecast(times, days, city_times, start: date, horizon_days: int, prior_weeks=4.0):
    rates = fit(times, days, city_times, prior_weeks)
    out = []
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        cells = [rates[(d.weekday(), p)] for p in range(len(PERIODS))]
        lam = sum(cells)
        out.append(
            {
                "date": d.isoformat(),
                "weekday": WEEKDAYS[d.weekday()],
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
        "days": out,
        "expected_total": round(total, 2),
        "interval_80": [lo, hi],
        "p_at_least_one": round(1 - math.exp(-total), 3),
        "weekly_profile": [
            {
                "weekday": WEEKDAYS[w],
                "periods": [round(rates[(w, p)], 3) for p in range(len(PERIODS))],
            }
            for w in range(7)
        ],
    }
