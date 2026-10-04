"""The smoke checker must respect which services the launcher starts."""

import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest


@pytest.fixture
def launcher():
    path = Path(__file__).resolve().parents[2] / "scripts" / "dev.py"
    spec = importlib.util.spec_from_file_location("dev_launcher", path)
    module = importlib.util.module_from_spec(spec)
    # The CLI configures terminal encoding at import; give it real text streams.
    with (
        io.TextIOWrapper(io.BytesIO()) as out,
        io.TextIOWrapper(io.BytesIO()) as err,
        redirect_stdout(out),
        redirect_stderr(err),
    ):
        spec.loader.exec_module(module)
    return module


def install_http(launcher, monkeypatch):
    calls = []
    responses = {
        "http://web/": '<div id="root"></div>',
        "http://web/api/health": '{}',
        "http://api/api/health": '{}',
        "http://api/api/disruptions/summary": json.dumps({"headline": {"incidents": 7}}),
    }

    def http(url, *args, **kwargs):
        calls.append(url)
        if url not in responses:
            raise ConnectionError("Service is unavailable")
        return 200, responses[url]

    monkeypatch.setattr(launcher, "http", http)
    return calls


def test_check_without_mcp_requires_only_running_api_and_ui(launcher, monkeypatch):
    calls = install_http(launcher, monkeypatch)
    assert launcher.check("http://api", "http://web", None)
    assert set(calls) == {
        "http://web/",
        "http://web/api/health",
        "http://api/api/health",
        "http://api/api/disruptions/summary",
    }


def test_check_with_unavailable_mcp_fails_even_when_api_and_ui_work(launcher, monkeypatch):
    calls = install_http(launcher, monkeypatch)
    assert not launcher.check("http://api", "http://web", "http://mcp")
    assert "http://mcp/mcp" in calls
    assert "http://mcp/mcp-info?check=true" in calls
    assert "http://api/api/mcp-info" in calls
