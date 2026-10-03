"""Disruption-count forecast for a user-chosen area/route/lane slice.

Model: expected incidents per (weekday, time-of-day period), estimated from the
slice's own history and shrunk toward a citywide weekly shape scaled to the
slice's overall rate (empirical-Bayes style; `prior_weeks` pseudo-weeks). Counts
are negative binomial: citywide daily counts vary about three times more than
Poisson allows (shared shocks such as weather), so the overdispersion is
estimated from citywide history and applied to every slice. It forecasts
*reported disruptions*, not traffic flow, delay or crash risk, and assumes the
next weeks resemble the training window.

Baseline for comparison: flat daily average over the same training window.
Settings were chosen with scripts/evaluate_forecast.py (rolling-origin backtest).
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
# Backtest (3 x 28-day folds, 56 slices): 16 beat 0-8 and 32 on log score, mostly by
# steadying sparse routes and intersections; busy slices are nearly unaffected.
PRIOR_WEEKS = 16.0


def period_of(hour: int) -> int:
    return next(i for i, (_, a, b) in enumerate(PERIODS) if a <= hour < b)


def _cell_counts(times: list[datetime], days: set[date]) -> Counter:
    return Counter((t.weekday(), period_of(t.hour)) for t in times if t.date() in days)


def fit(times, train_days, city_times, prior_weeks=PRIOR_WEEKS):
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


def dispersion(city_times, days, prior_weeks=PRIOR_WEEKS) -> float:
    """Citywide negative-binomial overdispersion phi (Var = lam + phi * lam^2), by moments."""
    rates = fit(city_times, days, city_times, prior_weeks)
    counts = Counter(t.date() for t in city_times)
    num = den = 0.0
    for d in days:
        lam = sum(rates[(d.weekday(), p)] for p in range(len(PERIODS)))
        num += (counts.get(d, 0) - lam) ** 2 - lam
        den += lam * lam
    return max(0.0, num / den) if den else 0.0


def nb_interval(lam: float, phi: float, level: float = 0.8) -> tuple[int, int]:
    """Central interval of a negative binomial with mean lam; Poisson when phi is 0."""
    if phi <= 0 or lam <= 0:
        return poisson_interval(lam, level)
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    r = 1 / phi
    q = lam / (r + lam)
    k, cdf, term, lo = 0, 0.0, (1 - q) ** r, None
    while True:
        cdf += term
        if lo is None and cdf >= lo_q:
            lo = k
        if cdf >= hi_q or k > 100_000:
            return lo, k
        term *= (k + r) / (k + 1) * q
        k += 1


def p_at_least_one(lam: float, phi: float) -> float:
    return 1 - (math.exp(-lam) if phi <= 0 else (1 + phi * lam) ** (-1 / phi))


def total_dispersion(lams: list[float], phi: float) -> float:
    """Dispersion of a sum of independent NB days: Var = sum(lam) + phi * sum(lam^2)."""
    total = sum(lams)
    return phi * sum(x * x for x in lams) / (total * total) if total else 0.0


def daily_expected(rates, start: date, horizon_days: int) -> list[float]:
    return [
        sum(rates[((start + timedelta(i)).weekday(), p)] for p in range(len(PERIODS)))
        for i in range(horizon_days)
    ]


def _binom_tail(k: int, n: int, p: float, upper: bool) -> float:
    def pmf(j):
        return math.exp(
            math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
            + j * math.log(p) + (n - j) * math.log1p(-p)
        )  # fmt: skip

    return min(1.0, sum(pmf(j) for j in (range(k, n + 1) if upper else range(k + 1))))


def recent_shift(recent: int, total: int, city_share: float) -> dict:
    """Is a slice's share of incidents in the recent window unusual versus the city's?

    Conditioning on the slice's total and comparing with the citywide recent share
    cancels shocks that hit the whole city (weather, holidays). Exact binomial test;
    p_value is two-sided. Callers screening many slices should adjust with
    benjamini_hochberg before labelling anything as rising or falling.
    """
    if total == 0 or not 0 < city_share < 1:
        return {"ratio": None, "direction": None, "p_value": 1.0}
    ratio = (recent / total) / city_share
    up = _binom_tail(recent, total, city_share, True)
    down = _binom_tail(recent, total, city_share, False)
    return {
        "ratio": round(ratio, 2),
        "direction": "rising" if ratio > 1 else "falling" if ratio < 1 else None,
        "p_value": min(1.0, 2 * min(up, down)),
    }


def benjamini_hochberg(p_values: list[float], q: float = 0.1) -> list[bool]:
    """Which tests stay significant at false-discovery rate q (Benjamini-Hochberg)."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    cutoff = 0
    for rank, i in enumerate(order, 1):
        if p_values[i] <= q * rank / len(p_values):
            cutoff = rank
    keep = set(order[:cutoff])
    return [i in keep for i in range(len(p_values))]


def backtest(times, days, city_times, test_days=28, prior_weeks=PRIOR_WEEKS):
    """Hold out the last `test_days` observed days; compare daily MAE with baseline."""
    ordered = sorted(days)
    if len(ordered) < test_days + 28:
        return None
    train, test = set(ordered[:-test_days]), ordered[-test_days:]
    rates = fit(times, train, city_times, prior_weeks)
    phi = dispersion(city_times, train, prior_weeks)
    flat = sum(1 for t in times if t.date() in train) / len(train)
    actual = Counter(t.date() for t in times)
    model_err = base_err = covered = 0.0
    for d in test:
        lam = sum(rates[(d.weekday(), p)] for p in range(len(PERIODS)))
        y = actual.get(d, 0)
        model_err += abs(y - lam)
        base_err += abs(y - flat)
        lo, hi = nb_interval(lam, phi)
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


def forecast(times, days, city_times, start: date, horizon_days: int, prior_weeks=PRIOR_WEEKS):
    rates = fit(times, days, city_times, prior_weeks)
    phi = dispersion(city_times, days, prior_weeks)
    out, lams = [], []
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        cells = [rates[(d.weekday(), p)] for p in range(len(PERIODS))]
        lam = sum(cells)
        lams.append(lam)
        out.append(
            {
                "date": d.isoformat(),
                "weekday": WEEKDAYS[d.weekday()],
                "expected": round(lam, 3),
                "p_at_least_one": round(p_at_least_one(lam, phi), 3),
                "periods": [
                    {
                        "period": PERIODS[p][0],
                        "expected": round(c, 3),
                        "p_at_least_one": round(p_at_least_one(c, phi), 3),
                    }
                    for p, c in enumerate(cells)
                ],
            }
        )
    total = sum(lams)
    total_phi = total_dispersion(lams, phi)
    lo, hi = nb_interval(total, total_phi)
    return {
        "days": out,
        "expected_total": round(total, 2),
        "interval_80": [lo, hi],
        "p_at_least_one": round(p_at_least_one(total, total_phi), 3),
        "dispersion": round(phi, 4),
        "weekly_profile": [
            {
                "weekday": WEEKDAYS[w],
                "periods": [round(rates[(w, p)], 3) for p in range(len(PERIODS))],
            }
            for w in range(7)
        ],
    }
