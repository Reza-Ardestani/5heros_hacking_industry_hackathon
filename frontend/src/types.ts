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
  arterial_lanes: number;
  junction_control: "signal" | "priority";
  turn_share: number;
  incident: IncidentSpec | null;
  extra_options: ExtraOption[];
  clearance_reduction: number;
  incident_weight: number;
  signal_install_cost_cad: number;
  signal_removal_cost_cad: number;
  clearance_program_cost_cad: number;
  turn_lane_cost_cad: number;
  turn_ban_cost_cad: number;
};
export type ExtraOption =
  | "signal_control"
  | "incident_clearance"
  | "turn_lane"
  | "turn_ban";
export type IncidentSpec = {
  direction: "east" | "west";
  start_s: number;
  duration_s: number;
  lanes_blocked: number;
  label: string;
};
export type IntersectionStudy = {
  intersection_key: string;
  scenario: Scenario;
  assumptions: string[];
  warnings: string[];
  evidence: {
    incidents: number;
    observed_days: number;
    lane_blocking: number;
    lane_blocking_pct: number;
    peak_lane_blocking: number;
    unspecified: number;
    unspecified_pct: number;
    collisions: number;
    signal_faults: number;
    live_now: string | null;
  };
  geometry: string;
};
export type IncidentEstimate = {
  status: "ok" | "no_lane_blocking_incidents";
  intersection_key: string;
  unspecified_pct: number;
  unspecified: number;
  incidents: number;
  lane_blocking: number;
  extra_delay_s_per_vehicle?: number;
  extra_delay_s_per_vehicle_blocked_direction?: number;
  vehicle_hours_lost_per_incident?: number;
  six_month_vehicle_hours_lost?: number;
  normal_delay_s_per_vehicle?: number;
  incident?: IncidentSpec;
  assumptions?: string[];
  warnings?: string[];
  method?: string;
  cached?: boolean;
};
export type EvidenceSummary = {
  headline: string;
  intersection_key: string | null;
  observed_facts: string[];
  options: {
    id: string;
    label: string;
    kind: string;
    sentence: string;
    modeled_delay_change_pct: number;
    feasible: boolean;
    recommended: boolean;
    six_month_scaled_vehicle_hours?: number;
  }[];
  options_that_reduce_delay: string[];
  proof_standard: string;
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
  kind?: string;
  main_green_share: number;
  main_lanes: number;
  capital_cost_cad: number;
  metrics: Metrics;
  comparison: {
    feasible: boolean;
    rejection_reasons: string[];
    rejection_details?: RejectionDetail[];
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
export type RejectionDetail = {
  rule: "budget" | "cross_street" | "complete_trips";
  setting: keyof Scenario | null;
  observed: number;
  limit: number;
  message: string;
};
export type DecisionExplanation = {
  rule: string;
  recommended_id: string;
  lowest_delay_id: string;
  lowest_delay_is_recommended: boolean;
  lowest_delay_rejected_because: string[];
  what_would_change: {
    id: string;
    label: string;
    possible: boolean;
    reason?: string;
    delay_s_per_vehicle?: number;
    settings: { setting: keyof Scenario; needed: number; current: number; message: string }[];
  }[];
};
export type Result = {
  scenario: Scenario;
  alternatives: Alternative[];
  recommended_id: string;
  decision?: DecisionExplanation;
  evidence_summary?: EvidenceSummary;
  incident_impact?: { extra_delay_s_per_vehicle: number; vehicle_hours_lost: number } | null;
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
export type View =
  | "problem"
  | "study"
  | "compare"
  | "intersections"
  | "evidence";
export type Camera = {
  id: string;
  location: string;
  image_url: string;
  distance_m: number;
};
export type Intersection = {
  key: string;
  roads: string[];
  quadrant: string | null;
  latitude: number;
  longitude: number;
  incidents: number;
  collisions: number;
  vulnerable_road_user: number;
  signal_faults: number;
  lane_blocking: number;
  unspecified?: number;
  unspecified_pct?: number;
  incident_delay_s?: number | null;
  peak_period: number;
  last_seen_local: string;
  signalized: boolean;
  signal: string | null;
  camera: Camera | null;
  volume_2024: number | null;
};
export type IntersectionDetail = Intersection & {
  caveat: string;
  incident_delay_estimate?: IncidentEstimate | null;
  by_category: { category: string; incidents: number }[];
  by_lane_impact: { lane_impact: string; incidents: number }[];
  by_direction: { direction: string; incidents: number }[];
  by_hour: number[];
  by_weekday: Record<string, number>;
  by_month: { month: string; incidents: number }[];
  closures_nearby: {
    location_text: string;
    description: string;
    start_local: string;
    end_local: string;
    closure_type: string;
    status_at_retrieval: string;
    distance_m: number;
  }[];
  recent: {
    start_local: string;
    category: string;
    lane_impact: string;
    travel_direction: string | null;
    description: string;
    location_text: string;
    period: string;
  }[];
};
export type DisruptionSummary = {
  caveat: string;
  manifest: {
    retrieved_at_utc: string;
    window: { start_local: string; months: number };
    database: string;
    sources: Record<string, { dataset: string; name: string; rows: number; page: string }>;
  };
  headline: {
    incidents: number;
    window_days: number;
    incidents_per_day: number;
    lane_blocking_pct: number;
    at_signalized_intersection_pct: number;
    closures_overlapping_window: number;
  };
  by_category: { category: string; category_group: string; incidents: number; share_pct: number }[];
  monthly: { month: string; incidents: number; days_with_data: number }[];
  intersections_indexed: number;
};
type HotspotLink = { key: string; distance_m: number; incidents_6mo: number } | null;
export type LiveFeed = {
  fetched_at_epoch: number;
  ok: boolean;
  persisted: boolean;
  errors: string[];
  cache_age_s: number;
  hotspot_threshold: number;
  incidents: {
    location_text: string;
    description: string;
    start_utc: string;
    quadrant: string;
    latitude: number | null;
    longitude: number | null;
    hotspot: HotspotLink;
  }[];
  active_closures: {
    location_text: string;
    description: string;
    start: string;
    end: string;
    hotspot: HotspotLink;
  }[];
  active_closures_at_hotspots: number;
};
export type Option = { value: string; incidents: number };
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
    category_mix: { category: string; share_pct: number }[];
  };
  forecast_start: string;
  horizon_days: number;
  expected_total: number;
  interval_80: [number, number];
  p_at_least_one: number;
  periods: string[];
  days: {
    date: string;
    weekday: string;
    expected: number;
    p_at_least_one: number;
    periods: { period: string; expected: number; p_at_least_one: number }[];
  }[];
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
  } | null;
  top_intersections: { key: string; incidents: number; expected_in_horizon: number }[];
  low_data: boolean;
  method: string;
  caveat: string;
};
