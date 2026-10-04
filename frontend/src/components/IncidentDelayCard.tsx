import React, { useState } from "react";
import { FlaskConical, Loader2, Timer } from "lucide-react";

import type { IncidentEstimate, IntersectionDetail, IntersectionStudy } from "../types";
import { number } from "../lib/format";
import { request } from "../lib/api";

/** Modeled seconds of delay per incident + share of unspecified incidents, and the
 * hand-off that turns this intersection into a corridor study (step 2). */
export function IncidentDelayCard({
  detail,
  onStudy,
  onEstimated,
}: {
  detail: IntersectionDetail;
  onStudy?: (study: IntersectionStudy) => void;
  onEstimated?: (estimate: IncidentEstimate) => void;
}) {
  const [estimate, setEstimate] = useState<IncidentEstimate | null>(
    detail.incident_delay_estimate ?? null,
  );
  const [busy, setBusy] = useState<"" | "estimate" | "study">("");
  const [error, setError] = useState("");
  const key = encodeURIComponent(detail.key);

  const runEstimate = (refresh = false) => {
    setBusy("estimate");
    setError("");
    request<IncidentEstimate>(
      `/api/disruptions/intersection/estimate?key=${key}${refresh ? "&refresh=true" : ""}`,
    )
      .then((e) => {
        setEstimate(e);
        onEstimated?.(e);
      })
      .catch((e) => setError(e.message))
      .finally(() => setBusy(""));
  };
  const openStudy = () => {
    setBusy("study");
    request<IntersectionStudy>(`/api/disruptions/intersection/study?key=${key}`)
      .then((s) => onStudy?.(s))
      .catch((e) => setError(e.message))
      .finally(() => setBusy(""));
  };
  const unspecified = detail.unspecified_pct ?? estimate?.unspecified_pct ?? 0;
  const ok = estimate?.status === "ok";
  return (
    <div className="incident-delay">
      <div className="incident-delay-figures">
        <div>
          <span>Extra delay per incident (modeled)</span>
          <strong>{ok ? `+${number(estimate!.extra_delay_s_per_vehicle!)} s` : "–"}</strong>
          <small>
            {ok
              ? `per vehicle · +${number(estimate!.extra_delay_s_per_vehicle_blocked_direction!)} s in the blocked direction`
              : estimate?.status === "no_lane_blocking_incidents"
                ? "No lane-blocking incidents recorded here"
                : "Not estimated yet (≈15 s SUMO run)"}
          </small>
        </div>
        <div>
          <span>Per incident / six months (modeled)</span>
          <strong>
            {ok ? `${number(estimate!.vehicle_hours_lost_per_incident!)} veh-h` : "–"}
          </strong>
          <small>
            {ok
              ? `≈ ${number(estimate!.six_month_vehicle_hours_lost!)} vehicle-hours over six months of peak incidents`
              : "Vehicle-hours lost"}
          </small>
        </div>
        <div>
          <span>Traffic incident (unspecified)</span>
          <strong>{number(unspecified)}%</strong>
          <small>
            {detail.unspecified ?? estimate?.unspecified ?? 0} of {detail.incidents} incidents
            have no stated cause
          </small>
        </div>
      </div>
      <div className="incident-delay-actions">
        <button
          className="button secondary"
          disabled={!!busy}
          onClick={() => runEstimate(ok)}
          title="Runs SUMO with and without one typical incident at this intersection"
        >
          {busy === "estimate" ? <Loader2 size={15} className="spin" /> : <Timer size={15} />}
          {ok ? "Re-estimate" : "Estimate seconds lost"}
        </button>
        {onStudy && (
          <button className="button primary" disabled={!!busy} onClick={openStudy}>
            {busy === "study" ? <Loader2 size={15} className="spin" /> : <FlaskConical size={15} />}
            Simulate this intersection
          </button>
        )}
      </div>
      {ok && estimate?.incident && (
        <p className="helper">
          Typical incident: {estimate.incident.lanes_blocked} lane(s){" "}
          {estimate.incident.direction}bound for{" "}
          {Math.round(estimate.incident.duration_s / 60)} min · {estimate.method}
          {estimate.cached ? " · cached result" : ""}
        </p>
      )}
      {error && <p className="incident-caution">{error}</p>}
    </div>
  );
}
