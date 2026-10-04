"""Chat assistant for the UI: answers questions with the MCP tools and moves the UI.

Every data answer comes from a tool on the in-process MCP server (app.mcp_server), so
the chat, an external agent and the HTTP API all see the same numbers. Two modes:

  builtin (default, no key, no network): a small rule-based router that recognises
      pages, intersections, routes, quadrants, horizons and models in the question.
  claude (ANTHROPIC_API_KEY set, or BB_CHAT_MODE=claude): Claude picks tools from the
      MCP catalogue plus a local navigate_ui tool. Falls back to builtin on any error.

Replies carry UI actions the frontend executes:
  {"type": "navigate", "view", "step"?, "intersection"?, "quadrant"?, "area"?,
   "prediction"?, "tab"?}
  {"type": "study", "intersection"}   build the study and open guided step 2
Chat never writes: predictions are not saved and collect_latest_data is not offered.
"""

import json
import re

from app.application import disruptions
from app.application.ports import ChatModel, ToolGateway

MAX_TOOL_ROUNDS = 6
HISTORY_TURNS = 10
CHAT_EXCLUDED_TOOLS = {"collect_latest_data"}  # polls the City and writes
QUADRANTS = ("NE", "NW", "SE", "SW")
VIEWS = ("problem", "study", "compare", "intersections", "evidence")
PAGE_LABELS = {
    "problem": "Guided study, step 1",
    "study": "Guided study",
    "compare": "Compare options",
    "intersections": "Intersections",
    "evidence": "Evidence & sources",
}
SUGGESTIONS = [
    "Top 5 hotspots in SE",
    "Forecast Deerfoot Trail next 7 days",
    "Open Deerfoot Trail & Glenmore Trail",
    "What is happening live right now?",
    "Simulate Glenmore Trail & Macleod Trail",
    "Go to evidence",
]

# Road-type words reduced to one spelling so "16th Avenue" matches "16 Ave".
ROAD_TYPES = {
    "avenue": "ave",
    "av": "ave",
    "street": "st",
    "trail": "tr",
    "road": "rd",
    "boulevard": "blvd",
    "drive": "dr",
    "highway": "hwy",
    "crescent": "cr",
    "gate": "gate",
    "way": "way",
    "parkway": "pkwy",
    "freeway": "fwy",
}
TYPE_WORDS = set(ROAD_TYPES.values()) | {"tr", "ave", "st", "rd"}


def _norm(text):
    words = re.findall(r"[a-z0-9]+", text.lower().replace("&", " and "))
    out = []
    for w in words:
        w = re.sub(r"^(\d+)(st|nd|rd|th)$", r"\1", w)
        out.append(ROAD_TYPES.get(w, w))
    return " " + " ".join(out) + " "


def _road_core(road):
    """'Deerfoot Trail' -> 'deerfoot'; '16 Avenue' -> '16 ave' (a bare number is too
    ambiguous to match on); quadrant suffixes are dropped."""
    words = _norm(road).split()
    words = [w for w in words if w.upper() not in QUADRANTS]
    if not words:
        return ""
    if words[0].isdigit():
        return " ".join(words[:2])
    named = [w for w in words if w not in TYPE_WORDS]
    return " ".join(named or words)


def _has(text, phrase):
    return bool(phrase) and f" {phrase} " in text


