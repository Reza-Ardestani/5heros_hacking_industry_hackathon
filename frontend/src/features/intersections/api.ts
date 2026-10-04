import { request } from "../../shared/http";
import type { IncidentEstimate, IntersectionStudy } from "../studies";
import type { DisruptionSummary, Intersection, IntersectionDetail, LiveFeed, Priorities } from "./types";
export const summary = () => request<DisruptionSummary>("/api/disruptions/summary");
export const intersections = (params: URLSearchParams | string) => request<{
  total: number;
  items: Intersection[];
}>(`/api/disruptions/intersections?${params}`);
export const detail = (key: string) => request<IntersectionDetail>(`/api/disruptions/intersection?key=${encodeURIComponent(key)}`);
export const live = (refresh: boolean) => request<LiveFeed>(`/api/disruptions/live${refresh ? "?refresh=true" : ""}`);
export const priorities = (params: URLSearchParams | string) => request<Priorities>(`/api/disruptions/priorities?${params}`);
export const getIntersectionStudy = (key: string) => request<IntersectionStudy>(`/api/disruptions/intersection/study?key=${encodeURIComponent(key)}`);
export const estimate = (key: string, refresh: boolean) => request<IncidentEstimate>(`/api/disruptions/intersection/estimate?key=${encodeURIComponent(key)}${refresh ? "&refresh=true" : ""}`);
