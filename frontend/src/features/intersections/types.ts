import type { IncidentEstimate } from "../studies";
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
  by_category: {
    category: string;
    incidents: number;
  }[];
  by_lane_impact: {
    lane_impact: string;
    incidents: number;
  }[];
  by_direction: {
    direction: string;
    incidents: number;
  }[];
  by_hour: number[];
  by_weekday: Record<string, number>;
  by_month: {
    month: string;
    incidents: number;
  }[];
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
    window: {
      start_local: string;
      months: number;
    };
    database: string;
    sources: Record<string, {
      dataset: string;
      name: string;
      rows: number;
      page: string;
    }>;
  };
  headline: {
    incidents: number;
    window_days: number;
    incidents_per_day: number;
    lane_blocking_pct: number;
    at_signalized_intersection_pct: number;
    closures_overlapping_window: number;
  };
  by_category: {
    category: string;
    category_group: string;
    incidents: number;
    share_pct: number;
  }[];
  monthly: {
    month: string;
    incidents: number;
    days_with_data: number;
  }[];
  intersections_indexed: number;
};
type HotspotLink = {
  key: string;
  distance_m: number;
  incidents_6mo: number;
} | null;
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
export type PriorityItem = {
  key: string;
  corridor: string;
  quadrants: string[];
  history_incidents: number;
  expected: number;
  interval_80: [
    number,
    number
  ];
  expected_lane_blocking: number;
  lane_blocking_pct: number;
  lane_impact_reported_pct: number;
  trend: "rising" | "falling" | "steady";
  trend_direction: "rising" | "falling" | null;
  trend_ratio: number | null;
  trend_p_value: number;
  peak_window: string;
  peak_window_share_pct: number;
  median_volume_2024: number | null;
  per_10k_daily_vehicles: number | null;
  top_intersections: string[];
  study_spot: string | null;
  study_spot_incidents: number;
  incident_delay_s: number | null;
};
type RankScore = {
  overlap_with_actual_top: number;
  captured_pct: number;
};
export type Priorities = {
  level: "corridor" | "intersection";
  horizon_days: number;
  forecast_start: string;
  quadrant: string | null;
  sort: string;
  min_incidents: number;
  eligible: number;
  items: PriorityItem[];
  analysis: {
    citywide_expected: number;
    citywide_interval_80: [
      number,
      number
    ];
    citywide_peak_window: string;
    top_n: number;
    top_share_of_citywide_pct: number;
    top_keys: string[];
    rising: string[];
    falling: string[];
    recent_window_days: number;
    ranking_check: {
      train_days: number;
      test_start: string;
      test_end: string;
      top_n: number;
      forecast: RankScore;
      past_counts: RankScore;
      spearman: number | null;
    } | null;
    calibration: {
      interval_80_coverage_pct: number;
      model_daily_mae: number;
      baseline_daily_mae: number;
      test_days: number;
    } | null;
    dispersion: number;
  };
  method: string;
  caveat: string;
};
