import { request } from "../../shared/http";
import type { ChatReply } from "./types";
export const info = () => request<{
  mode: "builtin" | "claude";
  suggestions: string[];
}>("/api/chat/info");
export const chat = (message: string, history: {
  role: string;
  content: string;
}[]) => request<ChatReply>("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, history }) });
