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
export type ExtraOption = "signal_control" | "incident_clearance" | "turn_lane" | "turn_ban";
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
  vehicles: {
    id: string;
    x: number;
    y: number;
    speed: number;
  }[];
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
  economics: {
    estimated_net_annual_value_cad: number;
    label: string;
  };
  tuning_trial: {
    metrics: Metrics;
    playback: Frame[];
    queues: {
      time_s: number;
      queue_m: number;
    }[];
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
    settings: {
      setting: keyof Scenario;
      needed: number;
      current: number;
      message: string;
    }[];
  }[];
};
export type Result = {
  scenario: Scenario;
  alternatives: Alternative[];
  recommended_id: string;
  decision?: DecisionExplanation;
  evidence_summary?: EvidenceSummary;
  incident_impact?: {
    extra_delay_s_per_vehicle: number;
    vehicle_hours_lost: number;
  } | null;
  pareto_ids: string[];
  stress_passed: boolean;
  simulator_version: string;
  limitations: string[];
  evaluation: {
    holdout_seeds: number[];
    optimization_seed: number;
  };
  stress_tests: {
    demand_factor: number;
    comparison: {
      feasible: boolean;
      delay_reduction_pct: number;
    };
  }[];
  cost_stress?: CostStress;
};
export type CostStress = {
  recommended_id: string;
  cost_factors: number[];
  budget_factors: number[];
  grid: string[][];
  robust_share_pct: number;
  verdict: string;
  headroom: {
    cost_increase_pct: number;
    min_budget_cad: number;
    fallback_id: string;
    fallback: string;
  } | null;
  switch_points: {
    id: string;
    label: string;
    needed_budget_cad: number;
    budget_increase_pct: number;
    cost_cut_pct: number;
  }[];
  blocked: {
    id: string;
    label: string;
    reason: string;
  }[];
  one_at_a_time: {
    id: string;
    label: string;
    factor: number;
    winner_id: string;
    winner: string;
  }[];
  economics: {
    net_annual_value_cad: number;
    worst_case_net_cad: number;
    worst_case: string;
    break_even_value_of_time_cad: number;
    value_of_time_cad: number;
  } | null;
  method: string;
};
export type Job = {
  id: string;
  status: string;
  trace: Trace[];
  result: Result | null;
  error: string | null;
};
export type Incidents = {
  source: {
    retrieved_at_utc: string;
    url: string;
    rows: number;
  };
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
