import { AlertTriangle, ArrowUpRight, FlaskConical, Info, LineChart, Loader2, Target, } from "lucide-react";
import { useEffect, useState } from "react";
import { number } from "../../shared/format";
import type { IntersectionStudy } from "../studies";
import * as api from "./api";
import type { Priorities, PriorityItem } from "./types";
const SORTS: Record<string, string> = {
  expected: "Expected incidents",
  lane_blocking: "Expected lane-blocking",
  rising: "Recent change",
  exposure: "Per 10k daily vehicles",
};
// Below this rank agreement in the hold-out check, a ranking is too noisy to steer by.
const WEAK_RANKING = 0.3;
const shortDate = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString("en-CA", {
  month: "short",
  day: "numeric",
});
function Change({ item }: {
  item: PriorityItem;
}) {
  if (item.trend_ratio == null)
    return <span className="badge neutral">–</span>;
  const pct = Math.round((item.trend_ratio - 1) * 100);
  const label = `${pct > 0 ? "+" : ""}${pct}%`;
  const title = `Share of incidents in the last 28 days vs the city's: ×${item.trend_ratio} (p = ${item.trend_p_value})`;
  if (item.trend === "rising")
    return (<span className="badge amber" title={title}>
      Rising {label}
    </span>);
  if (item.trend === "falling")
    return (<span className="badge green" title={title}>
      Falling {label}
    </span>);
  return (<span className="badge neutral" title={title}>
    {label} · within normal
  </span>);
}
// Which intersection a row's Simulate button studies. Prefer the busiest hotspot the
// synthetic arterial can represent; otherwise fall back to the busiest spot, which the
// study builder caps (freeway interchanges are not a signalized corridor).
function studyTarget(level: string, item: PriorityItem) {
  if (item.study_spot)
    return { spot: item.study_spot, capped: false };
  const spot = level === "intersection" ? item.key : item.top_intersections[0];
  return spot ? { spot, capped: true } : null;
}
export function PriorityPanel({ onForecast, onOpenIntersection, onStudy, }: {
  onForecast: (level: "corridor" | "intersection", item: PriorityItem, horizonDays: number) => void;
  onOpenIntersection: (key: string) => void;
  onStudy?: (study: IntersectionStudy) => void;
}) {
  const [level, setLevel] = useState<"corridor" | "intersection">("corridor"), [horizon, setHorizon] = useState(28), [quadrant, setQuadrant] = useState(""), [sort, setSort] = useState("expected"), [data, setData] = useState<Priorities | null>(null), [busy, setBusy] = useState(false), [studying, setStudying] = useState(""), [error, setError] = useState("");
  // Same hand-off as the intersection detail's "Simulate this intersection" button.
  const simulate = (key: string) => {
    setStudying(key);
    setError("");
    api.getIntersectionStudy(key)
      .then((s) => onStudy?.(s))
      .catch((e) => setError(e.message))
      .finally(() => setStudying(""));
  };
  useEffect(() => {
    let current = true;
    setBusy(true);
    const params = new URLSearchParams({
      level,
      horizon_days: String(horizon),
      quadrant,
      sort,
      limit: "15",
    });
    api.priorities(params)
      .then((d) => {
        if (current) {
          setData(d);
          setError("");
        }
      })
      .catch((e) => current && setError(e.message))
      .finally(() => current && setBusy(false));
    return () => {
      current = false;
    };
  }, [level, horizon, quadrant, sort]);
  const a = data?.analysis;
  const check = a?.ranking_check;
  const noun = level === "corridor" ? "corridors" : "intersections";
  const top = Math.max(1, ...(data?.items.map((i) => i.interval_80[1]) ?? [1]));
  const weak = check?.spearman != null && check.spearman < WEAK_RANKING;
  return (<section className="panel pr">
    <div className="panel-heading">
      <div>
        <h2>
          <Target size={17} /> Where to focus next
        </h2>
        <p className="helper">
          {data
            ? `Forecast ranking of ${data.eligible} ${noun} with ≥${data.min_incidents} incidents in six months · next ${data.horizon_days} days from ${shortDate(data.forecast_start)}`
            : "Ranking corridors by forecast disruptions…"}
        </p>
      </div>
      {busy && <Loader2 size={18} className="spin" aria-label="Loading" />}
    </div>

    <div className="px-form">
      <label className="px-field">
        <span>Rank</span>
        <select value={level} onChange={(e) => setLevel(e.target.value as "corridor" | "intersection")}>
          <option value="corridor">Corridors</option>
          <option value="intersection">Intersections</option>
        </select>
      </label>
      <label className="px-field">
        <span>Horizon</span>
        <select value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
          {[7, 14, 28].map((h) => (<option key={h} value={h}>
            Next {h} days
          </option>))}
        </select>
      </label>
      <label className="px-field">
        <span>Area</span>
        <select value={quadrant} onChange={(e) => setQuadrant(e.target.value)}>
          <option value="">All quadrants</option>
          {["NE", "NW", "SE", "SW"].map((q) => (<option key={q}>{q}</option>))}
        </select>
      </label>
      <label className="px-field">
        <span>Sort by</span>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          {Object.entries(SORTS).map(([v, l]) => (<option key={v} value={v}>
            {l}
          </option>))}
        </select>
      </label>
    </div>

    {error && (<div className="notice error" role="alert">
      <AlertTriangle size={18} />
      <span>{error}</span>
    </div>)}

    {a && data && (<>
      <div className="pr-stats">
        <div>
          <strong>
            {number(a.citywide_expected)}
            <small>
              {" "}
              ({a.citywide_interval_80[0]}–{a.citywide_interval_80[1]})
            </small>
          </strong>
          <span>
            expected incidents citywide, next {data.horizon_days} days (80%
            range) · busiest: {a.citywide_peak_window}
          </span>
        </div>
        <div>
          <strong>{a.top_share_of_citywide_pct}%</strong>
          <span>
            of expected citywide incidents fall on the top {a.top_n} {noun}
          </span>
        </div>
        <div>
          <strong>
            {check
              ? `${check.forecast.overlap_with_actual_top}/${check.top_n}`
              : "–"}
          </strong>
          <span>
            {check
              ? `of a top ${check.top_n} built before ${shortDate(check.test_start)} were in the actual top ${check.top_n} for ${shortDate(check.test_start)}–${shortDate(check.test_end)} · captured ${check.forecast.captured_pct}% of incidents (past counts alone: ${check.past_counts.captured_pct}%)`
              : "Not enough history for a ranking check"}
          </span>
        </div>
        <div>
          <strong>{a.rising.length + a.falling.length || "None"}</strong>
          <span>
            {a.rising.length + a.falling.length
              ? `${noun} with a real change in the last ${a.recent_window_days} days (${a.rising.length} rising, ${a.falling.length} falling)`
              : `${noun} changed beyond normal variation in the last ${a.recent_window_days} days (10% false-discovery rate)`}
          </span>
        </div>
        <div>
          <strong>
            {a.calibration
              ? `${a.calibration.interval_80_coverage_pct}%`
              : "–"}
          </strong>
          <span>
            {a.calibration
              ? `of the last ${a.calibration.test_days} days fell inside the citywide 80% range · daily error ${a.calibration.model_daily_mae} vs ${a.calibration.baseline_daily_mae} for a flat average`
              : "Calibration check unavailable"}
          </span>
        </div>
      </div>

      {check && (<p className={weak ? "incident-caution pr-note" : "helper pr-note"}>
        {weak ? (<>
          <AlertTriangle size={13} /> Ranking individual {noun} is
          unreliable here: forecast and actual rankings agreed only{" "}
          {check.spearman} (Spearman, 1 = identical) in the hold-out
          check. Prioritise corridors first, then look at intersections
          within them.
        </>) : (<>
          Hold-out rank agreement {check.spearman} (Spearman, 1 =
          identical). The forecast ranks about as well as past counts;
          its added value is the ranges, busiest window and change test.
        </>)}
      </p>)}

      <div className="ix-table pr-table">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>{level === "corridor" ? "Corridor" : "Intersection"}</th>
              <th>Expected (80% range)</th>
              <th title="Expected incidents × lane-blocking share, shrunk toward the city's">
                Lane-blocking
              </th>
              <th>Recent change</th>
              <th>Busiest window</th>
              <th>2024 volume</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((i, n) => (<tr key={i.key}>
              <td>{n + 1}</td>
              <td>
                <strong>{i.key}</strong>
                <small className="pr-sub">
                  {i.quadrants.join(" · ")} · {i.history_incidents} in six
                  months
                </small>
                {i.top_intersections.length > 0 && (<span className="pr-chips">
                  {i.top_intersections.map((k) => (<button key={k} className="text-link" onClick={() => onOpenIntersection(k)}>
                    {k}
                  </button>))}
                </span>)}
              </td>
              <td>
                <span className="pr-range" title={`80% range ${i.interval_80[0]}–${i.interval_80[1]}`}>
                  <i style={{
                    left: `${(100 * i.interval_80[0]) / top}%`,
                    width: `${(100 * (i.interval_80[1] - i.interval_80[0])) / top}%`,
                  }} />
                  <b style={{ left: `${(100 * i.expected) / top}%` }} />
                </span>
                <strong>{number(i.expected)}</strong>{" "}
                <small>
                  ({i.interval_80[0]}–{i.interval_80[1]})
                </small>
              </td>
              <td>
                <strong>{number(i.expected_lane_blocking)}</strong>
                <small className="pr-sub">
                  lane impact reported for {i.lane_impact_reported_pct}%
                </small>
              </td>
              <td>
                <Change item={i} />
              </td>
              <td>
                {i.peak_window}
                <small className="pr-sub">
                  {i.peak_window_share_pct}% of a week
                </small>
              </td>
              <td>
                {i.median_volume_2024
                  ? `${number(i.median_volume_2024 / 1000)}k/day`
                  : "–"}
                {i.per_10k_daily_vehicles != null && (<small className="pr-sub">
                  {i.per_10k_daily_vehicles} per 10k veh
                </small>)}
              </td>
              <td className="pr-actions">
                {onStudy &&
                  (() => {
                    const target = studyTarget(level, i);
                    if (!target)
                      return null;
                    return (<>
                      <button className="button primary" disabled={!!studying} title={`Build a SUMO study for ${target.spot} and open it in step 2`} onClick={() => simulate(target.spot)}>
                        {studying === target.spot ? (<Loader2 size={14} className="spin" />) : (<FlaskConical size={14} />)}{" "}
                        Simulate
                      </button>
                      <small className={`pr-sub${target.capped ? " pr-capped" : ""}`}>
                        {level === "corridor" && (<>at {target.spot} · </>)}
                        {target.capped
                          ? "freeway: traffic capped in the street model"
                          : `${i.study_spot_incidents} incidents, fits the street model`}
                      </small>
                    </>);
                  })()}
                <button className="button secondary" onClick={() => onForecast(data.level, i, data.horizon_days)}>
                  <LineChart size={14} /> Forecast
                </button>
                {level === "intersection" && (<button className="text-link" onClick={() => onOpenIntersection(i.key)}>
                  Details <ArrowUpRight size={13} />
                </button>)}
              </td>
            </tr>))}
          </tbody>
        </table>
      </div>

      <details className="pr-method">
        <summary>
          <Info size={13} /> How this ranking works
        </summary>
        <p>{data.method}</p>
        <p>{data.caveat}</p>
      </details>
    </>)}
  </section>);
}
