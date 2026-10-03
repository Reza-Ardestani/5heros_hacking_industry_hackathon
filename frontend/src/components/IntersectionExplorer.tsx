import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Camera,
  LineChart,
  Construction,
  MapPin,
  Radio,
  RefreshCw,
  Search,
  TrafficCone,
} from "lucide-react";

import type {
  IncidentEstimate,
  IntersectionStudy,
  DisruptionSummary,
  Intersection,
  IntersectionDetail,
  LiveFeed,
} from "../types";
import { request } from "../lib/api";
import { number } from "../lib/format";
import { IncidentDelayCard } from "./IncidentDelayCard";
import { PredictionPanel, emptySelection, type Selection } from "./PredictionPanel";
import { PriorityPanel } from "./PriorityPanel";

const LIVE_REFRESH_MS = 60_000;
// Calgary city-limit bounding box used to place points on the overview map.
const BOX = { north: 51.22, south: 50.84, west: -114.32, east: -113.86 };
const MAP_W = 320,
  MAP_H = 420;
const project = (lat: number, lon: number) => ({
  x: ((lon - BOX.west) / (BOX.east - BOX.west)) * MAP_W,
  y: ((BOX.north - lat) / (BOX.north - BOX.south)) * MAP_H,
});
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const calgaryTime = (iso: string) =>
  new Date(iso.replace(" ", "T").replace("+00:00", "Z")).toLocaleString(
    "en-CA",
    { timeZone: "America/Edmonton", dateStyle: "medium", timeStyle: "short" },
  );

function Bars({
  rows,
  max,
}: {
  rows: { label: string; value: number }[];
  max?: number;
}) {
  const top = max ?? Math.max(1, ...rows.map((r) => r.value));
  return (
    <div className="ix-bars">
      {rows.map((r) => (
        <div className="ix-bar-row" key={r.label} title={`${r.label}: ${r.value}`}>
          <span>{r.label}</span>
          <div>
            <i style={{ width: `${(100 * r.value) / top}%` }} />
          </div>
          <strong>{number(r.value)}</strong>
        </div>
      ))}
    </div>
  );
}

