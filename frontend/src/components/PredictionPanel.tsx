import React, { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Info, LineChart, Loader2, RotateCcw } from "lucide-react";

import type { PredictOptions, Prediction } from "../types";
import { request } from "../lib/api";
import { number } from "../lib/format";

export type Selection = {
  quadrant: string;
  route: string;
  direction: string;
  lane: string;
  category: string;
  intersection: string;
  horizon_days: number;
};
export const emptySelection: Selection = {
  quadrant: "",
  route: "",
  direction: "",
  lane: "",
  category: "",
  intersection: "",
  horizon_days: 7,
};
const DIRECTIONS: Record<string, string> = {
  NB: "Northbound",
  SB: "Southbound",
  EB: "Eastbound",
  WB: "Westbound",
};
const pct = (p: number) => `${Math.round(p * 100)}%`;

function Picker({
  label,
  value,
  options,
  all,
  onChange,
  format = (v: string) => v,
  disabled,
}: {
  label: string;
  value: string;
  options: { value: string; incidents: number }[];
  all: string;
  onChange: (v: string) => void;
  format?: (v: string) => string;
  disabled?: boolean;
}) {
  return (
    <label className="px-field">
      <span>{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        <option value="">{all}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {format(o.value)} ({o.incidents})
          </option>
        ))}
      </select>
    </label>
  );
}

