export type FlowInterval = {
  begin_s: number;
  end_s: number;
  main_vph: number;
  cross_vph: number;
};
export type Scenario = {
  main_vph: number;
  cross_vph: number;
  duration_s: number;
  seed: number;
  budget_cad: number;
  cross_guardrail_pct: number;
  retiming_cost_cad: number;
  widening_cost_cad: number;
  annual_operating_cost_cad: number;
  occupancy: number;
  value_of_time_cad: number;
  operating_days: number;
  asset_life_years: number;
  demand_kind: "synthetic" | "measured";
  demand_source: string;
  flow_profile: FlowInterval[] | null;
};
export type Metrics = {
  mean_delay_s: number;
  total_delay_s: number;
  main_mean_delay_s: number;
  cross_mean_delay_s: number;
  max_queue: number;
  completed: number;
  unserved: number;
  planned: number;
};
export type Frame = {
  time_s: number;
  vehicles: { id: string; x: number; y: number; speed: number }[];
};
export type Alternative = {
  id: string;
  label: string;
  main_green_share: number;
  main_lanes: number;
  capital_cost_cad: number;
  metrics: Metrics;
  comparison: {
    feasible: boolean;
    rejection_reasons: string[];
    delay_reduction_pct: number;
    cross_delay_change_pct: number;
    vehicle_hours_saved: number;
  };
  economics: { estimated_net_annual_value_cad: number; label: string };
  tuning_trial: {
    metrics: Metrics;
    playback: Frame[];
    queues: { time_s: number; queue_m: number }[];
  };
};
export type Trace = {
  agent: string;
  action: string;
  detail: string;
  at_utc: string;
};
export type Result = {
  scenario: Scenario;
  alternatives: Alternative[];
  recommended_id: string;
  pareto_ids: string[];
  stress_passed: boolean;
  simulator_version: string;
  limitations: string[];
  evaluation: { holdout_seeds: number[]; optimization_seed: number };
  stress_tests: {
    demand_factor: number;
    comparison: { feasible: boolean; delay_reduction_pct: number };
  }[];
};
export type Job = {
  id: string;
  status: string;
  trace: Trace[];
  result: Result | null;
  error: string | null;
};
export type Incidents = {
  source: { retrieved_at_utc: string; url: string; rows: number };
  raw_rows: number;
  context_events: number;
  records: {
    title: string;
    description: string;
    start_utc: string;
    latitude: number;
    longitude: number;
  }[];
};
export type View = "problem" | "study" | "compare" | "evidence";
