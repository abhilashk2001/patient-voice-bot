"""Fetch and download the Twilio call recording as mp3 (Phase 06, FR9).

Twilio serves recordings as mp3 directly (append `.mp3` to the recording URL),
so no ffmpeg/transcoding is needed. Recordings can take a few seconds to finalize
after a call ends, so `save_recording` polls a few times.
"""
import base64
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from utils import ensure_dir, read_json, write_json

PathLike = Any

TWILIO_RECORDING_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Recordings/{rec}.{ext}"


def build_recording_url(account_sid: str, recording_sid: str, ext: str = "mp3") -> str:
    """Build the media URL for a recording (mp3 by default)."""
    return TWILIO_RECORDING_URL.format(sid=account_sid, rec=recording_sid, ext=ext)


def fetch_recording(client: Any, call_sid: str) -> Optional[Any]:
    """Return the first recording object for a call, or None if none exists yet."""
    recordings = client.recordings.list(call_sid=call_sid, limit=1)
    return recordings[0] if recordings else None


def fetch_recording_sid(client: Any, call_sid: str) -> Optional[str]:
    """Return the SID of the recording for a call, or None if not available yet."""
    rec = fetch_recording(client, call_sid)
    return rec.sid if rec else None


def _default_http_get(url: str, auth: Tuple[str, str]) -> bytes:  # pragma: no cover - network
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def save_recording(
    client: Any,
    call_sid: str,
    dest_path: PathLike,
    *,
    account_sid: str,
    auth_token: str,
    http_get: Callable[[str, Tuple[str, str]], bytes] = _default_http_get,
    retries: int = 10,
    delay: float = 3.0,
) -> bool:
    """Download the call's recording to ``dest_path`` as mp3. Returns success.

    Polls up to ``retries`` times (Twilio finalizes recordings a few seconds
    after the call ends). Best-effort: returns False if none is found.
    """
    dest = Path(dest_path)
    for attempt in range(retries):
        rec = fetch_recording(client, call_sid)
        # Only download once the recording has finalized; the .mp3 media 404s
        # while it is still processing. (Fakes without a status are treated as ready.)
        if rec and getattr(rec, "status", "completed") == "completed":
            try:
                data = http_get(build_recording_url(account_sid, rec.sid), (account_sid, auth_token))
                ensure_dir(dest.parent)
                dest.write_bytes(data)
                return True
            except Exception:  # media not downloadable yet — keep polling
                pass
        if attempt < retries - 1:
            time.sleep(delay)
    return False


def fetch_missing_recordings(
    output_dir: str,
    client: Any,
    *,
    account_sid: str,
    auth_token: str,
    http_get: Callable[[str, Tuple[str, str]], bytes] = _default_http_get,
    retries: int = 6,
    delay: float = 3.0,
) -> int:
    """Download recordings for any call folder missing one. Returns count saved.

    Scans ``output_dir`` for call folders whose metadata.json has no
    ``recording_file`` but does have a ``call_sid``; downloads and updates
    metadata. Run after a batch of calls to grab slow-to-finalize recordings.
    """
    saved = 0
    for meta_path in sorted(Path(output_dir).glob("*/metadata.json")):
        meta = read_json(meta_path)
        if meta.get("recording_file") or not meta.get("call_sid"):
            continue
        dest = meta_path.parent / "recording.mp3"
        if save_recording(
            client, meta["call_sid"], dest,
            account_sid=account_sid, auth_token=auth_token,
            http_get=http_get, retries=retries, delay=delay,
        ):
            meta["recording_file"] = "recording.mp3"
            write_json(meta_path, meta)
            saved += 1
    return saved