export function PredictionPanel({
  selection,
  onSelect,
  onOpenIntersection,
}: {
  selection: Selection;
  onSelect: (s: Selection) => void;
  onOpenIntersection: (key: string) => void;
}) {
  const [options, setOptions] = useState<PredictOptions | null>(null),
    [result, setResult] = useState<Prediction | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const s = selection;
  const set = (patch: Partial<Selection>) => onSelect({ ...s, ...patch });

  // Route list depends on area; lanes/directions/intersections depend on route.
  useEffect(() => {
    const params = new URLSearchParams({ quadrant: s.quadrant, route: s.route });
    request<PredictOptions>(`/api/disruptions/options?${params}`)
      .then(setOptions)
      .catch((e) => setError(e.message));
  }, [s.quadrant, s.route]);

  // Only the newest request may update the panel; slower older responses are dropped.
  const latest = useRef(0);
  const run = () => {
    const id = ++latest.current;
    setBusy(true);
    setError("");
    const params = new URLSearchParams(
      Object.entries(s).map(([k, v]) => [k, String(v)]),
    );
    request<Prediction>(`/api/disruptions/predict?${params}`)
      .then((r) => id === latest.current && setResult(r))
      .catch((e) => id === latest.current && setError(e.message))
      .finally(() => id === latest.current && setBusy(false));
  };
  // Regenerate whenever the selection changes, so the panel is always current
  // (and shows a citywide example on first load).
  const key = JSON.stringify(s);
  useEffect(() => {
    const timer = setTimeout(run, 250);
    return () => clearTimeout(timer);
  }, [key]);

  const bt = result?.backtest;
  return (
    <section className="panel px">
      <div className="panel-heading">
        <div>
          <h2>
            <LineChart size={17} /> Predict disruptions for an area, route and lane
          </h2>
          <p className="helper">
            Choose where to look, then generate an expected count of City-reported
            incidents for the coming days.
          </p>
        </div>
        <button
          className="button secondary"
          onClick={() => onSelect(emptySelection)}
        >
          <RotateCcw size={14} /> Reset
        </button>
      </div>
      <div className="px-form">
        <Picker
          label="Area (quadrant)"
          value={s.quadrant}
          all="All Calgary"
          options={options?.quadrants ?? []}
          onChange={(v) =>
            set({ quadrant: v, route: "", intersection: "", direction: "", lane: "" })
          }
        />
        <Picker
          label="Route / corridor"
          value={s.route}
          all="All routes"
          options={options?.routes ?? []}
          onChange={(v) =>
            set({ route: v, intersection: "", direction: "", lane: "" })
          }
        />
        <Picker
          label="Direction"
          value={s.direction}
          all="Both / all directions"
          options={options?.directions ?? []}
          format={(v) => DIRECTIONS[v] ?? v}
          onChange={(v) => set({ direction: v })}
        />
        <Picker
          label="Lane"
          value={s.lane}
          all="Any lane"
          options={options?.lanes ?? []}
          onChange={(v) => set({ lane: v })}
        />
        <Picker
          label="Incident type"
          value={s.category}
          all="All types"
          options={options?.categories ?? []}
          onChange={(v) => set({ category: v })}
        />
        <Picker
          label="Intersection on route"
          value={s.intersection}
          all={s.route ? "Whole route" : "Pick a route first"}
          options={options?.intersections ?? []}
          disabled={!s.route && !s.intersection}
          onChange={(v) => set({ intersection: v })}
        />
        <label className="px-field">
          <span>Horizon</span>
          <select
            value={s.horizon_days}
            onChange={(e) => set({ horizon_days: Number(e.target.value) })}
          >
            {[1, 7, 14, 28].map((d) => (
              <option key={d} value={d}>
                Next {d} day{d > 1 ? "s" : ""}
              </option>
            ))}
          </select>
        </label>
        <button className="button primary px-run" onClick={run} disabled={busy}>
          {busy ? <Loader2 size={16} className="spin" /> : <LineChart size={16} />}
          Generate prediction
        </button>
      </div>
      {error && <p className="incident-caution">{error}</p>}
      {result && (
        <div className="px-result">
          <div className="px-headline">
            <div>
              <div className="eyebrow">
                {Object.values(result.selection).join(" · ") || "ALL CALGARY"}
              </div>
              <strong>{number(result.expected_total)}</strong>
              <span>
                expected incidents, {result.forecast_start} + {result.horizon_days}{" "}
                day{result.horizon_days > 1 ? "s" : ""}
              </span>
            </div>
            <div>
              <strong>
                {result.interval_80[0]}–{result.interval_80[1]}
              </strong>
              <span>80% range (negative binomial)</span>
            </div>
            <div>
              <strong>{pct(result.p_at_least_one)}</strong>
              <span>chance of at least one</span>
            </div>
            <div>
              <strong>{number(result.history.incidents)}</strong>
              <span>
                in history ({number(result.history.per_day)}/day over{" "}
                {result.history.observed_days} days)
              </span>
            </div>
            <div>
              <strong>
                {result.history.lane_blocking_pct == null
                  ? "–"
                  : `${result.history.lane_blocking_pct}%`}
              </strong>
              <span>historically blocked a lane</span>
            </div>
          </div>
          {result.low_data && (
            <p className="incident-caution">
              <Info size={13} /> Fewer than 20 past incidents match this selection;
              the forecast leans on the citywide weekly pattern.
            </p>
          )}
          <div className="px-grid">
            <div>
              <h3>Chance of ≥1 incident by day and period</h3>
              <div className="px-heat" role="table">
                <div role="row" className="px-heat-row head">
                  <span />
                  {result.periods.map((p) => (
                    <span key={p}>{p}</span>
                  ))}
                  <span>Day total</span>
                </div>
                {result.days.map((d) => (
                  <div role="row" className="px-heat-row" key={d.date}>
                    <span>
                      {d.weekday} {d.date.slice(5)}
                    </span>
                    {d.periods.map((p) => (
                      <span
                        key={p.period}
                        className="px-cell"
                        style={{
                          background: `rgba(22, 121, 108, ${0.06 + 0.8 * p.p_at_least_one})`,
                          color: p.p_at_least_one > 0.55 ? "#fff" : "#213b45",
                        }}
                        title={`${d.weekday} ${p.period}: expected ${p.expected}, P(≥1) ${pct(p.p_at_least_one)}`}
                      >
                        {pct(p.p_at_least_one)}
                      </span>
                    ))}
                    <strong title={`P(≥1) ${pct(d.p_at_least_one)}`}>
                      {number(d.expected)}
                    </strong>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3>Is the model better than a simple average?</h3>
              {bt ? (
                <table className="px-backtest">
                  <tbody>
                    <tr>
                      <td>Held-out test</td>
                      <td>
                        {bt.test_start} → {bt.test_end} ({bt.test_days} days, trained on{" "}
                        {bt.train_days})
                      </td>
                    </tr>
                    <tr>
                      <td>Actual vs expected</td>
                      <td>
                        {bt.actual_test_incidents} actual · {bt.model_expected_test_incidents}{" "}
                        expected
                      </td>
                    </tr>
                    <tr>
                      <td>Daily error, model</td>
                      <td>{bt.model_daily_mae} incidents/day (MAE)</td>
                    </tr>
                    <tr>
                      <td>Daily error, baseline</td>
                      <td>
                        {bt.baseline_daily_mae} — {bt.baseline}
                      </td>
                    </tr>
                    <tr>
                      <td>Verdict</td>
                      <td>
                        <strong>
                          {bt.improvement_vs_baseline_pct == null
                            ? "Not comparable"
                            : bt.improvement_vs_baseline_pct >= 2
                              ? `${bt.improvement_vs_baseline_pct}% lower error than baseline`
                              : "No better than the flat average for this slice"}
                        </strong>
                      </td>
                    </tr>
                    <tr>
                      <td>80% range hit rate</td>
                      <td>{bt.interval_80_coverage_pct}% of test days</td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <p className="empty-inline">Not enough history to backtest.</p>
              )}
              <h3>Likely incident types</h3>
              <ul className="px-mix">
                {result.history.category_mix.map((c) => (
                  <li key={c.category}>
                    <span>{c.category}</span>
                    <i style={{ width: `${c.share_pct}%` }} />
                    <strong>{c.share_pct}%</strong>
                  </li>
                ))}
              </ul>
              {result.top_intersections.length > 0 && (
                <>
                  <h3>Where in this selection</h3>
                  <ul className="px-spots">
                    {result.top_intersections.map((t) => (
                      <li key={t.key}>
                        <button
                          className="text-link"
                          onClick={() => onOpenIntersection(t.key)}
                        >
                          {t.key} <ArrowUpRight size={12} />
                        </button>
                        <span>
                          ≈{number(t.expected_in_horizon)} in horizon · {t.incidents} in
                          history
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
          <details className="px-method">
            <summary>Method and limits</summary>
            <p>{result.method}</p>
            <p>{result.caveat}</p>
          </details>
        </div>
      )}
    </section>
  );
}
