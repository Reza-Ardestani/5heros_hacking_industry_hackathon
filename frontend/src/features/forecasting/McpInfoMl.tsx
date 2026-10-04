import { BrainCircuit, CheckCircle2, CircleSlash, Loader2, Plug, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { number } from "../../shared/format";
import type { AreaFocus } from "../../shared/geo";
import * as api from "./api";
import type { McpInfo, MlBenchmark, MlInfo, Prediction } from "./types";
const MODEL_NAMES = ["flat", "bayes", "lightgbm"] as const;
const SHORT: Record<string, string> = { flat: "Flat", bayes: "Bayes", lightgbm: "LightGBM" };
function areaQuery(focus: AreaFocus | null, radius: number) {
  if (!focus)
    return "";
  return new URLSearchParams({
    lat: String(focus.lat),
    lon: String(focus.lon),
    radius_m: String(radius),
    area_label: focus.label,
  }).toString();
}
/** "mcp-info-ml" tab: ML details, model comparison and predictions for the focused area,
 * the standard multi-slice benchmark, and what the MCP server exposes right now. */
export function McpInfoMl({ focus, radius }: {
  focus: AreaFocus | null;
  radius: number;
}) {
  const [preds, setPreds] = useState<Record<string, Prediction>>({});
  const [ml, setMl] = useState<MlInfo | null>(null);
  const [bench, setBench] = useState<MlBenchmark | null>(null);
  const [mcp, setMcp] = useState<McpInfo | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const area = areaQuery(focus, radius);
  useEffect(() => {
    api.mlInfo().then(setMl).catch((e) => setError(e.message));
    api.benchmark().then(setBench).catch((e) => setError(e.message));
    api.mcpInfo().then(setMcp).catch((e) => setError(e.message));
  }, []);
  // Auto pick plus each model forced, for the focused area (or all of Calgary).
  useEffect(() => {
    let current = true;
    setBusy("area");
    setPreds({});
    const base = `horizon_days=7${area ? `&${area}` : ""}`;
    Promise.all(["auto", ...MODEL_NAMES].map((m) => api.predict(`${base}&model=${m}`).then((p) => [m, p] as const)))
      .then((pairs) => current && setPreds(Object.fromEntries(pairs)))
      .catch((e) => current && setError(e.message))
      .finally(() => current && setBusy(""));
    return () => {
      current = false;
    };
  }, [area]);
  const runSelfCheck = () => {
    setBusy("mcp");
    api.mcpInfo(true)
      .then(setMcp)
      .catch((e) => setError(e.message))
      .finally(() => setBusy(""));
  };
  const auto = preds.auto;
  const bt = auto?.backtest;
  const testMaes = bt?.models ? Object.values(bt.models).map((m) => m.test_daily_mae) : [];
  const maxMae = Math.max(0.001, ...testMaes);
  const lgb = ml?.models.find((m) => m.name === "lightgbm");
  const importance = preds.lightgbm?.model?.feature_importance;
  return (<div className="mim">
    {error && <p className="incident-caution">{error}</p>}

    <section className="mim-section">
      <h3>
        <BrainCircuit size={15} /> Model comparison ·{" "}
        {focus ? `within ${radius / 1000} km of ${focus.label}` : "all of Calgary"}
        {busy === "area" && <Loader2 size={14} className="spin" />}
      </h3>
      {!focus && (<p className="helper">Click any dot on the map to compare the models for that area.</p>)}
      {auto && (<>
        <p className="helper">
          {auto.history.incidents} incidents in this area over {auto.history.observed_days}{" "}
          days. Auto picked <strong>{auto.model?.label}</strong>
          {bt?.validation_start
            ? ` on validation days ${bt.validation_start} → ${bt.validation_end}; test days ${bt.test_start} → ${bt.test_end} were not used to choose.`
            : "."}
          {auto.model?.note ? ` ${auto.model.note}.` : ""}
        </p>
        {bt?.models ? (<table className="px-models mim-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Validation MAE</th>
              <th>Test MAE (lower is better)</th>
              <th>80% range hit</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(bt.models).map(([name, m]) => (<tr key={name} className={name === bt.selected_model ? "selected" : ""}>
              <td>
                {SHORT[name] ?? name}
                {name === bt.selected_model ? " ✓ chosen" : ""}
              </td>
              <td>{m.validation_daily_mae}</td>
              <td>
                <span className="mim-bar">
                  <i style={{ width: `${(100 * m.test_daily_mae) / maxMae}%` }} />
                </span>
                {m.test_daily_mae}
              </td>
              <td>{m.test_interval_80_coverage_pct}%</td>
            </tr>))}
            {(bt.not_eligible ?? []).map((n) => (<tr key={n} className="muted-row">
              <td>{SHORT[n] ?? n}</td>
              <td colSpan={3}>
                Not eligible: fewer than {lgb?.min_incidents ?? 30} incidents in this area
              </td>
            </tr>))}
          </tbody>
        </table>) : (<p className="helper">Not enough history in this area to backtest.</p>)}
      </>)}
    </section>

    <section className="mim-section">
      <h3>Predictions for the next 7 days, by model</h3>
      <div className="mim-preds">
        {MODEL_NAMES.map((m) => {
          const p = preds[m];
          if (!p)
            return null;
          const forced = p.model?.name !== m;
          const max = Math.max(0.01, ...p.days.map((d) => d.expected));
          return (<div key={m} className={`mim-pred ${bt?.selected_model === m ? "chosen" : ""}`}>
            <strong>{SHORT[m]}</strong>
            <span className="mim-big">{number(p.expected_total)}</span>
            <small>
              80% range {p.interval_80[0]}–{p.interval_80[1]}
              {forced ? ` · fell back to ${SHORT[p.model?.name ?? ""] ?? ""}` : ""}
            </small>
            <div className="mim-days">
              {p.days.map((d) => (<i key={d.date} title={`${d.weekday} ${d.date}: ${d.expected}`} style={{ height: `${(100 * d.expected) / max}%` }} />))}
            </div>
          </div>);
        })}
      </div>
    </section>

    {importance && (<section className="mim-section">
      <h3>What drives LightGBM here (share of split gain)</h3>
      <div className="ix-bars">
        {Object.entries(importance)
          .sort((a, b) => b[1] - a[1])
          .map(([f, v]) => (<div className="ix-bar-row" key={f} title={lgb?.features?.find((x) => x.name === f)?.meaning}>
            <span>{f}</span>
            <div>
              <i style={{ width: `${v}%` }} />
            </div>
            <strong>{v}%</strong>
          </div>))}
      </div>
    </section>)}

    {bench && (<section className="mim-section">
      <h3>Benchmark across standard selections (test-window daily MAE)</h3>
      <p className="helper">
        Best on test:{" "}
        {Object.entries(bench.best_on_test_counts)
          .map(([k, v]) => `${SHORT[k] ?? k} ${v}`)
          .join(" · ")}
        {"  ·  "}Chosen on validation:{" "}
        {Object.entries(bench.selected_counts)
          .map(([k, v]) => `${SHORT[k] ?? k} ${v}`)
          .join(" · ")}
      </p>
      <div className="ix-table">
        <table>
          <thead>
            <tr>
              <th>Selection</th>
              <th>Incidents</th>
              {MODEL_NAMES.map((m) => (<th key={m}>{SHORT[m]}</th>))}
              <th>Chosen</th>
              <th>7-day forecast</th>
            </tr>
          </thead>
          <tbody>
            {bench.slices.map((r) => (<tr key={r.slice}>
              <td>{r.slice}</td>
              <td>{r.incidents}</td>
              {MODEL_NAMES.map((m) => (<td key={m} className={r.best_on_test === m ? "mim-best" : ""}>
                {r.models[m]?.test_mae ?? "–"}
              </td>))}
              <td>{SHORT[r.selected_model ?? ""] ?? "–"}</td>
              <td>
                {number(r.forecast_7d)} ({r.interval_80[0]}–{r.interval_80[1]})
              </td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </section>)}

    {ml && (<section className="mim-section">
      <h3>ML model details</h3>
      <div className="mim-models">
        {ml.models.map((m) => (<div key={m.name}>
          <strong>
            {m.label} <span className="badge neutral">{m.type}</span>
          </strong>
          <p>{m.how}</p>
          {m.library && <p className="helper">{m.library}</p>}
          {m.features && (<ul>
            {m.features.map((f) => (<li key={f.name}>
              <code>{f.name}</code> {f.meaning}
            </li>))}
          </ul>)}
          {m.params && (<p className="helper mim-params">
            {m.rounds} rounds ·{" "}
            {Object.entries(m.params)
              .map(([k, v]) => `${k}=${String(v)}`)
              .join(" · ")}
          </p>)}
        </div>))}
      </div>
      <p className="helper">
        {ml.selection.rule} Metric: {ml.selection.metric}. {ml.no_external_models}
      </p>
    </section>)}

    <section className="mim-section">
      <h3>
        <Plug size={15} /> MCP server
        <button className="button secondary mim-check" onClick={runSelfCheck} disabled={busy === "mcp"}>
          {busy === "mcp" ? <Loader2 size={14} className="spin" /> : <CheckCircle2 size={14} />}
          Run self-check
        </button>
      </h3>
      {mcp && !mcp.reachable && (<p className="incident-caution">
        <TriangleAlert size={13} /> Not reachable at {mcp.probed_url}. Start it with{" "}
        <code>{mcp.how_to_start}</code>.
      </p>)}
      {mcp?.reachable && (<>
        <p className="helper">
          {mcp.server?.name} · {mcp.server?.sdk} · {mcp.endpoint?.transport} at{" "}
          <code>
            http://{mcp.endpoint?.host}:{mcp.endpoint?.port}
            {mcp.endpoint?.path}
          </code>
          {mcp.endpoint?.agentcore_compatible ? " · AgentCore-compatible" : ""} ·{" "}
          {mcp.summary?.tools} tools ({mcp.summary?.read_only} read-only)
          {mcp.summary?.self_check_ok != null &&
            ` · self-check: ${mcp.summary.self_check_ok} ok, ${mcp.summary.self_check_errors} errors, ${mcp.summary.self_check_not_run} not run`}
        </p>
        <div className="ix-table">
          <table>
            <thead>
              <tr>
                <th>Tool</th>
                <th>Access</th>
                <th>Status</th>
                <th>Arguments</th>
                <th>What it does</th>
              </tr>
            </thead>
            <tbody>
              {mcp.tools?.map((t) => (<tr key={t.name}>
                <td>
                  <code>{t.name}</code>
                </td>
                <td>{t.read_only ? "read" : "writes"}</td>
                <td>
                  {t.self_check?.status === "ok" ? (<span className="mim-ok">
                    <CheckCircle2 size={12} /> {t.self_check.ms} ms
                  </span>) : t.self_check?.status === "error" ? (<span className="mim-err">{t.self_check.error}</span>) : t.self_check?.status === "not_run" ? (<span className="mim-skip" title={t.self_check.reason}>
                    <CircleSlash size={12} /> not run
                  </span>) : ("–")}
                </td>
                <td>{Object.keys(t.arguments).join(", ") || "–"}</td>
                <td>{t.description}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
        {mcp.connect && (<p className="helper">
          Connect: <code>{mcp.connect.claude_code}</code>
        </p>)}
      </>)}
    </section>
  </div>);
}
