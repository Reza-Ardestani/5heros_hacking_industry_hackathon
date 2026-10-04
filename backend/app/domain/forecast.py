"""Disruption-count forecast for a user-chosen area/route/lane slice.

Three competing models, one interface (fit on days -> predict_day(date) = 5 period rates):

- flat      Flat daily average over the training days (the named baseline).
- bayes     Expected incidents per (weekday, time-of-day period) from the slice's own
            history, shrunk toward the citywide weekly shape scaled to the slice's rate
            (empirical Bayes, `prior_weeks` pseudo-weeks).
- lightgbm  Poisson gradient-boosted trees (app/domain/ml_forecast.py) on calendar,
            holiday, trend, citywide-rate and Bayes-rate features.

Ranges and probabilities are negative binomial: citywide daily counts vary about three
times more than Poisson allows (shared shocks such as weather), so the overdispersion is
estimated from citywide history and applied around whichever model is used.
`select_and_backtest` keeps Bayes unless another model is clearly better across four
rolling validation windows inside the training data, then scores every model on a later
held-out test window that played no part in the choice. The forecast uses the selected model refit on all observed days. Forecasts
*reported disruptions*, not flow, delay or crash risk, and assume the coming weeks
resemble the training window. Bayes settings were chosen with
scripts/evaluate_forecast.py (rolling-origin backtest).
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
# Backtest (3 x 28-day folds, 56 slices): 16 beat 0-8 and 32 on log score, mostly by
# steadying sparse routes and intersections; busy slices are nearly unaffected.
PRIOR_WEEKS = 16.0
TEST_DAYS = 28
# Model selection (scripts/evaluate_model_selection.py, 56 slices x 3 test windows): rolling
# 4 x 14-day validation with Bayes as the default and a 2-standard-error bar to switch had
# the lowest regret (2.0% vs 3.1% for one 28-day window and 2.2% for always-Bayes).
VALIDATION_FOLDS = 4
VALIDATION_FOLD_DAYS = 14
VALIDATION_DAYS = VALIDATION_FOLDS * VALIDATION_FOLD_DAYS
DEFAULT_MODEL = "bayes"
SWITCH_Z = 2.0


def period_of(hour: int) -> int:
    return next(i for i, (_, a, b) in enumerate(PERIODS) if a <= hour < b)


def _cell_counts(times: list[datetime], days: set[date]) -> Counter:
    return Counter((t.weekday(), period_of(t.hour)) for t in times if t.date() in days)


def fit(times, train_days, city_times, prior_weeks=PRIOR_WEEKS):
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

    def __init__(self, prior_weeks=PRIOR_WEEKS):
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


def _score(model, times, eval_days, phi=0.0):
    actual = Counter(t.date() for t in times)
    err = covered = expected = 0.0
    for d in eval_days:
        lam = sum(model.predict_day(d))
        y = actual.get(d, 0)
        err += abs(y - lam)
        expected += lam
        lo, hi = nb_interval(lam, phi)
        covered += lo <= y <= hi
    n = max(1, len(eval_days))
    return {
        "daily_mae": round(err / n, 3),
        "expected": round(expected, 1),
        "interval_80_coverage_pct": round(100 * covered / n, 1),
    }


def _daily_errors(model, actual, eval_days):
    return [abs(actual.get(d, 0) - sum(model.predict_day(d))) for d in eval_days]


def choose_model(val_errors: dict[str, list[float]], z: float = SWITCH_Z) -> tuple[str, dict]:
    """Default model unless a challenger beats it by more than z paired standard errors.

    Picking the lowest validation error outright chases noise: in the rolling evaluation
    (scripts/evaluate_model_selection.py) it chose the worst model in 41% of cases and lost
    to always using Bayes. Switching needs consistent evidence across validation days.
    """
    others = [n for n in val_errors if n != DEFAULT_MODEL]
    if not others:
        return DEFAULT_MODEL, {}
    challenger = min(others, key=lambda n: sum(val_errors[n]))
    diffs = [a - b for a, b in zip(val_errors[challenger], val_errors[DEFAULT_MODEL])]
    n = len(diffs)
    mean = sum(diffs) / n
    se = (sum((x - mean) ** 2 for x in diffs) / (n - 1)) ** 0.5 / n**0.5 if n > 1 else 0.0
    switch = mean < -z * se
    evidence = {
        "challenger": challenger,
        "daily_mae_gain": round(-mean, 3),
        "standard_error": round(se, 3),
        "z": round(-mean / se, 2) if se else None,
        "threshold_z": z,
    }
    return (challenger if switch else DEFAULT_MODEL), evidence


def select_and_backtest(times, days, city_times, test_days=TEST_DAYS):
    """Choose a model on rolling validation windows, then score all models on unseen test days.

    Timeline: [ training | val 1 | val 2 | val 3 | val 4 ] [ test (report only) ]
    Each validation window is scored by models fit on all days before it.
    """
    ordered = sorted(days)
    if len(ordered) < test_days + VALIDATION_DAYS + 28:
        return None
    train, test = ordered[:-test_days], ordered[-test_days:]
    folds = [
        (train[: len(train) - j * VALIDATION_FOLD_DAYS],
         train[len(train) - j * VALIDATION_FOLD_DAYS : len(train) - (j - 1) * VALIDATION_FOLD_DAYS])
        for j in range(VALIDATION_FOLDS, 0, -1)
    ]  # fmt: skip
    names = eligible_models(times, folds[0][0])  # eligible on the shortest training set
    actual = Counter(t.date() for t in times)
    val_errors = {n: [] for n in names}
    for fold_train, fold_val in folds:
        for n in names:
            val_errors[n] += _daily_errors(
                MODELS[n]().fit(times, fold_train, city_times), actual, fold_val
            )
    selected, evidence = choose_model(val_errors)
    phi = dispersion(city_times, train)  # ranges for the test window use training data only
    results = {}
    for n in names:
        model = MODELS[n]().fit(times, train, city_times)
        results[n] = {
            "label": MODELS[n].label,
            "validation_daily_mae": round(sum(val_errors[n]) / len(val_errors[n]), 3),
            **{f"test_{k}": v for k, v in _score(model, times, test, phi).items()},
        }
    val = [d for _, fold_val in folds for d in fold_val]
    flat, chosen = results["flat"], results[selected]
    return {
        "train_days": len(train),
        "validation_start": val[0].isoformat(),
        "validation_end": val[-1].isoformat(),
        "validation_folds": VALIDATION_FOLDS,
        "test_days": len(test),
        "test_start": test[0].isoformat(),
        "test_end": test[-1].isoformat(),
        "selected_model": selected,
        "selected_label": MODELS[selected].label,
        "selection_rule": (
            f"Bayes unless another model has lower daily error by more than {SWITCH_Z:g} "
            f"standard errors across {VALIDATION_FOLDS} rolling {VALIDATION_FOLD_DAYS}-day "
            "validation windows; test days were not used to choose."
        ),
        "selection_evidence": evidence,
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
        "dispersion": round(phi, 4),
    }


def forecast_evaluation(backtest, model_name):
    """Project held-out evidence for the actual forecast, not the automatic winner."""
    scores = (backtest or {}).get("models", {}).get(model_name)
    if scores is None:
        return None
    baseline_mae = backtest["baseline_daily_mae"]
    return {
        "model": model_name,
        "label": scores["label"],
        **{
            k: backtest[k]
            for k in (
                "train_days", "test_days", "test_start", "test_end", "actual_test_incidents",
                "baseline", "baseline_daily_mae",
            )
        },
        "model_expected_test_incidents": scores["test_expected"],
        "model_daily_mae": scores["test_daily_mae"],
        "interval_80_coverage_pct": scores["test_interval_80_coverage_pct"],
        "improvement_vs_baseline_pct": round(
            100 * (1 - scores["test_daily_mae"] / baseline_mae), 1
        )
        if baseline_mae
        else None,
    }


def backtest(times, days, city_times, test_days=TEST_DAYS, prior_weeks=PRIOR_WEEKS):
    """Bayes-only backtest against the flat baseline (kept for compatibility/tests)."""
    ordered = sorted(days)
    if len(ordered) < test_days + 28:
        return None
    train, test = ordered[:-test_days], ordered[-test_days:]
    phi = dispersion(city_times, train, prior_weeks)
    bayes = BayesModel(prior_weeks).fit(times, train, city_times)
    flat = FlatModel().fit(times, train, city_times)
    b, f = _score(bayes, times, test, phi), _score(flat, times, test, phi)
    return {
        "train_days": len(train),
        "test_days": len(test),
        "test_start": test[0].isoformat(),
        "test_end": test[-1].isoformat(),
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
    phi = dispersion(city_times, days)
    out, lams = [], []
    for i in range(horizon_days):
        d = start + timedelta(days=i)
        cells = m.predict_day(d)
        lam = sum(cells)
        lams.append(lam)
        out.append(
            {
                "date": d.isoformat(),
                "weekday": WEEKDAYS[d.weekday()],
                "holiday": d in ml_forecast.HOLIDAYS,
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
        "model": {
            "name": m.name,
            "label": m.label,
            "feature_importance": getattr(m, "feature_importance", None),
        },
        "days": out,
        "expected_total": round(total, 2),
        "interval_80": [lo, hi],
        "p_at_least_one": round(p_at_least_one(total, total_phi), 3),
        "dispersion": round(phi, 4),
    }
