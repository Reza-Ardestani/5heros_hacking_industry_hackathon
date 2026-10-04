import type { ChatAction } from "../../shared/navigation";
export type ChatReply = {
  reply: string;
  actions: ChatAction[];
  tools_used: string[];
  mode: "builtin" | "claude";
  suggestions: string[];
  notice?: string;
};
