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

from datetime import date, timedelta

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


def available():
    try:
        import lightgbm  # noqa: F401
    except ImportError:
        return False
    return True


class LightGBMForecaster:
    name = "lightgbm"
    label = "LightGBM (Poisson gradient-boosted trees)"

    def __init__(self, n_periods, period_of):
        self.n_periods, self.period_of = n_periods, period_of
        self.model = None

    def _rows(self, days, origin, city_rate, bayes):
        rows = []
        for d in days:
            for p in range(self.n_periods):
                w = d.weekday()
                rows.append(
                    [w, p, int(w >= 5), int(d in HOLIDAYS), (d - origin).days,
                     city_rate[(w, p)], bayes[(w, p)]]
                )  # fmt: skip
        return rows

    def fit(self, times, train_days, city_times, bayes_rates):
        from collections import Counter

        import lightgbm as lgb
        import numpy as np

        train_days = sorted(set(train_days))
        self.origin = train_days[0]
        n_wd = Counter(d.weekday() for d in train_days)
        city = Counter(
            (t.weekday(), self.period_of(t.hour)) for t in city_times if t.date() in set(train_days)
        )
        self.city_rate = {
            (w, p): city[(w, p)] / max(1, n_wd[w]) for w in range(7) for p in range(self.n_periods)
        }
        self.bayes = bayes_rates
        own = Counter((t.date(), self.period_of(t.hour)) for t in times)
        x = np.array(self._rows(train_days, self.origin, self.city_rate, self.bayes), dtype=float)
        y = np.array([own[(d, p)] for d in train_days for p in range(self.n_periods)], dtype=float)
        data = lgb.Dataset(x, y, feature_name=FEATURES, categorical_feature=[0, 1])
        self.model = lgb.train(PARAMS, data, num_boost_round=NUM_ROUNDS)
        gains = self.model.feature_importance(importance_type="gain")
        total = float(sum(gains)) or 1.0
        # Share of total split gain per feature (how much each feature drives predictions).
        self.feature_importance = {
            f: round(100 * float(g) / total, 1) for f, g in zip(FEATURES, gains, strict=True)
        }
        return self

    def predict_day(self, d):
        import numpy as np

        x = np.array(self._rows([d], self.origin, self.city_rate, self.bayes), dtype=float)
        return [max(0.0, float(v)) for v in self.model.predict(x)]


def daterange(start, n):
    return [start + timedelta(days=i) for i in range(n)]
