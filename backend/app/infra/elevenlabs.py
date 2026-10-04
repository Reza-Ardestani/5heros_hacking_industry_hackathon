"""Optional ElevenLabs text-to-speech for spoken chat replies.

Enabled only when ELEVENLABS_API_KEY is set on the server; the key never reaches the
browser. Optional: ELEVENLABS_VOICE_ID (default: a stock ElevenLabs voice) and
ELEVENLABS_MODEL (default: a low-latency model). Uses the standard library HTTP client,
so no new dependency.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Rachel", a premade ElevenLabs voice
DEFAULT_MODEL = "eleven_flash_v2_5"
MAX_CHARS = 1500  # chat replies are short; this caps cost per click
TIMEOUT_S = 30


class SpeechUnavailable(RuntimeError):
    """No key configured: the UI hides the speaker button."""


class SpeechFailed(RuntimeError):
    """ElevenLabs rejected the request or could not be reached."""


def _key() -> str | None:
    # ELEVEN_LABS_KEY is accepted too: it is a natural name for the Codespaces secret.
    return os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_LABS_KEY")


def available() -> bool:
    return bool(_key())


def info() -> dict:
    return {
        "available": available(),
        "provider": "ElevenLabs",
        "voice_id": os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE),
        "model": os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL),
        "max_chars": MAX_CHARS,
    }


def synthesize(text: str, opener=urlopen) -> bytes:
    """Return MP3 audio for `text` (trimmed to MAX_CHARS)."""
    key = _key()
    if not key:
        raise SpeechUnavailable("Set ELEVENLABS_API_KEY on the server to enable speech")
    text = " ".join(text.split())[:MAX_CHARS]
    if not text:
        raise ValueError("Nothing to speak")
    request = Request(
        API.format(voice=os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE)),
        data=json.dumps(
            {"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL)}
        ).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST",
    )
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
