#!/usr/bin/env python3
"""Run the whole app locally on any OS (no `make` needed): API + UI + MCP server.

    python scripts/dev.py            # start all three; Ctrl+C stops them
    python scripts/dev.py --check    # start, verify every endpoint, stop (exit 1 on failure)

Defaults: UI http://localhost:5173, API http://127.0.0.1:8008, MCP (streamable HTTP,
stateless) http://127.0.0.1:8000/mcp with its self-description at /mcp-info.
Requires uv and Node.js/npm on PATH. Installs dependencies on first run.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
# Server logs contain non-ASCII (e.g. Vite's arrow); never let the console encoding crash us.
for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding="utf-8", errors="replace")


def tool(name):
    path = shutil.which(name) or (shutil.which(f"{name}.cmd") if WINDOWS else None)
    if not path:
        sys.exit(f"'{name}' is not on PATH; install it first (see README.md).")
    return path


def http(url, data=None, timeout=10, accept="application/json, text/event-stream"):
    # Vite only serves index.html to requests that accept HTML, so page checks pass "text/html".
    headers = {"Accept": accept}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    with urlopen(Request(url, data=data, headers=headers), timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


def wait_for(name, url, deadline):
    while time.time() < deadline:
        try:
            http(url, timeout=5, accept="text/html,application/json,*/*")
            return True
        except HTTPError as error:  # any HTTP answer means the server is up
            if error.code < 500:
                return True
        except (URLError, OSError):
            pass
        time.sleep(1)
    print(f"[dev] {name} did not become ready at {url}", flush=True)
    return False


def pump(prefix, stream):
    for line in iter(stream.readline, ""):
        print(f"[{prefix}] {line.rstrip()}", flush=True)


def start(prefix, args, env=None, quiet=False):
    kwargs = {"cwd": ROOT, "env": {**os.environ, **(env or {})}, "text": True,
              "stdout": subprocess.PIPE, "stderr": subprocess.STDOUT,
              "encoding": "utf-8", "errors": "replace"}  # fmt: skip
    if WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(args, **kwargs)
    target = pump if not quiet else (lambda p, s: [None for _ in iter(s.readline, "")])
    threading.Thread(target=target, args=(prefix, proc.stdout), daemon=True).start()
    return proc


def stop(procs):
    for proc in procs:
        if proc.poll() is not None:
            continue
        if WINDOWS:  # npm/uv spawn children; kill the whole tree
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, check=False)  # fmt: skip
        else:
            os.killpg(proc.pid, signal.SIGTERM)


def check(api, web, mcp):
    """Verify UI, API, MCP streamable HTTP and mcp-info. Returns True if all pass."""
    results = []

    def record(name, fn):
        try:
            detail = fn()
            results.append((name, True, detail))
        except Exception as error:  # noqa: BLE001 - report every failure
            results.append((name, False, f"{type(error).__name__}: {error}"))

    def ui():
        status, body = http(f"{web}/", accept="text/html")
        assert status == 200 and '<div id="root">' in body, "index.html not served"
        status, _ = http(f"{web}/api/health")  # through the Vite proxy
        assert status == 200
        return "index.html served; /api proxied to the API"

    def api_health():
        status, _ = http(f"{api}/api/health")
        assert status == 200
        summary = json.loads(http(f"{api}/api/disruptions/summary", timeout=60)[1])
        return f"health ok; {summary['headline']['incidents']} incidents in the database"

    def mcp_protocol():
        init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "dev-check", "version": "1"}}}  # fmt: skip
        server = json.loads(http(f"{mcp}/mcp", init)[1])["result"]["serverInfo"]
        tools = json.loads(
            http(f"{mcp}/mcp", {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})[1]
        )
        call = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "predict_disruptions", "arguments": {"route": "Stoney Trail", "save": False}}}  # fmt: skip
        forecast = json.loads(
            json.loads(http(f"{mcp}/mcp", call, timeout=60)[1])["result"]["content"][0]["text"]
        )
        return (f"{server['name']}: {len(tools['result']['tools'])} tools over streamable HTTP; "
                f"predict_disruptions -> {forecast['expected_total']} expected")  # fmt: skip

    def mcp_info():
        info = json.loads(http(f"{mcp}/mcp-info?check=true", timeout=120)[1])
        s = info["summary"]
        assert s["self_check_errors"] == 0, info
        return (
            f"{s['tools']} tools described; self-check {s['self_check_ok']} ok, "
            f"{s['self_check_not_run']} not run"
        )

    def api_mcp_info():
        info = json.loads(http(f"{api}/api/mcp-info", timeout=60)[1])
        assert info["reachable"], info
        return f"API mirror reachable -> {info['probed_url']}"

    for name, fn in [("UI", ui), ("API", api_health), ("MCP streamable HTTP", mcp_protocol),
                     ("MCP /mcp-info", mcp_info), ("API /api/mcp-info", api_mcp_info)]:  # fmt: skip
        record(name, fn)
    for name, ok, detail in results:
        print(f"[check] {'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    return all(ok for _, ok, _ in results)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--api-port", type=int, default=8008)
    ap.add_argument("--web-port", type=int, default=5173)
    ap.add_argument("--mcp-port", type=int, default=8000)
    ap.add_argument("--no-mcp", action="store_true", help="start only the API and UI")
    ap.add_argument("--check", action="store_true", help="verify all endpoints, then stop")
    ap.add_argument("--quiet", action="store_true", help="hide server logs")
    args = ap.parse_args()
    uv, npm = tool("uv"), tool("npm")

    print("[dev] installing/checking dependencies ...", flush=True)
    subprocess.run([uv, "sync", "--frozen", "--group", "mcp"], cwd=ROOT / "backend", check=True)
    if not (ROOT / "frontend" / "node_modules").exists():
        subprocess.run([npm, "ci", "--no-audit", "--no-fund"], cwd=ROOT / "frontend", check=True)

    api = f"http://127.0.0.1:{args.api_port}"
    mcp = f"http://127.0.0.1:{args.mcp_port}"
    web = f"http://127.0.0.1:{args.web_port}"  # Vite binds 127.0.0.1 (frontend/package.json)
    run = [uv, "run", "--directory", "backend", "--group", "mcp"]
    quiet = args.quiet
    procs = [
        start("api", [*run, "uvicorn", "app.api:app", "--host", "127.0.0.1", "--port", str(args.api_port)],
              {"BB_MCP_URL": mcp}, quiet),
        start("web", [npm, "--prefix", "frontend", "run", "dev", "--", "--port", str(args.web_port)],
              {"API_URL": api}, quiet),
    ]  # fmt: skip
    if not args.no_mcp:
        procs.append(start("mcp", [*run, "python", "-m", "app.mcp_server", "--transport",
                                   "streamable-http", "--host", "127.0.0.1", "--port",
                                   str(args.mcp_port)], None, quiet))  # fmt: skip
    try:
        deadline = time.time() + 180
        ready = wait_for("API", f"{api}/api/health", deadline) and wait_for("UI", web, deadline)
        if not args.no_mcp:
            ready = ready and wait_for("MCP", f"{mcp}/mcp-info", deadline)
        if not ready:
            return 1
        print(
            "\n[dev] ready:\n"
            f"  UI                 {web}\n"
            f"  API docs           {api}/docs\n"
            + ("" if args.no_mcp else
               f"  MCP endpoint       {mcp}/mcp   (streamable HTTP, stateless)\n"
               f"  MCP info           {mcp}/mcp-info   (add ?check=true for a live self-test)\n"
               f"  MCP info via API   {api}/api/mcp-info\n"
               f"  Connect Claude     claude mcp add --transport http calgary-disruptions {mcp}/mcp\n"),
            flush=True,
        )  # fmt: skip
        if args.check:
            return 0 if check(api, web, mcp if not args.no_mcp else None) else 1
        print("[dev] Ctrl+C to stop", flush=True)
        while all(p.poll() is None for p in procs):
            time.sleep(1)
        print("[dev] a server exited; stopping the others", flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        stop(procs)


if __name__ == "__main__":
    sys.exit(main())
