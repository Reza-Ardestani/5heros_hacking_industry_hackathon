#!/usr/bin/env python3
"""Rolling-origin evaluation of the disruption forecast on real Calgary slices.

Scores forecast variants on citywide, quadrant, category, busy-route, sparse-route
and busy-intersection slices: 3 folds x 28 held-out days, each trained on every
observed day before its test window. Metrics: daily MAE (vs the flat baseline),
mean daily log predictive score (higher is better; rewards calibrated
uncertainty) and empirical coverage of the nominal 80% interval for daily
counts and 7-day totals (should be close to 80%).

  cd backend && uv run python ../scripts/evaluate_forecast.py
"""

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.application import disruptions as D
from app.bootstrap import configure_services
from app.domain import forecast as F

configure_services()

FOLDS, TEST = 3, 28
NP = len(F.PERIODS)
GROUPS = ("ALL", "city", "quad", "cat", "route", "route-sparse", "ix")


def build_slices(rows, city):
    def times(field, value):
        return [D.model_time(r) for r in rows if r[field] == value]

    def top(field, n):
        return [k for k, _ in Counter(r[field] for r in rows if r[field]).most_common(n)]

    slices = {"city": city}
    slices |= {f"quad:{q}": times("quadrant", q) for q in top("quadrant", 4)}
    slices |= {f"cat:{c}": times("category_group", c) for c in top("category_group", 6)}
    slices |= {f"route:{k}": times("corridor_key", k) for k in top("corridor_key", 15)}
    routes = Counter(r["corridor_key"] for r in rows if r["corridor_key"])
    sparse = [k for k, n in routes.most_common() if 15 <= n <= 40][:15]
    slices |= {f"route-sparse:{k}": times("corridor_key", k) for k in sparse}
    slices |= {f"ix:{k}": times("intersection_key", k) for k in top("intersection_key", 15)}
    return slices


def fit_weighted(times, train_days, city_times, prior_weeks, half_life=None):
    """forecast.fit plus optional exponential recency weights (half_life in days)."""
    end = max(train_days)

    def w(day):
        return 1.0 if half_life is None else 0.5 ** ((end - day).days / half_life)

    train = set(train_days)
    n_wd, own, city = defaultdict(float), defaultdict(float), defaultdict(float)
    for day in train:
        n_wd[day.weekday()] += w(day)
    for src, acc in ((times, own), (city_times, city)):
        for t in src:
            if t.date() in train:
                acc[(t.weekday(), F.period_of(t.hour))] += w(t.date())
    city_total = sum(city.values()) or 1
    own_daily = sum(own.values()) / sum(n_wd.values())
    return {
        (wd, p): (own[(wd, p)] + prior_weeks * own_daily * 7 * city[(wd, p)] / city_total)
        / (n_wd[wd] + prior_weeks)
        for wd in range(7)
        for p in range(NP)
    }


def daily_lambda(rates, day):
    return sum(rates[(day.weekday(), p)] for p in range(NP))


def moment_dispersion(times, train_days, rates):
    """Method-of-moments NB overdispersion: Var = lam + phi * lam^2."""
    counts = Counter(t.date() for t in times)
    num = den = 0.0
    for day in train_days:
        lam = daily_lambda(rates, day)
        num += (counts.get(day, 0) - lam) ** 2 - lam
        den += lam * lam
    return max(0.0, num / den) if den else 0.0


def logpmf(y, lam, phi):
    lam = max(lam, 1e-9)
    if phi <= 1e-9:
        return y * math.log(lam) - lam - math.lgamma(y + 1)
    r = 1 / phi
    return (
        math.lgamma(y + r) - math.lgamma(r) - math.lgamma(y + 1)
        + r * math.log(r / (r + lam)) + y * math.log(lam / (r + lam))
    )  # fmt: skip


def interval(lam, phi, level=0.8):
    if phi <= 1e-9:
        return F.poisson_interval(lam, level)
    lo_q, hi_q = (1 - level) / 2, 1 - (1 - level) / 2
    cdf, lo, k = 0.0, None, 0
    while True:
        cdf += math.exp(logpmf(k, lam, phi))
        if lo is None and cdf >= lo_q:
            lo = k
        if cdf >= hi_q or k > 10_000:
            return lo, k
        k += 1


