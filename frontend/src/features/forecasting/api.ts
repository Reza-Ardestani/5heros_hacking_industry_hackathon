import { request } from "../../shared/http";
import type { McpInfo, MlBenchmark, MlInfo, PredictOptions, Prediction } from "./types";
export const options = (params: URLSearchParams | string) => request<PredictOptions>(`/api/disruptions/options?${params}`);
export const predict = (params: URLSearchParams | string) => request<Prediction>(`/api/disruptions/predict?${params}`);
export const mlInfo = () => request<MlInfo>("/api/ml-info");
export const benchmark = () => request<MlBenchmark>("/api/ml/benchmark");
export const mcpInfo = (check = false) => request<McpInfo>(`/api/mcp-info${check ? "?check=true" : ""}`);
