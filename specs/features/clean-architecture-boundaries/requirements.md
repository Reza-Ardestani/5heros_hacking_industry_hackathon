# Clean architecture boundaries

Status: settled. User authorized a fast behavior-preserving refactor October 4, 2026.

- Domain and application must not import infrastructure, HTTP/MCP adapters or provider SDKs.
- Application coordinates injected storage, City data, tools and chat model ports.
- Infrastructure owns filesystem persistence, export seeding, SUMO and provider SDKs.
- Compose shared dependencies at API, MCP and CLI entry points.
- Preserve API/MCP responses, forecast selection, simulation outputs, offline seeding, storage fallback and chat behavior.
- Keep Pydantic scenario contracts and existing process-local caches/jobs for hackathon speed. No frontend rewrite, schema change, deployment or submission.
