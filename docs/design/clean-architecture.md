# Clean architecture boundaries

The backend keeps its modular monolith and existing endpoints. Domain rules and
application use cases have no imports of infrastructure, FastAPI, MCP, Anthropic,
LightGBM, SQL drivers or network clients. `app/bootstrap.py` composes concrete
adapters for the API, MCP server and CLI entry points.

- `application/ports.py`: persistence, simulator, tool gateway, chat model and
  City fetch/raw export contracts. `application/dependencies.py` supplies dependencies
  to the existing process-local disruption service.
- `infra/disruption_seed.py` and `infra/simulation_log.py`: offline export seeding
  and simulation recording; `infra/raw_sink.py`: optional raw dataset files.
- `infra/tool_gateway.py`: normalizes MCP SDK content to dictionaries.
- `infra/chat_model.py`: owns Claude configuration, client and SDK response conversion.
- `domain/ml_forecast.py`: forecast settings and injected forecaster contract;
  `infra/ml_forecast.py`: unchanged LightGBM numerical implementation.
- `domain/city_catalog.py`: shared dataset identifiers and attribution, without IO.

`make architecture` checks import direction and direct filesystem IO. Backend tests
also import all inner modules in a fresh process without loading outer adapters,
and execute the assistant through fake tool/model ports. This is a source guard,
not a proof of every possible dynamic dependency or runtime behavior.

Intentional hackathon compromises: Pydantic scenario contracts remain in domain;
forecaster registration and disruption caches remain process-local; job execution
uses the existing thread pool. Frontend now uses [feature-owned vertical slices](frontend-vertical-slices.md).
No claim of a fully framework-free backend domain.

[Requirements](../../specs/features/clean-architecture-boundaries/requirements.md),
[validation evidence](../../specs/features/clean-architecture-boundaries/progress.md).
