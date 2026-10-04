"""Optional Claude adapter. Credentials and SDK objects stay outside application."""

import os

from app.application.ports import ChatResponse


def chat_mode():
    mode = os.environ.get("BB_CHAT_MODE", "auto").lower()
    if mode == "claude" or (mode == "auto" and os.environ.get("ANTHROPIC_API_KEY")):
        return "claude"
    return "builtin"


class AnthropicChatModel:
    def __init__(self, model="claude-opus-5-5"):
        self.model = model
        self._client = None

    async def complete(self, *, system, tools, messages):
        import anthropic

        if self._client is None:
            self._client = anthropic.AsyncAnthropic()
        response = await self._client.beta.messages.create(
            model=self.model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=system,
            tools=tools,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        content = [
            block.model_dump(mode="json") if hasattr(block, "model_dump") else vars(block)
            for block in response.content
        ]
        return ChatResponse(response.stop_reason, content)
