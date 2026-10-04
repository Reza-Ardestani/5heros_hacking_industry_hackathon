import React from "react";
import {
  ArrowUpRight,
  CheckCircle2,
  Info,
  FlaskConical,
  ChevronRight,
  Loader2,
} from "lucide-react";
import type { Alternative, Result, Frame, Job } from "../types";
import { money, number, optionName } from "../lib/format";
import { WhyNotLowest } from "./DecisionExplain";

export function Stat({
  icon,
  label,
  value,
  note,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="panel stat">
      <div>
        {icon}
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      <p>{note}</p>
    </div>
  );
}
export function Decision({
  result,
  recommendation,
  reference,
  onCompare,
}: {
  result: Result;
  recommendation: Alternative;
  reference: Alternative;
  onCompare?: () => void;
}) {
  const improved =
    recommendation.id !== "reference" &&
    recommendation.comparison.feasible &&
    recommendation.comparison.delay_reduction_pct > 0;
  return (
    <section
      className={`decision-banner ${!result.stress_passed ? "caution" : ""}`}
    >
      <span className="decision-icon">
        {improved ? <CheckCircle2 size={25} /> : <Info size={25} />}
      </span>
      <div>
        <div className="eyebrow">
          {improved ? "RECOMMENDED IN THIS EXPERIMENT" : "REFERENCE RETAINED"}
        </div>
        <h3>
          {improved
            ? optionName(recommendation.id, recommendation.label)
            : "Keep the reference plan"}
        </h3>
        <p>
          {improved ? (
            <>
              <strong>
                {number(recommendation.comparison.delay_reduction_pct)}% less
                modeled delay
              </strong>{" "}
              · {number(reference.metrics.mean_delay_s)}s to{" "}
              {number(recommendation.metrics.mean_delay_s)}s per vehicle.
            </>
          ) : (
            "No alternative earns a feasible improvement on these inputs."
          )}{" "}
          {result.stress_passed
            ? "Both flow stress checks pass."
            : "Stress or feasibility warning: review evidence before proceeding."}
        </p>
        <WhyNotLowest result={result} />
      </div>
      {onCompare && (
        <button onClick={onCompare}>
          Review recommendation <ArrowUpRight size={17} />
        </button>
      )}
    </section>
  );
}
export function JobStatus({
  job,
  submitting,
  pollError,
  onStudy,
}: {
  job: Job | null;
  submitting: boolean;
  pollError: string;
  onStudy: () => void;
}) {
  const failed = !submitting && job?.status === "failed";
  const latest = job?.trace.at(-1);
  return (
    <section
      className="panel running-panel"
      role={failed ? "alert" : "status"}
      aria-live="polite"
    >
      {failed ? <Info size={24} /> : <Loader2 className="spinner" size={24} />}
      <div>
        <h3>
          {submitting
            ? "Submitting experiment"
            : failed
              ? "Simulation failed"
              : "Simulation running"}
        </h3>
        <p>
          {submitting
            ? "Waiting for the simulator to accept this study."
            : failed
              ? (job?.error ?? "The simulator could not complete this study.")
              : latest
                ? `${latest.agent}: ${latest.detail}`
                : "Preparing paired traffic inputs."}
        </p>
        {!submitting && !failed && (
          <span>
            {job?.trace.length ?? 0} recorded actions · results appear after
            evaluation
          </span>
        )}
        {!submitting && !failed && pollError && (
          <p role="alert">
            Updates interrupted: {pollError} Retrying automatically; the last
            known simulation status is running.
          </p>
        )}
        {failed && (
          <button className="button secondary" onClick={onStudy}>
            Review inputs and retry
          </button>
        )}
      </div>
    </section>
  );
}

