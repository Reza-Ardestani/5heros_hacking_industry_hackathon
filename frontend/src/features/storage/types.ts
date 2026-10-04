export type StorageState = {
  configured_backend: "sqlite" | "timescale";
  active_backend: "sqlite" | "timescale";
  primary_healthy: boolean | null;
  pending_events: number;
  last_sync_utc: string | null;
  last_error: string | null;
  retry_in_s: number;
  local_writes_durable: boolean;
};
