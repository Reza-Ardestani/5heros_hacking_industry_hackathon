import { request } from "../../shared/http";
import type { StorageState } from "./types";
export const status = (signal: AbortSignal) => request<{
  storage: StorageState;
}>("/api/disruptions/status", { signal });
