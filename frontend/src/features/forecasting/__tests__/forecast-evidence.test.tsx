import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PredictionPanel, emptySelection, } from "..";
import { request } from "../../../shared/http";
vi.mock("../../../shared/http", () => ({ request: vi.fn() }));
const evaluation = {
  model: "lightgbm",
  label: "LightGBM",
  train_days: 156,
  test_days: 28,
  test_start: "2026-09-05",
  test_end: "2026-10-02",
  actual_test_incidents: 600,
  model_expected_test_incidents: 570,
  model_daily_mae: 6.229,
  baseline: "Flat average",
  baseline_daily_mae: 6.856,
  improvement_vs_baseline_pct: 9.1,
  interval_80_coverage_pct: 82.1,
};
const prediction = {
  selection: {},
  history: {
    incidents: 1000,
    observed_days: 184,
    per_day: 5.4,
    lane_blocking_pct: 20,
    category_mix: [],
  },
  forecast_start: "2026-10-03",
  horizon_days: 7,
  expected_total: 143,
  interval_80: [100, 180],
  p_at_least_one: 1,
  periods: [],
  days: [],
  top_intersections: [],
  low_data: false,
  method: "test",
  caveat: "Reported incidents only",
  model: {
    name: "lightgbm",
    label: "LightGBM",
    requested: "lightgbm",
    note: null,
    eligible: [],
  },
  forecast_evaluation: evaluation,
  backtest: {
    ...evaluation,
    selected_model: "bayes",
    selected_label: "Bayes",
    model_daily_mae: 6.116,
    improvement_vs_baseline_pct: 10.8,
    interval_80_coverage_pct: 78.6,
    models: {
      bayes: {
        label: "Bayes",
        validation_daily_mae: 6,
        test_daily_mae: 6.116,
        test_interval_80_coverage_pct: 78.6,
      },
      lightgbm: {
        label: "LightGBM",
        validation_daily_mae: 7,
        test_daily_mae: 6.229,
        test_interval_80_coverage_pct: 82.1,
      },
    },
  },
};
beforeEach(() => {
  vi.useFakeTimers();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.clearAllMocks();
});
async function show(value: unknown) {
  vi.mocked(request).mockImplementation(async (url) => url.includes("options") ? {} : value);
  render(<PredictionPanel selection={emptySelection} onSelect={() => { }} onOpenIntersection={() => { }} />);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(300);
  });
}
it("distinguishes forced LightGBM evidence from the automatic Bayes choice", async () => {
  await show(prediction);
  expect(screen.getByText(/Automatic choice: Bayes/)).toBeTruthy();
  const summary = document.querySelector(".px-backtest")!.textContent!;
  expect(summary).toContain("Daily error, LightGBM6.229");
  expect(summary).toContain("9.1% lower error");
  expect(summary).toContain("82.1% of test days");
  expect(summary).not.toContain("10.8%");
  expect(summary).not.toContain("6.116");
});
it("shows unavailable evidence rather than another model's verdict", async () => {
  await show({ ...prediction, forecast_evaluation: null });
  expect(screen.getByText(/No comparable held-out evaluation for LightGBM/)).toBeTruthy();
  expect(document.querySelector(".px-backtest")).toBeNull();
});
it("labels fallback and uses actual Bayes evidence", async () => {
  await show({
    ...prediction,
    model: {
      ...prediction.model,
      name: "bayes",
      label: "Bayes",
      note: "Too few incidents; used bayes",
    },
    forecast_evaluation: {
      ...evaluation,
      model: "bayes",
      label: "Bayes",
      model_daily_mae: 6.116,
      improvement_vs_baseline_pct: 10.8,
    },
  });
  expect(screen.getByText(/fallback/)).toBeTruthy();
  expect(document.querySelector(".px-backtest")!.textContent).toContain("Daily error, Bayes6.116");
});
it.each([
  [0, "Same error as the flat baseline"],
  [-3, "3% higher error than baseline"],
  [null, "Not comparable: baseline has zero error"],
])("reports comparison %s without substituting automatic scores", async (percentage, verdict) => {
  await show({
    ...prediction,
    forecast_evaluation: {
      ...evaluation,
      improvement_vs_baseline_pct: percentage,
    },
  });
  expect(screen.getByText(verdict)).toBeTruthy();
});
