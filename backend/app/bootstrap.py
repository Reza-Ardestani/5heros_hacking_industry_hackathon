"""Shared composition root for HTTP, MCP and command-line entry points."""

from importlib.metadata import PackageNotFoundError, version

from app.application import disruptions
from app.application.assistant import Assistant
from app.application.dependencies import DisruptionDependencies
from app.domain import ml_forecast
from app.infra import city_open_data
from app.infra import ml_forecast as ml_adapter
from app.infra.chat_model import AnthropicChatModel, chat_mode
from app.infra.disruption_seed import seed_from_exports
from app.infra.disruption_store import ROOT, Store
from app.infra.tool_gateway import McpToolGateway


def configure_services():
    """Idempotent configuration; never replace a test/operator-selected store."""
    if disruptions.is_configured():
        return
    analysis = ROOT / "data" / "analysis"
    disruptions.configure(
        DisruptionDependencies(
            store_factory=Store,
            seed_store=lambda store: seed_from_exports(store, analysis),
            fetch_city=lambda key, params=None: city_open_data.fetch(key, params),
            get_json=lambda url: city_open_data.get_json(url, timeout=10, attempts=1),
            analysis_dir=analysis,
        )
    )
    try:
        library_version = version("lightgbm")
    except PackageNotFoundError:
        library_version = None
    ml_forecast.configure(ml_adapter.LightGBMForecaster, ml_adapter.available, library_version)


def create_assistant():
    configure_services()

    def server_factory():
        from app.mcp_server import build_server

        return build_server()

    return Assistant(
        tools=McpToolGateway(server_factory),
        model_factory=AnthropicChatModel,
        mode_selector=chat_mode,
    )
