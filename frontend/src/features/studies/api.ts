import { request } from "../../shared/http";
import type { Incidents, IntersectionStudy, Job, Scenario } from "./types";
export const defaults = () => request<{
  defaults: Scenario;
}>("/api/scenario");
export const incidents = () => request<Incidents>("/api/incidents");
export const job = (id: string) => request<Job>(`/api/jobs/${id}`);
export function submit(scenario: Scenario, study: IntersectionStudy | null) {
  const query = study ? `?origin=intersection&intersection_key=${encodeURIComponent(study.intersection_key)}` : "";
  return request<{
    id: string;
  }>(`/api/jobs${query}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(scenario) });
}
export const reportUrl = (id: string) => `/api/jobs/${id}/report`;
export const simulationUrl = (id: string) => `/api/simulations/${id}`;
