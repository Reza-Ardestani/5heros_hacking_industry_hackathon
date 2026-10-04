import React from "react";
import { AlertTriangle, ClipboardList, FileSearch, MapPin, X } from "lucide-react";

import type { ExtraOption, IntersectionStudy, Result, Scenario } from "../types";
import { money, number } from "../lib/format";

export const defaultStudyFields = {
  arterial_lanes: 1,
  junction_control: "signal" as const,
  turn_share: 0,
  incident: null,
  extra_options: [] as ExtraOption[],
  clearance_reduction: 0.5,
  incident_weight: 1,
  signal_install_cost_cad: 250000,
  signal_removal_cost_cad: 30000,
  clearance_program_cost_cad: 50000,
  turn_lane_cost_cad: 400000,
  turn_ban_cost_cad: 10000,
};

const OPTIONS: { id: ExtraOption; label: (s: Scenario) => string; cost: (s: Scenario) => number;
  note: string; needs?: (s: Scenario) => string | null }[] = [
  {
    id: "signal_control",
    label: (s) => (s.junction_control === "signal" ? "Remove signal at J2" : "Add signal at J2"),
    cost: (s) => (s.junction_control === "signal" ? s.signal_removal_cost_cad : s.signal_install_cost_cad),
    note: "Signal vs priority control at the hotspot junction. Delay only; safety needs review.",
  },
  {
    id: "incident_clearance",
    label: (s) => `Faster incident clearance (−${Math.round(s.clearance_reduction * 100)}%)`,
    cost: (s) => s.clearance_program_cost_cad,
    note: "Shorter lane blockage when an incident happens.",
    needs: (s) => (s.incident ? null : "Add an incident first"),
  },
  {
    id: "turn_lane",
    label: () => "Left-turn bay + protected phase",
    cost: (s) => s.turn_lane_cost_cad,
    note: "Turners leave the through lane and get a 10 s protected arrow.",
    needs: (s) => (s.turn_share > 0 ? null : "Set a left-turn share first"),
  },
  {
    id: "turn_ban",
    label: () => "Ban left turns at J2",
    cost: (s) => s.turn_ban_cost_cad,
    note: "Turners use the next junction (+36 s backtrack penalty each).",
    needs: (s) => (s.turn_share > 0 ? null : "Set a left-turn share first"),
  },
]; // fmt: skip

