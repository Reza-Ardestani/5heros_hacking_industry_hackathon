"""Normalize MCP SDK results before crossing the application boundary."""

import json


class McpToolGateway:
    def __init__(self, server_factory):
        self.server_factory = server_factory
        self._server = None

    @property
    def server(self):
        if self._server is None:
            self._server = self.server_factory()
        return self._server

    async def call(self, name, arguments):
        blocks = await self.server.call_tool(name, arguments)
        if isinstance(blocks, tuple):
            blocks = blocks[0]
        text = "".join(getattr(block, "text", "") for block in blocks)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    async def schemas(self):
        return [
            {
                "name": tool.name,
                "description": " ".join((tool.description or "").split()),
                "input_schema": tool.inputSchema,
            }
            for tool in await self.server.list_tools()
        ]