class Assistant:
    def __init__(self, tools: ToolGateway, model_factory=None, mode_selector=lambda: "builtin"):
        self.tools = tools
        self.model_factory = model_factory
        self.mode_selector = mode_selector
        self._index = None

    async def call(self, name, args, trail):
        if name == "predict_disruptions":
            args = {**args, "save": False}
        result = await self.tools.call(name, args)
        trail.append({"tool": name, "args": args})
        return result

    async def tool_schemas(self):
        return [tool for tool in await self.tools.schemas() if tool["name"] not in CHAT_EXCLUDED_TOOLS]

    # Entity lookup (cached per database version) ---------------------------------------
    def index(self):
        version = disruptions.store().version()
        if self._index is None or self._index[0] != version:
            items = disruptions.list_intersections("", "", "", "incidents", 100000)["items"]
            routes = [r["value"] for r in disruptions.options("", "")["routes"]]
            self._index = (version, items, routes)
        return self._index[1], self._index[2]

    def find_intersection(self, text):
        """Best intersection whose two road names both appear in the text."""
        t = _norm(text)
        items, _ = self.index()
        best = None
        for item in items:
            cores = [_road_core(r) for r in item["roads"]]
            hits = sum(_has(t, c) for c in cores)
            if hits >= 2:
                q = item["quadrant"] or ""
                score = (hits, _has(t, q.lower()), item["incidents"])
                if best is None or score > best[0]:
                    best = (score, item)
        return best[1] if best else None

    def find_route(self, text):
        t = _norm(text)
        _, routes = self.index()
        hits = [r for r in routes if _has(t, _road_core(r))]
        if not hits:
            return ""
        # Prefer the route whose quadrant suffix is also named, then the longest name.
        return max(hits, key=lambda r: (_has(t, r.split()[-1].lower()), len(r)))

    # Entry point --------------------------------------------------------------------
    async def reply(self, message, history=None):
        message = (message or "").strip()[:2000]
        if not message:
            return self._answer("Ask about hotspots, forecasts, live incidents or a page.")
        if self.mode_selector() == "claude":
            try:
                return await self.claude(message, history or [])
            except Exception as error:  # noqa: BLE001 - degrade to builtin, say why
                out = await self.builtin(message)
                out["notice"] = f"Claude unavailable ({type(error).__name__}); built-in answer."
                return out
        return await self.builtin(message)

    @staticmethod
    def _answer(reply, actions=(), trail=(), mode="builtin", suggestions=None):
        return {
            "reply": reply,
            "actions": list(actions),
            "tools_used": [t["tool"] for t in trail],
            "tool_calls": list(trail),
            "mode": mode,
            "suggestions": suggestions if suggestions is not None else [],
        }

    # Built-in router ------------------------------------------------------------------
    async def builtin(self, message):
        t = _norm(message)
        trail = []
        quadrant = next((q for q in QUADRANTS if _has(t, q.lower())), "")

        def has(*words):
            return any(_has(t, w) for w in words)

        if has("help", "what can you do", "how do i use", "commands"):
            return self._help()

        # Tools catalogue / data status
        if has("mcp", "tools") and not has("forecast", "predict"):
            tools = await self.tool_schemas()
            names = ", ".join(x["name"] for x in tools)
            return self._answer(
                f"The MCP server exposes {len(tools) + len(CHAT_EXCLUDED_TOOLS)} tools; this "
                f"chat uses {len(tools)} of them (not collect_latest_data, which writes): {names}. Full catalogue with live "
                "self-check is on the mcp-info-ml tab.",
                [{"type": "navigate", "view": "intersections", "tab": "mcp-info-ml"}],
                trail,
            )
        if has("status", "database", "how much data", "last update", "data status"):
            s = await self.call("get_data_status", {}, trail)
            lo, hi = s.get("incident_start_range_local") or ["?", "?"]
            return self._answer(
                f"The database holds {s['incidents']:,} incidents ({lo} to {hi}), "
                f"{s['closures']:,} closures, {s['travel_time_observations']:,} travel-time "
                f"observations and {s['simulation_runs']} simulation runs. Last collection: "
                f"{s.get('last_collect_utc') or s.get('last_run_utc') or 'unknown'} UTC.",
                [{"type": "navigate", "view": "evidence"}],
                trail,
            )

        # Pure navigation ("go to compare", "open evidence page")
        page = self._page(t)
        ix = self.find_intersection(message)
        nav_verb = has("go to", "open", "show", "take me", "navigate", "switch to", "page", "tab")
        if page and not ix and nav_verb:
            view, step, tab = page
            action = {"type": "navigate", "view": view}
            if step:
                action["step"] = step
            if tab:
                action["tab"] = tab
            label = "the mcp-info-ml tab" if tab else PAGE_LABELS[view]
            return self._answer(f"Opening {label}.", [action], trail)

        if has("live", "right now", "currently", "happening now", "current incidents"):
            return await self._live(trail)

        if has("simulate", "simulation", "study", "test options", "what should we do"):
            if ix:
                return await self._study(ix, trail)
            if not has("runs", "history", "log"):
                return self._answer(
                    "Which intersection? For example: 'simulate Deerfoot Trail & Glenmore "
                    "Trail'. Or open the Intersections page and press 'Study this "
                    "intersection'.",
                    [{"type": "navigate", "view": "intersections"}],
                    trail,
                )
            runs = await self.call("list_simulation_runs", {"limit": 5}, trail)
            return self._runs(runs, trail)

        if has("forecast", "predict", "prediction", "expect", "next", "upcoming", "will there"):
            return await self._predict(message, t, quadrant, ix, trail)

        if ix and has("delay", "seconds", "how bad"):
            return await self._detail(ix, trail, focus="delay")

        if has("top", "worst", "busiest", "hotspot", "hotspots", "most", "rank", "dangerous"):
            return await self._top(t, quadrant, trail)

        if has("summary", "overview", "how many", "total", "trend", "categories"):
            return await self._summary(trail)

        if ix:
            return await self._detail(ix, trail)
        route = self.find_route(message)
        if route:
            return await self._predict(message, t, quadrant, None, trail)
        if page:
            view, step, tab = page
            action = {"type": "navigate", "view": view, **({"step": step} if step else {})}
            if tab:
                action["tab"] = tab
            return self._answer(f"Opening {PAGE_LABELS[view]}.", [action], trail)
        if quadrant:
            return await self._top(t, quadrant, trail)
        return self._help(prefix="I did not recognise a place or page in that. ")

    @staticmethod
    def _page(t):
        def has(*w):
            return any(_has(t, x) for x in w)

        if has("mcp info", "mcp-info", "ml tab", "ml details", "model details", "mcp info ml"):
            return "intersections", None, "mcp-info-ml"
        if has("evidence", "sources", "source", "references", "report"):
            return "evidence", None, None
        if has("compare", "comparison", "recommendation", "step 4"):
            return "compare", 4, None
        m = re.search(r" step (\d) ", t)
        if m and 1 <= int(m.group(1)) <= 4:
            n = int(m.group(1))
            return ("problem" if n == 1 else "compare" if n == 4 else "study"), n, None
        if has("guided", "home", "start", "problem", "wizard"):
            return "problem", 1, None
        if has("intersections", "intersection", "explorer", "map"):
            return "intersections", None, None
        return None

    def _help(self, prefix=""):
        return self._answer(
            prefix + "I answer with the same tools the MCP server exposes and can move the app "
            "for you. Try: a page ('go to compare'), a place ('open 16 Avenue & Deerfoot "
            "Trail'), a ranking ('top 5 hotspots in NE'), a forecast ('forecast Stoney Trail "
            "next 14 days with lightgbm'), 'live now', 'data status', or 'simulate <"
            "intersection>'.",
            suggestions=SUGGESTIONS,
        )

    async def _summary(self, trail):
        s = await self.call("get_disruption_summary", {}, trail)
        h = s["headline"]
        groups = sorted(h["category_groups"].items(), key=lambda kv: -kv[1])[:3]
        mix = ", ".join(f"{k} {v:,}" for k, v in groups)
        return self._answer(
            f"{h['incidents']:,} reported incidents over {h['window_days']} days "
            f"({h['incidents_per_day']} a day). {h['lane_blocking_pct']}% blocked at least one "
            f"lane; {h['at_signalized_intersection_pct']}% were within 75 m of a signal. Largest "
            f"groups: {mix}. {s['caveat']}",
            [{"type": "navigate", "view": "intersections"}],
            trail,
        )

    async def _top(self, t, quadrant, trail):
        sort = (
            "collisions"
            if _has(t, "collision") or _has(t, "collisions") or _has(t, "crash")
            else "lane_blocking"
            if _has(t, "lane") or _has(t, "blocking")
            else "recent"
            if _has(t, "recent") or _has(t, "latest")
            else "incidents"
        )
        m = re.search(r" (?:top|worst|busiest) (\d{1,2}) ", t)
        limit = max(1, min(int(m.group(1)), 20)) if m else 5
        r = await self.call(
            "search_intersections", {"quadrant": quadrant, "sort": sort, "limit": limit}, trail
        )
        items = r["items"]
        if not items:
            return self._answer("No intersections match that filter.", [], trail)
        measure = {"collisions": "collisions", "lane_blocking": "lane_blocking"}.get(
            sort, "incidents"
        )
        lines = [
            f"{n}. {i['key']}: {i[measure]} {measure.replace('_', '-')}"
            + (
                f", ~{i['incident_delay_s']:.0f} s delay per incident"
                if i.get("incident_delay_s")
                else ""
            )
            for n, i in enumerate(items, 1)
        ]
        where = f" in {quadrant}" if quadrant else ""
        top = items[0]
        return self._answer(
            f"Top {len(items)} intersections{where} by {measure.replace('_', '-')} "
            f"(of {r['total']:,}):\n" + "\n".join(lines) + f"\nOpening {top['key']}.",
            [
                {
                    "type": "navigate",
                    "view": "intersections",
                    "intersection": top["key"],
                    "quadrant": quadrant,
                }
            ],
            trail,
        )

    async def _detail(self, item, trail, focus=""):
        d = await self.call("get_intersection_details", {"key": item["key"]}, trail)
        delay = item.get("incident_delay_s")
        parts = [
            (
                f"{d['key']}: {d['incidents']} reported incidents in the window, "
                f"{d.get('collisions', 0)} collisions, {d.get('lane_blocking', 0)} lane-blocking."
            )
        ]
        if d.get("unspecified_pct") is not None:
            parts.append(f"{d['unspecified_pct']}% are 'traffic incident (unspecified)'.")
        if delay:
            parts.append(
                f"Modelled delay per lane-blocking incident: about {delay:.0f} s "
                "per vehicle (SUMO estimate)."
            )
        elif focus == "delay":
            parts.append(
                "No delay estimate is stored yet; the detail panel can run one "
                "(about 15 s of simulation)."
            )
        parts.append("Signalized." if d.get("signalized") else "No City signal recorded.")
        return self._answer(
            " ".join(parts),
            [
                {
                    "type": "navigate",
                    "view": "intersections",
                    "intersection": d["key"],
                    "tab": "detail",
                }
            ],
            trail,
            suggestions=[f"Forecast {d['key']} next 7 days", f"Simulate {d['key']}"],
        )

    async def _predict(self, message, t, quadrant, ix, trail):
        m = re.search(r" (\d{1,2}) (day|days|d) ", t)
        horizon = int(m.group(1)) if m else 14 if _has(t, "2 weeks") else 7
        if _has(t, "month") or _has(t, "4 weeks"):
            horizon = 28
        if _has(t, "tomorrow"):
            horizon = 1
        horizon = max(1, min(horizon, 28))
        model = next((x for x in ("lightgbm", "bayes", "flat") if _has(t, x)), "auto")
        args = {"horizon_days": horizon, "model": model, "quadrant": quadrant}
        label = quadrant or "citywide"
        if ix:
            road = ix["roads"][0]
            route = f"{road} {ix['quadrant']}" if road[:1].isdigit() and ix["quadrant"] else road
            args.update(intersection=ix["key"], route=route, quadrant="")
            label = ix["key"]
        else:
            route = self.find_route(message)
            if route:
                args.update(route=route)
                label = route + (f" ({quadrant})" if quadrant and quadrant not in route else "")
        if _has(t, "collision") or _has(t, "collisions") or _has(t, "crash"):
            args["category"] = "Collision"
        p = await self.call("predict_disruptions", args, trail)
        b = p.get("forecast_evaluation") or {}
        lo, hi = p["interval_80"]
        improvement = b.get("improvement_vs_baseline_pct")
        verdict = (
            f" On the last {b['test_days']} held-out days {b['label']} had "
            + (
                "the same error as the flat baseline."
                if improvement == 0
                else f"{abs(improvement)}% {'lower' if improvement > 0 else 'higher'} error "
                "than the flat baseline."
            )
            if improvement is not None
            else (
                " No comparable held-out evaluation is available for this forecast model."
                if not b
                else " The flat baseline has zero error; percentage comparison is undefined."
            )
        )
        top = p.get("top_intersections") or []
        where = f" Most likely at {top[0]['key']}." if top and not ix else ""
        low = " Low data: treat as indicative only." if p.get("low_data") else ""
        selection = {k: v for k, v in args.items() if k not in ("save",)}
        return self._answer(
            f"{label}, next {horizon} day{'s' if horizon > 1 else ''}: about "
            f"{p['expected_total']:.1f} reported incidents (80% range {lo}–{hi}), model "
            f"{p['model']['name']}.{verdict}{where}{low} {p['caveat']}",
            [
                {
                    "type": "navigate",
                    "view": "intersections",
                    "prediction": selection,
                    **({"intersection": ix["key"]} if ix else {}),
                }
            ],
            trail,
        )

    async def _live(self, trail):
        live = await self.call("get_live_disruptions", {}, trail)
        incidents = live.get("incidents") or []
        closures = live.get("active_closures") or []
        linked = [i for i in incidents if i.get("hotspot")]
        lines = [
            f"- {i.get('location_text') or 'Unknown location'}"
            + (f" (near {i['hotspot']['key']})" if i.get("hotspot") else "")
            for i in incidents[:5]
        ]
        actions = [{"type": "navigate", "view": "intersections"}]
        if linked:
            actions[0]["intersection"] = linked[0]["hotspot"]["key"]
        stale = "" if live.get("ok", True) else " (City feed failed; showing last good copy)"
        return self._answer(
            f"Live from the City{stale}: {len(incidents)} active incidents and "
            f"{len(closures)} active closures ({live.get('active_closures_at_hotspots', 0)} at "
            "historic hotspots).\n" + "\n".join(lines),
            actions,
            trail,
        )

    async def _study(self, item, trail):
        s = await self.call("build_intersection_study", {"key": item["key"]}, trail)
        e = s.get("evidence", {})
        return self._answer(
            f"Built a study for {item['key']} from {e.get('incidents', '?')} incidents over "
            f"{e.get('observed_days', '?')} days ({e.get('lane_blocking_pct', '?')}% "
            "lane-blocking). Opening guided step 2 with these inputs; press Run simulation "
            "to test the options.",
            [{"type": "study", "intersection": item["key"]}],
            trail,
        )

    def _runs(self, runs, trail):
        items = runs.get("runs") or []
        if not items:
            return self._answer("No simulation runs are stored yet.", [], trail)
        lines = [
            f"- {(r.get('created_utc') or '')[:16]} {r.get('intersection_key') or 'default corridor'}"
            f": {r['status']}, recommended {r.get('recommended_id') or '-'}"
            for r in items
        ]
        return self._answer("Recent simulation runs:\n" + "\n".join(lines), [], trail)

    # Claude mode ---------------------------------------------------------------------
    async def claude(self, message, history):
        if self.model_factory is None:
            raise RuntimeError("Chat model is not configured")
        client: ChatModel = self.model_factory()
        tools = [*await self.tool_schemas(), NAVIGATE_TOOL]
        messages = [
            {"role": h["role"], "content": str(h["content"])[:4000]}
            for h in history[-HISTORY_TURNS:]
            if h.get("role") in ("user", "assistant") and h.get("content")
        ]
        # The API needs alternating turns that start with the user.
        while messages and messages[0]["role"] != "user":
            messages.pop(0)
        messages.append({"role": "user", "content": message})
        trail, actions = [], []
        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.complete(system=SYSTEM_PROMPT, tools=tools, messages=messages)
            if response.stop_reason == "refusal":
                raise RuntimeError("request declined")
            uses = [b for b in response.content if b["type"] == "tool_use"]
            if response.stop_reason != "tool_use" or not uses:
                text = "".join(b["text"] for b in response.content if b["type"] == "text").strip()
                return self._answer(text or "Done.", actions, trail, mode="claude")
            messages.append({"role": "assistant", "content": response.content})
            results = []
            for use in uses:
                try:
                    if use["name"] == NAVIGATE_TOOL["name"]:
                        action = _navigate_action(use["input"])
                        actions.append(action)
                        content = json.dumps({"ok": True, "action": action})
                    else:
                        out = await self.call(use["name"], dict(use["input"] or {}), trail)
                        content = json.dumps(out, default=str)[:60000]
                    results.append(
                        {"type": "tool_result", "tool_use_id": use["id"], "content": content}
                    )
                except Exception as error:  # noqa: BLE001 - returned to the model
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": use["id"],
                            "is_error": True,
                            "content": f"{type(error).__name__}: {error}",
                        }
                    )
            messages.append({"role": "user", "content": results})
        return self._answer(
            "I stopped after several tool calls; please narrow the question.",
            actions,
            trail,
            mode="claude",
        )


