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


def test_transcribe_posts_multipart_audio_and_returns_text(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    seen = {}

    def opener(request, timeout):
        seen.update(
            url=request.full_url, ctype=request.get_header("Content-type"), body=request.data
        )
        return FakeResponse(json.dumps({"text": "  Where should we\nstudy first? "}).encode())

    text = elevenlabs.transcribe(b"WEBM-AUDIO", "audio/webm;codecs=opus", opener)
    assert text == "Where should we study first?"
    assert seen["url"].endswith("/v1/speech-to-text")
    assert seen["ctype"].startswith("multipart/form-data; boundary=")
    assert b'name="model_id"' in seen["body"] and b"scribe_v1" in seen["body"]
    assert b'filename="question.webm"' in seen["body"] and b"WEBM-AUDIO" in seen["body"]


def test_transcribe_endpoint_handles_no_key_empty_and_ok(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_LABS_KEY", raising=False)
    headers = {"Content-Type": "audio/webm"}
    assert client.post("/api/speech/transcribe", content=b"x", headers=headers).status_code == 503
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    assert client.post("/api/speech/transcribe", content=b"", headers=headers).status_code == 422
    monkeypatch.setattr(
        elevenlabs, "transcribe", lambda audio, ctype: f"{len(audio)} bytes {ctype}"
    )
    r = client.post("/api/speech/transcribe", content=b"abcd", headers=headers)
    assert r.status_code == 200 and r.json() == {"text": "4 bytes audio/webm"}