function Columns({
  values,
  labels,
  caption,
  every = 1,
}: {
  values: number[];
  labels: string[];
  caption: string;
  every?: number;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const top = Math.max(1, ...values);
  const w = 100 / values.length;
  return (
    <figure className="ix-columns" aria-label={caption}>
      <div className="ix-columns-tip">
        {hover === null
          ? caption
          : `${labels[hover]} · ${values[hover]} incident${values[hover] === 1 ? "" : "s"}`}
      </div>
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" role="img">
        {values.map((v, i) => (
          <g
            key={i}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          >
            <rect x={i * w} y={0} width={w} height={40} fill="transparent" />
            <rect
              className={hover === i ? "active" : ""}
              x={i * w + w * 0.12}
              y={40 - (38 * v) / top}
              width={w * 0.76}
              height={(38 * v) / top}
              rx={0.6}
            />
          </g>
        ))}
      </svg>
      <div className="ix-columns-axis">
        {labels.map((l, i) => (
          <span key={l} style={{ width: `${w}%` }}>
            {i % every === 0 ? l : ""}
          </span>
        ))}
      </div>
    </figure>
  );
}

export function IntersectionExplorer({
  onStudy,
}: {
  onStudy?: (study: IntersectionStudy) => void;
}) {
  const [summary, setSummary] = useState<DisruptionSummary | null>(null),
    [mapPoints, setMapPoints] = useState<Intersection[]>([]),
    [list, setList] = useState<{ total: number; items: Intersection[] }>(),
    [detail, setDetail] = useState<IntersectionDetail | null>(null),
    [live, setLive] = useState<LiveFeed | null>(null),
    [selected, setSelected] = useState<string>(""),
    [query, setQuery] = useState(""),
    [quadrant, setQuadrant] = useState(""),
    [sort, setSort] = useState("incidents"),
    [error, setError] = useState(""),
    [liveBusy, setLiveBusy] = useState(false),
    [camTick, setCamTick] = useState(Date.now());
  const [prediction, setPrediction] = useState<Selection>(emptySelection),
    predictRef = useRef<HTMLDivElement>(null);
  const predictIntersection = (d: IntersectionDetail) => {
    const road = d.roads[0] ?? "";
    setPrediction({
      ...emptySelection,
      route: /^\d/.test(road) && d.quadrant ? `${road} ${d.quadrant}` : road,
      intersection: d.key,
    });
    predictRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const detailRef = useRef<HTMLElement>(null),
    scrollOnLoad = useRef(false);
  // Map dots and live-feed links jump to the detail panel; list clicks stay put.
  const focus = (key: string) => {
    scrollOnLoad.current = true;
    setSelected(key);
  };

  useEffect(() => {
    request<DisruptionSummary>("/api/disruptions/summary")
      .then(setSummary)
      .catch((e) => setError(e.message));
    request<{ items: Intersection[] }>("/api/disruptions/intersections?limit=200")
      .then((v) => {
        setMapPoints(v.items);
        setSelected((s) => s || v.items[0]?.key || "");
      })
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams({ q: query, quadrant, sort, limit: "40" });
    const timer = setTimeout(
      () =>
        request<{ total: number; items: Intersection[] }>(
          `/api/disruptions/intersections?${params}`,
        )
          .then(setList)
          .catch((e) => setError(e.message)),
      200,
    );
    return () => clearTimeout(timer);
  }, [query, quadrant, sort]);

  useEffect(() => {
    if (!selected) return;
    let current = true; // ignore responses for a selection the user already left
    request<IntersectionDetail>(
      `/api/disruptions/intersection?key=${encodeURIComponent(selected)}`,
    )
      .then((d) => {
        if (current) setDetail(d);
      })
      .catch((e) => current && setError(e.message));
    return () => {
      current = false;
    };
  }, [selected]);
  // Runs after the new detail has rendered (no reliance on animation frames,
  // which browsers pause in background tabs).
  useEffect(() => {
    if (!detail || !scrollOnLoad.current) return;
    scrollOnLoad.current = false;
    detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [detail]);

  const loadLive = (refresh = false) => {
    setLiveBusy(true);
    request<LiveFeed>(`/api/disruptions/live${refresh ? "?refresh=true" : ""}`)
      .then(setLive)
      .catch((e) => setError(e.message))
      .finally(() => setLiveBusy(false));
  };
  useEffect(() => {
    loadLive();
    const timer = setInterval(() => {
      loadLive();
      setCamTick(Date.now());
    }, LIVE_REFRESH_MS);
    return () => clearInterval(timer);
  }, []);

  const liveNear = useMemo(
    () =>
      new Set(
        (live?.incidents ?? [])
          .map((i) => i.hotspot?.key)
          .filter(Boolean) as string[],
      ),
    [live],
  );
  const mapMax = Math.max(1, ...mapPoints.map((p) => p.incidents));
  const fetched = live
    ? new Date(live.fetched_at_epoch * 1000).toLocaleTimeString("en-CA", {
        timeZone: "America/Edmonton",
        timeStyle: "short",
      })
    : "";

  return (
    <div className="ix">
      {error && (
        <div className="notice error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <section className="panel ix-live">
        <div className="panel-heading">
          <div>
            <h2>
              <Radio size={17} /> Live City feed
            </h2>
            <p className="helper">
              {live
                ? `${live.ok ? "Updated" : "Last good update"} ${fetched} MDT · auto-refresh 60 s · data.calgary.ca${live.persisted ? " · saved to database" : ""}`
                : "Connecting to City of Calgary open data…"}
            </p>
          </div>
          <button
            className="button secondary"
            onClick={() => loadLive(true)}
            disabled={liveBusy}
          >
            <RefreshCw size={15} className={liveBusy ? "spin" : ""} /> Refresh
          </button>
        </div>
        {live && !live.ok && (
          <p className="incident-caution">
            City API unreachable ({live.errors.join("; ")}). Showing the last
            successful response, if any.
          </p>
        )}
        <div className="ix-live-stats">
          <div>
            <strong>{live?.incidents.length ?? "–"}</strong>
            <span>current incidents</span>
          </div>
          <div>
            <strong>{live?.active_closures.length ?? "–"}</strong>
            <span>active road/lane closures</span>
          </div>
          <div>
            <strong>{live?.active_closures_at_hotspots ?? "–"}</strong>
            <span>
              closures within 400 m of a hotspot (≥{live?.hotspot_threshold ?? 5}{" "}
              incidents)
            </span>
          </div>
        </div>
        <div className="ix-live-list">
          {live?.incidents.length === 0 && (
            <p className="empty-inline">No incident reported by the City right now.</p>
          )}
          {live?.incidents.map((i, n) => (
            <article key={n}>
              <span className="ix-status critical">
                <AlertTriangle size={14} /> Live
              </span>
              <div>
                <strong>{i.location_text}</strong>
                <p>
                  {i.description} · started {calgaryTime(i.start_utc)}
                </p>
              </div>
              {i.hotspot ? (
                <button
                  className="text-link"
                  onClick={() => focus(i.hotspot!.key)}
                >
                  {i.hotspot.key}: {i.hotspot.incidents_6mo} in 6 mo
                  <ArrowUpRight size={14} />
                </button>
              ) : (
                <span className="muted">No prior incident within 400 m</span>
              )}
            </article>
          ))}
        </div>
      </section>

      <PriorityPanel
        onForecast={(level, item, horizonDays) => {
          setPrediction({
            ...emptySelection,
            route: item.corridor,
            intersection: level === "intersection" ? item.key : "",
            horizon_days: horizonDays,
          });
          predictRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }}
        onOpenIntersection={focus}
        onStudy={onStudy}
      />

      <div ref={predictRef}>
        <PredictionPanel
          selection={prediction}
          onSelect={setPrediction}
          onOpenIntersection={focus}
        />
      </div>

      {summary && (
        <section className="ix-headline">
          {[
            [number(summary.headline.incidents), `incidents · ${summary.headline.window_days} days`],
            [number(summary.headline.incidents_per_day), "incidents per day"],
            [`${summary.headline.lane_blocking_pct}%`, "blocked at least one lane"],
            [`${summary.headline.at_signalized_intersection_pct}%`, "within 75 m of a signal"],
            [number(summary.intersections_indexed), "intersections indexed"],
          ].map(([v, l]) => (
            <div className="panel" key={l}>
              <strong>{v}</strong>
              <span>{l}</span>
            </div>
          ))}
        </section>
      )}

      <div className="ix-main">
        <section className="panel ix-list">
          <div className="panel-heading">
            <h2>Intersections</h2>
            <span className="helper">{list ? `${number(list.total)} match` : ""}</span>
          </div>
          <div className="ix-filters">
            <label className="ix-search">
              <Search size={15} />
              <input
                placeholder="Search a road, e.g. Macleod"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search intersections"
              />
            </label>
            <select
              value={quadrant}
              onChange={(e) => setQuadrant(e.target.value)}
              aria-label="Quadrant"
            >
              <option value="">All quadrants</option>
              {["NE", "NW", "SE", "SW"].map((q) => (
                <option key={q}>{q}</option>
              ))}
            </select>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              aria-label="Sort by"
            >
              <option value="incidents">Most incidents</option>
              <option value="lane_blocking">Most lane-blocking</option>
              <option value="collisions">Most collisions</option>
              <option value="recent">Most recent</option>
            </select>
          </div>
          <ol>
            {list?.items.map((i) => (
              <li key={i.key}>
                <button
                  className={i.key === selected ? "selected" : ""}
                  onClick={() => setSelected(i.key)}
                >
                  <span className="ix-name">
                    {i.key}
                    {liveNear.has(i.key) && (
                      <em className="ix-status critical">
                        <AlertTriangle size={11} /> live
                      </em>
                    )}
                  </span>
                  <span className="ix-meter">
                    <i
                      style={{
                        width: `${(100 * i.incidents) / (list.items[0]?.incidents || 1)}%`,
                      }}
                    />
                  </span>
                  <small>
                    {i.incidents} incidents · {i.lane_blocking} lane-blocking ·{" "}
                    {i.collisions} collisions · {number(i.unspecified_pct ?? 0)}% unspecified
                    {i.incident_delay_s != null &&
                      ` · +${number(i.incident_delay_s)} s/veh per incident`}
                  </small>
                </button>
              </li>
            ))}
          </ol>
        </section>

        <section className="panel ix-map">
          <div className="panel-heading">
            <h2>Where disruptions recur</h2>
            <span className="helper">Top 200 · dot area = incidents</span>
          </div>
          <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} role="img" aria-label="Calgary incident hotspot map">
            <rect width={MAP_W} height={MAP_H} rx={8} className="ix-map-bg" />
            {(() => {
              const c = project(51.0447, -114.0719);
              return (
                <g className="ix-map-axes">
                  <line x1={c.x} x2={c.x} y1={0} y2={MAP_H} />
                  <line x1={0} x2={MAP_W} y1={c.y} y2={c.y} />
                  <text x={8} y={16}>NW</text>
                  <text x={MAP_W - 24} y={16}>NE</text>
                  <text x={8} y={MAP_H - 8}>SW</text>
                  <text x={MAP_W - 24} y={MAP_H - 8}>SE</text>
                </g>
              );
            })()}
            {mapPoints.map((p) => {
              const { x, y } = project(p.latitude, p.longitude);
              return (
                <circle
                  key={p.key}
                  cx={x}
                  cy={y}
                  r={2 + 9 * Math.sqrt(p.incidents / mapMax)}
                  className={`ix-dot ${p.key === selected ? "selected" : ""}`}
                  onClick={() => focus(p.key)}
                >
                  <title>{`${p.key}: ${p.incidents} incidents`}</title>
                </circle>
              );
            })}
            {live?.incidents.map((i, n) => {
              if (i.latitude == null || i.longitude == null) return null;
              const { x, y } = project(i.latitude, i.longitude);
              return (
                <g key={`live-${n}`} className="ix-live-dot">
                  <circle cx={x} cy={y} r={9} className="pulse" />
                  <circle cx={x} cy={y} r={4.5} />
                  <title>{`LIVE: ${i.location_text} — ${i.description}`}</title>
                </g>
              );
            })}
          </svg>
          <div className="ix-legend">
            <span>
              <i className="hist" /> Six-month incident history
            </span>
            <span>
              <i className="live" /> Live incident now
            </span>
          </div>
        </section>
      </div>

      {detail && (
        <section className="panel ix-detail" ref={detailRef}>
          <div className="ix-detail-head">
            <div>
              <div className="eyebrow">INTERSECTION DETAIL</div>
              <h2>{detail.key}</h2>
              <div className="ix-badges">
                <span className={`badge ${detail.signalized ? "green" : "neutral"}`}>
                  <TrafficCone size={12} />{" "}
                  {detail.signalized ? `Signal: ${detail.signal}` : "No City signal within 75 m"}
                </span>
                {detail.quadrant && <span className="badge neutral">{detail.quadrant}</span>}
                <span className="badge blue">
                  {detail.volume_2024
                    ? `2024 volume ≈ ${number(detail.volume_2024)} veh/day`
                    : "No matched 2024 volume"}
                </span>
                <span className="badge neutral">Last incident {detail.last_seen_local}</span>
                {liveNear.has(detail.key) && (
                  <span className="ix-status critical">
                    <AlertTriangle size={12} /> Live incident nearby
                  </span>
                )}
              </div>
              <button
                className="button secondary ix-predict"
                onClick={() => predictIntersection(detail)}
              >
                <LineChart size={15} /> Predict this intersection
              </button>
            </div>
            <div className="ix-kpis">
              {[
                [detail.incidents, "incidents"],
                [detail.lane_blocking, "lane-blocking"],
                [detail.collisions, "collisions"],
                [detail.vulnerable_road_user, "pedestrian/cyclist"],
                [detail.signal_faults, "signal faults"],
                [detail.peak_period, "in peak periods"],
              ].map(([v, l]) => (
                <div key={l as string}>
                  <strong>{v}</strong>
                  <span>{l}</span>
                </div>
              ))}
            </div>
          </div>
          <IncidentDelayCard
            key={detail.key}
            detail={detail}
            onStudy={onStudy}
            onEstimated={(est: IncidentEstimate) =>
              setList((l) =>
                l && {
                  ...l,
                  items: l.items.map((i) =>
                    i.key === est.intersection_key
                      ? { ...i, incident_delay_s: est.extra_delay_s_per_vehicle ?? null }
                      : i,
                  ),
                },
              )
            }
          />
          <div className="ix-detail-grid">
            <div className="ix-camera">
              <h3>
                <Camera size={15} /> Live camera
              </h3>
              {detail.camera ? (
                <>
                  <img
                    src={`${detail.camera.image_url}?t=${camTick}`}
                    alt={`City traffic camera: ${detail.camera.location}`}
                  />
                  <p className="helper">
                    {detail.camera.id} · {detail.camera.location} ·{" "}
                    {detail.camera.distance_m} m away · refreshes every 60 s
                  </p>
                </>
              ) : (
                <p className="empty-inline">No City camera nearby.</p>
              )}
            </div>
            <div>
              <h3>Incident types</h3>
              <Bars
                rows={detail.by_category.map((c) => ({
                  label: c.category,
                  value: c.incidents,
                }))}
              />
              <h3>Lane impact</h3>
              <Bars
                rows={detail.by_lane_impact.map((c) => ({
                  label: c.lane_impact,
                  value: c.incidents,
                }))}
              />
            </div>
            <div>
              <h3>Time of day (local)</h3>
              <Columns
                values={detail.by_hour}
                labels={Array.from({ length: 24 }, (_, h) => `${h}:00`)}
                caption="Hover a bar for the hourly count"
                every={6}
              />
              <h3>Day of week</h3>
              <Columns
                values={WEEKDAYS.map((d) => detail.by_weekday[d] ?? 0)}
                labels={WEEKDAYS}
                caption="Hover a bar for the daily count"
              />
              <h3>By month</h3>
              <Columns
                values={detail.by_month.map((m) => m.incidents)}
                labels={detail.by_month.map((m) => m.month.slice(2))}
                caption="Hover a bar for the monthly count"
              />
              <h3>Direction of travel</h3>
              <Bars
                rows={detail.by_direction.map((c) => ({
                  label: c.direction,
                  value: c.incidents,
                }))}
              />
            </div>
          </div>
          <div className="ix-detail-grid two">
            <div>
              <h3>
                <Construction size={15} /> Closures within 400 m
              </h3>
              {detail.closures_nearby.length ? (
                <ul className="ix-closures">
                  {detail.closures_nearby.map((c, n) => (
                    <li key={n}>
                      <strong>
                        {c.closure_type} · {c.status_at_retrieval}
                      </strong>
                      <span>
                        {c.location_text} ({c.distance_m} m) · {c.start_local} →{" "}
                        {c.end_local}
                      </span>
                      <p>{c.description}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="empty-inline">
                  No current or scheduled closure in the City detour feed.
                </p>
              )}
            </div>
            <div>
              <h3>
                <MapPin size={15} /> Most recent incidents
              </h3>
              <div className="ix-table">
                <table>
                  <thead>
                    <tr>
                      <th>When (MDT)</th>
                      <th>Type</th>
                      <th>Lane impact</th>
                      <th>Dir.</th>
                      <th>Reported location</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.recent.map((r, n) => (
                      <tr key={n} title={r.description}>
                        <td>{r.start_local}</td>
                        <td>{r.category}</td>
                        <td>{r.lane_impact}</td>
                        <td>{r.travel_direction ?? "–"}</td>
                        <td>{r.location_text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <p className="incident-caution">{detail.caveat}</p>
        </section>
      )}
    </div>
  );
}
