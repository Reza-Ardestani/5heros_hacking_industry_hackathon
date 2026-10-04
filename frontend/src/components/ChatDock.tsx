import React, { useEffect, useRef, useState } from "react";
import { ChevronDown, Loader2, MessageSquare, Send, Square, Volume2, X } from "lucide-react";
import { request } from "../lib/api";
import type { ChatAction, ChatReply } from "../types";

type Message = {
  role: "user" | "assistant";
  content: string;
  tools?: string[];
  opened?: string;
  notice?: string;
  error?: boolean;
};

const PAGES: Record<string, string> = {
  problem: "Guided study",
  study: "Guided study",
  compare: "Compare options",
  intersections: "Intersections",
  evidence: "Evidence & sources",
};

function describe(actions: ChatAction[]) {
  const a = actions[0];
  if (!a) return undefined;
  if (a.type === "study") return `Guided study · ${a.intersection}`;
  if (a.tab === "mcp-info-ml") return "Intersections · mcp-info-ml";
  if (a.prediction) return "Intersections · prediction panel";
  if (a.intersection) return `Intersections · ${a.intersection}`;
  return PAGES[a.view] + (a.step ? ` · step ${a.step}` : "");
}

// Bottom-docked assistant. Answers come from the MCP tools via POST /api/chat; any
// actions in the reply are handed to the app to navigate.
export function ChatDock({ onAction }: { onAction: (a: ChatAction) => Promise<void> }) {
  const [open, setOpen] = useState(false),
    [messages, setMessages] = useState<Message[]>([]),
    [input, setInput] = useState(""),
    [busy, setBusy] = useState(false),
    [mode, setMode] = useState<"builtin" | "claude">("builtin"),
    [suggestions, setSuggestions] = useState<string[]>([]),
    [canSpeak, setCanSpeak] = useState(false),
    [speaking, setSpeaking] = useState<{
      index: number;
      loading: boolean;
    } | null>(null);
  const listRef = useRef<HTMLDivElement>(null),
    inputRef = useRef<HTMLInputElement>(null),
    audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    request<{ mode: "builtin" | "claude"; suggestions: string[] }>("/api/chat/info")
      .then((i) => {
        setMode(i.mode);
        setSuggestions(i.suggestions);
      })
      .catch(() => undefined); // the dock still works; errors show on send
    // ElevenLabs voice is optional: the speaker button only appears when the server has a key.
    request<{ available: boolean }>("/api/speech/info")
      .then((i) => setCanSpeak(i.available))
      .catch(() => setCanSpeak(false));
  }, []);

  const stopSpeaking = () => {
    audioRef.current?.pause();
    audioRef.current = null;
    setSpeaking(null);
  };
  const speak = async (index: number, text: string) => {
    if (speaking?.index === index) return stopSpeaking();
    stopSpeaking();
    setSpeaking({ index, loading: true });
    try {
      const r = await fetch("/api/speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!r.ok)
        throw new Error(
          (await r.json().catch(() => null))?.detail ?? `Speech failed (${r.status})`,
        );
      const url = URL.createObjectURL(await r.blob());
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setSpeaking((s) => (s?.index === index ? null : s));
      };
      setSpeaking({ index, loading: false });
      await audio.play();
    } catch (e) {
      setSpeaking(null);
      setMessages((m) => [...m, { role: "assistant", content: (e as Error).message, error: true }]);
    }
  };
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, busy, open]);
  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    const history = messages
      .filter((m) => !m.error)
      .slice(-10)
      .map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: message }]);
    setInput("");
    setBusy(true);
    try {
      const r = await request<ChatReply>("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });
      setMode(r.mode);
      if (r.suggestions.length) setSuggestions(r.suggestions);
      let opened = describe(r.actions);
      for (const a of r.actions) {
        try {
          await onAction(a);
        } catch (e) {
          opened = `Could not open: ${(e as Error).message}`;
        }
      }
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: r.reply,
          tools: r.tools_used,
          opened,
          notice: r.notice,
        },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", content: (e as Error).message, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  if (!open)
    return (
      <button className="chat-launcher" onClick={() => setOpen(true)} aria-label="Open assistant">
        <MessageSquare size={17} />
        Ask about traffic or go to a page
      </button>
    );

  return (
    <section
      className="chat-dock"
      aria-label="Assistant"
      onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
    >
      <header>
        <MessageSquare size={16} />
        <strong>Assistant</strong>
        <span className={`chat-mode ${mode}`}>
          {mode === "claude" ? "Claude + MCP tools" : "Built-in · MCP tools"}
        </span>
        <button className="chat-icon" onClick={() => setOpen(false)} aria-label="Minimise">
          <ChevronDown size={17} />
        </button>
        {messages.length > 0 && (
          <button className="chat-icon" onClick={() => setMessages([])} aria-label="Clear chat">
            <X size={16} />
          </button>
        )}
      </header>
      <div className="chat-log" ref={listRef} aria-live="polite">
        {messages.length === 0 && (
          <p className="chat-empty">
            Ask about hotspots, forecasts, live incidents or data status, or say where to go.
            Answers use the same tools as the MCP server.
          </p>
        )}
        {messages.map((m, i) => (
          <div className={`chat-msg ${m.role}${m.error ? " error" : ""}`} key={i}>
            <p>{m.content}</p>
            {canSpeak && m.role === "assistant" && !m.error && (
              <button
                className="chat-speak"
                onClick={() => speak(i, m.content)}
                aria-label={
                  speaking?.index === i ? "Stop reading aloud" : "Read aloud (ElevenLabs)"
                }
                title={speaking?.index === i ? "Stop" : "Read aloud (ElevenLabs)"}
              >
                {speaking?.index === i ? (
                  speaking.loading ? (
                    <Loader2 size={13} className="spin" />
                  ) : (
                    <Square size={12} />
                  )
                ) : (
                  <Volume2 size={13} />
                )}
              </button>
            )}
            {(m.tools?.length || m.opened || m.notice) && (
              <div className="chat-meta">
                {m.tools?.map((t, j) => (
                  <span className="chat-tool" key={j}>
                    MCP · {t}
                  </span>
                ))}
                {m.opened && <span className="chat-opened">Opened {m.opened}</span>}
                {m.notice && <span className="chat-notice">{m.notice}</span>}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="chat-msg assistant pending">Working…</div>}
      </div>
      {suggestions.length > 0 && (
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button key={s} disabled={busy} onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
      )}
      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          ref={inputRef}
          value={input}
          maxLength={2000}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. forecast Stoney Trail next 14 days"
          aria-label="Message"
        />
        <button className="button primary" disabled={busy || !input.trim()} aria-label="Send">
          <Send size={15} />
        </button>
      </form>
    </section>
  );
}
