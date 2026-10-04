import io
import json
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.infra import elevenlabs


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_speech_is_off_without_a_key(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_LABS_KEY", raising=False)
    client = TestClient(app)
    assert client.get("/api/speech/info").json()["available"] is False
    r = client.post("/api/speech", json={"text": "Hello"})
    assert r.status_code == 503 and "ELEVENLABS_API_KEY" in r.json()["detail"]


def test_synthesize_sends_key_voice_and_trimmed_text(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice123")
    seen = {}

    def opener(request, timeout):
        seen.update(url=request.full_url, headers=dict(request.header_items()),
                    body=json.loads(request.data), timeout=timeout)  # fmt: skip
        return FakeResponse(b"ID3-mp3-bytes")

    audio = elevenlabs.synthesize("  Deerfoot   Trail:\n58 expected " + "x" * 5000, opener)
    assert audio == b"ID3-mp3-bytes"
    assert "/text-to-speech/voice123" in seen["url"]
    assert seen["headers"]["Xi-api-key"] == "test-key"
    assert seen["body"]["text"].startswith("Deerfoot Trail: 58 expected")
    assert len(seen["body"]["text"]) == elevenlabs.MAX_CHARS
    assert seen["body"]["model_id"] == elevenlabs.DEFAULT_MODEL


def test_elevenlabs_errors_are_reported_not_raised_raw(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "bad-key")
    body = json.dumps({"detail": {"message": "Invalid API key"}}).encode()

    def opener(request, timeout):
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(body))

    with pytest.raises(elevenlabs.SpeechFailed, match="401: Invalid API key"):
        elevenlabs.synthesize("Hello", opener)


def test_speech_endpoint_returns_mp3(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(elevenlabs, "synthesize", lambda text: b"mp3:" + text.encode())
    r = TestClient(app).post("/api/speech", json={"text": "Top hotspot"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg"
    assert r.content == b"mp3:Top hotspot"


def test_eleven_labs_key_is_accepted_as_an_alternative_name(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("ELEVEN_LABS_KEY", "alt-key")
    assert elevenlabs.available()