/** Banner shown when the study was built from an intersection's City data. */
export function StudyBanner({ study, onClear }: { study: IntersectionStudy; onClear: () => void }) {
  const e = study.evidence;
  return (
    <section className="panel study-banner">
      <div className="panel-heading">
        <div>
          <div className="eyebrow">STUDY BUILT FROM CITY DATA</div>
          <h2>
            <MapPin size={16} /> {study.intersection_key}
          </h2>
          <p className="helper">{study.geometry}</p>
        </div>
        <button className="button secondary" onClick={onClear}>
          <X size={14} /> Back to default study
        </button>
      </div>
      <div className="study-chips">
        <span>{e.incidents} incidents / {e.observed_days} days</span>
        <span>{e.lane_blocking} lane-blocking ({number(e.lane_blocking_pct)}%)</span>
        <span>{e.peak_lane_blocking} in weekday peaks</span>
        <span>{e.unspecified} unspecified ({number(e.unspecified_pct)}%)</span>
        <span>{e.collisions} collisions · {e.signal_faults} signal faults</span>
        {e.live_now && <span className="live">Live now: {e.live_now}</span>}
      </div>
      {study.warnings.map((w) => (
        <p className="incident-caution study-warning" key={w}>
          <AlertTriangle size={13} /> {w}
        </p>
      ))}
      <details className="study-assumptions">
        <summary>How the inputs were derived ({study.assumptions.length} assumptions)</summary>
        <ul>
          {study.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}

/** Corridor, incident and option controls (step 2, left column). */
export function StudyDesign({
  scenario,
  onChange,
  disabled,
}: {
  scenario: Scenario;
  onChange: (patch: Partial<Scenario>) => void;
  disabled?: boolean;
}) {
  const s = scenario;
  const incident = s.incident;
  const toggle = (id: ExtraOption, on: boolean) =>
    onChange({
      extra_options: on ? [...s.extra_options, id] : s.extra_options.filter((o) => o !== id),
    });
  return (
    <div className="study-design">
      <h3>Corridor & hotspot junction (J2)</h3>
      <div className="design-grid">
        <label>
          Arterial lanes / direction
          <select
            value={s.arterial_lanes}
            disabled={disabled}
            onChange={(e) => {
              const lanes = +e.target.value;
              onChange({
                arterial_lanes: lanes,
                incident: incident && { ...incident, lanes_blocked: Math.min(incident.lanes_blocked, lanes) },
              });
            }}
          >
            {[1, 2, 3].map((n) => (
              <option key={n}>{n}</option>
            ))}
          </select>
        </label>
        <label>
          J2 control today
          <select
            value={s.junction_control}
            disabled={disabled}
            onChange={(e) => onChange({ junction_control: e.target.value as Scenario["junction_control"] })}
          >
            <option value="signal">Signal</option>
            <option value="priority">No signal (priority)</option>
          </select>
        </label>
        <label>
          Left turns at J2 · {Math.round(s.turn_share * 100)}%
          <input
            type="range"
            min="0"
            max="0.4"
            step="0.05"
            disabled={disabled}
            value={s.turn_share}
            onChange={(e) => {
              const share = +e.target.value;
              onChange({
                turn_share: share,
                extra_options: share > 0 ? s.extra_options
                  : s.extra_options.filter((o) => o !== "turn_lane" && o !== "turn_ban"),
              }); // fmt: skip
            }}
          />
        </label>
      </div>

      <h3>
        <label className="check">
          <input
            type="checkbox"
            checked={!!incident}
            disabled={disabled}
            onChange={(e) =>
              onChange(
                e.target.checked
                  ? { incident: { direction: "east", start_s: 120, duration_s: 1200, lanes_blocked: 1,
                      label: "Lane-blocking incident (assumed)" } }
                  : { incident: null, extra_options: s.extra_options.filter((o) => o !== "incident_clearance") },
              )
            } // fmt: skip
          />
          Include a lane-blocking incident at J2
        </label>
      </h3>
      {incident && (
        <div className="design-grid">
          <label>
            Direction
            <select
              value={incident.direction}
              disabled={disabled}
              onChange={(e) => onChange({ incident: { ...incident, direction: e.target.value as "east" | "west" } })}
            >
              <option value="east">Eastbound</option>
              <option value="west">Westbound</option>
            </select>
          </label>
          <label>
            Lanes blocked
            <select
              value={incident.lanes_blocked}
              disabled={disabled}
              onChange={(e) => onChange({ incident: { ...incident, lanes_blocked: +e.target.value } })}
            >
              {Array.from({ length: s.arterial_lanes }, (_, i) => i + 1).map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          <label>
            Duration · {Math.round(incident.duration_s / 60)} min
            <input
              type="range"
              min="60"
              max="3600"
              step="60"
              disabled={disabled}
              value={incident.duration_s}
              onChange={(e) => onChange({ incident: { ...incident, duration_s: +e.target.value } })}
            />
          </label>
          <label>
            How often · {number(s.incident_weight * 100)}% of peaks
            <input
              type="range"
              min="0.005"
              max="1"
              step="0.005"
              disabled={disabled}
              value={s.incident_weight}
              onChange={(e) => onChange({ incident_weight: +e.target.value })}
            />
          </label>
        </div>
      )}

      <h3>Extra options for the agents</h3>
      <div className="option-checks">
        {OPTIONS.map((o) => {
          const blocked = o.needs?.(s) ?? null;
          return (
            <label key={o.id} className={`check option-check ${blocked ? "blocked" : ""}`}>
              <input
                type="checkbox"
                disabled={disabled || !!blocked}
                checked={s.extra_options.includes(o.id)}
                onChange={(e) => toggle(o.id, e.target.checked)}
              />
              <span>
                <strong>
                  {o.label(s)} · {money(o.cost(s))}
                </strong>
                <small>{blocked ?? o.note}</small>
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

/** Dynamic "What the agents will test" list (step 2). */
export function TestPlan({ scenario }: { scenario: Scenario }) {
  const s = scenario;
  const items: [string, string, number][] = [
    [s.junction_control === "signal" ? "Equal-green reference" : "Current priority control",
      "Establish the reference on identical arrivals.", 0],
    ["Signal retiming", "Shift arterial green, then revise if cross-street harm is too high.",
      s.retiming_cost_cad],
    ["Extra arterial lane", "Test capacity against the same demand. Construction feasibility remains open.",
      s.widening_cost_cad],
    ...OPTIONS.filter((o) => s.extra_options.includes(o.id)).map(
      (o) => [o.label(s), o.note, o.cost(s)] as [string, string, number],
    ),
  ]; // fmt: skip
  // "Signal retiming" covers two options (first proposal + outcome-based revision).
  const runs = (items.length + 1) * 3 * (s.incident && s.incident_weight < 1 ? 2 : 1);
  return (
    <section className="panel intervention-menu">
      <div className="panel-heading">
        <h2>What the agents will test</h2>
        <span className="badge neutral">{items.length} OPTIONS</span>
      </div>
      {items.map(([label, description, cost], i) => (
        <div className="intervention-row" key={label}>
          <span>{String(i + 1).padStart(2, "0")}</span>
          <div>
            <strong>{label}</strong>
            <p>{description}</p>
          </div>
          <small>{money(cost)}</small>
        </div>
      ))}
      <p className="helper test-plan-note">
        {runs} hold-out simulations
        {s.incident && s.incident_weight < 1
          ? ` (normal + incident conditions, weighted ${number(s.incident_weight * 100)}% incident)`
          : ""}
        {" "}+ proposal and stress runs.
      </p>
    </section>
  );
}

/** Step 3 / compare: six-month evidence + modeled effects, per option. */
export function EvidenceSummaryPanel({ result }: { result: Result }) {
  const s = result.evidence_summary;
  if (!s) return null;
  return (
    <section className="panel evidence-summary">
      <div className="panel-heading">
        <div>
          <h2>
            <FileSearch size={16} /> Evidence summary
            {s.intersection_key ? ` · ${s.intersection_key}` : ""}
          </h2>
          <p className="helper">{s.headline}</p>
        </div>
      </div>
      <div className="evidence-grid">
        <div>
          <h3>
            <ClipboardList size={14} /> Observed (City records{s.intersection_key ? ", six months" : ""})
          </h3>
          {s.observed_facts.length ? (
            <ul>
              {s.observed_facts.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          ) : (
            <p className="helper">
              No intersection attached. Build a study from the Intersections tab to include six
              months of City data.
            </p>
          )}
        </div>
        <div>
          <h3>Modeled effect of each option</h3>
          <ul className="evidence-options">
            {s.options.map((o) => (
              <li key={o.id} className={o.recommended ? "recommended" : o.feasible ? "" : "rejected"}>
                <strong>
                  {o.label}
                  {o.recommended ? " · recommended" : o.feasible ? "" : " · not eligible"}
                </strong>
                <span>{o.sentence}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <p className="incident-caution">{s.proof_standard}</p>
    </section>
  );
}
