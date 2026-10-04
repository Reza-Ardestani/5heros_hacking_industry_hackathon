"""Optional ElevenLabs voice for the chat: text-to-speech replies and speech-to-text questions.

Enabled only when ELEVENLABS_API_KEY (or ELEVEN_LABS_KEY) is set on the server; the key
never reaches the browser. Optional: ELEVENLABS_VOICE_ID (default: a stock ElevenLabs
voice), ELEVENLABS_MODEL (text-to-speech, default: a low-latency model) and
ELEVENLABS_STT_MODEL (speech-to-text). Uses the standard library HTTP client, so no new
dependency.
"""

import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TTS_API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
STT_API = "https://api.elevenlabs.io/v1/speech-to-text"
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Rachel", a premade ElevenLabs voice
DEFAULT_MODEL = "eleven_flash_v2_5"
DEFAULT_STT_MODEL = "scribe_v1"
MAX_CHARS = 1500  # chat replies are short; this caps cost per click
MAX_AUDIO_BYTES = 5_000_000  # about a minute of browser-recorded speech
TIMEOUT_S = 30


class SpeechUnavailable(RuntimeError):
    """No key configured: the UI hides the speaker and microphone buttons."""


class SpeechFailed(RuntimeError):
    """ElevenLabs rejected the request or could not be reached."""


def _key() -> str | None:
    # ELEVEN_LABS_KEY is accepted too: it is a natural name for the Codespaces secret.
    return os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_LABS_KEY")


def _require_key() -> str:
    key = _key()
    if not key:
        raise SpeechUnavailable("Set ELEVENLABS_API_KEY on the server to enable speech")
    return key


def available() -> bool:
    return bool(_key())


def info() -> dict:
    return {
        "available": available(),
        "provider": "ElevenLabs",
        "voice_id": os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE),
        "model": os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL),
        "stt_model": os.environ.get("ELEVENLABS_STT_MODEL", DEFAULT_STT_MODEL),
        "max_chars": MAX_CHARS,
        "max_audio_bytes": MAX_AUDIO_BYTES,
    }


def _send(request: Request, opener) -> bytes:
    try:
        with opener(request, timeout=TIMEOUT_S) as response:
            return response.read()
    except HTTPError as error:
        # ElevenLabs explains failures (bad key, quota, unknown voice) in a JSON body.
        try:
            detail = json.loads(error.read()).get("detail")
            message = detail.get("message") if isinstance(detail, dict) else detail
        except (ValueError, AttributeError):
            message = None
        raise SpeechFailed(
            f"ElevenLabs returned {error.code}: {message or error.reason}"
        ) from error
    except (URLError, TimeoutError) as error:
        raise SpeechFailed(f"Could not reach ElevenLabs: {error}") from error


def synthesize(text: str, opener=urlopen) -> bytes:
    """Return MP3 audio for `text` (trimmed to MAX_CHARS)."""
    key = _require_key()
    text = " ".join(text.split())[:MAX_CHARS]
    if not text:
        raise ValueError("Nothing to speak")
    request = Request(
        TTS_API.format(voice=os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE)),
        data=json.dumps(
            {"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL)}
        ).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST",
    )
    return _send(request, opener)


def transcribe(audio: bytes, content_type: str, opener=urlopen) -> str:
    """Return the text spoken in `audio` (a short browser recording, e.g. audio/webm)."""
    key = _require_key()
    if not audio:
        raise ValueError("No audio received")
    if len(audio) > MAX_AUDIO_BYTES:
        raise ValueError("Recording is too long; keep questions under about a minute")
    mime = (content_type or "audio/webm").split(";")[0].strip() or "audio/webm"
    extension = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a",
                 "audio/mpeg": "mp3", "audio/wav": "wav"}.get(mime, "webm")  # fmt: skip
    boundary = uuid.uuid4().hex
    model = os.environ.get("ELEVENLABS_STT_MODEL", DEFAULT_STT_MODEL)
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="model_id"\r\n\r\n{model}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="question.{extension}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode()
        + audio
        + f"\r\n--{boundary}--\r\n".encode()
    )
    request = Request(
        STT_API,
        data=body,
        headers={
            "xi-api-key": key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        result = json.loads(_send(request, opener))
    except ValueError as error:
        raise SpeechFailed("ElevenLabs returned an unreadable transcription") from error
    return " ".join(str(result.get("text", "")).split())