def _navigate_action(args):
    view = args.get("view")
    if view not in VIEWS and args.get("study_intersection"):
        view = "study"
    if args.get("study_intersection"):
        return {"type": "study", "intersection": args["study_intersection"]}
    if view not in VIEWS:
        raise ValueError(f"view must be one of {VIEWS}")
    action = {"type": "navigate", "view": view}
    for key in ("step", "intersection", "quadrant", "tab", "prediction", "area"):
        if args.get(key) not in (None, "", {}):
            action[key] = args[key]
    return action


NAVIGATE_TOOL = {
    "name": "navigate_ui",
    "description": (
        "Move the user's Bottleneck Busters app. Use it whenever the user asks to go to, "
        "open or show something, and after answering about a specific intersection, area or "
        "forecast so they can see it. Pages: problem (guided study step 1), study (steps 2-3),"
        " compare (step 4 recommendation), intersections (map, list, detail, prediction "
        "panel, mcp-info-ml tab), evidence (sources and data). study_intersection builds a "
        "SUMO study for that intersection key and opens step 2."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "view": {"type": "string", "enum": list(VIEWS)},
            "step": {"type": "integer", "minimum": 1, "maximum": 4},
            "intersection": {"type": "string", "description": "Intersection key to open"},
            "quadrant": {"type": "string", "enum": ["", *QUADRANTS]},
            "tab": {"type": "string", "enum": ["detail", "mcp-info-ml"]},
            "prediction": {
                "type": "object",
                "description": "Prediction panel selection (same fields as "
                "predict_disruptions: quadrant, route, direction, lane, category, "
                "intersection, horizon_days, model, lat, lon, radius_m)",
            },
            "area": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "radius_m": {"type": "number"},
                    "label": {"type": "string"},
                },
                "required": ["lat", "lon"],
            },
            "study_intersection": {"type": "string"},
        },
    },
}

SYSTEM_PROMPT = """\
You are the assistant inside Bottleneck Busters, a Calgary traffic planning app. Answer \
with the tools: they read the app's database of City of Calgary Open Data (reported \
incidents, closures, travel times, signals, cameras) and its forecasts and SUMO studies. \
Never invent numbers; if a tool cannot answer, say so. Counts are reported disruptions, \
not traffic flow, delay or crash risk: pass that caveat on with any count or forecast, \
and quote forecast_evaluation with any forecast. Its scores belong to the actual forecast \
model; backtest describes automatic validation selection. If forecast_evaluation is null, \
state that comparable held-out evidence is unavailable; never substitute another model's \
scores. Resolve place names with \
search_intersections or get_prediction_options before using them as keys. When the user \
wants to see something, or your answer concerns one intersection, area or forecast, call \
navigate_ui so the app shows it. Keep replies short: two to five sentences, or a short \
list for rankings."""
