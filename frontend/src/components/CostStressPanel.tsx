import React from "react";
import { CheckCircle2, Info, Scale } from "lucide-react";

import type { Result } from "../types";
import { money, number, optionName } from "../lib/format";

const pct = (f: number) =>
  f === 1
    ? "as set"
    : `${f > 1 ? "+" : "−"}${Math.round(Math.abs(f - 1) * 100)}%`;

export function CostStressPanel({ result }: { result: Result }) {
  const s = result.cost_stress;
  if (!s) return null; // results saved before the stress test existed
  const label = (id: string) =>
    optionName(id, result.alternatives.find((a) => a.id === id)?.label);
  const robust = s.robust_share_pct === 100;
  const cells = s.grid.length * s.cost_factors.length;
  const wins = Math.round((s.robust_share_pct / 100) * cells);
  // Same facts as s.verdict (kept for the exported report), in the UI's option names.
  const rec = label(s.recommended_id);
  const changes = [
    s.headroom &&
      `its cost rises more than ${number(s.headroom.cost_increase_pct)}% (above ${money(result.scenario.budget_cad)}), when ${label(s.headroom.fallback_id)} takes over`,
    s.switch_points[0] &&
      `the budget reaches ${money(s.switch_points[0].needed_budget_cad)} (+${number(s.switch_points[0].budget_increase_pct)}%), when ${label(s.switch_points[0].id)} becomes affordable`,
  ].filter(Boolean);
  const verdict = robust
    ? `Robust: ${rec} stays the recommendation for every tested combination of costs and budget (each −50% to +50%).`
    : `${rec} wins in ${wins} of ${cells} cost/budget combinations.${changes.length ? ` It changes if ${changes.join(" or if ")}.` : ""}`;
  return (
    <section className="panel cs">
      <div className="panel-heading">
        <div>
          <h2>
            <Scale size={17} /> Cost &amp; budget stress test
          </h2>
          <p className="helper">
            Does the recommendation hold if every capital cost and the budget
            are each 50% lower or higher? No re-simulation: costs do not change
            traffic.
          </p>
        </div>
        <span className={`badge ${robust ? "green" : "amber"}`}>
          {robust ? "ROBUST" : `HOLDS IN ${wins} OF ${cells}`}
        </span>
      </div>

      <p className={`cs-verdict ${robust ? "ok" : "warn"}`}>
        {robust ? <CheckCircle2 size={16} /> : <Info size={16} />}
        <span>{verdict}</span>
      </p>
      {s.economics && s.economics.net_annual_value_cad < 0 && (
        // The study rule picks the lowest delay within budget; it does not test payback.
        <p className="cs-verdict warn">
          <Info size={16} />
          <span>
            Does not pay for itself at the assumed costs: net{" "}
            {money(s.economics.net_annual_value_cad)} a year. It needs drivers'
            time to be worth {money(s.economics.break_even_value_of_time_cad)}/h
            (assumed {money(s.economics.value_of_time_cad)}/h). Treat it as a
            delay fix to verify, not a proven investment.
          </span>
        </p>
      )}

      <div className="cs-body">
        <figure
          className="cs-grid"
          aria-label="Recommended option by cost and budget change"
        >
          <div className="cs-corner">Budget ↓ · Costs →</div>
          {s.cost_factors.map((f) => (
            <div key={`c${f}`} className="cs-axis">
              {pct(f)}
            </div>
          ))}
          {s.grid.map((row, i) => (
            <React.Fragment key={s.budget_factors[i]}>
              <div className="cs-axis">{pct(s.budget_factors[i])}</div>
              {row.map((winner, j) => (
                <div
                  key={j}
                  className={`cs-cell ${winner === s.recommended_id ? "same" : "changed"} ${
                    s.budget_factors[i] === 1 && s.cost_factors[j] === 1
                      ? "base"
                      : ""
                  }`}
                  title={`Budget ${pct(s.budget_factors[i])}, costs ${pct(s.cost_factors[j])}: ${label(winner)}`}
                >
                  {winner === s.recommended_id ? "✓" : label(winner)}
                </div>
              ))}
            </React.Fragment>
          ))}
          <figcaption>
            ✓ = {label(s.recommended_id)} still recommended · outlined cell =
            current settings
          </figcaption>
        </figure>

        <div className="cs-facts">
          {s.headroom && (
            <div>
              <strong>+{number(s.headroom.cost_increase_pct)}%</strong>
              <span>
                cost headroom: {label(s.recommended_id)} stays within budget
                until its cost passes {money(result.scenario.budget_cad)}; then{" "}
                {label(s.headroom.fallback_id)} is chosen
              </span>
            </div>
          )}
          {s.switch_points[0] && (
            <div>
              <strong>{money(s.switch_points[0].needed_budget_cad)}</strong>
              <span>
                budget at which {label(s.switch_points[0].id)} (lower delay, now
                over budget) would win: +
                {number(s.switch_points[0].budget_increase_pct)}%, or its cost
                falling {number(s.switch_points[0].cost_cut_pct)}%
              </span>
            </div>
          )}
          {s.economics && (
            <div>
              <strong>{money(s.economics.worst_case_net_cad)}</strong>
              <span>
                net annual value in the worst case ({s.economics.worst_case});
                breaks even at a value of time of{" "}
                {money(s.economics.break_even_value_of_time_cad)}/h vs{" "}
                {money(s.economics.value_of_time_cad)}/h assumed
              </span>
            </div>
          )}
        </div>
      </div>

      {(s.blocked.length > 0 || s.one_at_a_time.length > 0) && (
        <ul className="cs-notes">
          {s.blocked.map((b) => (
            <li key={b.id}>
              <strong>{label(b.id)}</strong> has lower delay but no cost change
              can make it win: {b.reason}.
            </li>
          ))}
          {s.one_at_a_time.map((c) => (
            <li key={`${c.id}${c.factor}`}>
              If only <strong>{label(c.id)}</strong> costs {pct(c.factor)}, the
              recommendation becomes <strong>{label(c.winner_id)}</strong>.
            </li>
          ))}
        </ul>
      )}
      <p className="incident-caution">{s.method}</p>
    </section>
  );
}
