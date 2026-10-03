import React from "react";
import { ArrowUpRight, Database, Lightbulb, ListChecks, SlidersHorizontal } from "lucide-react";

import type { Job, Result, Scenario } from "../types";
import { money, number, optionName, settingName, settingValue } from "../lib/format";

/** One line answering "why not the lowest-delay option?" for the decision banner. */
export function WhyNotLowest({ result }: { result: Result }) {
  const d = result.decision;
  if (!d || d.lowest_delay_is_recommended) return null;
  const lowest = result.alternatives.find((a) => a.id === d.lowest_delay_id);
  const fix = d.what_would_change.find((c) => c.id === d.lowest_delay_id);
  if (!lowest) return null;
  return (
    <p className="why-not">
      <strong>
        Lowest delay overall: {optionName(lowest.id, lowest.label)} (
        {number(lowest.metrics.mean_delay_s)}s/vehicle)
      </strong>{" "}
      is not recommended because {d.lowest_delay_rejected_because.join("; ").toLowerCase()}.
      {fix?.possible && fix.settings.length > 0 && (
        <>
          {" "}
          It would qualify with{" "}
          {fix.settings
            .map((s) => `${settingName[s.setting] ?? s.setting} ≥ ${settingValue(s.setting, s.needed)}`)
            .join(" and ")}{" "}
          (step 2).
        </>
      )}
    </p>
  );
}

/** Step 2: what the current settings do, and which change would alter the outcome. */
export function SettingsAdvisor({
  scenario,
  result,
  onApply,
  disabled,
}: {
  scenario: Scenario;
  result: Result | null | undefined;
  onApply: (key: keyof Scenario, value: number) => void;
  disabled?: boolean;
}) {
  const d = result?.decision;
  return (
    <section className="panel advisor">
      <div className="panel-heading">
        <div>
          <h2>
            <SlidersHorizontal size={16} /> How your settings shape the result
          </h2>
          <p className="helper">
            The recommendation is the lowest-delay option that passes every rule below.
          </p>
        </div>
      </div>
      <ul className="advisor-rules">
        <li>
          <strong>Capital budget {money(scenario.budget_cad)}</strong>
          <span>Options costing more are excluded however much delay they save.</span>
        </li>
        <li>
          <strong>Cross-street limit {number(scenario.cross_guardrail_pct)}%</strong>
          <span>
            Options that raise average cross-street delay by more than this are excluded.
            Raising it favours the arterial; lowering it protects side streets.
          </span>
        </li>
        <li>
          <strong>
            Arrivals {number(scenario.main_vph)} arterial / {number(scenario.cross_vph)} cross
            veh/h
          </strong>
          <span>
            Heavier arterial demand makes retiming and capacity more valuable; heavier cross
            demand makes the cross-street limit bind sooner.
          </span>
        </li>
      </ul>
      {d ? (
        <div className="advisor-changes">
          <h3>
            <Lightbulb size={15} /> From your last run
          </h3>
          {d.what_would_change.length === 0 ? (
            <p className="helper">
              {optionName(d.recommended_id)} already has the lowest delay among all options;
              no setting change would pick a faster one.
            </p>
          ) : (
            d.what_would_change.map((c) => (
              <div className="advisor-change" key={c.id}>
                <div>
                  <strong>
                    {optionName(c.id, c.label)}
                    {c.delay_s_per_vehicle != null &&
                      ` · ${number(c.delay_s_per_vehicle)}s/vehicle`}
                  </strong>
                  <span>
                    {c.possible
                      ? c.settings.map((s) => s.message).join("; ")
                      : `Cannot qualify by changing a setting: ${c.reason}`}
                  </span>
                </div>
                {c.possible &&
                  c.settings.map((s) => (
                    <button
                      key={s.setting}
                      className="button secondary"
                      disabled={disabled}
                      onClick={() => onApply(s.setting, s.needed)}
                      title="Changes the setting; run the study again to see the effect"
                    >
                      Set {settingName[s.setting] ?? s.setting} to{" "}
                      {settingValue(s.setting, s.needed)}
                    </button>
                  ))}
              </div>
            ))
          )}
          <p className="helper">
            Applying a change only edits the inputs. Run the study again: the simulator, not
            this hint, decides the outcome.
          </p>
        </div>
      ) : (
        <p className="helper advisor-empty">
          Run the study once to see which setting would change the recommendation.
        </p>
      )}
    </section>
  );
}

/** Step 3: every action and simulator trial, and where they are stored. */
export function SimulationLog({ job }: { job: Job }) {
  const result = job.result;
  if (!result) return null;
  const rows = result.alternatives.flatMap((a) => [
    { alt: a, purpose: "tuning", seed: a.tuning_trial ? result.evaluation.optimization_seed : null,
      metrics: a.tuning_trial?.metrics },
    ...((a as unknown as { holdout_trials?: { seed: number; metrics: typeof a.metrics }[] })
      .holdout_trials ?? []
    ).map((t) => ({ alt: a, purpose: "hold-out", seed: t.seed, metrics: t.metrics })),
  ]); // fmt: skip
  return (
    <section className="panel sim-log">
      <div className="panel-heading">
        <div>
          <h2>
            <ListChecks size={16} /> Simulation log
          </h2>
          <p className="helper">
            {job.trace.length} agent actions · {rows.length} option trials ·{" "}
            {result.stress_tests.length * 2} stress trials
          </p>
        </div>
        <a
          className="text-link"
          href={`/api/simulations/${job.id}`}
          target="_blank"
          rel="noreferrer"
        >
          <Database size={13} /> Stored as run {job.id.slice(0, 8)} <ArrowUpRight size={13} />
        </a>
      </div>
      <div className="sim-log-grid">
        <ol className="sim-actions">
          {job.trace.map((t, i) => (
            <li key={i}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              <div>
                <strong>
                  {t.agent} · {t.action}
                </strong>
                <p>{t.detail}</p>
              </div>
            </li>
          ))}
        </ol>
        <div className="ix-table">
          <table>
            <thead>
              <tr>
                <th>Option</th>
                <th>Trial</th>
                <th>Seed</th>
                <th>Delay/veh</th>
                <th>Cross delay</th>
                <th>Trips done</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) =>
                r.metrics ? (
                  <tr key={i}>
                    <td>{optionName(r.alt.id, r.alt.label)}</td>
                    <td>{r.purpose}</td>
                    <td>{r.seed ?? "–"}</td>
                    <td>{number(r.metrics.mean_delay_s)}s</td>
                    <td>{number(r.metrics.cross_mean_delay_s)}s</td>
                    <td>
                      {r.metrics.completed}/{r.metrics.planned}
                    </td>
                  </tr>
                ) : null,
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
