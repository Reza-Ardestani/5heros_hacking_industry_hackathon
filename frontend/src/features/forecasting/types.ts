export type ForecastModel = "flat" | "bayes" | "lightgbm";
export type Option = {
  value: string;
  incidents: number;
};
export type PredictOptions = {
  quadrants: Option[];
  routes: Option[];
  directions: Option[];
  lanes: Option[];
  categories: Option[];
  intersections: Option[];
  max_horizon_days: number;
};
export type Prediction = {
  selection: Record<string, string>;
  history: {
    incidents: number;
    observed_days: number;
    per_day: number;
    lane_blocking_pct: number | null;
    category_mix: {
      category: string;
      share_pct: number;
    }[];
  };
  forecast_start: string;
  horizon_days: number;
  expected_total: number;
  interval_80: [
    number,
    number
  ];
  p_at_least_one: number;
  periods: string[];
  days: {
    date: string;
    weekday: string;
    expected: number;
    p_at_least_one: number;
    periods: {
      period: string;
      expected: number;
      p_at_least_one: number;
    }[];
  }[];
  forecast_evaluation?: {
    model: ForecastModel;
    label: string;
    train_days: number;
    test_days: number;
    test_start: string;
    test_end: string;
    actual_test_incidents: number;
    model_expected_test_incidents: number;
    model_daily_mae: number;
    baseline: string;
    baseline_daily_mae: number;
    improvement_vs_baseline_pct: number | null;
    interval_80_coverage_pct: number;
  } | null;
  backtest: {
    train_days: number;
    test_days: number;
    test_start: string;
    test_end: string;
    actual_test_incidents: number;
    model_expected_test_incidents: number;
    model_daily_mae: number;
    baseline: string;
    baseline_daily_mae: number;
    improvement_vs_baseline_pct: number | null;
    interval_80_coverage_pct: number;
    selected_model?: ForecastModel;
    selected_label?: string;
    selection_rule?: string;
    validation_start?: string;
    validation_end?: string;
    not_eligible?: ForecastModel[];
    models?: Record<string, {
      label: string;
      validation_daily_mae: number;
      test_daily_mae: number;
      test_interval_80_coverage_pct: number;
      test_expected: number;
    }>;
  } | null;
  model?: {
    name: ForecastModel;
    label: string;
    requested: string;
    eligible: ForecastModel[];
    note: string | null;
    feature_importance: Record<string, number> | null;
  };
  top_intersections: {
    key: string;
    incidents: number;
    expected_in_horizon: number;
  }[];
  low_data: boolean;
  method: string;
  caveat: string;
};
export type McpTool = {
  name: string;
  description: string;
  read_only: boolean;
  arguments: Record<string, {
    default: unknown;
    description?: string;
  }>;
  self_check?: {
    status: "ok" | "error" | "not_run";
    ms?: number;
    reason?: string;
    error?: string;
  };
};
export type McpInfo = {
  reachable: boolean;
  probed_url: string;
  error?: string;
  how_to_start?: string;
  server?: {
    name: string;
    sdk: string;
  };
  endpoint?: {
    path: string;
    transport: string;
    host: string;
    port: number;
    agentcore_compatible: boolean;
  };
  tools?: McpTool[];
  summary?: Record<string, number>;
  connect?: Record<string, string>;
};
export type MlInfo = {
  task: string;
  models: {
    name: string;
    label: string;
    type: string;
    how: string;
    library?: string;
    available?: boolean;
    params?: Record<string, unknown>;
    rounds?: number;
    features?: {
      name: string;
      meaning: string;
    }[];
    min_incidents?: number;
  }[];
  selection: {
    validation_days: number;
    test_days: number;
    rule: string;
    metric: string;
    interval: string;
  };
  no_external_models: string;
};
export type MlBenchmark = {
  observed_days: number;
  slices: {
    slice: string;
    incidents: number;
    selected_model: string | null;
    best_on_test: string;
    models: Record<string, {
      validation_mae: number;
      test_mae: number;
      test_coverage_pct: number;
    }>;
    forecast_7d: number;
    interval_80: [
      number,
      number
    ];
  }[];
  best_on_test_counts: Record<string, number>;
  selected_counts: Record<string, number>;
};
