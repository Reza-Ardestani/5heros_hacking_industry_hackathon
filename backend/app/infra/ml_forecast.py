"""LightGBM SDK adapter for the domain forecasting contract."""

from app.domain.ml_forecast import FEATURES, HOLIDAYS, NUM_ROUNDS, PARAMS


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