export function EmptyState({ onStudy }: { onStudy: () => void }) {
  return (
    <section className="panel empty-state">
      <FlaskConical size={32} />
      <h2>No results yet.</h2>
      <p>
        Define a study and run the simulator. Recommendations come from actual
        outcomes.
      </p>
      <button className="button primary" onClick={onStudy}>
        Set up experiment <ChevronRight size={17} />
      </button>
    </section>
  );
}
export function Network({
  current,
  active,
}: {
  current: Frame | undefined;
  active: Alternative | undefined;
}) {
  return (
    <div className="network-view">
      <div className="network-topline">
        <span>NETWORK SCHEMATIC</span>
        <span>J1—J3 · 90-second signal cycle</span>
      </div>
      <svg
        viewBox="-70 -30 1740 700"
        role="img"
        aria-label="Synthetic three-junction corridor with actual SUMO vehicle positions"
      >
        <defs>
          <pattern
            id="blocks"
            width="140"
            height="120"
            patternUnits="userSpaceOnUse"
          >
            <rect x="8" y="8" width="124" height="104" rx="5" fill="#eff1ee" />
            <path
              d="M 0 0 H 140 V 120"
              fill="none"
              stroke="#e3e8e2"
              strokeWidth="2"
            />
          </pattern>
        </defs>
        <rect x="-70" y="-30" width="1740" height="700" fill="url(#blocks)" />
        <rect x="75" y="65" width="190" height="115" rx="15" fill="#dae8d3" />
        <rect
          x="1320"
          y="430"
          width="185"
          height="135"
          rx="16"
          fill="#dae8d3"
        />
        {[400, 800, 1200].map((x, i) => (
          <g key={x}>
            <rect x={x - 24} y="0" width="48" height="600" fill="#c1c9c9" />
            <path
              d={`M ${x} 0 V 600`}
              stroke="#f9fbfb"
              strokeDasharray="11 10"
              strokeWidth="2"
            />
            <text x={x + 45} y="125" fill="#697978" fontSize="22">
              Cross {i + 1}
            </text>
          </g>
        ))}
        <rect x="0" y="259" width="1600" height="82" rx="5" fill="#768b90" />
        <path
          d="M 0 300 H 1600"
          stroke="#edf2ed"
          strokeDasharray="17 12"
          strokeWidth="2"
        />
        {active?.main_lanes === 2 && (
          <>
            <path
              d="M 0 278 H 1600 M 0 322 H 1600"
              stroke="#a8bbc0"
              strokeDasharray="12 10"
              strokeWidth="1"
            />
          </>
        )}
        <text x="35" y="230" fill="#3c555d" fontSize="25" fontWeight="600">
          Arterial · 1.6 km
        </text>
        {[400, 800, 1200].map((x, i) => (
          <g key={x}>
            <rect x={x - 24} y="259" width="48" height="82" fill="#8ba0a4" />
            <rect
              x={x - 43}
              y="361"
              width="86"
              height="38"
              rx="6"
              fill="#fff"
              stroke="#d2dcd6"
            />
            <text
              x={x}
              y="388"
              textAnchor="middle"
              fill="#354d4f"
              fontSize="24"
              fontWeight="600"
            >
              J{i + 1}
            </text>
          </g>
        ))}
        {current?.vehicles.map((v) => (
          <rect
            key={v.id}
            x={v.x - 5}
            y={600 - v.y - 3}
            width="11"
            height="6"
            rx="2"
            fill={v.speed < 2 ? "#dc6b3c" : "#163d4b"}
          />
        ))}
        {!current && (
          <g>
            <rect
              x="435"
              y="451"
              width="730"
              height="73"
              rx="10"
              fill="#ffffff"
              stroke="#d9e2dc"
            />
            <text
              x="800"
              y="496"
              textAnchor="middle"
              fill="#4e6566"
              fontSize="24"
            >
              Run experiment to replay simulated traffic
            </text>
          </g>
        )}
      </svg>
      <div className="network-legend">
        <span>
          <i className="dot navy" />
          Moving
        </span>
        <span>
          <i className="dot orange" />
          Slow / stopped
        </span>
        <strong>
          {active
            ? `${Math.round(active.main_green_share * 100)}% arterial green · ${active.main_lanes} lane${active.main_lanes > 1 ? "s" : ""}/direction`
            : "Synthetic layout · straight trips only"}
        </strong>
      </div>
    </div>
  );
}
export function CostChart({
  alternatives,
  frontier,
}: {
  alternatives: Alternative[];
  frontier: string[];
}) {
  const maxDelay =
      Math.max(1, ...alternatives.map((a) => a.metrics.mean_delay_s)) * 1.15,
    maxCost = Math.max(1, ...alternatives.map((a) => a.capital_cost_cad));
  const x = (a: Alternative) =>
      60 + (Math.log10(1 + a.capital_cost_cad) / Math.log10(1 + maxCost)) * 390,
    y = (a: Alternative) => 195 - (a.metrics.mean_delay_s / maxDelay) * 160;
  return (
    <div className="cost-chart">
      <svg
        viewBox="0 0 510 255"
        role="img"
        aria-label="Hold-out mean delay versus estimated capital cost on a logarithmic scale"
      >
        {[0, 1, 2].map((i) => (
          <g key={i}>
            <line
              x1="60"
              x2="465"
              y1={35 + i * 80}
              y2={35 + i * 80}
              stroke="#e3e8e4"
            />
            <text
              x="48"
              y={39 + i * 80}
              textAnchor="end"
              fill="#687b7e"
              fontSize="12"
            >
              {Math.round(maxDelay * (1 - i * 0.5))}s
            </text>
          </g>
        ))}
        {alternatives.map((a) => (
          <g key={a.id}>
            <circle
              cx={x(a)}
              cy={y(a)}
              r={frontier.includes(a.id) ? 8 : 6}
              fill={a.comparison.feasible ? "#1d7768" : "#ce7645"}
            />
            <text
              x={x(a)}
              y={y(a) - 15}
              textAnchor={
                a.id === "reference"
                  ? "start"
                  : a.id === "capacity"
                    ? "end"
                    : "middle"
              }
              fontSize="12"
              fill="#3e575d"
            >
              {optionName(a.id, a.label)}
            </text>
          </g>
        ))}
        <text x="60" y="222" fill="#687b7e" fontSize="12">
          $0
        </text>
        <text x="450" y="222" textAnchor="end" fill="#687b7e" fontSize="12">
          {money(maxCost)}
        </text>
        <text x="255" y="247" textAnchor="middle" fill="#687b7e" fontSize="12">
          Estimated capital cost · lower delay is better
        </text>
      </svg>
    </div>
  );
}
