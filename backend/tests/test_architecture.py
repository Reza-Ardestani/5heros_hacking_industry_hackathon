"""Enforce boundaries and exercise use cases with provider-independent adapters."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from app.application.assistant import Assistant
from app.application.ports import ChatResponse

CHECKER = Path(__file__).resolve().parents[2] / "scripts" / "check_architecture.py"
spec = importlib.util.spec_from_file_location("architecture", CHECKER)
architecture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(architecture)


def test_architecture_gate_checks_code_and_rejects_outer_dependencies():
    assert architecture.check() == []
    assert architecture.violations("from app.infra import simulation", "application")
    assert architecture.violations("from ..infra import simulation", "application")
    assert architecture.violations("from app import api", "domain")
    assert architecture.violations("from app.application import jobs", "domain")
    assert architecture.violations("import anthropic", "application")
    assert architecture.violations("path.write_text('data')", "application")


def test_inner_modules_import_without_loading_outer_adapters():
    code = """
import importlib
import pathlib
import sys
for layer in ('domain', 'application'):
    for path in pathlib.Path('app', layer).glob('*.py'):
        importlib.import_module(f'app.{layer}.{path.stem}')
assert not any(name.startswith(('app.infra', 'app.api', 'app.mcp_server', 'app.bootstrap'))
               for name in sys.modules)
assert not {'anthropic', 'mcp', 'lightgbm', 'fastapi', 'psycopg'} & sys.modules.keys()
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=CHECKER.parents[1] / "backend",
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.anyio
async def test_assistant_accepts_neutral_ports_and_blocks_prediction_writes():
    class Tools:
        def __init__(self):
            self.calls = []

        async def schemas(self):
            return [{"name": "predict_disruptions"}, {"name": "collect_latest_data"}]

        async def call(self, name, arguments):
            self.calls.append((name, arguments))
            return {"expected": 3}

    class Model:
        def __init__(self):
            self.calls = 0

        async def complete(self, *, system, tools, messages):
            self.calls += 1
            assert [tool["name"] for tool in tools] == ["predict_disruptions", "navigate_ui"]
            if self.calls == 1:
                return ChatResponse(
                    "tool_use",
                    [
                        {
                            "type": "tool_use",
                            "id": "p1",
                            "name": "predict_disruptions",
                            "input": {"save": True},
                        }
                    ],
                )
            assert messages[-1]["content"][0]["tool_use_id"] == "p1"
            return ChatResponse("end_turn", [{"type": "text", "text": "Three expected."}])

    tools, model = Tools(), Model()
    assistant = Assistant(tools, model_factory=lambda: model, mode_selector=lambda: "claude")
    result = await assistant.reply("forecast")
    assert result["reply"] == "Three expected."
    assert tools.calls == [("predict_disruptions", {"save": False})]
