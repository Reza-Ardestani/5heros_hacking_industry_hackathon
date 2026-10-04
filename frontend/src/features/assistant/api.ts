import { request, requestBlob } from "../../shared/http";
import type { ChatReply } from "./types";
export const info = () => request<{
  mode: "builtin" | "claude";
  suggestions: string[];
}>("/api/chat/info");
export const chat = (message: string, history: {
  role: string;
  content: string;
}[]) => request<ChatReply>("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, history }) });

// Optional ElevenLabs voice (server holds the key): availability, read-aloud, transcription.
export const speechInfo = () => request<{ available: boolean }>("/api/speech/info");
export const speak = (text: string) => requestBlob("/api/speech", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
export const transcribe = async (audio: Blob) => (await request<{ text: string }>("/api/speech/transcribe", { method: "POST", headers: { "Content-Type": audio.type || "audio/webm" }, body: audio })).text;
