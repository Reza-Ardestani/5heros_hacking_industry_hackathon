#!/usr/bin/env python3
"""Compare model-selection rules for forecast.select_and_backtest on real Calgary slices.

For every slice and each of 3 outer test windows (28 days each, most recent first), a rule
sees only the days before the test window, picks flat / bayes / lightgbm, and is scored by
the chosen model's daily MAE on the test window. Rules:

  single28      current rule: one 28-day validation window
  rolling KxW   K consecutive W-day validation windows (expanding training), mean MAE
  ... +1se      rolling, then the simplest model (flat < bayes < lightgbm) whose paired
                daily-error gap to the best is within one standard error
  always_*      fixed choices, for reference
  oracle        best model on the test window (unattainable; the floor)

Scores are relative, so busy and sparse slices count equally: "regret" is the chosen
model's test MAE over the oracle's, minus 1, averaged over slice x window.

  cd backend && uv run python ../scripts/evaluate_model_selection.py
"""

import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.application import disruptions as D
from app.bootstrap import configure_services
from app.domain import forecast as F
from evaluate_forecast import build_slices

configure_services()

OUTER, TEST = 3, 28
SIMPLICITY = ["flat", "bayes", "lightgbm"]
ROLLING = {"single28": (1, 28), "rolling 2x28": (2, 28), "rolling 4x14": (4, 14), "rolling 3x21": (3, 21)}  # fmt: skip


def errors(model, times_by_day, days):
    return [abs(times_by_day.get(d, 0) - sum(model.predict_day(d))) for d in days]


def windows(pre, k, w):
    """[(train_days, val_days)] for k consecutive w-day windows ending at the end of pre."""
    return [(pre[: len(pre) - j * w], pre[len(pre) - j * w : len(pre) - (j - 1) * w]) for j in range(k, 0, -1)]  # fmt: skip


def choose(val_errs, names, one_se):
    """val_errs[name] = list of per-day errors over all validation windows (same days)."""
    means = {n: statistics.fmean(val_errs[n]) for n in names}
    best = min(names, key=lambda n: (means[n], SIMPLICITY.index(n)))
    if not one_se:
        return best
    for n in sorted(names, key=SIMPLICITY.index):
        diffs = [a - b for a, b in zip(val_errs[n], val_errs[best])]
        se = statistics.stdev(diffs) / len(diffs) ** 0.5 if len(diffs) > 1 else 0.0
        if statistics.fmean(diffs) <= se:
            return n
    return best


def choose_anchor(val_errs, names, z):
    """Bayes unless another model beats it by more than z paired standard errors."""
    others = [n for n in names if n != "bayes"]
    best = min(others, key=lambda n: statistics.fmean(val_errs[n]))
    diffs = [a - b for a, b in zip(val_errs[best], val_errs["bayes"])]
    se = statistics.stdev(diffs) / len(diffs) ** 0.5
    return best if statistics.fmean(diffs) < -z * se else "bayes"


def main():
    data = D._load()
    days, city = sorted(data["observed_days"]), data["city_times"]
    slices = build_slices(data["incidents"], city)
    rules = [*ROLLING, *(f"{r} +1se" for r in ROLLING if r != "single28")]
    rules += [f"{r} bayes-unless-{z}se" for r in ROLLING for z in (1, 2)]
    rules += ["SHIPPED forecast.choose_model", "always_flat", "always_bayes", "always_lightgbm"]
    rules += ["oracle"]
    picks, regret, vs_bayes, worst = (
        defaultdict(Counter),
        defaultdict(list),
        defaultdict(list),
        Counter(),
    )
    group_regret = defaultdict(lambda: defaultdict(list))
    cases = 0
    for name, times in slices.items():
        by_day = Counter(t.date() for t in times)
        for f in range(OUTER):
            cut = len(days) - TEST * (OUTER - f)
            pre, test = days[:cut], days[cut : cut + TEST]
            fits = {}

            def model(n, train, fits=fits, times=times):
                key = (n, len(train))
                if key not in fits:
                    fits[key] = F.MODELS[n]().fit(times, train, city)
                return fits[key]

            # Candidates: eligible on the shortest training set any rule uses.
            names = F.eligible_models(times, pre[: len(pre) - 4 * 14])
            test_mae = {n: statistics.fmean(errors(model(n, pre), by_day, test)) for n in names}
            oracle = min(test_mae.values()) or 1e-9
            chosen = {}
            for rule, (k, w) in ROLLING.items():
                val = {n: [] for n in names}
                for train, vdays in windows(pre, k, w):
                    for n in names:
                        val[n] += errors(model(n, train), by_day, vdays)
                chosen[rule] = choose(val, names, one_se=False)
                if rule != "single28":
                    chosen[f"{rule} +1se"] = choose(val, names, one_se=True)
                for z in (1, 2):
                    chosen[f"{rule} bayes-unless-{z}se"] = choose_anchor(val, names, z)
            shipped = {n: [] for n in names}
            for train, vdays in windows(pre, F.VALIDATION_FOLDS, F.VALIDATION_FOLD_DAYS):
                for n in names:
                    shipped[n] += errors(model(n, train), by_day, vdays)
            chosen["SHIPPED forecast.choose_model"] = F.choose_model(shipped)[0]
            for n in ("flat", "bayes"):
                chosen[f"always_{n}"] = n
            chosen["always_lightgbm"] = "lightgbm" if "lightgbm" in names else "bayes"
            chosen["oracle"] = min(names, key=lambda n: test_mae[n])
            worst_model = max(names, key=lambda n: test_mae[n]) if len(names) > 1 else None
            for rule in rules:
                pick = chosen[rule]
                picks[rule][pick] += 1
                r = test_mae[pick] / oracle - 1
                regret[rule].append(r)
                group_regret[rule][name.split(":")[0]].append(r)
                vs_bayes[rule].append(test_mae[pick] / (test_mae["bayes"] or 1e-9) - 1)
                worst[rule] += pick == worst_model and test_mae[pick] > oracle
            cases += 1

    print(f"{len(slices)} slices x {OUTER} test windows = {cases} cases\n")
    groups = ("city", "quad", "cat", "route", "route-sparse", "ix")
    print(f"{'rule':30} {'regret':>7} {'vs bayes':>9} {'worst':>6}   " + " ".join(f"{g:>7}" for g in groups) + "   picks")  # fmt: skip
    for rule in rules:
        g = " ".join(f"{100 * statistics.fmean(group_regret[rule][x]):6.1f}%" for x in groups)
        print(
            f"{rule:30} {100 * statistics.fmean(regret[rule]):6.1f}% "
            f"{100 * statistics.fmean(vs_bayes[rule]):+8.1f}% {worst[rule]:6d}   {g}   "
            + ", ".join(f"{k} {v}" for k, v in picks[rule].most_common())
        )


if __name__ == "__main__":
    main()
