import { useEffect, useState } from "react";
import * as api from "./api";
import type { StorageState } from "./types";
export function StorageIndicator({ state }: {
  state: StorageState;
}) {
  const fallback = state.configured_backend === "timescale" && state.active_backend === "sqlite";
  const title = fallback
    ? "SQLite recovery active"
    : state.active_backend === "timescale"
      ? "TimescaleDB synchronized"
      : "Local SQLite storage";
  return (<div className={fallback ? "notice caution" : "notice"} role="status">
    <span>
      <strong>{title}</strong>
      {fallback
        ? ` · Collected data remains available locally. ${state.pending_events} changes awaiting sync.`
        : " · Collected data available."}
      {state.last_sync_utc && ` Last sync: ${new Date(`${state.last_sync_utc}Z`).toLocaleString()}.`}
    </span>
  </div>);
}
export function StorageStatus() {
  const [state, setState] = useState<StorageState | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let current = true;
    let controller: AbortController | null = null;
    const refresh = async () => {
      controller?.abort();
      controller = new AbortController();
      const pending = controller;
      try {
        const result = await api.status(pending.signal);
        if (current && !pending.signal.aborted) {
          setState(result.storage);
          setUnavailable(false);
        }
      }
      catch {
        if (current && !pending.signal.aborted)
          setUnavailable(true);
      }
    };
    void refresh();
    const timer = setInterval(() => void refresh(), 15000);
    return () => {
      current = false;
      clearInterval(timer);
      controller?.abort();
    };
  }, []);
  if (unavailable)
    return <p className="notice caution" role="status">Storage status unavailable; freshness not verified.</p>;
  return state ? <StorageIndicator state={state} /> : null;
}