def evaluate(variant, slices, days):
    """variant(times, train_days) -> (rates, daily phi). Returns totals per slice group."""
    totals = {g: defaultdict(float) for g in GROUPS}
    for name, times in slices.items():
        counts = Counter(t.date() for t in times)
        for f in range(FOLDS):
            cut = len(days) - TEST * (FOLDS - f)
            train, test = days[:cut], days[cut : cut + TEST]
            rates, phi = variant(times, train)
            flat = sum(counts.get(x, 0) for x in train) / len(train)
            m = defaultdict(float)
            for day in test:
                lam, y = daily_lambda(rates, day), counts.get(day, 0)
                lo, hi = interval(lam, phi)
                m["mae"] += abs(y - lam)
                m["flat_mae"] += abs(y - flat)
                m["log"] += logpmf(y, lam, phi)
                m["cov_day"] += lo <= y <= hi
                m["n_day"] += 1
            for i in range(0, TEST, 7):
                week = test[i : i + 7]
                lam = sum(daily_lambda(rates, x) for x in week)
                y = sum(counts.get(x, 0) for x in week)
                # Sum of 7 independent NB days with similar means: phi_week ~ phi / 7.
                lo, hi = interval(lam, phi / 7)
                m["cov_week"] += lo <= y <= hi
                m["n_week"] += 1
            for g in ("ALL", name.split(":")[0]):
                for k, v in m.items():
                    totals[g][k] += v
    return totals


def report(label, totals):
    print(f"\n== {label}")
    for g in GROUPS:
        m = totals[g]
        print(
            f"{g:>12}: MAE {m['mae'] / m['n_day']:.3f} (flat {m['flat_mae'] / m['n_day']:.3f})"
            f"  log {m['log'] / m['n_day']:+.4f}"
            f"  cov80 day {100 * m['cov_day'] / m['n_day']:5.1f}%"
            f" week {100 * m['cov_week'] / m['n_week']:5.1f}%"
        )


def main():
    data = D._load()
    days, city = sorted(data["observed_days"]), data["city_times"]
    slices = build_slices(data["incidents"], city)
    print(f"{len(slices)} slices; {FOLDS} folds x {TEST} test days; {len(days)} observed days")

    report("CURRENT: forecast.fit(prior_weeks=4), Poisson",
           evaluate(lambda t, tr: (F.fit(t, tr, city, 4.0), 0.0), slices, days))  # fmt: skip
    for pw in (0, 1, 2, 8, 16, 32):
        report(f"prior_weeks={pw}, Poisson",
               evaluate(lambda t, tr, pw=pw: (fit_weighted(t, tr, city, pw), 0.0), slices, days))  # fmt: skip
    for hl in (14, 28, 56, 112):
        report(f"prior_weeks=4, half_life={hl}d, Poisson",
               evaluate(lambda t, tr, hl=hl: (fit_weighted(t, tr, city, 4, hl), 0.0), slices, days))  # fmt: skip

    def nb_slice(t, tr):
        r = fit_weighted(t, tr, city, 4)
        return r, moment_dispersion(t, tr, r)

    def nb_city(t, tr):
        return fit_weighted(t, tr, city, 4), moment_dispersion(
            city, tr, fit_weighted(city, tr, city, 4)
        )

    report("prior_weeks=4, NB phi per slice", evaluate(nb_slice, slices, days))
    report("prior_weeks=4, NB phi from citywide", evaluate(nb_city, slices, days))
    for pw in (8, 16):
        report(f"prior_weeks={pw}, NB phi from citywide",
               evaluate(lambda t, tr, pw=pw: (fit_weighted(t, tr, city, pw), nb_city(t, tr)[1]),
                        slices, days))  # fmt: skip
    report(f"SHIPPED: forecast.fit + forecast.dispersion (prior_weeks={F.PRIOR_WEEKS:g})",
           evaluate(lambda t, tr: (F.fit(t, tr, city), F.dispersion(city, tr)), slices, days))  # fmt: skip


if __name__ == "__main__":
    main()
