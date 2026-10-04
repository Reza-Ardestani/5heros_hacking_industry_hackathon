import React from "react";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import { request } from "../src/lib/api";
import { defaultStudyFields } from "../src/components/StudyDesign";

vi.mock("../src/lib/api", () => ({ request: vi.fn() }));
vi.mock("../src/components/ChatDock", () => ({ ChatDock: () => null }));

const scenario = {
  main_vph: 1050,
  cross_vph: 160,
  duration_s: 900,
  seed: 42,
  budget_cad: 100000,
  cross_guardrail_pct: 30,
  retiming_cost_cad: 15000,
  widening_cost_cad: 1200000,
  annual_operating_cost_cad: 2000,
  occupancy: 1.2,
  value_of_time_cad: 20,
  operating_days: 250,
  asset_life_years: 10,
  demand_kind: "synthetic",
  demand_source: "Synthetic directional arrivals; not CalTRACS",
  flow_profile: null,
  ...defaultStudyFields,
};
const metrics = {
  mean_delay_s: 100,
  total_delay_s: 10000,
  main_mean_delay_s: 100,
  cross_mean_delay_s: 80,
  max_queue: 100,
  completed: 100,
  unserved: 0,
  planned: 100,
};
const result = {
  scenario,
  recommended_id: "reference",
  pareto_ids: ["reference"],
  stress_passed: true,
  simulator_version: "test",
  limitations: [],
  evaluation: { holdout_seeds: [43, 44, 45], optimization_seed: 42 },
  stress_tests: [],
  alternatives: [
    {
      id: "reference",
      label: "Reference plan",
      main_green_share: 0.5,
      main_lanes: 1,
      capital_cost_cad: 0,
      metrics,
      comparison: {
        feasible: true,
        rejection_reasons: [],
        delay_reduction_pct: 0,
        cross_delay_change_pct: 0,
        vehicle_hours_saved: 0,
      },
      economics: { estimated_net_annual_value_cad: 0, label: "Illustrative" },
      tuning_trial: { metrics, playback: [], queues: [] },
    },
  ],
};
let next: unknown;
let accept: (value: unknown) => void;

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal("scrollTo", vi.fn());
  next = {
    id: "study-1",
    status: "running",
    trace: [
      {
        agent: "SUMO",
        action: "evaluate",
        detail: "Evaluating paired seeds",
        at_utc: "2026-10-03T20:00:00Z",
      },
    ],
    result: null,
    error: null,
  };
  vi.mocked(request).mockImplementation(async (url, options) => {
    if (url === "/api/scenario") return { defaults: scenario };
    if (url === "/api/incidents") return null;
    if (url === "/api/jobs" && options?.method === "POST") {
      return new Promise((resolve) => {
        accept = resolve;
      });
    }
    if (url === "/api/jobs/study-1") {
      if (next instanceof Error) throw next;
      return next;
    }
    throw new Error(`Unexpected request: ${url}`);
  });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});
async function mount() {
  await act(async () => {
    render(<App />);
  });
}
async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}
async function submit() {
  fireEvent.click(
    screen.getAllByRole("button", { name: /Choose interventions/ })[0],
  );
  fireEvent.click(screen.getAllByRole("button", { name: "Run simulation" })[0]);
  await act(async () => {
    accept({ id: "study-1" });
  });
}
function compare() {
  fireEvent.click(screen.getByRole("button", { name: "Compare options" }));
}

describe("Compare job lifecycle in the actual application", () => {
  it("shows setup only when idle; submission status survives navigation", async () => {
    await mount();
    compare();
    expect(screen.getByText("No results yet.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Set up experiment/ }));
    fireEvent.click(
      screen.getAllByRole("button", { name: "Run simulation" })[0],
    );
    compare();
    expect(
      screen.getByRole("heading", { name: "Submitting experiment" }),
    ).toBeTruthy();
    expect(screen.queryByText("No results yet.")).toBeNull();
    expect(
      screen
        .getByRole("link", { name: "Export report" })
        .getAttribute("aria-disabled"),
    ).toBe("true");
    await act(async () => {
      accept({ id: "study-1" });
    });
    expect(screen.getByRole("heading", { name: "A recommendation you can inspect." })).toBeTruthy();
    await advance(500);
    expect(screen.getByText("SUMO: Evaluating paired seeds")).toBeTruthy();
  });

  it("retains progress during polling failure and clears it on recovery", async () => {
    await mount();
    await submit();
    compare();
    next = new Error("Temporary disconnect");
    await advance(500);
    expect(
      screen.getByRole("heading", { name: "Simulation running" }),
    ).toBeTruthy();
    expect(screen.getByText(/Retrying automatically/)).toBeTruthy();
    expect(screen.queryByText("No results yet.")).toBeNull();
    next = {
      id: "study-1",
      status: "running",
      trace: [],
      result: null,
      error: null,
    };
    await advance(2000);
    expect(screen.queryByText(/Retrying automatically/)).toBeNull();
    expect(
      screen.getByRole("heading", { name: "Simulation running" }),
    ).toBeTruthy();
  });

  it("shows terminal failure with recovery action in Compare and study", async () => {
    await mount();
    await submit();
    compare();
    next = {
      id: "study-1",
      status: "failed",
      trace: [],
      result: null,
      error: "Simulator unavailable",
    };
    await advance(500);
    expect(screen.getByText("Simulator unavailable")).toBeTruthy();
    expect(screen.queryByText("No results yet.")).toBeNull();
    fireEvent.click(
      screen.getByRole("button", { name: "Review inputs and retry" }),
    );
    expect(
      screen.getByRole("heading", { name: "Simulation failed" }),
    ).toBeTruthy();
    expect(
      screen
        .getAllByRole("button", { name: "Run simulation" })[0]
        .hasAttribute("disabled"),
    ).toBe(false);
  });

  it("replaces progress with completed results and preserves stale-input warning", async () => {
    await mount();
    await submit();
    compare();
    next = {
      id: "study-1",
      status: "completed",
      trace: [],
      result,
      error: null,
    };
    await advance(500);
    expect(screen.getByText("REFERENCE RETAINED")).toBeTruthy();
    expect(
      screen.queryByRole("heading", { name: "Simulation running" }),
    ).toBeNull();
    expect(screen.queryByText("No results yet.")).toBeNull();
    expect(
      screen
        .getAllByRole("link", { name: "Export report" })[0]
        .getAttribute("href"),
    ).toBe("/api/jobs/study-1/report");
    fireEvent.click(screen.getByRole("button", { name: "Guided study" }));
    fireEvent.click(
      screen.getAllByRole("button", { name: /Choose interventions/ })[0],
    );
    fireEvent.change(
      screen.getByRole("spinbutton", { name: "Cross-street delay guardrail" }),
      { target: { value: "40" } },
    );
    compare();
    expect(
      screen.getByText(
        /Inputs changed. Results still describe the previous run/,
      ),
    ).toBeTruthy();
  });
});
