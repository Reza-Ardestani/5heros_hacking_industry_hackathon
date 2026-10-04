import React from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { StorageIndicator, StorageStatus, type StorageState } from "../src/components/StorageStatus";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

const healthy: StorageState = {
  configured_backend: "timescale", active_backend: "timescale", primary_healthy: true,
  pending_events: 0, last_sync_utc: "2026-10-04T08:00:00", last_error: null,
  retry_in_s: 0, local_writes_durable: true,
};

it("replaces healthy label with recovery and backlog, then recovers", () => {
  const { rerender } = render(<StorageIndicator state={healthy} />);
  expect(screen.getByRole("status").textContent).toContain("TimescaleDB synchronized");
  rerender(<StorageIndicator state={{ ...healthy, active_backend: "sqlite", primary_healthy: false,
    pending_events: 17, last_error: "connection_unavailable" }} />);
  expect(screen.getByRole("status").textContent).toContain("SQLite recovery active");
  expect(screen.getByRole("status").textContent).toContain("17 changes awaiting sync");
  expect(screen.queryByText("TimescaleDB synchronized")).toBeNull();
  rerender(<StorageIndicator state={healthy} />);
  expect(screen.getByRole("status").textContent).toContain("TimescaleDB synchronized");
});

it("does not claim healthy storage when status endpoint fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  render(<StorageStatus />);
  await waitFor(() => expect(screen.getByRole("status").textContent).toContain("freshness not verified"));
  expect(screen.queryByText("TimescaleDB synchronized")).toBeNull();
});
